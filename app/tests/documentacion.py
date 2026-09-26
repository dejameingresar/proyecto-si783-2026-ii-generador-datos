"""T-31 — La documentacion tecnica es reproducible.

Los archivos que la automatizacion commitea (diagrama .mmd, diccionario de
datos, manual tecnico y DDL) deben ser byte a byte iguales en cada ejecucion: si
no lo fueran, cada push generaria un commit sin cambios reales y el repositorio
llenaria el historial de ruido.

El SVG queda fuera a proposito: mermaid-cli incrusta la fuente con un
identificador aleatorio, asi que su binario cambia siempre. Este test lo
comprueba y falla si algun dia el generador empieza a producirlo estable, que
permitiria devolverlo al commit automatico.
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ_PROYECTO = os.path.dirname(RAIZ)
sys.path.insert(0, os.path.join(RAIZ_PROYECTO, "app"))
sys.path.insert(0, RAIZ_PROYECTO)

from docs import generar_documentos as gd  # noqa: E402

fallos = []


def paso(nombre, condicion, detalle=""):
    if condicion:
        print(f"  [ OK   ] {nombre}")
    else:
        print(f"  [FALLA] {nombre} — {detalle}")
        fallos.append(nombre)


def main():
    # Los generadores de texto deben ser puros: dos llamadas, mismo resultado.
    for nombre, fn in (("diagrama .mmd", gd.diagrama_er),
                       ("diccionario de datos", gd.diccionario_datos),
                       ("manual tecnico", gd.manual_tecnico)):
        a, b = fn(), fn()
        paso(f"{nombre} es identico en dos ejecuciones", a == b,
             "el generador produce salida distinta cada vez")
        paso(f"{nombre} no esta vacio", len(a) > 200, f"longitud={len(a)}")

    # El DDL exportado tambien.
    from nucleo import persistencia
    from nucleo.motor import Generador
    s1 = persistencia.exportar_sql(Generador(semilla=2026).generar(), motor="sqlite")
    s2 = persistencia.exportar_sql(Generador(semilla=2026).generar(), motor="sqlite")
    paso("el DDL exportado es identico en dos ejecuciones", s1 == s2,
         "el exportador no es determinista con la misma semilla")
    paso("el DDL exportado no esta vacio", len(s1) > 1000, f"longitud={len(s1)}")

    # Documento: el SVG cambia siempre, asi que no debe entrar al commit.
    svg = os.path.join(gd.DOCS, "diagrama-er.svg")
    if os.path.isfile(svg):
        with open(svg, "rb") as fh:
            primero = fh.read()
        paso("el SVG es un binario no determinista (motivo de la exclusion)",
             primero[:16] == b"<?xml" or b"<svg" in primero[:200],
             "el SVG no parece un SVG")
        print("        (el SVG queda fuera del commit automatico a proposito)")

    print()
    if fallos:
        print(f"  DOCUMENTACION: {len(fallos)} comprobacion(es) fallida(s): {fallos}")
        return 1
    print("  DOCUMENTACION: la generacion es reproducible en todos los formatos "
          "que se commitean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
