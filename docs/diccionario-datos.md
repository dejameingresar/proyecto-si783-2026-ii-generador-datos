# Diccionario de datos — EPSIS Salud — clinica de especialidades medicas

Generado por `docs/generar_documentos.py` desde `app/nucleo/esquemas.py`. No editar a mano.

8 tablas · 57 columnas.

## especialidad

_Catalogo de especialidades medicas de la clinica_

| columna | tipo (SQLite) | tipo (PostgreSQL) | nulos | clave | generador |
| :- | :- | :- | :- | :- | :- |
| `id_especialidad` | `INTEGER` | `INTEGER` | no | PK | — |
| `codigo` | `TEXT(10)` | `VARCHAR(10)` | no | UNIQUE | codigo |
| `nombre` | `TEXT(60)` | `VARCHAR(60)` | no | UNIQUE | especialidad_nombre |
| `descripcion` | `TEXT` | `TEXT` | sí |  | especialidad_descripcion |

Índices: (nombre).

## medico

| columna | tipo (SQLite) | tipo (PostgreSQL) | nulos | clave | generador |
| :- | :- | :- | :- | :- | :- |
| `id_medico` | `INTEGER` | `INTEGER` | no | PK | — |
| `dni` | `CHAR(8)` | `CHAR(8)` | no | UNIQUE | dni |
| `nombres` | `TEXT(80)` | `VARCHAR(80)` | no |  | nombres |
| `apellidos` | `TEXT(80)` | `VARCHAR(80)` | no |  | apellidos |
| `email` | `VARCHAR(120)` | `VARCHAR(120)` | no | UNIQUE | email_de_fila |
| `telefono` | `VARCHAR(20)` | `VARCHAR(20)` | sí |  | telefono |
| `fecha_ingreso` | `TEXT` | `DATE` | no |  | fecha_ingreso |
| `salario` | `REAL` | `NUMERIC(10, 2)` | no |  | salario |
| `activo` | `INTEGER` | `BOOLEAN` | no |  | booleano |
| `id_especialidad` | `INTEGER` | `INTEGER` | no | FK → especialidad.id_especialidad (RESTRICT) | — |

Índices: (id_especialidad).

## paciente

| columna | tipo (SQLite) | tipo (PostgreSQL) | nulos | clave | generador |
| :- | :- | :- | :- | :- | :- |
| `id_paciente` | `INTEGER` | `INTEGER` | no | PK | — |
| `dni` | `CHAR(8)` | `CHAR(8)` | no | UNIQUE | dni |
| `nombres` | `TEXT(80)` | `VARCHAR(80)` | no |  | nombres |
| `apellidos` | `TEXT(80)` | `VARCHAR(80)` | no |  | apellidos |
| `fecha_nacimiento` | `TEXT` | `DATE` | no |  | nacimiento |
| `sexo` | `TEXT` | `TEXT` | no |  | enum ['M', 'F', 'O'] |
| `email` | `VARCHAR(120)` | `VARCHAR(120)` | sí |  | email_de_fila |
| `telefono` | `VARCHAR(20)` | `VARCHAR(20)` | sí |  | telefono |
| `direccion` | `TEXT(160)` | `VARCHAR(160)` | sí |  | direccion |
| `fecha_registro` | `TEXT` | `DATE` | no |  | fecha_registro |

Índices: (apellidos).

## turno

| columna | tipo (SQLite) | tipo (PostgreSQL) | nulos | clave | generador |
| :- | :- | :- | :- | :- | :- |
| `id_turno` | `INTEGER` | `INTEGER` | no | PK | — |
| `id_medico` | `INTEGER` | `INTEGER` | no | FK → medico.id_medico (CASCADE) | — |
| `fecha` | `TEXT` | `DATE` | no |  | fecha_registro |
| `hora_inicio` | `TEXT` | `TIME` | no |  | hora |
| `hora_fin` | `TEXT` | `TIME` | no |  | hora |
| `consulta` | `TEXT(40)` | `VARCHAR(40)` | no |  | tipo_consulta |

Restricciones `UNIQUE` compuestas: (id_medico, fecha, hora_inicio).

Índices: (fecha).

## cita

| columna | tipo (SQLite) | tipo (PostgreSQL) | nulos | clave | generador |
| :- | :- | :- | :- | :- | :- |
| `id_cita` | `INTEGER` | `INTEGER` | no | PK | — |
| `codigo` | `TEXT(12)` | `VARCHAR(12)` | no | UNIQUE | codigo |
| `id_paciente` | `INTEGER` | `INTEGER` | no | FK → paciente.id_paciente (RESTRICT) | — |
| `id_turno` | `INTEGER` | `INTEGER` | no | FK → turno.id_turno (CASCADE) | — |
| `fecha` | `TEXT` | `DATE` | no |  | fecha_registro |
| `hora` | `TEXT` | `TIME` | no |  | hora |
| `estado` | `TEXT` | `TEXT` | no |  | enum ['PROGRAMADA', 'ATENDIDA', 'CANCELADA', 'NO_ASISTIO'] |
| `motivo` | `TEXT(120)` | `VARCHAR(120)` | no |  | diagnostico |

Índices: (id_paciente); (fecha).

## medicamento

_Farmaco en existencia, con precio y stock_

| columna | tipo (SQLite) | tipo (PostgreSQL) | nulos | clave | generador |
| :- | :- | :- | :- | :- | :- |
| `id_medicamento` | `INTEGER` | `INTEGER` | no | PK | — |
| `codigo` | `TEXT(12)` | `VARCHAR(12)` | no | UNIQUE | codigo |
| `nombre` | `TEXT(80)` | `VARCHAR(80)` | no | UNIQUE | medicamento_nombre |
| `categoria` | `TEXT(40)` | `VARCHAR(40)` | no |  | medicamento_categoria |
| `presentacion` | `TEXT(60)` | `VARCHAR(60)` | sí |  | medicamento_presentacion |
| `precio_unitario` | `REAL` | `NUMERIC(10, 2)` | no |  | precio |
| `stock` | `INTEGER` | `INTEGER` | no |  | stock |

Índices: (categoria).

## receta

| columna | tipo (SQLite) | tipo (PostgreSQL) | nulos | clave | generador |
| :- | :- | :- | :- | :- | :- |
| `id_receta` | `INTEGER` | `INTEGER` | no | PK | — |
| `id_cita` | `INTEGER` | `INTEGER` | sí | FK → cita.id_cita (SET NULL) | — |
| `id_medico` | `INTEGER` | `INTEGER` | no | FK → medico.id_medico (RESTRICT) | — |
| `fecha_emision` | `TEXT` | `DATE` | no |  | fecha_registro |
| `diagnostico` | `TEXT(120)` | `VARCHAR(120)` | no |  | diagnostico |
| `observaciones` | `TEXT` | `TEXT` | sí |  | observacion |

Índices: (id_cita).

## detalle_receta

| columna | tipo (SQLite) | tipo (PostgreSQL) | nulos | clave | generador |
| :- | :- | :- | :- | :- | :- |
| `id_detalle` | `INTEGER` | `INTEGER` | no | PK | — |
| `id_receta` | `INTEGER` | `INTEGER` | no | FK → receta.id_receta (CASCADE) | — |
| `id_medicamento` | `INTEGER` | `INTEGER` | no | FK → medicamento.id_medicamento (RESTRICT) | — |
| `cantidad` | `INTEGER` | `INTEGER` | no |  | cantidad |
| `dosis` | `TEXT(80)` | `VARCHAR(80)` | no |  | dosis |
| `duracion_dias` | `INTEGER` | `INTEGER` | no |  | duracion_dias |

Restricciones `UNIQUE` compuestas: (id_receta, id_medicamento).

Índices: (id_medicamento).
