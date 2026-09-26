# DataForge

### Generador de datos de prueba para bases de datos relacionales, a partir de una definición declarativa de esquema

**Asignatura:** SI-783 Base de Datos II · Ciclo 7 · 2026-II
**Integrantes:** Patrick Elvis Rodriguez Cardenas (2022075751) · Nicole Luciana Rios Cohaila (2022075745)
**Docente:** Ing. Patrick Jose Cuadros Quiroga

---

## Aplicación

Funciona y es ejecutable con solo la biblioteca estándar de Python:

```bash
python3 app.py          # abre http://127.0.0.1:8000
```

Sin `pip install`, sin `node_modules`, sin servidor de base de datos: `sqlite3`,
`http.server` y `random` vienen con Python. Las tres verificaciones que se pueden
ejecutar desde la terminal:

```bash
python3 app/tests/casos.py        # 30 casos de prueba del núcleo · sale != 0 si falla
python3 app/tests/linea_base.py   # medición comparada que respalda el objetivo OI5
python3 app/tests/smoke.py        # recorrido del flujo real en Chromium
```

- Detalle de la aplicación, reglas y estructura: [`app/README.md`](app/README.md)
- Salida real de las tres verificaciones: [`app/tests/EVIDENCIAS.md`](app/tests/EVIDENCIAS.md)

## Entregables por semana

| Semana | Entregable | Estado |
| :- | :- | :- |
| 1 | Título, problema detallado con fuentes, objetivos de investigación y solución medibles | Este documento (secciones 1-4) |
| 2 | FD01 Informe de Factibilidad · FD02 Informe de Visión | `FD01-EPIS-Informe de Factibilidad-DataForge.docx` · `FD02-EPIS-Informe Vision-DataForge.docx` |
| 3 | FD03 Informe SRS · FD04 Informe SAD | `FD03-EPIS-Informe SRS-DataForge.docx` · `FD04-EPIS-Informe SAD-DataForge.docx` |
| 4-6 | Aplicación desplegada + automatizaciones que generan diagramas y manuales desde el repositorio | `.github/workflows/` · pendiente de fijar el destino de despliegue |

## 1. Título

**DataForge: generador de datos de prueba para bases de datos relacionales a partir
de una definición declarativa de esquema.**

La herramienta recibe la definición de un esquema relacional (tablas, columnas,
tipos, claves primarias, foráneas, únicas, índices y restricciones `CHECK`) y produce
un lote de datos coherente con ese esquema, más el script `CREATE TABLE` + `INSERT`
listo para ejecutarse en SQLite, PostgreSQL o MySQL. La misma definición declarativa
alimenta las tres salidas, de modo que la base que se crea en la demo y el script que
se entrega no pueden divergir entre sí.

## 2. Problema detallado (con fuentes)

Para desarrollar y probar una aplicación contra una base de datos hace falta un volumen
de datos que *parezca real* y que, sobre todo, sea **válido**: que no rompa las claves
foráneas, que no duplique valores declarados únicos, que no se salga del dominio de una
columna `CHECK` y que no deje campos obligatorios vacíos. El generador que no conoce
esas restricciones produce justo el resultado contrario —el conjunto de datos que de
verdad rompe la aplicación— y el equipo termina poblando tablas a mano: archivos `.sql`
gigantes, tiempos de carga largos y scripts de borrado que nadie recuerda ejecutar.

Las herramientas comerciales de generación de datos resuelven el volumen pero no la
trazabilidad: no explican de dónde sale cada restricción, no son reproducibles, y su
salida suele quedar atada a un único motor. Los scripts de relleno a medida, en cambio,
no se reutilizan y cada proyecto empieza de cero.

- **El repositorio de la Facultad (`github.com/UPT-FAING-EPIS`) muestra el formato que
  se espera de un proyecto de base de datos** —esquema, DDL y datos de ejemplo—, pero los
  proyectos de cursos anteriores no ofrecen una herramienta reutilizable que genere
  ese volumen de forma verificable. Este proyecto ocupa ese espacio: usa lo previo como
  base, no como copia. [Fuente: github.com/UPT-FAING-EPIS]
- **ProblemHunt define que un problema es válido cuando hay usuarios dispuestos a pagar
  por su solución**; la generación de datos de prueba es una necesidad recurrente de
  cualquier equipo que valide software contra una base real, y la vía de pago es evitar
  el trabajo manual de poblar tablas. [Fuente: problemhunt.pro]
- **Renati (SUNEDU) se referencia como marco de investigación sobre digitalización y
  trazabilidad**, según la guía de fuentes del curso. En ese marco, poder justificar que
  los datos generados cumplen el esquema es lo que convierte un conjunto de filas en una
  evidencia de prueba reproducible. [Fuente: renati.sunedu.gob.pe]
- **Radio Uno (`radiouno.pe`) difunde de forma constante noticias sobre servicios y
  sistemas digitales locales**, lo que evidencia la actividad de desarrollo de software
  en la región y la demanda de bases de datos bien pobladas para probar esos sistemas.
  [Fuente: radiouno.pe]

El problema concreto que ataca DataForge es, en una frase: **no existe una herramienta
de escritorio o web, sin dependencias, que genere datos de prueba coherentes con las
restricciones de un esquema relacional y entregue a la vez el mismo lote en los tres
motores más usados, de forma reproducible y con la evidencia de que el lote es válido.**

## 3. Objetivos de investigación (medibles)

- **OI1.** Determinar en qué medida un generador que conoce las restricciones del esquema
  produce lotes sin violaciones de integridad referencial.
  > *Medible:* con la semilla 2026 y los volúmenes por defecto, `PRAGMA foreign_key_check`
  > sobre la base SQLite creada devuelve **0 violaciones**, y las 8 columnas de clave
  > foránea del esquema reportan **0 filas huérfanas** (T-14, reproducido en
  > `app/tests/EVIDENCIAS.md`).

- **OI2.** Evaluar si el lote generado respeta las restricciones declaradas: unicidad de
  claves primarias y de columnas `UNIQUE`, unicidad de restricciones compuestas y
  dominios de las columnas enumeradas.
  > *Medible:* **8/8** columnas `UNIQUE` sin repeticiones, **0** duplicados en las 2
  > restricciones `UNIQUE` compuestas (`turno`, `detalle_receta`) y **0** valores fuera
  > de dominio en las 2 columnas `enum` (T-10, T-19, T-20).

- **OI3.** Comprobar que la generación es **reproducible**: la misma entrada produce
  exactamente la misma salida.
  > *Medible:* `Generador(semilla=42).generar()` ejecutado dos veces produce objetos
  > idénticos, y semillas distintas (42 y 43) producen lotes distintos (T-08).

- **OI4.** Verificar que una única definición declarativa produce DDL válido y
  equivalente en SQLite, PostgreSQL y MySQL.
  > *Medible:* los tres scripts contienen las 8 tablas, y cada tipo se traduce al
  > equivalente nativo del motor (`BOOLEAN` en PostgreSQL, `TINYINT(1)` y `ENUM(...)`
  > nativo en MySQL, `CHECK (sexo IN (...))` donde no hay `ENUM`). El script de
  > SQLite se ejecuta de principio a fin sobre un motor real (T-04, T-06, T-17).

- **OI5.** Estimar la tasa de datos defectuosos que produce el generador frente a un
  generador que solo conoce el tipo de cada columna, y su impacto sobre el trabajo de
  ajuste manual del lote.
  > *Medible:* con la misma semilla y 200 filas por tabla, un generador genérico (valores
  > al azar por tipo, que es lo que hacen las herramientas comerciales) logra que el motor
  > acepte **343 de 1 600 filas (21,4 %)** y rechace **1 257**, empezando por
  > `especialidad: UNIQUE constraint failed: especialidad.codigo` y perdiendo la tabla
  > `paciente` entera. DataForge acepta **1 213 de 1 213 filas (100 %)** del mismo
  > esquema, con **100 %** de completitud en las columnas obligatorias y 0 huérfanas
  > (T-13, T-19 y `app/tests/linea_base.py`).

## 4. Objetivos de solución (alcance del equipo)

- **OS1.** Implementar ladefinición declarativa del esquema (8 tablas, 57 columnas, 8
  claves foráneas, 8 columnas `UNIQUE`, 2 `UNIQUE` compuestas, 9 índices, 2 dominios
  `enum` y 7 restricciones `CHECK`).
  > *Medible:* el esquema se declara una sola vez en `app/nucleo/esquemas.py` y alimenta
  > el DDL, la generación de datos y la validación, sin duplicar definiciones.

- **OS2.** Implementar el motor de generación que respeta claves foráneas, unicidades y
  restricciones `CHECK`, con soporte de semilla y volúmenes configurables por tabla.
  > *Medible:* las 30 pruebas de `app/tests/casos.py` pasan y cubren las tres familias de
  > restricciones, incluidos los casos negativos (violación deliberada de FK y de
  > `UNIQUE` que el motor debe rechazar).

- **OS3.** Generar el DDL y el lote exportable en los tres motores, más CSV.
  > *Medible:* el botón de exportación produce el script correcto para PostgreSQL,
  > MySQL y SQLite, y un CSV con un bloque por tabla; el script de SQLite se ejecuta
  > sobre un motor real sin errores (T-17, T-18, T-27).

- **OS4.** Incorporar una verificación independiente que pregunte al propio motor si el
  lote es válido, en lugar de confiar en el generador.
  > *Medible:* `validar_en_sqlite` más `PRAGMA foreign_key_check` devuelven 0 problemas
  > sobre el lote cargado (T-14); la interfaz muestra ese resultado en vivo.

- **OS5.** Entregar una aplicación ejecutable sin dependencias, con interfaz web propia.
  > *Medible:* `python3 app.py` levanta la aplicación y `app/tests/smoke.py` recorre el
  > flujo completo (cargar, cambiar volumen, regenerar, verificar en SQLite, exportar a
  > los tres motores, CSV y provocar un error) con todos los pasos en verde y sin errores
  > de JavaScript ni respuestas 5xx.

- **OS6.** Publicar la aplicación en un servicio público y automatizar la generación de
  los diagramas y los manuales técnicos a partir del repositorio.
  > *Medible:* cada `push` a la rama principal dispara las automatizaciones de
  > `.github/workflows/`, que regeneran el diagrama ER, el diccionario de datos y el
  > manual técnico desde el código, y dejarlos disponibles en una URL pública.

## 5. Alcance y límites

- El esquema de demostración es **EPSIS Salud** (8 tablas de una clínica: especialidad,
  médico, paciente, turno, cita, medicamento, receta y detalle de receta). El generador
  no está atado a ese dominio: la definición de `esquemas.py` es el punto de extensión.
- Los datos son **sintéticos y de catálogo**, no registros reales de pacientes. Los
  nombres, apellidos, diagnósticos y medicamentos provienen de listas declaradas en
  `app/nucleo/generadores.py`; el DNI se genera con 8 dígitos porque es lo que RENIEC
  registra (el dígito verificador del DNI peruano no se imprime en el documento, se
  calcula bajo demanda).
- **No se conecta a ningún motor remoto.** SQLite es el motor de la demo porque no
  requiere instalación; PostgreSQL y MySQL se cubren por exportación del script.
- Las métricas de calidad se calculan sobre el lote **antes** de insertarlo, y se
  vuelven a comprobar sobre la base ya creada; son dos verificaciones independientes.

## 6. Estructura

```
proyecto-si783-2026-ii-generador-datos/
├── app.py                       Servidor HTTP (http.server) — sin dependencias
├── .github/workflows/           Automatizaciones (semanas 4-6)
├── docs/                        Diagramas y manuales generados
└── app/
    ├── nucleo/                  Núcleo sin dependencias del navegador
    │   ├── esquemas.py          Definición declarativa del esquema (fuente única)
    │   ├── generadores.py       Catálogos del dominio y generadores de valores
    │   ├── ddl.py               DDL portable a SQLite / PostgreSQL / MySQL
    │   ├── motor.py             Generación, métricas y verificación
    │   ├── persistencia.py      Carga en SQLite y exportación SQL / CSV
    │   └── api.py               API de la interfaz (probada desde la terminal)
    ├── web/                     Interfaz (HTML + CSS + JS sin framework)
    └── tests/
        ├── casos.py             30 pruebas del núcleo
        ├── smoke.py             Recorrido del flujo real en Chromium
        ├── linea_base.py        Medición comparada del objetivo OI5
        ├── EVIDENCIAS.md        Salida real de las tres verificaciones
        └── capturas/            Capturas del recorrido
```
