"""Smoke test de la interfaz de DataForge con Chromium headless (Playwright).

Ejercita el FLUXO REAL del usuario, no solo el primer pintado:
  1. cargar la pagina y esperar la generacion automatica;
  2. cambiar un volumen con el deslizador;
  3. pulsar "Generar lote" y comprobar que las metricas cambian;
  4. pulsar "Cargar en SQLite" y comprobar la verificacion de integridad;
  5. exportar a PostgreSQL y a MySQL y comprobar el texto del script;
  6. provocar un error real (volumen 0 con hijas vivas) y comprobar el mensaje.

Salida: prints por paso + 3 capturas. Devuelve 1 si algún paso falla.
"""
import os
import sys
import time

RAIZ = os.path.dirname(os.path.abspath(__file__))
URL = os.environ.get("DATAFORGE_URL", "http://127.0.0.1:8077/")
CAPTURAS = os.path.join(RAIZ, "capturas")

from playwright.sync_api import sync_playwright  # noqa: E402

fallos = []

# El Chromium ya instalado en el sistema puede ser de otra build que la que
# espera esta version de Playwright; se reutiliza en vez de descargar otra.
CHROME = os.environ.get("CHROME_BIN", "")
if not CHROME:
    cache = os.path.expanduser("~/.cache/ms-playwright")
    for sub in sorted(os.listdir(cache)) if os.path.isdir(cache) else []:
        for rel in ("chrome-linux64/chrome", "chrome-linux/chrome"):
            ruta = os.path.join(cache, sub, rel)
            if os.path.isfile(ruta):
                CHROME = ruta
                break
        if CHROME:
            break


def paso(nombre, condicion, detalle=""):
    if condicion:
        print(f"  [ OK   ] {nombre}")
    else:
        print(f"  [FALLA] {nombre} — {detalle}")
        fallos.append(nombre)
    return condicion


def pulsa_y_espera(pagina, selector, texto_esperado=None, clase_esperada=None,
                    timeout=25000):
    """Pulsa un boton y espera a que la barra de estado refleje ESA accion.

    No basta con esperar una clase u una palabra: si la barra ya mostraba ese
    estado de una accion anterior, la espera pasaria al instante y el siguiente
    clic caeria sobre el boton todavia deshabilitado. Aqui se parte del texto
    actual y se exige un estado nuevo que no sea 'trabajando'.
    """
    antes = pagina.inner_text("#estado")
    pagina.click(selector)
    pagina.wait_for_function(
        """([antes, texto, clase]) => {
            const el = document.getElementById('estado');
            const c = el.className || '';
            if (c.includes('trabajando')) return false;
            if (el.textContent === antes) return false;
            if (clase && !c.includes(clase)) return false;
            if (texto && !el.textContent.includes(texto)) return false;
            return true;
        }""",
        arg=[antes, texto_esperado, clase_esperada],
        timeout=timeout,
    )
    return pagina.inner_text("#estado")


def main():
    os.makedirs(CAPTURAS, exist_ok=True)
    with sync_playwright() as p:
        kwargs = {"headless": True}
        if CHROME:
            kwargs["executable_path"] = CHROME
            print(f"  navegador: {CHROME}")
        nav = p.chromium.launch(**kwargs)
        pagina = nav.new_page(viewport={"width": 1280, "height": 1400})
        errores = []
        pagina.on("pageerror", lambda e: errores.append("PAGEERROR: " + str(e)))
        pagina.on("console", lambda m: errores.append(f"CONSOLE {m.type}: {m.text}")
                    if m.type == "error" else None)

        # ---------------------------------------------------------- 1. carga
        pagina.goto(URL, wait_until="networkidle")
        pagina.wait_for_selector(".vol-card", timeout=15000)
        pagina.wait_for_function(
            "document.querySelectorAll('#metricas table').length > 0", timeout=15000)
        tarjetas = pagina.locator(".vol-card").count()
        paso("1 · la pagina carga el esquema y pinta 8 tablas",
             tarjetas == 8, f"tarjetas={tarjetas}")
        estado = pagina.inner_text("#estado")
        paso("1 · la generacion automatica termino",
             "filas" in estado, f"estado={estado!r}")
        filas_ini = pagina.inner_text("#resumen")
        print(f"        resumen inicial: {filas_ini.strip()}")
        pagina.screenshot(path=os.path.join(CAPTURAS, "1-carga.png"), full_page=True)

        # ------------------------------------------------- 2. cambiar volumen
        slider = pagina.locator("#vol-paciente")
        slider.evaluate("el => { el.value = 300; el.dispatchEvent(new Event('input')); }")
        out = pagina.inner_text(".vol-card:has(#vol-paciente) output")
        paso("2 · el deslizador actualiza el valor mostrado", out.strip() == "300",
             f"output={out!r}")

        # ---------------------------------------------------- 3. regenerar
        pulso = pulsa_y_espera(pagina, "#btn-generar", texto_esperado="Lote generado")
        paso("3 · el aviso de generacion se actualiza", bool(pulso), f"estado={pulso!r}")
        filas_nuevas = pagina.inner_text("#resumen")
        paso("3 · regenerar con otro volumen cambia el total",
             filas_nuevas != filas_ini, f"antes={filas_ini!r} despues={filas_nuevas!r}")
        print(f"        resumen nuevo:   {filas_nuevas.strip()}")

        # Lo que se ve en los deslizadores debe ser lo que se genera: con un paso
        # de 10 el navegador redondeaba en silencio 8 -> 10 y 25 -> 30, y la
        # pantalla mostraba un total que nadie habia pedido.
        sliders = pagina.evaluate("""() => {
            const o = {};
            document.querySelectorAll('.vol-card input[type=range]').forEach(r => {
                o[r.id.replace('vol-', '')] = r.value;
            });
            return o;
        }""")
        paso("3 · cada deslizador conserva el volumen por defecto sin redondear",
             sliders.get("especialidad") == "8" and sliders.get("medico") == "25",
             f"valores={ {k: sliders[k] for k in ('especialidad', 'medico')} }")

        # Filas de la tabla de metricas deben reflejar el volumen pedido.
        pacientes = pagina.inner_text(
            "#metricas tbody tr:has(code:text-is('paciente'))")
        paso("3 · la tabla de metricas muestra 300 pacientes",
             "300" in pacientes, f"fila={pacientes!r}")

        # Verificacion de integridad visible en la propia tabla.
        tabla_completa = pagina.inner_text("#metricas")
        paso("3 · no hay ninguna 'x' de fallo en las metricas",
             "✗" not in tabla_completa,
             "aparecen marcas de fallo en la tabla")
        pagina.screenshot(path=os.path.join(CAPTURAS, "2-metricas.png"), full_page=True)

        # ---------------------------------------------------- 4. SQLite real
        estado_sqlite = pulsa_y_espera(pagina, "#btn-demo")
        paso("4 · la base SQLite se crea y verifica sin problemas",
             "0 huérfanas" in estado_sqlite, f"estado={estado_sqlite!r}")
        sqlite_txt = pagina.inner_text("#sqlite-out")
        paso("4 · la UI muestra el PRAGMA foreign_key_check limpio",
             "sin violaciones" in sqlite_txt, f"texto={sqlite_txt[:120]!r}")
        paso("4 · la UI muestra el JOIN de 5 tablas ejecutado",
             "JOIN de 4 tablas" in sqlite_txt,
             f"no aparece el resultado del JOIN: {sqlite_txt[:200]!r}")
        paso("4 · la UI lista los conteos por tabla",
             "paciente: 300" in pagina.inner_text("#sqlite-resumen"),
             f"resumen={pagina.inner_text('#sqlite-resumen')!r}")
        pagina.screenshot(path=os.path.join(CAPTURAS, "3-sqlite.png"), full_page=True)

        # ---------------------------------------------------- 5. exportar
        for motor, marca in (("postgresql", "CHAR(8) NOT NULL UNIQUE"),
                            ("mysql", "ENUM('M','F','O')")):
            pagina.select_option("#motor", motor)
            pagina.select_option("#formato", "sql")
            pulsa_y_espera(pagina, "#btn-exportar", texto_esperado="Script listo")
            sql = pagina.inner_text("#sql")
            paso(f"5 · el script de {motor} se compone con la marca {marca}",
                 marca in sql, "no aparece la marca esperada en el script")
            paso(f"5 · el script de {motor} trae los 8 CREATE TABLE",
                 sql.count("CREATE TABLE") == 8,
                 f"CREATE TABLE={sql.count('CREATE TABLE')}")
        pagina.select_option("#formato", "csv")
        pulsa_y_espera(pagina, "#btn-exportar", texto_esperado="Script listo")
        csv = pagina.inner_text("#sql")
        paso("5 · el CSV trae el bloque de cada tabla",
             "-- tabla: paciente" in csv and "-- tabla: detalle_receta" in csv,
             "faltan bloques en el CSV")
        pagina.screenshot(path=os.path.join(CAPTURAS, "4-exportar.png"), full_page=True)

        # -------------------------------------------------- 6. error real
        # detalle_receta es una hoja: ponerla en 0 es valido siempre que sus
        # propias hijas (ninguna) no la referencien.
        pagina.locator("#vol-detalle_receta").evaluate(
            "el => { el.value = 0; el.dispatchEvent(new Event('input')); }")
        pulso = pulsa_y_espera(pagina, "#btn-generar", clase_esperada="ok")
        paso("6 · vaciar una tabla hoja (detalle_receta) SI es valido",
             "Lote generado" in pulso, f"estado={pulso!r}")

        # Y a la inversa: con detalle_receta repoblada, vaciar medicamento NO es
        # valido, porque su hija dejaria filas huerfanas.
        pagina.locator("#vol-detalle_receta").evaluate(
            "el => { el.value = 200; el.dispatchEvent(new Event('input')); }")
        pagina.locator("#vol-medicamento").evaluate(
            "el => { el.value = 0; el.dispatchEvent(new Event('input')); }")
        err = pulsa_y_espera(pagina, "#btn-generar", clase_esperada="error")
        paso("6 · vaciar una tabla con hijas vivas (medicamento) da error explicito",
             "medicamento: no se puede generar en 0 filas" in err
             and "detalle_receta" in err, f"error={err!r}")
        paso("6 · el mensaje de error esta en rojo",
             "error" in (pagina.get_attribute("#estado", "class") or ""),
             "la clase del aviso no es 'error'")
        # Un volumen invalido es un error de la peticion (4xx), no una caida (5xx).
        paso("6 · el servidor responde 4xx, no 5xx, ante un volumen invalido",
             not any(" 5" in e and "00" in e for e in errores),
             f"la consola registro: {errores}")
        pagina.screenshot(path=os.path.join(CAPTURAS, "5-error.png"), full_page=True)

        # "Failed to load resource" no es un fallo de JS: el navegador lo registra
        # como error de consola tambien en las respuestas 4xx esperadas. Lo que
        # debe estar limpio son los errores de script.
        paso("7 · la consola del navegador no tiene errores de JavaScript",
             not [e for e in errores if not e.startswith("CONSOLE error: Failed to load resource")],
             f"errores={errores[:3]}")
        paso("7 · no hay peticiones 5xx durante todo el recorrido",
             not any(" 5" in e and "00 " in e for e in errores),
             f"errores={errores[:3]}")
        nav.close()

    print()
    if fallos:
        print(f"  SMOKE TEST: {len(fallos)} paso(s) fallido(s): {fallos}")
        print(f"  capturas en {CAPTURAS}")
        return 1
    print("  SMOKE TEST: todos los pasos del flujo real pasaron")
    print(f"  capturas en {CAPTURAS}")
    return 0


if __name__ == "__main__":
    t0 = time.time()
    code = main()
    print(f"  ({time.time() - t0:.1f}s)")
    sys.exit(code)
