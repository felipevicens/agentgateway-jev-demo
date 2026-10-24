#!/usr/bin/env bash
# Laya (laya-serve) en :8100, protocolo /v1/systemone.
#   ./scripts/lanzar_laya.sh gpu     # CUDA
#   ./scripts/lanzar_laya.sh cpu
#
# Carga los dos checkpoints. OJO: el campo "model" de la peticion elige cual:
#   "laya" = ingles (421M, el que mejor rinde aqui) | "multilingual" = 322M
# En el gateway son los modelos "laya" y "laya-ml". Comprueba en la respuesta
# el campo routing.model para saber cual se ha usado.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/entorno.sh"
necesita_venv
modo="${1:-gpu}"
case "$modo" in gpu) dev=cuda ;; cpu) dev=cpu ;; *) echo "Uso: $0 gpu|cpu"; exit 1 ;; esac

liberar_puerto "$PUERTO_LAYA"
echo "Laya en $dev -> http://127.0.0.1:$PUERTO_LAYA/v1/systemone  (comprobar: curl localhost:$PUERTO_LAYA/health)"
LAYA_PORT="$PUERTO_LAYA" LAYA_HOST=127.0.0.1 LAYA_DEVICE="$dev" \
LAYA_MODELS="${LAYA_MODELS:-english,multilingual}" \
  exec "$VENV/bin/laya-serve"
