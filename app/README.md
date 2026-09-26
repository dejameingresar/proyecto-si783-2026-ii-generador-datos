# DataForge — manual de la aplicación

Generador de datos de prueba para bases de datos relacionales. Todo con la
biblioteca estándar de Python: **sin `pip install`, sin `node_modules`, sin
servidor de base de datos**.

---

## 1. Cómo ejecutarla

```bash
python3 app.py                    # http://127.0.0.1:8000
python3 app.py --puerto 9000      # otro puerto
python3 app.py --sin-navegador    # no abrir el navegador
```

Requiere Python 3.9 o superior. `sqlite3`, `http.server` y `random` vienen con
el intérprete.

## 2. Qué hace

1. **Recibe un esquema declarativo** (`app/nucleo/esquemas.py`): 8 tablas, 57
   columnas, 8 claves foráneas, 8 columnas `UNIQUE`, 2 `UNIQUE` compuestas,
   9 índices, 2 dominios `enum` y 7 restricciones `CHECK`.
2. **Genera un lote coherente** con ese esquema, con semilla y volumen por tabla.
3. **Exporta el mismo lote** como script `CREATE TABLE` + `INSERT` para SQLite,
   PostgreSQL o MySQL, y también en CSV.
4. **Verifica el lote en la base real**: crea las tablas en SQLite, inserta y
   pregunta al propio motor si hay filas huérfanas o claves repetidas.

Las cuatro cosas salen de la **misma** definición del esquema, así que la base de
la demo y el script exportado no pueden divergir.

## 3. La interfaz, paso a paso

1. **Esquema declarativo.** Cada tabla tiene un deslizador con su número de
   filas. Las tablas con clave foránea muestran a qué tabla apuntan
   (`FK → paciente`). Los valores por defecto son los de la demo.
2. **Semilla.** El número de la esquina superior derecha. La misma semilla
   produce siempre el mismo lote; cambiarla produce otro distinto. Se usa para
   reproducir un caso concreto.
3. **Generar lote.** Calcula los datos y muestra, por tabla: filas, columnas,
   unicidad, completitud, si los dominios `enum` se respetan y cuántas filas
   huérfanas hay. Debajo aparecen muestras de filas reales.
4. **Cargar en SQLite.** Crea la base en memoria, inserta el lote y ejecuta
   `PRAGMA foreign_key_check`. Muestra el resultado, los conteos por tabla, las
   citas agrupadas por estado y el resultado de un `JOIN` de cinco tablas.
   **Este paso es la prueba de que los datos sirven.**
5. **Exportar.** Elige motor (PostgreSQL, MySQL, SQLite) o CSV, pulsa
   «Generar script» y descarga el archivo.

## 4. Reglas que respeta el generador

| Restricción | Cómo la cumple |
| :- | :- |
| Clave primaria | Entero correlativo asignado por el motor, nunca el generador |
| Clave foránea | Se elige entre los identificadores que ya existen en la tabla padre |
| `UNIQUE` simple | Se lleva registro de los valores ya usados y se reintenta si repite |
| `UNIQUE` compuesta | Se compara la combinación contra las filas ya generadas |
| `CHECK (col IN (...))` | Dominio cerrado; se puede cambiar desde la configuración |
| `CHECK (hora_fin > hora_inicio)` | Se evalúa con la fila completa, no campo por campo |
| `NOT NULL` | Los campos obligatorios nunca salen vacíos |
| Dependencia entre tablas | Se generan en orden: primero las padres, luego las hijas |

Si una petición es imposible (por ejemplo, vaciar `medicamento` mientras
`detalle_receta` sigue generando filas), la aplicación **lo explica y no genera
nada**, en vez de producir un lote corrupto.

## 5. Verificaciones

```bash
python3 app/tests/casos.py        # 30 pruebas del núcleo, sale != 0 si falla
python3 app/tests/linea_base.py   # medición comparada (objetivo OI5)
python3 app/tests/smoke.py        # flujo real en Chromium (requiere playwright)
```

La salida real de las tres está en [`tests/EVIDENCIAS.md`](tests/EVIDENCIAS.md).

## 6. Estructura

```
app/
├── nucleo/
│   ├── esquemas.py        Definición declarativa del esquema (fuente única)
│   ├── generadores.py     Catálogos del dominio y generadores de valores
│   ├── ddl.py             DDL portable a SQLite / PostgreSQL / MySQL
│   ├── motor.py           Generación, métricas y verificación
│   ├── persistencia.py    Carga en SQLite y exportación SQL / CSV
│   └── api.py             API de la interfaz (probada desde la terminal)
├── web/
│   ├── index.html         La página
│   ├── css/estilos.css
│   └── js/app.js          Controlador: toda la lógica vive en el servidor
└── tests/
```

El núcleo no importa nada del navegador: las mismas funciones que usa la
interfaz se prueban desde la terminal.

## 7. Adaptarla a otro dominio

1. Edita `TABLAS` en `app/nucleo/esquemas.py` y ajusta `orden_insercion`
   (una tabla padre debe ir antes que sus hijas).
2. Añade los tipos que needs en `MAPA` de `app/nucleo/ddl.py`, para los tres
   motores.
3. Añade o ajusta los catálogos y generadores en
   `app/nucleo/generadores.py`.
4. Ejecuta `python3 app/tests/casos.py`: los casos que dependen del esquema
   dirán qué falta.

## 8. Límites conocidos

- Los datos son **sintéticos y de catálogo**, no registros reales. Los nombres,
  diagnósticos y medicamentos salen de listas declaradas en
  `generadores.py`.
- El DNI tiene 8 dígitos porque es lo que RENIEC registra: el dígito
  verificador del DNI peruano no se imprime en el documento, se calcula bajo
  demanda contra un servicio externo.
- No se conecta a motores remotos. SQLite es el motor de la demo porque no
  requiere instalación; PostgreSQL y MySQL se cubren por exportación.
- El `CHECK` de MySQL usa `ENUM` nativo; en SQLite y PostgreSQL se traduce a
  `CHECK (col IN (...))`, que es el equivalente funcional.
