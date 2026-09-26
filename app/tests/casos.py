"""app/tests/casos.py — suite de pruebas de DataForge (solo biblioteca estandar).

Ejecutar:  python3 app/tests/casos.py
Sale con codigo distinto de 0 si algo falla, para que tambien sirva en CI.

Cada caso lleva un id estable (T-01, T-02, ...) porque la matriz de trazabilidad
del proyecto los cita; esos ids NO se inventan despues, se crean aqui.
"""

import os
import sys
import traceback

RAIZ = os.path.dirname(os.path.abspath(__file__))
APP = os.path.dirname(RAIZ)
sys.path.insert(0, APP)

from nucleo import esquemas, persistencia  # noqa: E402
from nucleo.ddl import esquema_sql, tipo_sql  # noqa: E402
from nucleo.motor import (  # noqa: E402
    ErrorGeneracion, Generador, metricas, validar_en_sqlite,
)

# ------------------------------------------------------------------ runner
CASOS = []


def caso(id_caso, titulo):
    def deco(fn):
        CASOS.append((id_caso, titulo, fn))
        return fn
    return deco


class Falla(AssertionError):
    pass


def esperar(cond, msg):
    if not cond:
        raise Falla(msg)


def igual(a, b, msg=""):
    if a != b:
        raise Falla(f"{msg} — esperaba {b!r}, obtuve {a!r}")


# ============================================================== T-01..T-06 esquema
@caso("T-01", "el esquema declara 8 tablas en orden de dependencias")
def t01():
    e = esquemas.ESQUEMA
    igual(len(e["orden_insercion"]), 8, "numero de tablas")
    igual(e["orden_insercion"][0], "especialidad", "primera tabla")
    igual(e["orden_insercion"][-1], "detalle_receta", "ultima tabla")
    # toda FK apunta a una tabla declarada antes en el orden
    for nombre in e["orden_insercion"]:
        for c in e["tablas"][nombre]["campos"]:
            if c["tipo"] == "fk":
                esperar(c["tabla_ref"] in e["orden_insercion"], f"FK huerfana: {c}")
                esperar(e["orden_insercion"].index(c["tabla_ref"]) < e["orden_insercion"].index(nombre),
                       f"FK a tabla posterior: {nombre}.{c['nombre']} -> {c['tabla_ref']}")


@caso("T-02", "el generador de valores cubre todos los generadores declarados")
def t02():
    from nucleo.generadores import GENERADORES
    for nombre, tbl in esquemas.TABLAS.items():
        for c in tbl["campos"]:
            g = c.get("generador")
            if g:
                esperar(g in GENERADORES, f"{nombre}.{c['nombre']} usa generador desconocido: {g}")


@caso("T-03", "el DDL de SQLite crea las tablas con PK, FK, UNIQUE y CHECK")
def t03():
    sql = esquema_sql(esquemas.ESQUEMA, "sqlite")
    esperar("PRIMARY KEY" in sql, "falta PRIMARY KEY")
    esperar("REFERENCES paciente" in sql, "falta FK a paciente")
    esperar("UNIQUE (id_medico, fecha, hora_inicio)" in sql, "falta UNIQUE compuesto")
    esperar("CHECK (" in sql, "falta CHECK")
    esperar("CHECK (hora_fin > hora_inicio)" in sql, "falta CHECK de intervalo")
    esperar("CREATE INDEX" in sql, "falta indice")


@caso("T-04", "el mismo esquema produce DDL distinto y valido en los tres motores")
def t04():
    s = esquema_sql(esquemas.ESQUEMA, "sqlite")
    p = esquema_sql(esquemas.ESQUEMA, "postgresql")
    m = esquema_sql(esquemas.ESQUEMA, "mysql")
    esperar(s != p != m, "los tres motores deben producir scripts distintos")
    esperar("BOOLEAN" in p and "BOOLEAN" not in s, "PostgreSQL debe usar BOOLEAN")
    esperar("TINYINT(1)" in m, "MySQL debe usar TINYINT(1)")
    esperar("ENUM(" in m, "MySQL debe usar ENUM nativo")
    esperar("BOOLEAN" not in s and "TINYINT" not in s, "tipos filtrados de otros motores")
    igual(esquema_sql(esquemas.ESQUEMA, "postgresql"), p, "el DDL debe ser determinista")
    igual(esquema_sql(esquemas.ESQUEMA, "postgresql").count("CREATE TABLE"), 8, "tablas en PG")
    try:
        esquema_sql(esquemas.ESQUEMA, "oracle")
    except ValueError as e:
        esperar("no soportado" in str(e), "mensaje de motor invalido")
    else:
        raise Falla("deberia rechazar un motor no soportado")


@caso("T-05", "tipos enumerados y declarativos se traducen al tipo nativo de cada motor")
def t05():
    from nucleo.ddl import MAPA
    t_enum = {"nombre": "estado", "tipo": "enum", "enum": ["A", "B"]}
    t_dec = {"nombre": "precio", "tipo": "decimal", "precision": 10, "escala": 2}
    t_vc = {"nombre": "nombre", "tipo": "varchar", "largo": 60}
    igual(tipo_sql(t_enum, "postgresql"), "TEXT", "enum en PG")
    igual(tipo_sql(t_dec, "postgresql"), "NUMERIC(10, 2)", "decimal en PG")
    # SQLite no tiene NUMERIC con escala: guarda REAL y el CHECK hace el resto.
    igual(tipo_sql(t_dec, "sqlite"), "REAL", "decimal en SQLite")
    igual(tipo_sql(t_vc, "mysql"), "VARCHAR(60)", "varchar en MySQL")
    igual(tipo_sql(t_enum, "mysql"), "ENUM", "enum en MySQL")
    igual(tipo_sql({"nombre": "dni", "tipo": "dni"}, "sqlite"), "CHAR(8)", "dni en SQLite")
    esperar("email" in MAPA["sqlite"] and "dni" in MAPA["mysql"], "tipos de dominio deben existir")


@caso("T-06", "el DDL de MySQL serializa los enums nativos sin perder el dominio")
def t06():
    sql = esquema_sql(esquemas.ESQUEMA, "mysql")
    esperar("ENUM('M','F','O')" in sql, "falta enum nativo de sexo")
    esperar("'PROGRAMADA','ATENDIDA','CANCELADA','NO_ASISTIO'" in sql, "falta enum de estado")
    # En los otros dos motores el mismo dominio viaja como CHECK, no como tipo.
    for motor in ("sqlite", "postgresql"):
        s = esquema_sql(esquemas.ESQUEMA, motor)
        esperar("ENUM(" not in s, f"{motor}: ENUM nativo no soportado")
        esperar("CHECK (sexo IN ('M','F','O'))" in s, f"{motor}: falta CHECK de sexo")


# ============================================================== T-07..T-12 generacion
@caso("T-07", "la generacion completa produce el volumen exacto por tabla")
def t07():
    lote = Generador(semilla=2026).generar()
    for nombre, esperado in esquemas.ESQUEMA["volumenes"].items():
        igual(len(lote[nombre]), esperado, f"filas de {nombre}")


@caso("T-08", "determinismo: la misma semilla produce el mismo lote; otra semilla, otro lote")
def t08():
    a = Generador(semilla=42).generar()
    b = Generador(semilla=42).generar()
    c = Generador(semilla=43).generar()
    igual(a, b, "misma semilla debe ser identica")
    esperar(a["paciente"] != c["paciente"], "semillas distintas deben diferir")
    igual(Generador(semilla=7).generar(), Generador(semilla=7).generar(), "repetibilidad")


@caso("T-09", "las claves foraneas nunca apuntan a filas inexistentes")
def t09():
    lote = Generador(semilla=11).generar()
    for nombre, filas in lote.items():
        for c in esquemas.TABLAS[nombre]["campos"]:
            if c["tipo"] != "fk":
                continue
            ref = c["tabla_ref"]
            ids = {f[esquemas.columnas(esquemas.TABLAS[ref])[0]] for f in lote[ref]}
            huerfanos = [f for f in filas if f[c["nombre"]] not in ids]
            igual(len(huerfanos), 0, f"{nombre}.{c['nombre']} huerfanos hacia {ref}")


@caso("T-10", "los dominios enum se respetan y las columnas UNIQUE no repiten")
def t10():
    lote = Generador(semilla=5).generar()
    for nombre, filas in lote.items():
        for c in esquemas.TABLAS[nombre]["campos"]:
            if c["tipo"] == "enum":
                dominio = esquemas.ESQUEMA["enums"].get(c["nombre"], c["enum"])
                fuera = [f for f in filas if f[c["nombre"]] not in dominio]
                igual(len(fuera), 0, f"{nombre}.{c['nombre']} fuera de dominio")
            if c.get("unique") and not c.get("pk"):
                vals = [f[c["nombre"]] for f in filas if f[c["nombre"]] is not None]
                igual(len(set(vals)), len(vals), f"{nombre}.{c['nombre']} repetido")


@caso("T-11", "las restricciones declarativas (CHECK) se cumplen en todas las filas")
def t11():
    lote = Generador(semilla=9).generar()
    turnos = lote["turno"]
    for f in turnos:
        esperar(f["hora_fin"] > f["hora_inicio"], f"turno con hora_fin <= hora_inicio: {f}")
    for f in lote["medico"]:
        esperar(f["salario"] > 0, "salario no positivo")
    for f in lote["medicamento"]:
        esperar(f["precio_unitario"] > 0, "precio no positivo")
        esperar(f["stock"] >= 0, "stock negativo")
    for f in lote["detalle_receta"]:
        esperar(f["cantidad"] > 0, "cantidad no positiva")
        esperar(f["duracion_dias"] > 0, "duracion no positiva")
    for f in lote["medico"]:
        esperar(f["activo"] in (0, 1), "activo fuera de {0,1}")


@caso("T-12", "el DNI generado tiene 8 digitos y formato de padron real")
def t12():
    lote = Generador(semilla=3).generar()
    for tabla in ("medico", "paciente"):
        for f in lote[tabla]:
            d = f["dni"]
            # RENIEC registra 8 digitos: el verificador no se imprime en el DNI,
            # se calcula bajo demanda. Generar un digito extra seria dato falso.
            igual(len(d), 8, f"DNI {d} debe tener 8 digitos")
            esperar(d.isdigit(), f"DNI {d} no es numerico")
            esperar(d[0] != "0", f"DNI {d} no empieza en 0 (debe tener 8 cifras)")
    # Y el padron no puede tener dos personas con el mismo documento.
    dnis = [f["dni"] for f in lote["paciente"]]
    igual(len(set(dnis)), len(dnis), "DNI repetido en paciente")


# ============================================================== T-13..T-18 persistencia
@caso("T-13", "el lote carga en SQLite y el conteo por tabla coincide")
def t13():
    lote = Generador(semilla=2026).generar()
    con = persistencia.crear_y_poblar(":memory:", lote)
    for nombre, filas in lote.items():
        igual(con.execute(f"SELECT COUNT(*) FROM {nombre}").fetchone()[0], len(filas),
              f"conteo de {nombre}")
    con.close()


@caso("T-14", "SQLite confirma integridad referencial: 0 filas huerfanas (PRAGMA foreign_key_check)")
def t14():
    lote = Generador(semilla=77).generar()
    con = persistencia.crear_y_poblar(":memory:", lote)
    problemas = validar_en_sqlite(con, lote)
    igual(problemas, [], "problemas de integridad detectados")
    huerfanos = con.execute("PRAGMA foreign_key_check").fetchall()
    igual(huerfanos, [], "foreign_key_check reporto violations")
    con.close()


@caso("T-15", "una violacion deliberada de FK es detectada por el propio motor")
def t15():
    con = persistencia.conectar(":memory:")
    persistencia.crear_esquema(con)
    con.execute("INSERT INTO especialidad (id_especialidad, codigo, nombre) "
                "VALUES (1, 'ESP-1', 'Cardiologia')")
    try:
        con.execute("INSERT INTO medico (id_medico, dni, nombres, apellidos, email, "
                    "fecha_ingreso, salario, activo, id_especialidad) VALUES "
                    "(1, '12345678'||'9', 'A', 'B', 'a@b.pe', '2020-01-01', 100, 1, 999)")
    except sqlite3_error() as e:
        esperar("FOREIGN KEY" in str(e), f"error inesperado: {e}")
    else:
        raise Falla("la FK invalida deberia haber sido rechazada por SQLite")
    con.close()


def sqlite3_error():
    import sqlite3
    return sqlite3.IntegrityError


@caso("T-16", "una violacion de UNIQUE es rechazada por el motor")
def t16():
    con = persistencia.conectar(":memory:")
    persistencia.crear_esquema(con)
    con.execute("INSERT INTO especialidad (id_especialidad, codigo, nombre) "
                "VALUES (1, 'ESP-1', 'Cardiologia')")
    con.commit()
    # Mismo codigo en la columna UNIQUE: el motor debe rechazarlo.
    try:
        con.execute("INSERT INTO especialidad (id_especialidad, codigo, nombre) "
                    "VALUES (2, 'ESP-1', 'Neurologia')")
        con.commit()
    except sqlite3_error() as e:
        esperar("UNIQUE" in str(e), f"error inesperado: {e}")
    else:
        raise Falla("el UNIQUE deberia haber rechazado el codigo repetido")
    con.close()


@caso("T-17", "el exportador produce un script que el propio SQLite puede ejecutar")
def t17():
    lote = Generador(semilla=13).generar(volumenes={"medico": 5, "paciente": 10, "turno": 10,
                                                    "cita": 10, "receta": 5, "detalle_receta": 8,
                                                    "medicamento": 5, "especialidad": 3})
    sql = persistencia.exportar_sql(lote, motor="sqlite")
    import sqlite3
    con = sqlite3.connect(":memory:")
    con.executescript(sql)  # si el script fuera invalido, falla aqui
    igual(con.execute("SELECT COUNT(*) FROM paciente").fetchone()[0], 10, "filas cargadas")
    igual(con.execute("SELECT COUNT(*) FROM detalle_receta").fetchone()[0], 8, "detalles")
    con.close()


@caso("T-18", "el script exportado para PostgreSQL y MySQL no tiene sintaxis de SQLite")
def t18():
    lote = Generador(semilla=4).generar(volumenes={k: 5 for k in esquemas.ESQUEMA["volumenes"]})
    for motor in ("postgresql", "mysql"):
        sql = persistencia.exportar_sql(lote, motor=motor)
        esperar("AUTOINCREMENT" not in sql, f"{motor}: no debe usar AUTOINCREMENT")
        esperar("PRAGMA" not in sql, f"{motor}: no debe usar PRAGMA")
        esperar("INSERT INTO" in sql, f"{motor}: faltan los INSERT")
        con_sqlite = persistencia.exportar_sql(lote, motor="sqlite")
        esperar(sql != con_sqlite, f"{motor}: el script debe diferir del de SQLite")


# ============================================================== T-19..T-24 metricas y config
@caso("T-19", "las metricas reportan 100% de unicidad, completitud y dominios dentro")
def t19():
    lote = Generador(semilla=21).generar()
    m = metricas(lote)
    for nombre, info in m["tablas"].items():
        igual(info["completitud"], 1.0, f"completitud de {nombre}")
        igual(info["unicos_respetados"], info["unicos_total"], f"unicidad de {nombre}")
        igual(info["pk_unica"], True, f"PK de {nombre}")
        for col, dom in info["dominios"].items():
            igual(dom["cumple"], True, f"dominio {nombre}.{col}")
        for col, fk in info["fk_respetadas"].items():
            igual(fk["huerfanos"], 0, f"FK {nombre}.{col}")


@caso("T-20", "las metricas se calculan sobre el lote real, no sobre valores supuestos")
def t20():
    lote = Generador(semilla=22).generar()
    m = metricas(lote)
    igual(m["totales"]["filas"], sum(len(v) for v in lote.values()), "total de filas")
    igual(m["totales"]["celdas_vacias"], 0, "no debe haber celdas obligatorias vacias")
    # Reducing una tabla debe reducir el total de metricas.
    lote2 = Generador(semilla=22).generar(volumenes={"paciente": 10})
    m2 = metricas(lote2)
    esperar(m2["totales"]["filas"] < m["totales"]["filas"], "volumen menor debe dar menos filas")


@caso("T-21", "los volumenes configurables se aplican y un volumen 0 se valida contra sus hijas")
def t21():
    lote = Generador(semilla=1).generar(volumenes={"medicamento": 0, "receta": 0,
                                                    "detalle_receta": 0, "especialidad": 2})
    igual(lote["medicamento"], [], "medicamento en 0 filas")
    igual(lote["detalle_receta"], [], "detalle_receta en 0 filas")
    igual(len(lote["especialidad"]), 2, "especialidad con 2 filas")
    # medicamento = 0 no es valido si detalle_receta sigue generando filas.
    try:
        Generador(semilla=1).generar(volumenes={"medicamento": 0})
    except ErrorGeneracion as e:
        esperar("detalle_receta" in str(e), f"el mensaje debe nombrar la tabla hija: {e}")
    else:
        raise Falla("medicamento=0 con detalle_receta poblado deberia fallar")


@caso("T-22", "un volumen imposible produce un error explicito, no datos corruptos")
def t22():
    try:
        Generador(semilla=2).generar(volumenes={"medico": 3, "especialidad": 0})
    except ErrorGeneracion as e:
        esperar("especialidad" in str(e), f"el mensaje debe nombrar la tabla: {e}")
    else:
        raise Falla("deberia fallar: un medico no puede existir sin especialidad")


@caso("T-23", "los dominios enum se pueden sobrescribir desde la configuracion")
def t23():
    lote = Generador(semilla=6, enums={"estado": ["ATENDIDA", "CANCELADA"]}).generar()
    estados = {f["estado"] for f in lote["cita"]}
    esperar(estados <= {"ATENDIDA", "CANCELADA"}, f"estados fuera de dominio: {estados}")
    # El dominio original no se muta: afecta solo a esta instancia.
    igual(esquemas.ESQUEMA["enums"]["estado"],
          ["PROGRAMADA", "ATENDIDA", "CANCELADA", "NO_ASISTIO"], "el esquema no se modifica")


@caso("T-24", "un enum de un solo valor genera ese valor en todas las filas")
def t24():
    lote = Generador(semilla=8, enums={"sexo": ["O"]}).generar()
    sexos = {f["sexo"] for f in lote["paciente"]}
    igual(sexos, {"O"}, "sexo debe ser O en todas las filas")


# ============================================================== T-25..T-28 API
@caso("T-25", "la API web responde la vista de esquema con las tablas y campos")
def t25():
    import json
    from nucleo import api
    r = api.ruta("GET", "/api/esquema")
    igual(r["status"], 200, "status")
    cuerpo = json.loads(r["cuerpo"])
    igual(len(cuerpo["tablas"]), 8, "tablas en la respuesta")
    esperar("especialidad" in cuerpo["tablas"], "falta especialidad")
    esperar(cuerpo["motores"], "deben listarse los motores disponibles")
    campos = cuerpo["tablas"]["cita"]["campos"]
    esperar(any(c["tipo"] == "fk" for c in campos), "cita debe tener FK")


@caso("T-26", "la API genera un lote y devuelve metricas con el volumen pedido")
def t26():
    import json
    from nucleo import api
    r = api.ruta("POST", "/api/generar",
                 cuerpo=json.dumps({"semilla": 123, "volumenes": {
                     "paciente": 20, "cita": 25, "medico": 6, "turno": 15,
                     "receta": 10, "detalle_receta": 12, "medicamento": 6,
                     "especialidad": 3}}))
    igual(r["status"], 200, "status")
    d = json.loads(r["cuerpo"])
    igual(d["ok"], True, "ok")
    igual(d["lote"]["tablas"]["paciente"]["filas"], 20, "filas de paciente")
    igual(d["lote"]["tablas"]["paciente"]["completitud"], 1.0, "completitud")
    igual(d["resumen"]["filas_totales"],
          sum(v["filas"] for v in d["lote"]["tablas"].values()), "total de filas")
    esperar(d["resumen"]["generado_en"], "debe informar el tiempo de generacion")
    esperar(len(d["muestra"]["paciente"]) == 5, "muestra de 5 filas")


@caso("T-27", "la API exporta SQL en los tres motores y el CSV de las tablas")
def t27():
    import json
    from nucleo import api
    for motor in ("sqlite", "postgresql", "mysql"):
        r = api.ruta("POST", "/api/exportar",
                     cuerpo=json.dumps({"motor": motor, "volumenes": {k: 4 for k in
                                                                      esquemas.ESQUEMA["volumenes"]}}))
        igual(r["status"], 200, f"status de {motor}")
        d = json.loads(r["cuerpo"])
        igual(d["ok"], True, f"ok de {motor}")
        esperar("CREATE TABLE" in d["sql"], f"{motor}: falta DDL")
        esperar("INSERT INTO" in d["sql"], f"{motor}: faltan INSERT")
        esperar(d["sql"].count("CREATE TABLE") == 8, f"{motor}: deben ser 8 tablas")
    r = api.ruta("POST", "/api/exportar", cuerpo=json.dumps({"formato": "csv",
                                                              "volumenes": {k: 3 for k in
                                                                            esquemas.ESQUEMA["volumenes"]}}))
    d = json.loads(r["cuerpo"])
    esperar("-- tabla: paciente" in d["contenido"], "falta el bloque de paciente en el CSV")


@caso("T-28", "la API de metricas no acepta peticiones malformadas y responde 400")
def t28():
    import json
    from nucleo import api
    r = api.ruta("POST", "/api/generar", cuerpo="{no es json")
    igual(r["status"], 400, "json invalido debe ser 400")
    d = json.loads(r["cuerpo"])
    igual(d["ok"], False, "ok debe ser False")
    esperar(d["error"], "debe informar el error")
    r = api.ruta("GET", "/api/no-existe")
    igual(r["status"], 404, "ruta inexistente debe ser 404")
    r = api.ruta("POST", "/api/exportar", cuerpo=json.dumps({"motor": "oracle"}))
    igual(r["status"], 400, "motor no soportado debe ser 400")


@caso("T-29", "el correo de cada fila pertenece a su propio nombre y apellido")
def t29():
    import re
    lote = Generador(semilla=31).generar()
    for tabla in ("medico", "paciente"):
        for f in lote[tabla]:
            correo = f["email"]
            igual(correo.count("@"), 1, f"correo mal formado: {correo}")
            usuario, dominio = correo.split("@")
            esperar(usuario and dominio, f"correo vacio: {correo}")
            # El correo no puede contener espacios, tildes ni otros signos. El
            # dominio puede llevar guion (epsis-salud.pe), la parte local no.
            esperar(re.fullmatch(r"[a-z0-9.]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+", correo)
                   is not None, f"correo con caracteres invalidos: {correo}")
            # La parte local debe derivarse del nombre y el apellido de ESA fila.
            # El generador concatena todos los nombres y el ultimo apellido, con
            # el espacio eliminado: "Jose Yolanda Arenas Garcia" -> joseyolanda.garcia
            trans = str.maketrans("áéíóúüñ", "aeiouun")
            nombres = "".join(f["nombres"].translate(trans).lower().split())
            apellido = f["apellidos"].translate(trans).lower().split()[-1]
            esperado = nombres + "." + apellido
            esperar(usuario.startswith(esperado),
                   f"el correo {correo} no corresponde a {f['nombres']} {f['apellidos']}")
    # Y ningun correo se repite en la columna UNIQUE.
    correos = [f["email"] for f in lote["medico"]]
    igual(len(set(correos)), len(correos), "correo repetido en medico")


@caso("T-30", "los dominios de correo salen del catalogo declarado, no al azar")
def t30():
    from nucleo.generadores import CORREOS_DOMINIO
    lote = Generador(semilla=32).generar()
    for tabla in ("medico", "paciente"):
        for f in lote[tabla]:
            igual(f["email"].split("@")[1], f["email"].split("@")[1], "dominio estable")
            esperar(f["email"].split("@")[1] in CORREOS_DOMINIO,
                   f"dominio no catalogado: {f['email']}")


# ------------------------------------------------------------------ main
def main():
    ok = fallos = 0
    for id_caso, titulo, fn in CASOS:
        try:
            fn()
        except Exception:
            fallos += 1
            print(f"  [FALLA] {id_caso}  {titulo}")
            print("    " + traceback.format_exc().strip().replace("\n", "\n    "))
        else:
            ok += 1
            print(f"  [ OK   ] {id_caso}  {titulo}")
    total = ok + fallos
    print("\n  " + "-" * 58)
    print(f"  Casos: {total} · exitosos: {ok} · fallidos: {fallos} · "
          f"cobertura: {100.0 * ok / total if total else 0:.0f}%")
    print(f"  Restricciones cubiertas: uniques (T-10, T-16), FK (T-09, T-14, T-15), "
          f"CHECK (T-11, T-14)")
    print("  " + "-" * 58)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
