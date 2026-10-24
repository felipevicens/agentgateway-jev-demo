#!/usr/bin/env bash
# Un curl por tipo de pregunta (noul, choice, score y combinado) contra agentgateway.
#
#   MODEL=jev   ./demo_curl.sh     # JEV (API nativa de TypeSafe)
#   MODEL=laya  ./demo_curl.sh     # Laya local (laya-serve)
#   MODEL=julia ./demo_curl.sh     # Julia-1 local (julia_serve.py)
#
# Requiere el gateway en marcha (localhost:4000) y el modelo seleccionado.
set -euo pipefail

MODEL="${MODEL:-jev}"
GATEWAY="${GATEWAY:-http://localhost:4000}"

echo "=========================================================="
echo "  token429 System One Demos // Modelo: $MODEL"
echo "  Gateway: $GATEWAY/v1/systemone"
echo "=========================================================="

# 1. noul: ¿Es sarcasmo?
echo -e "\n--- Paso 1: noul (¿Es sarcasmo?) ---"
curl -sS -X POST "$GATEWAY/v1/systemone" \
  -H 'Content-Type: application/json' \
  -d "{
    \"model\": \"$MODEL\",
    \"state\": {\"mensaje\": \"Qué bien, otro lunes lloviendo\"},
    \"questions\": {
      \"es_sarcasmo\": {
        \"type\": \"noul\",
        \"instructions\": \"¿Este mensaje contiene sarcasmo o ironía?\"
      }
    }
  }" | python3 -m json.tool

# 2. choice: ¿Qué emoji le pondrías?
echo -e "\n--- Paso 2: choice (¿Qué emoji le pondrías?) ---"
curl -sS -X POST "$GATEWAY/v1/systemone" \
  -H 'Content-Type: application/json' \
  -d "{
    \"model\": \"$MODEL\",
    \"state\": {\"mensaje\": \"Menuda sorpresa, otra reunión que podría haber sido un email\"},
    \"questions\": {
      \"emoji\": {
        \"type\": \"choice\",
        \"instructions\": \"¿Qué emoji describe mejor la reacción a este mensaje?\",
        \"criteria\": {
          \"🤩\": \"Entusiasmo o admiración\",
          \"😊\": \"Alegría o amabilidad\",
          \"😐\": \"Neutralidad o indiferencia\",
          \"🙄\": \"Sarcasmo, frustración o resignación\",
          \"😡\": \"Enfado visible\"
        }
      }
    }
  }" | python3 -m json.tool

# 3. score: ¿Cuántas estrellas?
echo -e "\n--- Paso 3: score (¿Cuántas estrellas?) ---"
curl -sS -X POST "$GATEWAY/v1/systemone" \
  -H 'Content-Type: application/json' \
  -d "{
    \"model\": \"$MODEL\",
    \"state\": {\"mensaje\": \"Pedí una pizza y tardó dos horas en llegar, además estaba completamente fría.\"},
    \"questions\": {
      \"estrellas\": {
        \"type\": \"score\",
        \"instructions\": \"¿Cuántas estrellas de 1 a 5 merece esta experiencia?\",
        \"criteria\": [
          \"1 estrella: Pésima, inaceptable\",
          \"2 estrellas: Mala con fallos graves\",
          \"3 estrellas: Regular\",
          \"4 estrellas: Buena\",
          \"5 estrellas: Excelente\"
        ]
      }
    }
  }" | python3 -m json.tool

# 4. Combinado: Las 3 primitivas en 1 sola llamada (Single Pass)
echo -e "\n--- Paso 4: Combinado (Reseña con Sarcasmo: Sarcasmo + Emoji + Estrellas) ---"
curl -sS -X POST "$GATEWAY/v1/systemone" \
  -H 'Content-Type: application/json' \
  -d "{
    \"model\": \"$MODEL\",
    \"state\": {\"resena\": \"Qué maravilla de servicio, solo tardaron 2 horas en traer la pizza fría\"},
    \"questions\": {
      \"es_sarcasmo\": {
        \"type\": \"noul\",
        \"instructions\": \"¿El autor de la reseña está usando sarcasmo o ironía?\"
      },
      \"emoji\": {
        \"type\": \"choice\",
        \"instructions\": \"¿Qué emoji representa mejor el sentimiento de la reseña?\",
        \"criteria\": {
          \"🤩\": \"Entusiasmo o admiración\",
          \"😊\": \"Alegría o satisfacción\",
          \"😐\": \"Neutralidad\",
          \"🙄\": \"Sarcasmo, frustración o resignación\",
          \"😡\": \"Enfado visible\"
        }
      },
      \"estrellas\": {
        \"type\": \"score\",
        \"instructions\": \"¿Cuántas estrellas de 1 a 5 merece esta reseña?\",
        \"criteria\": [
          \"1 estrella: Pésima, totalmente insatisfecho\",
          \"2 estrellas: Mala con fallos graves\",
          \"3 estrellas: Regular\",
          \"4 estrellas: Buena\",
          \"5 estrellas: Excelente\"
        ]
      }
    }
  }" | python3 -m json.tool
