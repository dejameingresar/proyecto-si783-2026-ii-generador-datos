"""nucleo.persistencia — carga del lote en SQLite y exportación de SQL portable.

SQLite es el motor de la demo (no requiere instalar nada), pero el script
exportado usa el mismo DDL y los mismos datos en sintaxis PostgreSQL/MySQL, que es
lo que el docente puede correr en los labs.
"""

import sqlite3

from . import esquemas
from .ddl import esquema_sql
from .motor import sql_literal


def conectar(ruta=":memory:"):
    con = sqlite3.connect(ruta)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def crear_esquema(con, esquema=None, motor="sqlite", incluir_drop=True):
    """Ejecuta el DDL del esquema en la conexión."""
    esquema = esquema or esquemas.ESQUEMA
    script = esquema_sql(esquema, motor, incluir_drop)
    con.executescript(script)
    con.commit()
    return con


def _col_literal_sqlite(valor):
    if valor is None:
        return "NULL"
    if isinstance(valor, bool):
        return "1" if valor else "0"
    if isinstance(valor, (int, float)):
        return repr(valor)
    return sql_literal(valor)


def insertar_lote(con, lote, esquema=None, lote_indice=0):
    """Inserta el lote con INSERT ... SELECT cuando es posible (mucho más rápido)."""
    esquema = esquema or esquemas.ESQUEMA
    tablas = esquema["tablas"]
    insertadas = {}
    for nombre in esquema["orden_insercion"]:
        filas = lote.get(nombre) or []
        if not filas:
            insertadas[nombre] = 0
            continue
        cols = esquemas.columnas(tablas[nombre])
        # Identico para las dos sintaxis: los tipos declarados son portables.
        select = " UNION ALL ".join(
            "SELECT " + ", ".join(_col_literal_sqlite(f[c]) for c in cols)
            for f in filas
        )
        con.execute(
            f"INSERT INTO {nombre} ({', '.join(cols)}) {select}"
        )
        insertadas[nombre] = len(filas)
    con.commit()
    return insertadas


def exportar_sql(lote, esquema=None, motor="postgresql", lote_indice=0, con_inserts=True):
    """Script completo (DDL + INSERT) del lote para el motor indicado."""
    esquema = esquema or esquemas.ESQUEMA
    tablas = esquema["tablas"]
    partes = [esquema_sql(esquema, motor, incluir_drop=True)]
    if not con_inserts:
        return partes[0]
    for nombre in esquema["orden_insercion"]:
        filas = lote.get(nombre) or []
        if not filas:
            continue
        cols = esquemas.columnas(tablas[nombre])
        valores = []
        for f in filas:
            fila_txt = ", ".join(sql_literal(f[c]) for c in cols)
            valores.append(f"  ({fila_txt})")
        partes.append(
            f"INSERT INTO {nombre} ({', '.join(cols)}) VALUES\n"
            + ",\n".join(valores) + ";"
        )
    return "\n\n".join(partes) + "\n"


def exportar_csv(lote, esquema=None):
    """Un CSV por tabla dentro de un único archivo (encabezado con el nombre)."""
    esquema = esquema or esquemas.ESQUEMA
    tablas = esquema["tablas"]
    bloques = []
    for nombre in esquema["orden_insercion"]:
        filas = lote.get(nombre) or []
        if not filas:
            continue
        cols = esquemas.columnas(tablas[nombre])
        lineas = [",".join(_csv_valor(c) for c in cols)]
        for f in filas:
            lineas.append(",".join(_csv_valor(f[c]) for c in cols))
        bloques.append(f"-- tabla: {nombre}\n" + "\n".join(lineas))
    return "\n\n".join(bloques) + "\n"


def _csv_valor(v):
    if v is None:
        return ""
    s = str(v)
    if any(c in s for c in ',"\n'):
        return '"' + s.replace('"', '""') + '"'
    return s


def crear_y_poblar(ruta, lote, esquema=None):
    """Atajo: base nueva con el esquema creado y el lote cargado (una transaccion)."""
    esquema = esquema or esquemas.ESQUEMA
    con = conectar(ruta)
    crear_esquema(con, esquema)
    insertar_lote(con, lote, esquema)
    return con
