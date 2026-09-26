#!/usr/bin/env python3
"""Genera los artefactos tecnicos del proyecto a partir del codigo.

Un solo lugar produce todas las salidas, y todas se derivan de la definicion
declarativa del esquema (app/nucleo/esquemas.py) y de la suite de pruebas:

    docs/diagrama-er.mmd       diagrama entidad-relacion (Mermaid)
    docs/diagrama-er.svg       el mismo diagrama, en SVG
    docs/diccionario-datos.md  tabla por tabla y columna por columna
    docs/ddl.sql               DDL de SQLite con el lote de ejemplo
    docs/manual-tecnico.md      manual tecnico de uso y arquitectura

Se invoca desde .github/workflows/documentacion.yml en cada push, y tambien a
mano:  python3 docs/generar_documentos.py

Ninguna salida esta escrita a mano: si el esquema cambia, esto se regenera.
"""

import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "app"))
DOCS = os.path.join(RAIZ, "docs")

from nucleo import esquemas, persistencia  # noqa: E402
from nucleo.ddl import tipo_sql  # noqa: E402
from nucleo.motor import Generador, metricas, validar_en_sqlite  # noqa: E402

SEMILLA = 2026


# --------------------------------------------------------------------- ER
# Tipos legibles para el diagrama. Los tipos logicos internos ('dni', 'email',
# 'fk') no son tipos SQL: se traducen a lo que realmente se guarda.
TIPO_DIAGRAMA = {
    "dni": "CHAR", "email": "VARCHAR", "telefono": "VARCHAR", "fk": "INT",
}


def _tipo_legible(campo):
    """Tipo a mostrar en el diagrama, con su longitud cuando la tiene."""
    if campo["tipo"] == "enum":
        return "ENUM"
    base = TIPO_DIAGRAMA.get(campo["tipo"], campo["tipo"].upper())
    largo = campo.get("largo")
    if largo and campo["tipo"] not in ("fk",):
        return f"{base}({largo})"
    return base


def diagrama_er():
    """Diagrama entidad-relacion en Mermaid (erDiagram)."""
    e = esquemas.ESQUEMA
    lineas = ["%% Generado por docs/generar_documentos.py — no editar a mano",
              f"%% Esquema: {e['titulo']}", "erDiagram"]
    for nombre in e["orden_insercion"]:
        t = e["tablas"][nombre]
        lineas.append(f"    {nombre} {{")
        for c in t["campos"]:
            tipo = _tipo_legible(c)
            if c.get("pk"):
                marca = "PK"
            elif c["tipo"] == "fk":
                marca = "FK"
            elif c.get("unique"):
                marca = "UK"
            else:
                marca = ""
            # Mermaid no admite un '?' de nulabilidad en el nombre: la clave
            # de la columna debe ser un identificador. Se marca la opcionalidad en
            # el comentario de la linea, que si es valido.
            sufijo = ' "opcional"' if c.get("nullable", False) else ""
            linea = f"        {tipo} {c['nombre']} {marca}".rstrip() + sufijo
            lineas.append(linea)
        lineas.append("    }")
    for nombre in e["orden_insercion"]:
        for c in e["tablas"][nombre]["campos"]:
            if c["tipo"] == "fk":
                # En Mermaid, el lado padre es "||" (uno y solo uno) y el lado
                # hijo "o{" (cero o varios) u "o|" (cero o uno) segun admita
                # nulos. "||{hijo}" no es valido: el parser lo rechaza.
                cardinalidad = "o|" if c.get("nullable", False) else "o{"
                # Mermaid exige: entidadPadre ||--o{ entidadHija : etiqueta
                # Mermaid exige un espacio entre la cardinalidad y la llave:
                # "||--o{ medico", no "||--o{{medico}".
                linea = (f"    {c['tabla_ref']} ||--{cardinalidad} {nombre}"
                         f" : \"{c['nombre']}\"")
                lineas.append(linea)
    return "\n".join(lineas) + "\n"


# ------------------------------------------------------------- diccionario
def diccionario_datos():
    e = esquemas.ESQUEMA
    out = [f"# Diccionario de datos — {e['titulo']}", "",
           "Generado por `docs/generar_documentos.py` desde "
           "`app/nucleo/esquemas.py`. No editar a mano.", "",
           f"{len(e['orden_insercion'])} tablas · "
           f"{sum(len(e['tablas'][t]['campos']) for t in e['orden_insercion'])} columnas.", ""]
    for nombre in e["orden_insercion"]:
        t = e["tablas"][nombre]
        out += [f"## {nombre}", ""]
        if t.get("descripcion"):
            out += [f"_{t['descripcion']}_", ""]
        out += ["| columna | tipo (SQLite) | tipo (PostgreSQL) | nulos | clave | generador |",
                "| :- | :- | :- | :- | :- | :- |"]
        for c in t["campos"]:
            if c.get("pk"):
                clave = "PK"
            elif c["tipo"] == "fk":
                clave = f"FK → {c['tabla_ref']}.{c['columna_ref']} ({c.get('on_delete', 'RESTRICT')})"
            elif c.get("unique"):
                clave = "UNIQUE"
            else:
                clave = ""
            gen = c.get("generador") or c.get("derivado") or (
                f"enum {c['enum']}" if c["tipo"] == "enum" else "—")
            out.append(
                f"| `{c['nombre']}` | `{tipo_sql(c, 'sqlite')}` | "
                f"`{tipo_sql(c, 'postgresql')}` | "
                f"{'sí' if c.get('nullable', False) else 'no'} | {clave} | {gen} |")
        if t.get("unicas"):
            out += ["", "Restricciones `UNIQUE` compuestas: " +
                    "; ".join("(" + ", ".join(u) + ")" for u in t["unicas"]) + "."]
        if t.get("indices"):
            out += ["", "Índices: " +
                    "; ".join("(" + ", ".join(i["columnas"]) + ")" for i in t["indices"]) + "."]
        out += [""]
    return "\n".join(out)


# ------------------------------------------------------------------ manual
def manual_tecnico():
    e = esquemas.ESQUEMA
    lote = Generador(semilla=SEMILLA).generar()
    m = metricas(lote)
    con = persistencia.crear_y_poblar(":memory:", lote)
    problemas = validar_en_sqlite(con, lote)
    conteos = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
               for t in e["orden_insercion"]}
    con.close()

    total = sum(len(v) for v in lote.values())
    unic = sum(t["unicos_respetados"] for t in m["tablas"].values())
    unic_tot = sum(t["unicos_total"] for t in m["tablas"].values())

    return f"""# Manual técnico — DataForge

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

**{e['titulo']}** — {e['resumen']}

Orden de generación (una tabla padre antes que sus hijas):

{chr(10).join(f'{i}. `{t}`' for i, t in enumerate(e['orden_insercion'], 1))}

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

## 6. Lote de ejemplo (semilla {SEMILLA})

Total: **{total}** filas en {len(e['orden_insercion'])} tablas.

| tabla | filas |
| :- | --: |
{chr(10).join(f'| `{t}` | {conteos[t]} |' for t in e['orden_insercion'])}

- Unicidad: **{unic}/{unic_tot}** columnas `UNIQUE` sin repeticiones.
- Completitud: **{100 * (1 - m['totales']['celdas_vacias'] / max(1, m['totales']['celdas_obligatorias'])):.0f} %**
  de las celdas obligatorias.
- Integridad referencial: **{len(problemas)}** problemas al verificar contra
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
"""


def main():
    os.makedirs(DOCS, exist_ok=True)
    salidas = {
        "diagrama-er.mmd": diagrama_er(),
        "diccionario-datos.md": diccionario_datos(),
        "ddl.sql": None,  # se escribe aparte (no es texto)
        "manual-tecnico.md": manual_tecnico(),
    }
    for nombre, contenido in salidas.items():
        if contenido is None:
            continue
        ruta = os.path.join(DOCS, nombre)
        with open(ruta, "w", encoding="utf-8") as fh:
            fh.write(contenido)
        print(f"  generado: docs/{nombre} ({len(contenido)} bytes)")

    # DDL + INSERT de SQLite, con el lote de ejemplo.
    lote = Generador(semilla=SEMILLA).generar()
    sql = persistencia.exportar_sql(lote, motor="sqlite")
    with open(os.path.join(DOCS, "ddl.sql"), "w", encoding="utf-8") as fh:
        fh.write(sql)
    print(f"  generado: docs/ddl.sql ({len(sql)} bytes)")

    # SVG del diagrama, si hay mermaid-cli disponible (opcional).
    mmd = os.path.join(DOCS, "diagrama-er.mmd")
    svg = os.path.join(DOCS, "diagrama-er.svg")
    if os.path.isfile(svg):
        os.remove(svg)
    try:
        subprocess.run(["npx", "-y", "@mermaid-js/mermaid-cli", "-i", mmd, "-o", svg],
                       check=True, capture_output=True, timeout=180)
        print(f"  generado: docs/diagrama-er.svg")
    except Exception as e:  # sin red o sin node: el .mmd sigue siendo la fuente
        print(f"  aviso: no se pudo renderizar el SVG ({type(e).__name__}). "
              "El diagrama queda en docs/diagrama-er.mmd")
    return 0


if __name__ == "__main__":
    sys.exit(main())
