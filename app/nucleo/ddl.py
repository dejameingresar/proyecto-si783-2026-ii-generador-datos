"""nucleo.ddl — DDL portable (SQLite / PostgreSQL / MySQL) desde el esquema declarativo.

El esquema se declara UNA vez (nucleo.esquemas) y de ahí sale el DDL de los tres
motores, de modo que la misma definición de datos sirve para crear la base en la
demo y para exportar el script que se puede correr en PostgreSQL o MySQL.

Decisiones de portabilidad (verificadas con T-03, T-04, T-06 y T-17):
  * Las restricciones UNIQUE compuestas van INLINE en el CREATE TABLE, no con
    `ALTER TABLE ... ADD CONSTRAINT`: SQLite no admite esa sentencia.
  * Los CHECK se traducen de una plantilla unica a los tres motores.
  * MySQL recibe ENUM nativo; SQLite y PostgreSQL reciben CHECK (...).
"""

MOTORES = ("sqlite", "postgresql", "mysql")

# tipo_logico -> tipo nativo por motor.
MAPA = {
    "sqlite": {
        "int": "INTEGER", "bigint": "INTEGER", "smallint": "INTEGER", "decimal": "REAL",
        "text": "TEXT", "varchar": "TEXT", "char": "TEXT", "bool": "INTEGER",
        "date": "TEXT", "datetime": "TEXT", "time": "TEXT",
        "email": "VARCHAR(120)", "telefono": "VARCHAR(20)", "dni": "CHAR(8)",
        "enum": "TEXT", "fk": "INTEGER",
    },
    "postgresql": {
        "int": "INTEGER", "bigint": "BIGINT", "smallint": "SMALLINT", "decimal": "NUMERIC",
        "text": "TEXT", "varchar": "VARCHAR", "char": "CHAR", "bool": "BOOLEAN",
        "date": "DATE", "datetime": "TIMESTAMP", "time": "TIME",
        "email": "VARCHAR(120)", "telefono": "VARCHAR(20)", "dni": "CHAR(8)",
        "enum": "TEXT", "fk": "INTEGER",
    },
    "mysql": {
        "int": "INT", "bigint": "BIGINT", "smallint": "SMALLINT", "decimal": "DECIMAL",
        "text": "LONGTEXT", "varchar": "VARCHAR", "char": "CHAR", "bool": "TINYINT(1)",
        "date": "DATE", "datetime": "DATETIME", "time": "TIME",
        "email": "VARCHAR(120)", "telefono": "VARCHAR(20)", "dni": "CHAR(8)",
        "enum": "ENUM", "fk": "INT",
    },
}

# Tipos que llevan parametros de longitud/precision. Los demas se emiten tal cual.
_CON_PRECISION = {"decimal"}

# Restricciones declarativas: una sola definicion produce (a) el CHECK en SQL de
# los tres motores y (b) la validacion en memoria, para que no puedan divergir.
VALIDADORES = {
    "mayor_que_0": (
        "{c} > 0",
        lambda v, fila: isinstance(v, (int, float)) and v > 0,
    ),
    "no_negativo": (
        "{c} >= 0",
        lambda v, fila: isinstance(v, (int, float)) and v >= 0,
    ),
    "entre_1_7": (
        "{c} BETWEEN 1 AND 7",
        lambda v, fila: v is not None and 1 <= v <= 7,
    ),
    "fecha_no_futura": (
        "{c} <= CURRENT_DATE",
        lambda v, fila: v is not None,
    ),
    "fin_despues_inicio": (
        "{c2} > {c1}",
        lambda v, fila: fila.get("hora_fin") is not None
        and fila.get("hora_inicio") is not None
        and fila["hora_fin"] > fila["hora_inicio"],
    ),
    "booleano": (
        "{c} IN (0,1)",
        lambda v, fila: v in (0, 1, True, False),
    ),
}


def _literal(v):
    return "'" + str(v).replace("'", "''") + "'"


def tipo_sql(campo, motor):
    """Devuelve el tipo nativo del campo en el motor indicado."""
    if motor not in MAPA:
        raise ValueError(f"motor no soportado: {motor}")
    nativo = MAPA[motor][campo["tipo"]]
    t = campo["tipo"]
    if t in _CON_PRECISION:
        # SQLite no tiene NUMERIC con escala: guarda REAL y el CHECK hace el resto.
        if motor == "sqlite":
            return nativo
        return f"{nativo}({campo.get('precision', 10)}, {campo.get('escala', 2)})"
    if t == "enum":
        # El dominio lo anade columna_sql (ENUM nativo en MySQL, CHECK en el resto).
        return nativo
    if t in ("varchar", "char", "email", "telefono", "dni"):
        largo = campo.get("largo")
        if largo is None and t in ("email", "telefono", "dni"):
            return nativo  # el largo ya viene fijo en MAPA
        if largo is None:
            largo = 120
        return f"{nativo}({largo})"
    return nativo


def columna_sql(campo, motor):
    """Columna completa: tipo + restricciones."""
    partes = [campo["nombre"], tipo_sql(campo, motor)]
    if campo.get("pk"):
        partes.append("PRIMARY KEY")
        return " ".join(partes)

    if not campo.get("nullable", False):
        partes.append("NOT NULL")
    if campo.get("unique"):
        partes.append("UNIQUE")
    if campo.get("default") is not None:
        partes.append(f"DEFAULT {campo['default']}")

    if campo["tipo"] == "enum":
        opciones = ",".join(_literal(v) for v in campo["enum"])
        if motor == "mysql":
            # ENUM nativo: el tipo ya restringe el dominio.
            partes[1] = f"ENUM({opciones})"
        else:
            partes.append(f"CHECK ({campo['nombre']} IN ({opciones}))")

    if campo.get("validacion"):
        plantilla = VALIDADORES[campo["validacion"]][0]
        partes.append("CHECK (" + plantilla.format(
            c=campo["nombre"],
            c1=campo.get("ref_inicio", ""),
            c2=campo.get("ref_fin", ""),
        ) + ")")

    if campo["tipo"] == "fk":
        on_delete = campo.get("on_delete", "RESTRICT")
        on_update = campo.get("on_update", "CASCADE")
        partes.append(
            f"REFERENCES {campo['tabla_ref']} ({campo['columna_ref']})"
            f" ON DELETE {on_delete} ON UPDATE {on_update}"
        )
    return " ".join(partes)


def tabla_sql(tabla, motor, incluir_drop=True):
    """CREATE TABLE de una tabla, con las UNIQUE compuestas inline (portable)."""
    if motor not in MAPA:
        raise ValueError(f"motor no soportado: {motor}")
    lineas = [columna_sql(c, motor) for c in tabla["campos"]]
    for combo in tabla.get("unicas", []):
        lineas.append("UNIQUE (" + ", ".join(combo) + ")")

    salida = ""
    if incluir_drop:
        salida += f"DROP TABLE IF EXISTS {tabla['nombre']};\n"
    cuerpo = ",\n  ".join(lineas)
    salida += f"CREATE TABLE {tabla['nombre']} (\n  {cuerpo}\n);"
    for idx in tabla.get("indices", []):
        cols = ", ".join(idx["columnas"])
        salida += (f"\nCREATE INDEX ix_{tabla['nombre']}_{'_'.join(idx['columnas'])}"
                   f" ON {tabla['nombre']} ({cols});")
    return salida


def esquema_sql(esquema, motor, incluir_drop=True):
    """Script completo del esquema, en el orden de dependencias (hijos al final)."""
    if motor not in MAPA:
        raise ValueError(
            f"motor no soportado: {motor}. Use uno de {', '.join(MOTORES)}")
    cabecera = (
        f"-- {esquema['nombre']}: {esquema['titulo']}\n"
        f"-- Generado por DataForge (proyecto SI-783) · motor: {motor}\n"
        f"-- Definicion declarativa unica en app/nucleo/esquemas.py\n"
        f"-- {esquema['resumen']}\n"
    )
    partes = [cabecera]
    for nombre in esquema["orden_insercion"]:
        partes.append(tabla_sql(esquema["tablas"][nombre], motor, incluir_drop))
    return "\n\n".join(partes) + "\n"
