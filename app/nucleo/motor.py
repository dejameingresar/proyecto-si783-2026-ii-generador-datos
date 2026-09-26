"""nucleo.motor — motor de generación de datos.

Responsabilidades:
  1. generar filas tabla por tabla respetando claves foráneas, uniques y CHECK;
  2. garantizar determinismo: la misma semilla produce exactamente las mismas
     filas (requisito para que el docente pueda reproducir la demo);
  3. informar métricas de calidad del lote (unicidad, completitud, dominios,
     integridad referencial) que son la evidencia de los objetivos medibles.

No depende de la base de datos: genera estructuras de datos en memoria, y quien
las persiste es `nucleo.persistencia`.
"""

import datetime as dt
import random
from collections import Counter

from . import esquemas
from .ddl import VALIDADORES
from .generadores import GENERADORES, email_de_fila


class ErrorGeneracion(Exception):
    pass


def dominio_declarado(campo, esquema):
    """Dominio efectivo de un campo enum: el del esquema o el sobrescrito por la UI."""
    return esquema.get("enums", {}).get(campo["nombre"], campo["enum"])


def _norm_enum(valor, opciones):
    """Ajusta el valor al dominio del enum (tolerante a mayúsculas y prefijos)."""
    if valor is None or not opciones:
        return None
    texto = str(valor).strip()
    for o in opciones:
        if o.lower() == texto.lower():
            return o
    for o in opciones:
        if texto and o.lower().startswith(texto.lower()):
            return o
    return opciones[0]


def _a_fecha(valor):
    if isinstance(valor, dt.datetime):
        return valor.date().isoformat()
    if isinstance(valor, dt.date):
        return valor.isoformat()
    return str(valor)


def _a_hora(valor):
    if isinstance(valor, dt.time):
        return valor.strftime("%H:%M:%S")
    return str(valor)


def _ajustar_tipo(valor, campo):
    """Convierte el valor del generador al tipo lógico del campo."""
    t = campo["tipo"]
    if valor is None:
        return None
    if t in ("date", "datetime"):
        return _a_fecha(valor)
    if t == "time":
        return _a_hora(valor)
    if t == "bool":
        return 1 if valor else 0
    if t in ("int", "bigint", "smallint"):
        return int(valor)
    if t == "decimal":
        return round(float(valor), 2)
    return valor


def sql_literal(valor):
    """Literal SQL portable (comillas dobles escapadas, NULL explícito)."""
    if valor is None:
        return "NULL"
    if isinstance(valor, bool):
        return "1" if valor else "0"
    if isinstance(valor, (int, float)):
        return repr(valor)
    return "'" + str(valor).replace("'", "''") + "'"


class Generador:
    """Genera un lote de datos coherente con el esquema declarado."""

    def __init__(self, esquema=None, semilla=2026, enums=None):
        self.esquema = esquema or esquemas.ESQUEMA
        self.rng = random.Random(semilla)
        self.semilla = semilla
        self.enums = dict(self.esquema.get("enums", {}))
        if enums:
            for campo, opciones in enums.items():
                if opciones:
                    self.enums[campo] = list(opciones)
        self._usados = {}
        self._tablas = self.esquema["tablas"]

    # ------------------------------------------------------------- generación
    def _valor_unico(self, campo, tabla_nombre):
        """Genera un valor que no repita dentro de su columna única."""
        clave = (tabla_nombre, campo["nombre"])
        vistos = self._usados.setdefault(clave, set())
        gen = GENERADORES.get(campo.get("generador"), lambda rng, c: "dato")
        for _ in range(500):
            valor = _ajustar_tipo(gen(self.rng, campo), campo)
            if valor is None or valor in vistos:
                continue
            vistos.add(valor)
            return valor
        raise ErrorGeneracion(
            f"agotados los valores unicos para {tabla_nombre}.{campo['nombre']}: "
            "reduce el volumen o amplia el dominio del generador"
        )

    def _valor_simple(self, campo):
        gen = GENERADORES.get(campo.get("generador"))
        if gen is None:
            return None
        return _ajustar_tipo(gen(self.rng, campo), campo)

    def _validar(self, campo, valor, fila):
        """Aplica el validador declarativo en memoria (el mismo que el CHECK SQL)."""
        if not campo.get("validacion"):
            return True
        _, fn = VALIDADORES[campo["validacion"]]
        return bool(fn(valor, fila))

    def _fk_valor(self, campo, disponibles):
        tabla_ref = campo["tabla_ref"]
        ids = disponibles.get(tabla_ref) or []
        if not ids:
            raise ErrorGeneracion(
                f"no hay filas de {tabla_ref} para la FK {campo['nombre']}: "
                "esa tabla debe generarse antes"
            )
        return self.rng.choice(ids)

    def _cumple_unicas(self, tbl, fila, existentes):
        for combo in tbl.get("unicas", []):
            clave = tuple(fila.get(c) for c in combo)
            for f in existentes:
                if tuple(f.get(c) for c in combo) == clave:
                    return False
        return True

    def generar_tabla(self, nombre_tabla, n, disponibles):
        """Genera n filas válidas de una tabla; devuelve la lista de dicts."""
        tbl = self._tablas[nombre_tabla]
        cols = esquemas.columnas(tbl)
        filas = []
        intentos = 0
        intentos_max = n * 60 + 300
        while len(filas) < n and intentos < intentos_max:
            intentos += 1
            fila = {}
            for campo in tbl["campos"]:
                if campo.get("pk"):
                    # PK entera correlativa: la asigna el motor, no el generador.
                    fila[campo["nombre"]] = len(filas) + 1
                elif campo["tipo"] == "fk":
                    fila[campo["nombre"]] = self._fk_valor(campo, disponibles)
                elif campo["tipo"] == "enum":
                    opciones = self.enums.get(campo["nombre"]) or campo["enum"]
                    fila[campo["nombre"]] = _norm_enum(self.rng.choice(opciones), opciones)
                elif campo.get("derivado"):
                    # Se resuelve mas abajo, con la fila completa. Aqui queda en
                    # None para que las UNIQUE compuestas tengan algo que comparar.
                    fila[campo["nombre"]] = None
                elif campo.get("unique"):
                    fila[campo["nombre"]] = self._valor_unico(campo, nombre_tabla)
                else:
                    fila[campo["nombre"]] = self._valor_simple(campo)
            if not self._cumple_unicas(tbl, fila, filas):
                continue
            # Campos derivados: se calculan con la fila ya completa, para que el
            # correo pertenezca al nombre de la MISMA fila.
            for campo in tbl["campos"]:
                if campo.get("derivado") == "email_de_fila":
                    fila[campo["nombre"]] = email_de_fila(fila, self.rng)
                    # Es una columna UNIQUE: si el correo ya salio, se reintenta
                    # la fila completa en vez de devolver un duplicado.
                    clave = (nombre_tabla, campo["nombre"])
                    vistos = self._usados.setdefault(clave, set())
                    if fila[campo["nombre"]] in vistos:
                        continue
                    vistos.add(fila[campo["nombre"]])
            # Los CHECK que miran dos columnas (fin_despues_inicio) necesitan la
            # fila completa, así que se evaluan al final.
            if not all(self._validar(c, fila.get(c["nombre"]), fila) for c in tbl["campos"]):
                continue
            filas.append(fila)
        if len(filas) < n:
            raise ErrorGeneracion(
                f"{nombre_tabla}: solo {len(filas)}/{n} filas validas tras {intentos} "
                "intentos — las restricciones son demasiado estrictas para el volumen pedido"
            )
        _ = cols
        return filas

    def generar(self, volumenes=None):
        """Genera el lote completo respetando el orden de dependencias."""
        vol = dict(self.esquema.get("volumenes", {}))
        if volumenes:
            vol.update(volumenes)
        disponibles, lote = {}, {}
        for nombre in self.esquema["orden_insercion"]:
            n = int(vol.get(nombre, 10))
            if n < 0:
                raise ErrorGeneracion(f"{nombre}: el volumen no puede ser negativo ({n})")
            if n == 0:
                # Una tabla vacia solo es valida si ninguna tabla que la referencia
                # sigue generando filas; si no, quedarian huerfanas.
                hijas_vivas = [h for h in self._hijas(nombre) if int(vol.get(h, 0)) > 0]
                if hijas_vivas:
                    raise ErrorGeneracion(
                        f"{nombre}: no se puede generar en 0 filas porque "
                        f"{', '.join(sorted(hijas_vivas))} "
                        f"{'siguen' if len(hijas_vivas) > 1 else 'sigue'} generando "
                        f"filas que la referencian. Ponga tambien en 0 o "
                        f"suba el volumen de {nombre}."
                    )
                disponibles[nombre] = []
                lote[nombre] = []
                continue
            filas = self.generar_tabla(nombre, n, disponibles)
            lote[nombre] = filas
            disponibles[nombre] = [f[esquemas.columnas(self._tablas[nombre])[0]] for f in filas]
        return lote

    def _hijas(self, tabla):
        """Tablas que tienen una FK hacia `tabla` (usado en los mensajes de error)."""
        hijas = []
        for nombre, t in self._tablas.items():
            for c in t["campos"]:
                if c["tipo"] == "fk" and c["tabla_ref"] == tabla:
                    hijas.append(nombre)
                    break
        return hijas


# ------------------------------------------------------------------ métricas
def metricas(lote, esquema=None):
    """Métricas de calidad del lote: son la evidencia de los objetivos medibles."""
    esquema = esquema or esquemas.ESQUEMA
    tablas = esquema["tablas"]
    m = {"tablas": {}, "totales": {"filas": 0, "columnas": 0, "celdas_obligatorias": 0,
                                   "celdas_vacias": 0}}

    for nombre, filas in lote.items():
        tbl = tablas[nombre]
        cols = esquemas.columnas(tbl)
        pk = next((c["nombre"] for c in tbl["campos"] if c.get("pk")), cols[0])
        n = len(filas)
        info = {
            "filas": n,
            "columnas": len(cols),
            "pk_unica": (len({f[pk] for f in filas}) == n) if n else True,
            "unicos_respetados": 0,
            "unicos_total": 0,
            "completitud": 1.0,
            "dominios": {},
            "fk_respetadas": {},
        }
        m["totales"]["filas"] += n
        m["totales"]["columnas"] += len(cols)

        obligatorios = [c for c in tbl["campos"]
                        if not c.get("nullable", False) and c.get("generador") is not None]
        celdas_ok = sum(1 for f in filas for c in obligatorios
                        if f.get(c["nombre"]) is not None)
        celdas_tot = n * len(obligatorios)
        vacias = celdas_tot - celdas_ok
        m["totales"]["celdas_obligatorias"] += celdas_tot
        m["totales"]["celdas_vacias"] += vacias
        info["completitud"] = (celdas_ok / celdas_tot) if celdas_tot else 1.0

        for campo in tbl["campos"]:
            if not campo.get("unique") or campo.get("pk"):
                continue
            info["unicos_total"] += 1
            vals = [f.get(campo["nombre"]) for f in filas if f.get(campo["nombre"]) is not None]
            if len(set(vals)) == len(vals):
                info["unicos_respetados"] += 1

        for campo in tbl["campos"]:
            if campo["tipo"] != "enum":
                continue
            declarado = dominio_declarado(campo, esquema)
            conteo = Counter(f.get(campo["nombre"]) for f in filas)
            info["dominios"][campo["nombre"]] = {
                "declarado": list(declarado),
                "observado": dict(conteo),
                "cumple": all(f.get(campo["nombre"]) in declarado for f in filas),
            }

        for campo in tbl["campos"]:
            if campo["tipo"] != "fk":
                continue
            ref = campo["tabla_ref"]
            ids_ref = {f[esquemas.columnas(tablas[ref])[0]] for f in lote.get(ref, [])}
            vals = [f.get(campo["nombre"]) for f in filas]
            info["fk_respetadas"][campo["nombre"]] = {
                "tabla_ref": ref,
                "huerfanos": sum(1 for v in vals if v not in ids_ref),
                "distintas": len({v for v in vals if v is not None}),
                "referencias_disponibles": len(ids_ref),
            }
        m["tablas"][nombre] = info
    return m


def validar_en_sqlite(con, lote, esquema=None):
    """Verifica con el propio SQLite que no hay huérfanos, duplicados ni pérdidas.

    Comprobación independiente: no confía en el generador, pregunta a la BD.
    """
    esquema = esquema or esquemas.ESQUEMA
    tablas = esquema["tablas"]
    problemas = []
    for nombre in esquema["orden_insercion"]:
        tbl = tablas[nombre]
        total = con.execute(f"SELECT COUNT(*) FROM {nombre}").fetchone()[0]
        esperado = len(lote.get(nombre, []))
        if total != esperado:
            problemas.append(f"{nombre}: {total} filas en la BD frente a {esperado} generadas")
        for campo in tbl["campos"]:
            if not campo.get("unique") or campo.get("pk"):
                continue
            dup = con.execute(
                f"SELECT COUNT(*) - COUNT(DISTINCT {campo['nombre']}) FROM {nombre}"
            ).fetchone()[0]
            if dup:
                problemas.append(
                    f"{nombre}.{campo['nombre']}: {dup} duplicados en columna UNIQUE")
        for combo in tbl.get("unicas", []):
            # SQLite no admite COUNT(DISTINCT a, b): se cuenta el total y se
            # restan los grupos repetidos, que es el numero de filas sobrantes.
            cols = ", ".join(combo)
            duplicados = con.execute(
                f"SELECT COALESCE(SUM(n - 1), 0) FROM "
                f"(SELECT COUNT(*) AS n FROM {nombre} GROUP BY {cols} HAVING COUNT(*) > 1)"
            ).fetchone()[0]
            if duplicados:
                problemas.append(
                    f"{nombre} ({cols}): {duplicados} duplicados en la restriccion "
                    "UNIQUE compuesta")
        for campo in tbl["campos"]:
            if campo["tipo"] != "fk":
                continue
            huerfanos = con.execute(
                f"SELECT COUNT(*) FROM {nombre} n "
                f"LEFT JOIN {campo['tabla_ref']} p "
                f"ON n.{campo['nombre']} = p.{campo['columna_ref']} "
                f"WHERE p.{campo['columna_ref']} IS NULL"
            ).fetchone()[0]
            if huerfanos:
                problemas.append(f"{nombre}.{campo['nombre']}: {huerfanos} filas huerfanas "
                                 f"hacia {campo['tabla_ref']}")
    return problemas
