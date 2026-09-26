#!/usr/bin/env python3
"""DataForge — servidor de la aplicacion (solo biblioteca estandar).

    python3 app.py                # http://127.0.0.1:8000
    python3 app.py --puerto 9000
    python3 app.py --sin-navegador

No requiere `pip install`: el nucleo logico, SQLite y el servidor HTTP son de
Python. La interfaz es una pagina estatica que consume nucleo/api.py.
"""

import argparse
import os
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RAIZ = os.path.dirname(os.path.abspath(__file__))   # raíz del proyecto
APP = os.path.join(RAIZ, "app")                     # código de la aplicación
sys.path.insert(0, APP)

from nucleo import api  # noqa: E402

RAIZ_WEB = os.path.join(APP, "web")
TIPOS = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
}


class Manejador(BaseHTTPRequestHandler):
    server_version = "DataForge/1.0"

    def log_message(self, formato, *args):  # salida limpia en la demo
        sys.stderr.write(f"  {formato % args}\n")

    def _envia(self, status, cuerpo, tipo="application/json; charset=utf-8"):
        if isinstance(cuerpo, str):
            cuerpo = cuerpo.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _estatico(self, camino_rel):
        # Sin pathlib ni traversal: se resuelve dentro de app/web y se comprueba.
        limpio = os.path.normpath(camino_rel).lstrip("./")
        destino = os.path.join(RAIZ_WEB, limpio)
        if not os.path.abspath(destino).startswith(os.path.abspath(RAIZ_WEB) + os.sep):
            return self._envia(403, "403", "text/plain; charset=utf-8")
        if os.path.isdir(destino):
            destino = os.path.join(destino, "index.html")
        if not os.path.isfile(destino):
            return self._envia(404, f"no existe: {limpio}", "text/plain; charset=utf-8")
        ext = os.path.splitext(destino)[1]
        with open(destino, "rb") as fh:
            self._envia(200, fh.read(), TIPOS.get(ext, "application/octet-stream"))

    def do_GET(self):
        camino = self.path.split("?")[0]
        if camino.startswith("/api/"):
            consulta = self.path.split("?")[1].split("&") if "?" in self.path else []
            r = api.ruta("GET", self.path, query=consulta)
            return self._envia(r["status"], r["cuerpo"])
        if camino in ("/", "/index.html"):
            return self._estatico("index.html")
        return self._estatico(camino.lstrip("/"))

    def do_POST(self):
        largo = int(self.headers.get("Content-Length") or 0)
        cuerpo = self.rfile.read(largo).decode("utf-8") if largo else ""
        r = api.ruta("POST", self.path, cuerpo=cuerpo)
        self._envia(r["status"], r["cuerpo"])


def main():
    ap = argparse.ArgumentParser(description="DataForge · generador de datos")
    ap.add_argument("--puerto", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--sin-navegador", action="store_true",
                    help="no abrir el navegador automaticamente")
    args = ap.parse_args()

    if not os.path.isdir(RAIZ_WEB):
        print(f"ERROR: falta la interfaz en {RAIZ_WEB}", file=sys.stderr)
        return 1

    servidor = ThreadingHTTPServer((args.host, args.puerto), Manejador)
    url = f"http://{args.host}:{args.puerto}/"
    print("=" * 62)
    print("  DataForge · generador de datos para bases de datos")
    print(f"  Esquema: {api.vista_esquema()['titulo']}")
    print(f"  Abrir:   {url}")
    print("  Ctrl+C para detener")
    print("=" * 62)
    if not args.sin_navegador:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n  servidor detenido")
    finally:
        servidor.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
