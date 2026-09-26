# Manual técnico — DataForge

Generador de datos de prueba para bases de datos relacionales.
**SI-783 Base de Datos II** · Patrick Elvis Rodriguez Cardenas (2022075751) ·
Nicole Luciana Rios Cohaila (2022075745).

> Documento generado por `docs/generar_documentos.py` desde el código del
> repositorio. Si el esquema o las pruebas cambian, este manual se regenera solo.

## 1. Qué hace

DataForge recibe la definición de un esquema relacional y produce (a) un lote de
datos que cumple todas las restricciones declaradas y (b) el script
`CREATE TABLE` + `INSERT` para SQLite, PostgreSQL o MySQL. Las dos salidas salen
de la **misma** definición declarativa, de modo que no pueden divergir.

## 2. Puesta en marcha

```bash
python3 app.py          # http://127.0.0.1:8000
```

Sin `pip install` ni servidor de base de datos: usa `sqlite3` y `http.server`,
ambos de la biblioteca estándar. Opciones: `--puerto N`, `--host H`,
`--sin-navegador`.

## 3. Arquitectura

| Módulo | Responsabilidad |
| :- | :- |
| `nucleo/esquemas.py` | Definición declarativa del esquema. Fuente única de verdad. |
| `nucleo/generadores.py` | Catálogos del dominio (nombres, diagnósticos, medicamentos) y generadores de valores. |
| `nucleo/ddl.py` | Traduce el esquema a DDL de SQLite, PostgreSQL y MySQL. |
| `nucleo/motor.py` | Genera el lote, calcula métricas y verifica contra el motor. |
| `nucleo/persistencia.py` | Carga en SQLite y exporta SQL y CSV. |
| `nucleo/api.py` | API de la interfaz. No depende del navegador, se prueba desde la terminal. |
| `app.py` | Servidor HTTP. Traduce HTTP a llamadas de `api.py`. |
| `web/` | Interfaz. Toda la lógica vive en el servidor. |

El núcleo no importa nada del navegador: las mismas funciones que usa la interfaz
se prueban desde la terminal, sin levantar el servidor.

## 4. El esquema

**EPSIS Salud — clinica de especialidades medicas** — 8 tablas: especialidad, medico, paciente, turno, cita, medicamento, receta y detalle_receta. Incluye claves foraneas, uniques compuestos, indices y restricciones CHECK.

Orden de generación (una tabla padre antes que sus hijas):

1. `especialidad`
2. `medico`
3. `paciente`
4. `turno`
5. `cita`
6. `medicamento`
7. `receta`
8. `detalle_receta`

## 5. Restricciones que respeta

| Restricción | Cómo la cumple |
| :- | :- |
| Clave primaria | Entero correlativo asignado por el motor |
| Clave foránea | Se elige entre identificadores que ya existen en la tabla padre |
| `UNIQUE` simple | Registro de valores usados; se reintenta si repite |
| `UNIQUE` compuesta | Se compara la combinación contra las filas ya generadas |
| `CHECK (col IN (...))` | Dominio cerrado, configurable |
| `CHECK (hora_fin > hora_inicio)` | Se evalúa con la fila completa |
| `NOT NULL` | Los campos obligatorios nunca salen vacíos |

## 6. Lote de ejemplo (semilla 2026)

Total: **1213** filas en 8 tablas.

| tabla | filas |
| :- | --: |
| `especialidad` | 8 |
| `medico` | 25 |
| `paciente` | 120 |
| `turno` | 180 |
| `cita` | 400 |
| `medicamento` | 30 |
| `receta` | 150 |
| `detalle_receta` | 300 |

- Unicidad: **8/8** columnas `UNIQUE` sin repeticiones.
- Completitud: **100 %**
  de las celdas obligatorias.
- Integridad referencial: **0** problemas al verificar contra
  SQLite con `PRAGMA foreign_key_check`.

## 7. Verificaciones

```bash
python3 app/tests/casos.py        # 30 casos del núcleo
python3 app/tests/linea_base.py   # medición comparada (OI5)
python3 app/tests/smoke.py        # flujo real en Chromium
```

## 8. Portabilidad

Una definición, tres motores. Tipos relevantes:

| Tipo lógico | SQLite | PostgreSQL | MySQL |
| :- | :- | :- | :- |
| booleano | `INTEGER` | `BOOLEAN` | `TINYINT(1)` |
| decimal | `REAL` | `NUMERIC(p,e)` | `DECIMAL(p,e)` |
| enum | `CHECK (col IN (...))` | `CHECK (col IN (...))` | `ENUM(...)` nativo |
| clave foránea | `REFERENCES` en línea | `REFERENCES` en línea | `REFERENCES` en línea |

Las restricciones `UNIQUE` compuestas van **en línea** en el `CREATE TABLE`, no
con `ALTER TABLE ... ADD CONSTRAINT`: SQLite no admite esa sentencia.

## 9. Límites conocidos

- Los datos son sintéticos y provienen de catálogos declarados; no son registros
  reales.
- El DNI tiene 8 dígitos porque es lo que RENIEC registra: el dígito verificador
  no se imprime en el documento, se calcula bajo demanda.
- No se conecta a motores remotos; PostgreSQL y MySQL se cubren por exportación.
