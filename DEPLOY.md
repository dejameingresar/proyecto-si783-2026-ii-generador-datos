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
| Recorrido del flujo real en navegador | 22/22 pasos en verde | `python3 app/tests/smoke.py` |
| Diagrama ER, diccionario de datos, manual técnico, DDL | Generados desde el código | `python3 docs/generar_documentos.py` |
| Automatización de pruebas y documentación | Configurada | `.github/workflows/documentacion.yml` |
| Publicación de la documentación en Pages | Configurada | `.github/workflows/publicar.yml` |

Ambas automatizaciones hacen algo real, no decorativo:

- **`documentacion.yml`** corre las tres suites, **vuelve a generar los diagramas y
  manuales desde el código**, **ejecuta el DDL generado en una base SQLite de verdad**
  (si el DDL fuera inválido, la automatización falla) y sube la evidencia como
  artefacto. En la rama principal, además, commitea la documentación regenerada para
  que el repositorio nunca muestre documentación desactualizada.
- **`publicar.yml`** publica `docs/` en GitHub Pages, con concurrencia controlada
  para que dos publicaciones no se pisen.

## 2. La decisión que falta: dónde vive la aplicación

GitHub Pages **solo sirve archivos estáticos**: no ejecuta Python. Por eso, con la
arquitectura actual (servidor `http.server` + SQLite), hay dos caminos reales.

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

## 4. Nota sobre la documentación publicada

`publicar.yml` deja la **documentación técnica** (diagrama ER, diccionario de datos,
manual, DDL de ejemplo) en una URL pública de Pages, porque eso sí es estático y sí
sirve para pages. La **aplicación interactiva** necesita un hosting que ejecute
Python: es el punto 2 de esta nota.

## 5. Comandos útiles

```bash
python3 app.py                                    # aplicación en local
python3 app/tests/casos.py                        # pruebas del núcleo
python3 docs/generar_documentos.py               # regenerar diagramas y manuales
python3 docs/generar_documentos.py               # el SVG requiere npx mermaid-cli
```
