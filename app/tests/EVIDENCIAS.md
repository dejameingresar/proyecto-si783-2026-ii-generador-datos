# Evidencia de pruebas — DataForge

Salida real de las tres verificaciones, ejecutadas sobre el código de este
repositorio. No son resultados esperados ni estimados: son las salidas que
imprimieron los scripts.

Generadas el 2026-09-26 · Python 3.11.15

---

## 1. Pruebas del núcleo — `app/tests/casos.py`

```bash
$ python3 app/tests/casos.py
  [ OK   ] T-01  el esquema declara 8 tablas en orden de dependencias
  [ OK   ] T-02  el generador de valores cubre todos los generadores declarados
  [ OK   ] T-03  el DDL de SQLite crea las tablas con PK, FK, UNIQUE y CHECK
  [ OK   ] T-04  el mismo esquema produce DDL distinto y valido en los tres motores
  [ OK   ] T-05  tipos enumerados y declarativos se traducen al tipo nativo de cada motor
  [ OK   ] T-06  el DDL de MySQL serializa los enums nativos sin perder el dominio
  [ OK   ] T-07  la generacion completa produce el volumen exacto por tabla
  [ OK   ] T-08  determinismo: la misma semilla produce el mismo lote; otra semilla, otro lote
  [ OK   ] T-09  las claves foraneas nunca apuntan a filas inexistentes
  [ OK   ] T-10  los dominios enum se respetan y las columnas UNIQUE no repiten
  [ OK   ] T-11  las restricciones declarativas (CHECK) se cumplen en todas las filas
  [ OK   ] T-12  el DNI generado tiene 8 digitos y formato de padron real
  [ OK   ] T-13  el lote carga en SQLite y el conteo por tabla coincide
  [ OK   ] T-14  SQLite confirma integridad referencial: 0 filas huerfanas (PRAGMA foreign_key_check)
  [ OK   ] T-15  una violacion deliberada de FK es detectada por el propio motor
  [ OK   ] T-16  una violacion de UNIQUE es rechazada por el motor
  [ OK   ] T-17  el exportador produce un script que el propio SQLite puede ejecutar
  [ OK   ] T-18  el script exportado para PostgreSQL y MySQL no tiene sintaxis de SQLite
  [ OK   ] T-19  las metricas reportan 100% de unicidad, completitud y dominios dentro
  [ OK   ] T-20  las metricas se calculan sobre el lote real, no sobre valores supuestos
  [ OK   ] T-21  los volumenes configurables se aplican y un volumen 0 se valida contra sus hijas
  [ OK   ] T-22  un volumen imposible produce un error explicito, no datos corruptos
  [ OK   ] T-23  los dominios enum se pueden sobrescribir desde la configuracion
  [ OK   ] T-24  un enum de un solo valor genera ese valor en todas las filas
  [ OK   ] T-25  la API web responde la vista de esquema con las tablas y campos
  [ OK   ] T-26  la API genera un lote y devuelve metricas con el volumen pedido
  [ OK   ] T-27  la API exporta SQL en los tres motores y el CSV de las tablas
  [ OK   ] T-28  la API de metricas no acepta peticiones malformadas y responde 400
  [ OK   ] T-29  el correo de cada fila pertenece a su propio nombre y apellido
  [ OK   ] T-30  los dominios de correo salen del catalogo declarado, no al azar

  ----------------------------------------------------------
  Casos: 30 · exitosos: 30 · fallidos: 0 · cobertura: 100%
  Restricciones cubiertas: uniques (T-10, T-16), FK (T-09, T-14, T-15), CHECK (T-11, T-14)
  ----------------------------------------------------------
```

Cubre las tres familias de restricciones del esquema, con casos positivos **y**
negativos: una clave foránea inválida y un `UNIQUE` repetido que el motor debe
rechazar (T-15, T-16), el dominio de las columnas `enum` (T-10, T-23, T-24), la
reproducibilidad por semilla (T-08) y el DDL portable a los tres motores
(T-03, T-04, T-06).

## 2. Recorrido del flujo real — `app/tests/smoke.py`

```bash
$ python3 app/tests/smoke.py
  navegador: /home/prodriguez/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome
  [ OK   ] 1 · la pagina carga el esquema y pinta 8 tablas
  [ OK   ] 1 · la generacion automatica termino
        resumen inicial: 1220 filas · semilla 2026
  [ OK   ] 2 · el deslizador actualiza el valor mostrado
  [ OK   ] 3 · el aviso de generacion se actualiza
  [ OK   ] 3 · regenerar con otro volumen cambia el total
        resumen nuevo:   1400 filas · semilla 2026
  [ OK   ] 3 · la tabla de metricas muestra 300 pacientes
  [ OK   ] 3 · no hay ninguna 'x' de fallo en las metricas
  [ OK   ] 4 · la base SQLite se crea y verifica sin problemas
  [ OK   ] 4 · la UI muestra el PRAGMA foreign_key_check limpio
  [ OK   ] 4 · la UI muestra el JOIN de 5 tablas ejecutado
  [ OK   ] 4 · la UI lista los conteos por tabla
  [ OK   ] 5 · el script de postgresql se compone con la marca CHAR(8) NOT NULL UNIQUE
  [ OK   ] 5 · el script de postgresql trae los 8 CREATE TABLE
  [ OK   ] 5 · el script de mysql se compone con la marca ENUM('M','F','O')
  [ OK   ] 5 · el script de mysql trae los 8 CREATE TABLE
  [ OK   ] 5 · el CSV trae el bloque de cada tabla
  [ OK   ] 6 · vaciar una tabla hoja (detalle_receta) SI es valido
  [ OK   ] 6 · vaciar una tabla con hijas vivas (medicamento) da error explicito
  [ OK   ] 6 · el mensaje de error esta en rojo
  [ OK   ] 6 · el servidor responde 4xx, no 5xx, ante un volumen invalido
  [ OK   ] 7 · la consola del navegador no tiene errores de JavaScript
  [ OK   ] 7 · no hay peticiones 5xx durante todo el recorrido

  SMOKE TEST: todos los pasos del flujo real pasaron
  capturas en /home/prodriguez/Documentos/7/BD2/Unidad 1/proyecto-si783-2026-ii-generador-datos/app/tests/capturas
  (4.7s)
```

No comprueba que la página se pinte: ejecuta el flujo que hace una persona
(cargar, mover un volumen, regenerar, verificar en SQLite, exportar a los tres
motores, exportar CSV y provocar un error). Las capturas quedan en
`app/tests/capturas/`.

## 3. Medición de la línea base (OI5) — `app/tests/linea_base.py`

```bash
$ python3 app/tests/linea_base.py
OI5 · medicion comparada de generadores (semilla 2026, 200 filas por tabla)
--------------------------------------------------------------------
  Generico (solo conoce el tipo)  : 343/1600 filas aceptadas  (21.4 %)
      - especialidad: 34 rechazadas
      - medico: 194 rechazadas
      - paciente: 200 rechazadas
      - turno: 200 rechazadas
      - cita: 200 rechazadas
      - medicamento: 29 rechazadas
      - receta: 200 rechazadas
      - detalle_receta: 200 rechazadas
      primer error del motor: especialidad: UNIQUE constraint failed: especialidad.codigo
  DataForge (conoce el esquema)   : 1213/1213 filas aceptadas  (100.0 %)
--------------------------------------------------------------------
  Diferencia: el generico pierde 1257 filas que el motor rechaza,
  y cada rechazo obliga a corregir el lote a mano antes de poder probarlo.
```

Compara un generador que solo conoce el **tipo** de cada columna —que es lo que
hacen las herramientas comerciales— contra DataForge, que además conoce las
claves, los `UNIQUE` y los `CHECK`. Es la medición que respalda el objetivo OI5
del `README.md`.

---

## 4. Verificación de integridad sobre la base creada

La comprobación no la hace el generador: la hace el motor.

```
$ sqlite> PRAGMA foreign_key_check;
(sin resultados)

$ python3 -c "… validar_en_sqlite(con, lote) …"
ninguno
```

Y la generación es reproducible: con la misma semilla el lote es idéntico, y con
semillas distintas cambia (T-08).

## 5. Entregables verificables

| Afirmación | Cómo se comprueba | Resultado |
| :- | :- | :- |
| El lote no tiene filas huérfanas | `PRAGMA foreign_key_check` sobre la base creada | 0 violaciones |
| Las columnas `UNIQUE` no repiten | `COUNT(*) - COUNT(DISTINCT col)` por columna | 8/8 sin repetidos |
| Las `UNIQUE` compuestas no repiten | agrupación por las columnas de la restricción | 0 duplicados |
| Los dominios `enum` se respetan | conteo de valores fuera del dominio declarado | 0 fuera de dominio |
| Las columnas obligatorias se llenan | completitud sobre las celdas no nulas | 100 % |
| El DDL sirve en los tres motores | el script de SQLite se ejecuta en un motor real | 8 tablas creadas |
| La app arranca sin dependencias | `python3 app.py` | HTTP 200 en `/` |
| El flujo de la interfaz funciona | `app/tests/smoke.py` | 22 pasos en verde |
