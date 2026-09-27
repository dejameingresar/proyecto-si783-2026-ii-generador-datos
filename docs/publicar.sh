#!/usr/bin/env bash
# Publica la documentación técnica de DataForge en Surge.
#
#   bash docs/publicar.sh
#
# Qué sube: solo los artefactos que se generan desde el código (portada, manual,
# diccionario de datos, DDL de ejemplo y el diagrama ER). NO sube el código ni
# el __pycache__ de docs/.
#
# El token de Surge se lee de ~/.netrc, así que este script no pide contraseña.
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOMINIO="${DATAFORGE_DOMINIO:-dataforge-si783-2026.surge.sh}"
CONTAINER="${1:-}"

echo "==> Regenerando la documentación desde el código"
cd "$RAIZ"
python3 docs/generar_documentos.py

# El SVG no es determinista (mermaid-cli incrusta una fuente con id aleatorio),
# pero se publica igual: lo que importa es que la URL lo muestre.
echo
echo "==> Preparando $CONTAINER"
if [ -n "$CONTAINER" ]; then
  rm -rf "$CONTAINER"
  mkdir -p "$CONTAINER"
  for f in index.html manual-tecnico.md diccionario-datos.md ddl.sql \
           diagrama-er.mmd diagrama-er.svg; do
    cp "$RAIZ/docs/$f" "$CONTAINER/$f"
  done
  cat > "$CONTAINER/200.html" <<'HTML'
<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<title>DataForge · documentación técnica</title>
<meta http-equiv="refresh" content="0; url=./">
</head><body><p><a href="./">DataForge · documentación técnica</a></p></body></html>
HTML
  echo "    $(ls "$CONTAINER" | wc -l) archivos"
  echo
  echo "==> Publicando en https://$DOMINIO"
  npx -y surge@latest "$CONTAINER" "$DOMINIO"
else
  echo "    (sin contenedor: no se publico nada. Indica uno, p. ej. /tmp/publicar)"
  exit 1
fi

echo
echo "==> Comprobando que la URL responde"
for f in "" manual-tecnico.md diccionario-datos.md ddl.sql diagrama-er.svg; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "https://$DOMINIO/$f")
  printf '    HTTP %s  /%s\n' "$code" "$f"
  [ "$code" = "200" ] || { echo "    FALLO: /$f devolvio $code"; exit 1; }
done

echo
echo "Publicado: https://$DOMINIO"
