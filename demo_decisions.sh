#!/usr/bin/env bash
# La MISMA pregunta con el formato de la API Decisions de OpenAI (POST
# /v1/decisions) contra un modelo System One. agentgateway 1.7.0 traduce la
# peticion y la respuesta entre Decisions y SystemOne, asi que un cliente que
# solo habla Decisions funciona con JEV, Laya o Julia-1.
#
#   MODEL=jev   ./demo_decisions.sh
#   MODEL=laya  ./demo_decisions.sh
#   MODEL=julia ./demo_decisions.sh
#
# Diferencias de formato respecto a /v1/systemone: el texto va en "input" (no
# "state"), "questions" es una LISTA con "id", y la pregunta de si/no se llama
# "predicate" (no "noul"). La respuesta trae "answers" como lista.
set -euo pipefail

MODEL="${MODEL:-jev}"
GATEWAY="${GATEWAY:-http://localhost:4000}"

echo "=========================================================="
echo "  Formato OpenAI Decisions // Modelo: $MODEL"
echo "  Gateway: $GATEWAY/v1/decisions"
echo "=========================================================="

curl -sS -X POST "$GATEWAY/v1/decisions" \
  -H 'Content-Type: application/json' \
  -d "{
    \"model\": \"$MODEL\",
    \"input\": \"Me han cobrado dos veces el mismo pedido.\",
    \"questions\": [
      {
        \"id\": \"es_urgente\",
        \"type\": \"predicate\",
        \"instructions\": \"¿Es urgente?\"
      }
    ]
  }" | python3 -m json.tool
