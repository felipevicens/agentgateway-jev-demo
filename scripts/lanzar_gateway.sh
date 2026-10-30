#!/usr/bin/env bash
# agentgateway en :4000 con los modelos jev, laya, laya-ml y julia.
# Renderiza el template con las claves del .env (TYPESAFE_API_KEY, OPENROUTER_API_KEY).
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/entorno.sh"
necesita_venv
[ -f "$REPO/.env" ] || echo "AVISO: no hay .env; JEV (TypeSafe) no funcionara."
liberar_puerto "$PUERTO_GATEWAY"
cd "$REPO"
AGENTGATEWAY_BIN="${AGENTGATEWAY_BIN:-$BIN/agentgateway}" exec "$PY" jev_guardrail_agentgateway.py
