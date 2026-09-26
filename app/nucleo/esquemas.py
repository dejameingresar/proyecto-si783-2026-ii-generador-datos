"""nucleo.esquemas — definición declarativa del esquema EPSIS Salud.

Cada tabla se declara con campos, generador asociado, clave foránea y
restricciones. De esta única definición salen: el DDL de SQLite/PostgreSQL/MySQL
(nucleo.ddl), la generación de datos (nucleo.motor) y la validación en memoria
(nucleo.motor), de modo que la base creada y el script exportado no pueden
divergir.
"""

# Orden de inserción: primero las tablas padrem, después las hijas. También es
# el orden en que el DDL emite los CREATE TABLE.
ORDEN_INSERCCION = [
    "especialidad",
    "medico",
    "paciente",
    "turno",
    "cita",
    "medicamento",
    "receta",
    "detalle_receta",
]

TABLAS = {
    "especialidad": {
        "nombre": "especialidad",
        "descripcion": "Catalogo de especialidades medicas de la clinica",
        "campos": [
            {"nombre": "id_especialidad", "tipo": "int", "pk": True, "nullable": False},
            {"nombre": "codigo", "tipo": "varchar", "largo": 10, "unique": True,
             "nullable": False, "generador": "codigo", "prefijo": "ESP"},
            {"nombre": "nombre", "tipo": "varchar", "largo": 60, "unique": True,
             "nullable": False, "generador": "especialidad_nombre"},
            {"nombre": "descripcion", "tipo": "text", "nullable": True,
             "generador": "especialidad_descripcion"},
        ],
        "unicas": [],
        "indices": [{"columnas": ["nombre"]}],
    },
    "medico": {
        "nombre": "medico",
        "campos": [
            {"nombre": "id_medico", "tipo": "int", "pk": True, "nullable": False},
            {"nombre": "dni", "tipo": "dni", "unique": True, "nullable": False,
             "generador": "dni"},
            {"nombre": "nombres", "tipo": "varchar", "largo": 80, "nullable": False,
             "generador": "nombres"},
            {"nombre": "apellidos", "tipo": "varchar", "largo": 80, "nullable": False,
             "generador": "apellidos"},
            {"nombre": "email", "tipo": "email", "unique": True, "nullable": False,
             "derivado": "email_de_fila"},
            {"nombre": "telefono", "tipo": "telefono", "nullable": True,
             "generador": "telefono"},
            {"nombre": "fecha_ingreso", "tipo": "date", "nullable": False,
             "generador": "fecha_ingreso"},
            {"nombre": "salario", "tipo": "decimal", "precision": 10, "escala": 2,
             "nullable": False, "generador": "salario", "validacion": "mayor_que_0"},
            {"nombre": "activo", "tipo": "bool", "nullable": False, "default": "1",
             "generador": "booleano", "validacion": "booleano"},
            {"nombre": "id_especialidad", "tipo": "fk", "nullable": False,
             "tabla_ref": "especialidad", "columna_ref": "id_especialidad",
             "on_delete": "RESTRICT"},
        ],
        "unicas": [],
        "indices": [{"columnas": ["id_especialidad"]}],
    },
    "paciente": {
        "nombre": "paciente",
        "campos": [
            {"nombre": "id_paciente", "tipo": "int", "pk": True, "nullable": False},
            {"nombre": "dni", "tipo": "dni", "unique": True, "nullable": False,
             "generador": "dni"},
            {"nombre": "nombres", "tipo": "varchar", "largo": 80, "nullable": False,
             "generador": "nombres"},
            {"nombre": "apellidos", "tipo": "varchar", "largo": 80, "nullable": False,
             "generador": "apellidos"},
            {"nombre": "fecha_nacimiento", "tipo": "date", "nullable": False,
             "generador": "nacimiento"},
            {"nombre": "sexo", "tipo": "enum", "enum": ["M", "F", "O"], "nullable": False},
            {"nombre": "email", "tipo": "email", "nullable": True,
             "derivado": "email_de_fila"},
            {"nombre": "telefono", "tipo": "telefono", "nullable": True,
             "generador": "telefono"},
            {"nombre": "direccion", "tipo": "varchar", "largo": 160, "nullable": True,
             "generador": "direccion"},
            {"nombre": "fecha_registro", "tipo": "date", "nullable": False,
             "generador": "fecha_registro"},
        ],
        "unicas": [],
        "indices": [{"columnas": ["apellidos"]}],
    },
    "turno": {
        "nombre": "turno",
        "campos": [
            {"nombre": "id_turno", "tipo": "int", "pk": True, "nullable": False},
            {"nombre": "id_medico", "tipo": "fk", "nullable": False,
             "tabla_ref": "medico", "columna_ref": "id_medico", "on_delete": "CASCADE"},
            {"nombre": "fecha", "tipo": "date", "nullable": False,
             "generador": "fecha_registro"},
            {"nombre": "hora_inicio", "tipo": "time", "nullable": False,
             "generador": "hora"},
            {"nombre": "hora_fin", "tipo": "time", "nullable": False,
             "generador": "hora", "validacion": "fin_despues_inicio",
             "ref_inicio": "hora_inicio", "ref_fin": "hora_fin"},
            {"nombre": "consulta", "tipo": "varchar", "largo": 40, "nullable": False,
             "generador": "tipo_consulta"},
        ],
        "unicas": [["id_medico", "fecha", "hora_inicio"]],
        "indices": [{"columnas": ["fecha"]}],
    },
    "cita": {
        "nombre": "cita",
        "campos": [
            {"nombre": "id_cita", "tipo": "int", "pk": True, "nullable": False},
            {"nombre": "codigo", "tipo": "varchar", "largo": 12, "unique": True,
             "nullable": False, "generador": "codigo", "prefijo": "CIT"},
            {"nombre": "id_paciente", "tipo": "fk", "nullable": False,
             "tabla_ref": "paciente", "columna_ref": "id_paciente",
             "on_delete": "RESTRICT"},
            {"nombre": "id_turno", "tipo": "fk", "nullable": False,
             "tabla_ref": "turno", "columna_ref": "id_turno", "on_delete": "CASCADE"},
            {"nombre": "fecha", "tipo": "date", "nullable": False,
             "generador": "fecha_registro"},
            {"nombre": "hora", "tipo": "time", "nullable": False, "generador": "hora"},
            {"nombre": "estado", "tipo": "enum",
             "enum": ["PROGRAMADA", "ATENDIDA", "CANCELADA", "NO_ASISTIO"],
             "nullable": False},
            {"nombre": "motivo", "tipo": "varchar", "largo": 120, "nullable": False,
             "generador": "diagnostico"},
        ],
        "unicas": [],
        "indices": [{"columnas": ["id_paciente"]}, {"columnas": ["fecha"]}],
    },
    "medicamento": {
        "nombre": "medicamento",
        "descripcion": "Farmaco en existencia, con precio y stock",
        "campos": [
            {"nombre": "id_medicamento", "tipo": "int", "pk": True, "nullable": False},
            {"nombre": "codigo", "tipo": "varchar", "largo": 12, "unique": True,
             "nullable": False, "generador": "codigo", "prefijo": "MED"},
            {"nombre": "nombre", "tipo": "varchar", "largo": 80, "unique": True,
             "nullable": False, "generador": "medicamento_nombre"},
            {"nombre": "categoria", "tipo": "varchar", "largo": 40, "nullable": False,
             "generador": "medicamento_categoria"},
            {"nombre": "presentacion", "tipo": "varchar", "largo": 60, "nullable": True,
             "generador": "medicamento_presentacion"},
            {"nombre": "precio_unitario", "tipo": "decimal", "precision": 10, "escala": 2,
             "nullable": False, "generador": "precio", "validacion": "mayor_que_0"},
            {"nombre": "stock", "tipo": "int", "nullable": False, "default": "0",
             "generador": "stock", "validacion": "no_negativo"},
        ],
        "unicas": [],
        "indices": [{"columnas": ["categoria"]}],
    },
    "receta": {
        "nombre": "receta",
        "campos": [
            {"nombre": "id_receta", "tipo": "int", "pk": True, "nullable": False},
            {"nombre": "id_cita", "tipo": "fk", "nullable": True,
             "tabla_ref": "cita", "columna_ref": "id_cita", "on_delete": "SET NULL"},
            {"nombre": "id_medico", "tipo": "fk", "nullable": False,
             "tabla_ref": "medico", "columna_ref": "id_medico", "on_delete": "RESTRICT"},
            {"nombre": "fecha_emision", "tipo": "date", "nullable": False,
             "generador": "fecha_registro"},
            {"nombre": "diagnostico", "tipo": "varchar", "largo": 120, "nullable": False,
             "generador": "diagnostico"},
            {"nombre": "observaciones", "tipo": "text", "nullable": True,
             "generador": "observacion"},
        ],
        "unicas": [],
        "indices": [{"columnas": ["id_cita"]}],
    },
    "detalle_receta": {
        "nombre": "detalle_receta",
        "campos": [
            {"nombre": "id_detalle", "tipo": "int", "pk": True, "nullable": False},
            {"nombre": "id_receta", "tipo": "fk", "nullable": False,
             "tabla_ref": "receta", "columna_ref": "id_receta", "on_delete": "CASCADE"},
            {"nombre": "id_medicamento", "tipo": "fk", "nullable": False,
             "tabla_ref": "medicamento", "columna_ref": "id_medicamento",
             "on_delete": "RESTRICT"},
            {"nombre": "cantidad", "tipo": "int", "nullable": False,
             "generador": "cantidad", "validacion": "mayor_que_0"},
            {"nombre": "dosis", "tipo": "varchar", "largo": 80, "nullable": False,
             "generador": "dosis"},
            {"nombre": "duracion_dias", "tipo": "int", "nullable": False,
             "generador": "duracion_dias", "validacion": "mayor_que_0"},
        ],
        "unicas": [["id_receta", "id_medicamento"]],
        "indices": [{"columnas": ["id_medicamento"]}],
    },
}

ESQUEMA = {
    "nombre": "epsis_salud",
    "titulo": "EPSIS Salud — clinica de especialidades medicas",
    "resumen": (
        "8 tablas: especialidad, medico, paciente, turno, cita, medicamento, "
        "receta y detalle_receta. Incluye claves foraneas, uniques compuestos, "
        "indices y restricciones CHECK."
    ),
    "tablas": TABLAS,
    "orden_insercion": ORDEN_INSERCCION,
    # Valores por defecto de los campos enum: el motor los usa y el usuario puede
    # cambiarlos desde la UI.
    "enums": {
        "sexo": ["M", "F", "O"],
        "estado": ["PROGRAMADA", "ATENDIDA", "CANCELADA", "NO_ASISTIO"],
    },
    # Cuántas filas genera la app por tabla con los parámetros por defecto.
    "volumenes": {
        "especialidad": 8,
        "medico": 25,
        "paciente": 120,
        "turno": 180,
        "cita": 400,
        "medicamento": 30,
        "receta": 150,
        "detalle_receta": 300,
    },
}


def tabla(nombre):
    if nombre not in TABLAS:
        raise KeyError(f"tabla inexistente en el esquema: {nombre}")
    return TABLAS[nombre]


def columnas(tbl):
    return [c["nombre"] for c in tbl["campos"]]
