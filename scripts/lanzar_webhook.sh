#!/usr/bin/env bash
# Webhook del guardrail (:8000). El gateway le pregunta a este servidor si deja
# pasar cada mensaje del chat protegido.
#   ./scripts/lanzar_webhook.sh          # juez: JEV (por defecto)
#   GUARD_BACKEND=laya ./scripts/lanzar_webhook.sh
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/entorno.sh"
necesita_venv
liberar_puerto "$PUERTO_WEBHOOK"
cd "$REPO"
echo "Webhook del guardrail ($GUARD_BACKEND) en :$PUERTO_WEBHOOK"
GUARD_BACKEND="${GUARD_BACKEND:-jev}" PYTHONUNBUFFERED=1 exec "$PY" jev_guardrail_webhook.py
