# Despliegue — qué está listo y qué falta decidir

La asignación (semanas 4-6) pide: *aplicación desplegada en nube o servicio público,
mediante automatizaciones que generen adicionalmente los diagramas y manuales técnicos
desde un repositorio git.*

Esta nota separa lo que **ya está hecho** de lo que **falta decidir**, para que la
decisión de hosting se tome con la evidencia a la vista.

---

## 1. Lo que ya funciona (verificado)

| Entregable | Estado | Cómo se verifica |
| :- | :- | :- |
| Aplicación ejecutable sin dependencias | Listo | `python3 app.py` → HTTP 200 |
| Pruebas del núcleo | 30/30 en verde | `python3 app/tests/casos.py` |
| Medición de la línea base (OI5) | Ejecutada | `python3 app/tests/linea_base.py` |
| Reproducibilidad de la documentación | Verificada | `python3 app/tests/documentacion.py` |
| Recorrido del flujo real en navegador | 23/23 pasos en verde | `python3 app/tests/smoke.py` |
| Diagrama ER, diccionario de datos, manual técnico, DDL | Generados desde el código | `python3 docs/generar_documentos.py` |
| **Documentación publicada (URL pública)** | **Hecho** | <http://dataforge-si783-2026.surge.sh> |
| Automatización de pruebas y documentación | Configurada | `.github/workflows/documentacion.yml` |
| Publicación de la documentación en Pages | Configurada | `.github/workflows/publicar.yml` |

### Documentación publicada en Surge

<http://dataforge-si783-2026.surge.sh>

Contiene la portada, el manual técnico, el diccionario de datos, el script DDL
con 1 213 filas de ejemplo y el diagrama ER. Todo verificado: los seis archivos
responden HTTP 200 y la página se renderiza con el diagrama completo.

Se publica con un solo comando, que además regenera la documentación y verifica
la URL al terminar:

```bash
bash docs/publicar.sh /tmp/publicar
```

El token se lee de `~/.netrc` (`machine surge.surge.sh`), así que el script no
pide contraseña. La automatización de GitHub lo inyecta desde los secretos
`SURGE_LOGIN` y `SURGE_TOKEN`; si no están, omite la publicación con un aviso
en vez de fallar.

Ambas automatizaciones hacen algo real, no decorativo:

- **`documentacion.yml`** corre las tres suites, **vuelve a generar los diagramas y
  manuales desde el código**, **ejecuta el DDL generado en una base SQLite de verdad**
  (si el DDL fuera inválido, la automatización falla) y sube la evidencia como
  artefacto. En la rama principal, además, commitea la documentación regenerada para
  que el repositorio nunca muestre documentación desactualizada.
- **`publicar.yml`** publica `docs/` en GitHub Pages, con concurrencia controlada
  para que dos publicaciones no se pisen.

## 2. La decisión que sigue pendiente: dónde vive la aplicación

GitHub Pages y Surge **solo sirven archivos estáticos**: no ejecutan Python. Por
eso, con la arquitectura actual (servidor `http.server` + SQLite), hay dos caminos
reales para la **aplicación interactiva**.

### Opción A — Hospedar la aplicación Python (recomendada)

| Servicio | Qué hay que hacer | Costo |
| :- | :- | :- |
| **Render** | Subir `render.yaml` (o conectar el repo) con el comando `python3 app.py` y el puerto que asigne | Plan gratuito, se duerme tras un rato sin uso |
| **Railway** | Conectar el repo, comando `python3 app.py` | Plan gratuito limitado |
| **Fly.io** | `fly.toml` con `command = "python3 app.py"` | Plan gratuito limitado |

**Ventaja:** se reutiliza tal cual la aplicación ya verificada. Sin reescribir nada.
**Requisito:** una cuenta gratuita en el servicio (la creas tú; yo no puedo).

```bash
# Con Render, el archivo es esto (no hace falta tocar el código):
services:
  - type: web
    name: dataforge
    runtime: python
    buildCommand: echo "sin dependencias"
    startCommand: python3 app.py --host 0.0.0.0 --puerto $PORT --sin-navegador
```

`app.py` ya acepta `--host` y `--puerto`, que es justo lo que exigen estos servicios.

### Opción B — Versión estática en JavaScript (GitHub Pages)

Reimplementar el generador en JavaScript para el navegador, con SQLite compilado a
WebAssembly (`sql.js`). **Solo tiene sentido si el destino final es Pages**; si no,
es reescribir la aplicación sin ganar nada.

## 3. Por qué no está decidido todavía

Pediste dejar el repositorio, las pruebas y la documentación listos antes de elegir
hosting. Eso es exactamente el estado actual. La decisión pendiente es de una línea:

> **¿Render, Railway u otro hosting con Python (opción A), o pages con una versión
> en JavaScript (opción B)?**

Si la respuesta es A, el siguiente paso es añadir `render.yaml` y conectar el
repositorio: quince minutos. Si es B, es un proyecto aparte.

## 4. Comandos útiles

```bash
python3 app.py                       # aplicación en local
python3 app/tests/casos.py            # 30 pruebas del núcleo
python3 app/tests/linea_base.py       # medición comparada (OI5)
python3 app/tests/documentacion.py   # la documentación es reproducible
python3 docs/generar_documentos.py   # regenerar diagramas y manuales
bash docs/publicar.sh /tmp/publicar   # publicar en Surge y verificar la URL
```

## 5. Nota sobre la documentación publicada

La **documentación técnica** sí está publicada, porque es estática y se sirve
desde un alojamiento de archivos:

- **Surge (hecho y verificado):** <http://dataforge-si783-2026.surge.sh> —
  portada, diagrama ER, diccionario de datos, manual y DDL con 1 213 filas de
  ejemplo. Los seis archivos responden HTTP 200 y la página renderiza el
  diagrama completo. Se publica con `bash docs/publicar.sh /tmp/publicar`.
- **GitHub Pages (configurado):** `publicar.yml` deja lo mismo en la URL de
  Pages del repositorio, si prefieres esa dirección.

Lo que **no** puede vivir en ninguno de los dos es la **aplicación
interactiva**: necesita un hosting que ejecute Python, que es el punto 2 de
esta nota.
