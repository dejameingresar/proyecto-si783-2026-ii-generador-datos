"""nucleo.api — la API de la app, independiente del servidor HTTP.

Toda la logica de la interfaz vive aqui y se prueba desde la terminal (T-25..T-28),
de modo que `app.py` (el servidor) solo traduce HTTP a llamadas de esta funcion.
"""

import json
import time

from . import esquemas, persistencia
from .ddl import MOTORES
from .motor import ErrorGeneracion, Generador, metricas, validar_en_sqlite


def _json(cuerpo, status=200):
    return {"status": status, "cuerpo": json.dumps(cuerpo, ensure_ascii=False)}


def _error(mensaje, status=400):
    return _json({"ok": False, "error": mensaje}, status)


def _cuerpo_json(peticion):
    if not peticion:
        return {}
    return json.loads(peticion)


def _normaliza_volumenes(bruto, esquema=None):
    """Acepta el volumen del cliente y lo acota al esquema conocido."""
    esquema = esquema or esquemas.ESQUEMA
    vol = {}
    for nombre, n in (bruto or {}).items():
        if nombre not in esquema["tablas"]:
            raise ValueError(f"tabla desconocida: {nombre}")
        vol[nombre] = max(0, min(int(n), 2000))
    return vol


def vista_esquema():
    """Estructura del esquema para pintar la interfaz."""
    e = esquemas.ESQUEMA
    tablas = {}
    for nombre in e["orden_insercion"]:
        t = e["tablas"][nombre]
        tablas[nombre] = {
            "descripcion": t.get("descripcion", ""),
            "campos": t["campos"],
            "unicas": t.get("unicas", []),
            "indices": t.get("indices", []),
            "volumen": e["volumenes"][nombre],
            "columnas": esquemas.columnas(t),
        }
    return {
        "nombre": e["nombre"],
        "titulo": e["titulo"],
        "resumen": e["resumen"],
        "tablas": tablas,
        "orden": e["orden_insercion"],
        "motores": list(MOTORES),
        "enums": e["enums"],
    }


def _resumen_lote(lote, m, elapsed):
    filas = sum(len(v) for v in lote.values())
    return {
        "filas_totales": filas,
        "tablas": len(lote),
        "generado_en": f"{elapsed * 1000:.1f} ms",
        "unicidad": f"{m['tablas']and sum(t['unicos_respetados'] for t in m['tablas'].values())}/{sum(t['unicos_total'] for t in m['tablas'].values())}",
        "completitud": (1.0 - m["totales"]["celdas_vacias"] / m["totales"]["celdas_obligatorias"])
        if m["totales"]["celdas_obligatorias"] else 1.0,
    }


def ruta(metodo, camino, cuerpo=None, query=None):
    """Punto de entrada unico de la API. Devuelve {status, cuerpo}."""
    camino = (camino or "/").split("?")[0]
    q = {}
    for par in (query or []):
        if "=" in par:
            k, v = par.split("=", 1)
            q[k] = v

    try:
        if camino == "/api/esquema" and metodo == "GET":
            return _json(vista_esquema())

        if camino in ("/api/generar", "/api/generar/") and metodo == "POST":
            datos = _cuerpo_json(cuerpo)
            vol = _normaliza_volumenes(datos.get("volumenes"))
            semilla = int(datos.get("semilla", 2026))
            g = Generador(semilla=semilla, enums=datos.get("enums"))
            t0 = time.perf_counter()
            lote = g.generar(vol)
            elapsed = time.perf_counter() - t0
            m = metricas(lote)
            return _json({
                "ok": True,
                "semilla": semilla,
                "lote": m,
                "resumen": _resumen_lote(lote, m, elapsed),
                "muestra": {k: v[:5] for k, v in lote.items()},
            })

        if camino in ("/api/exportar", "/api/exportar/") and metodo == "POST":
            datos = _cuerpo_json(cuerpo)
            vol = _normaliza_volumenes(datos.get("volumenes"))
            semilla = int(datos.get("semilla", 2026))
            lote = Generador(semilla=semilla, enums=datos.get("enums")).generar(vol)
            formato = datos.get("formato", "sql")
            if formato == "csv":
                return _json({
                    "ok": True,
                    "formato": "csv",
                    "nombre": "epsis_salud_datos.csv",
                    "contenido": persistencia.exportar_csv(lote),
                    "filas": sum(len(v) for v in lote.values()),
                })
            motor = datos.get("motor", "postgresql")
            if motor not in MOTORES:
                return _error(f"motor no soportado: {motor}. Use uno de {', '.join(MOTORES)}")
            return _json({
                "ok": True,
                "formato": "sql",
                "motor": motor,
                "nombre": f"epsis_salud_{motor}.sql",
                "sql": persistencia.exportar_sql(lote, motor=motor),
                "filas": sum(len(v) for v in lote.values()),
            })

        if camino in ("/api/demo", "/api/demo/") and metodo == "POST":
            # Carga real en SQLite: la demo abre una base de datos de verdad.
            datos = _cuerpo_json(cuerpo)
            vol = _normaliza_volumenes(datos.get("volumenes"))
            lote = Generador(semilla=int(datos.get("semilla", 2026)),
                             enums=datos.get("enums")).generar(vol)
            con = persistencia.crear_y_poblar(":memory:", lote)
            problemas = validar_en_sqlite(con, lote)
            filas = con.execute(
                "SELECT 'especialidad', COUNT(*) FROM especialidad "
                "UNION ALL SELECT 'medico', COUNT(*) FROM medico "
                "UNION ALL SELECT 'paciente', COUNT(*) FROM paciente "
                "UNION ALL SELECT 'turno', COUNT(*) FROM turno "
                "UNION ALL SELECT 'cita', COUNT(*) FROM cita "
                "UNION ALL SELECT 'medicamento', COUNT(*) FROM medicamento "
                "UNION ALL SELECT 'receta', COUNT(*) FROM receta "
                "UNION ALL SELECT 'detalle_receta', COUNT(*) FROM detalle_receta"
            ).fetchall()
            consultas = con.execute(
                "SELECT c.estado, COUNT(*) n FROM cita c GROUP BY c.estado "
                "ORDER BY n DESC LIMIT 5"
            ).fetchall()
            muestra = con.execute(
                "SELECT p.nombres, p.apellidos, e.nombre AS especialidad "
                "FROM paciente p JOIN cita ci ON ci.id_paciente = p.id_paciente "
                "JOIN turno t ON t.id_turno = ci.id_turno "
                "JOIN medico m ON m.id_medico = t.id_medico "
                "JOIN especialidad e ON e.id_especialidad = m.id_especialidad "
                "LIMIT 5"
            ).fetchall()
            con.close()
            return _json({
                "ok": True,
                "problemas": problemas,
                "conteos": {t: n for t, n in filas},
                "citas_por_estado": {e: n for e, n in consultas},
                "join_ejemplo": [list(r) for r in muestra],
            })

        return _error(f"ruta no encontrada: {metodo} {camino}", 404)
    except json.JSONDecodeError as e:
        return _error(f"JSON invalido: {e}")
    except ValueError as e:
        return _error(str(e))
    except ErrorGeneracion as e:
        # Volumenes o dominio invalidos: es un error de la peticion (400), no
        # del servidor. Devolver 500 haria que un fallo del usuario pareciera
        # una caida de la aplicacion.
        return _error(str(e))
    except Exception as e:  # noqa: BLE001 - la UI muestra el error, no se cae el server
        return _error(f"{type(e).__name__}: {e}", 500)
