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
| **Repositorio en GitHub** | **Hecho** | <https://github.com/dejameingresar/proyecto-si783-2026-ii-generador-datos> |
| **Configuración de despliegue en Render** | **Hecho** | [`render.yaml`](render.yaml) |
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

## 2. Dónde vive la aplicación: Render

**Decidido: Render.** DataForge es un servidor Python con base de datos SQLite
dentro. Los alojamientos de archivos estáticos (GitHub Pages, Surge) solo
sirven archivos y **no ejecutan Python**, así que la aplicación necesita un
hosting que corra procesos.

El proyecto de Calidad sí se publica en GitHub Pages porque su aplicación es
HTML + JavaScript puro: se abre con doble clic, sin servidor. DataForge es la
otra categoría, y su equivalente es Render.

| Servicio | Qué hay que hacer | Costo |
| :- | :- | :- |
| **Render** (elegido) | Crear cuenta y conectar el repo; Render lee `render.yaml` y crea el servicio | Plan gratuito |
| Railway | Conectar el repo, comando `python3 app.py` | Plan gratuito limitado |
| Fly.io | `fly.toml` con `command = "python3 app.py"` | Plan gratuito limitado |

**Lo único que requiere una cuenta es la cuenta de Render.** El repositorio
ya está en GitHub y la configuración de despliegue ya está en el repositorio,
así que después de crear la cuenta el despliegue es un clic.

### La alternativa descartada: reescribir en JavaScript para Pages

Se podría reimplementar el generador en JavaScript con SQLite compilado a
WebAssembly (`sql.js`) para que viva en Pages y tener la misma dirección que el
proyecto de Calidad. Se descartó porque sería reescribir la aplicación y volver
a probar todo, y el resultado sería una reimplementación en el navegador, no la
aplicación con su base de datos que pide la consigna.

## 3. Comandos útiles

```bash
python3 app.py                       # aplicación en local
python3 app/tests/casos.py            # 30 pruebas del núcleo
python3 app/tests/linea_base.py       # medición comparada (OI5)
python3 app/tests/documentacion.py   # la documentación es reproducible
python3 docs/generar_documentos.py   # regenerar diagramas y manuales
```

## 4. Cómo desplegar la aplicación

La aplicación **sí** es desplegable: es un servidor Python, y Render lo ejecuta
tal cual porque no tiene dependencias externas.

1. Crear una cuenta en <https://render.com> (plan gratuito).
2. En el panel: **New → Blueprint**, y apuntar a este repositorio.
3. Render lee [`render.yaml`](render.yaml) y crea el servicio solo:
   - no instala nada (el build solo comprueba la versión de Python);
   - arranca con `python3 app.py --host 0.0.0.0 --puerto $PORT`;
   - usa `/api/esquema` como *health check*.
4. En unos minutos queda en `https://dataforge-si783.onrender.com`.

**Nota sobre el plan gratuito:** el servicio se duerme tras unos minutos sin
uso y tarda unos segundos en despertar la primera petición. Para la
presentación conviene abrir la URL un par de minutos antes.

## 5. Por qué no se publica en GitHub Pages

GitHub Pages (y Surge, y cualquier alojamiento de archivos estáticos) solo
sirven archivos: **no ejecutan Python**. El proyecto de Calidad sí se publica
en Pages porque su aplicación es HTML + JavaScript puro y se abre con doble
clic, sin servidor. DataForge es un servidor con base de datos, así que su
equivalente correcto es Render.

La documentación técnica sí se puede publicar en Pages, y ya está preparada
(`.github/workflows/publicar.yml`); es un complemento, no un sustituto de la
aplicación.