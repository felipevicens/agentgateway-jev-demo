#!/usr/bin/env bash
# Web interactiva (http://localhost:3000). Solo escucha en 127.0.0.1.
# Necesita el gateway y los modelos arrancados (la pestaña del chat, ademas, el webhook).
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/entorno.sh"
necesita_venv
liberar_puerto "$PUERTO_WEB"
cd "$REPO"
echo "Web en http://localhost:$PUERTO_WEB"
WEB_PORT="$PUERTO_WEB" exec "$PY" web_demo/server.py
