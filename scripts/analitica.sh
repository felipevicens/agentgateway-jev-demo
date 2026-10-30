#!/usr/bin/env bash
# Resumen de lo que ha pasado por el gateway (peticiones, errores, tokens y coste
# por proveedor y modelo), con la CLI nueva de agentgateway 1.7.0.
#   ./scripts/analitica.sh                       # agrupado por proveedor y modelo
#   ./scripts/analitica.sh --by model --since 1h # cualquier opcion de agctl
# Lee el log de peticiones del gateway (request-logs.db), asi que necesita el
# gateway en marcha. Mas opciones: agctl standalone analytics --help
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/entorno.sh"
AGCTL="${AGCTL:-$BIN/agctl}"
[ -x "$AGCTL" ] || { echo "Falta agctl. Ejecuta: ./scripts/instalar.sh gateway"; exit 1; }
export AGCTL_CONFIG="${AGCTL_CONFIG:-$REPO/.agctl.yaml}"   # fichero inexistente: agctl no lo necesita
export AGCTL_STANDALONE_ADDRESS="${AGCTL_STANDALONE_ADDRESS:-http://127.0.0.1:15000}"
if [ "$#" -eq 0 ]; then set -- --by provider,model; fi
exec "$AGCTL" standalone analytics "$@"
