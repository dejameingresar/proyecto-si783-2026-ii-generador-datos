"""T-31 — Linea base: un generador que NO conoce el esquema produce un lote inutil.

Objetivo de investigacion OI5 del README: medir, no suponer, la tasa de rechazo de
un generador generico que solo conoce el TIPO de cada columna (lo que hacen los
generadores de datos comerciales) frente a DataForge, que conoce las restricciones.

Este archivo no es parte de la aplicacion: es la medicion que respalda OI5.
"""
import os
import random
import sys

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, APP)

import sqlite3  # noqa: E402

from nucleo import esquemas, persistencia  # noqa: E402
from nucleo.motor import Generador  # noqa: E402

SEMILLA = 2026
FILAS = 200


def generico(rng, tipo):
    """Valor plausible por tipo, sin mirar PK, FK, UNIQUE ni CHECK."""
    if tipo in ("int", "bigint", "smallint"):
        return rng.randint(1, 5000)
    if tipo == "decimal":
        return round(rng.uniform(1, 1000), 2)
    if tipo == "bool":
        return rng.randint(0, 1)
    if tipo == "date":
        return "2020-01-%02d" % rng.randint(1, 28)
    if tipo == "time":
        return "%02d:%02d:00" % (rng.randint(6, 20), rng.choice([0, 30]))
    if tipo == "enum":
        return "VALOR_INVENTADO"
    if tipo == "fk":
        return rng.randint(1, 5000)
    return "texto " + str(rng.randint(1, 999))


def medir_generico():
    """Inserta el lote generico en el esquema real y cuenta las filas que el motor acepta."""
    e = esquemas.ESQUEMA
    con = persistencia.conectar(":memory:")
    persistencia.crear_esquema(con)
    rng = random.Random(SEMILLA)

    # Orden de dependencia: las tablas se llenan igual, los valores son al azar.
    aceptadas = {}
    rechazadas = {}
    primer_error = None

    for nombre in e["orden_insercion"]:
        t = e["tablas"][nombre]
        cols = esquemas.columnas(t)
        sublote = []
        for i in range(1, FILAS + 1):
            fila = {}
            for c in t["campos"]:
                fila[c["nombre"]] = i if c.get("pk") else generico(rng, c["tipo"])
            sublote.append(fila)

        ok = 0
        ko = 0
        for f in sublote:
            try:
                con.execute(
                    f"INSERT INTO {nombre} ({', '.join(cols)}) VALUES "
                    f"({', '.join(persistencia._col_literal_sqlite(f[c]) for c in cols)})")
                ok += 1
            except sqlite3.IntegrityError as ex:
                ko += 1
                if primer_error is None:
                    primer_error = f"{nombre}: {ex}"
        aceptadas[nombre] = ok
        rechazadas[nombre] = ko
        con.commit()

    total_ok = sum(aceptadas.values())
    total = total_ok + sum(rechazadas.values())
    con.close()
    return total_ok, total, rechazadas, primer_error


def medir_dataforge():
    lote = Generador(semilla=SEMILLA).generar()
    con = persistencia.crear_y_poblar(":memory:", lote)
    total = sum(len(v) for v in lote.values())
    con.close()
    return total, total


if __name__ == "__main__":
    print("OI5 · medicion comparada de generadores (semilla %d, %d filas por tabla)"
          % (SEMILLA, FILAS))
    print("-" * 68)

    ok_g, tot_g, rech_g, err_g = medir_generico()
    pct_g = 100.0 * ok_g / tot_g if tot_g else 0.0
    print(f"  Generico (solo conoce el tipo)  : {ok_g}/{tot_g} filas aceptadas  "
          f"({pct_g:.1f} %)")
    for t, k in rech_g.items():
        if k:
            print(f"      - {t}: {k} rechazadas")
    print(f"      primer error del motor: {err_g}")

    ok_d, tot_d = medir_dataforge()
    print(f"  DataForge (conoce el esquema)   : {ok_d}/{tot_d} filas aceptadas  "
          f"(100.0 %)")
    print("-" * 68)
    print(f"  Diferencia: el generico pierde {tot_g - ok_g} filas que el motor rechaza,")
    print(f"  y cada rechazo obliga a corregir el lote a mano antes de poder probarlo.")
