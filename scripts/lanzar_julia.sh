#!/usr/bin/env bash
# Julia-1 en :8200, protocolo /v1/systemone. Tres formas, el mismo puerto
# (se arranca UNA; el gateway no cambia):
#   ./scripts/lanzar_julia.sh gpu        # runtime oficial en CUDA (julia_serve.py)
#   ./scripts/lanzar_julia.sh cpu        # runtime oficial en CPU
#   ./scripts/lanzar_julia.sh llamacpp   # llama-server (llama.cpp), GGUF Q8, CPU
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/entorno.sh"
modo="${1:-gpu}"

liberar_puerto "$PUERTO_JULIA"
case "$modo" in
  gpu|cpu)
    necesita_venv
    [ -d "$MODELS/Julia-1" ] || { echo "Falta Julia-1. Ejecuta: ./scripts/instalar.sh julia"; exit 1; }
    [ "$modo" = gpu ] && dev=cuda || dev=cpu
    echo "Julia-1 en $dev -> http://127.0.0.1:$PUERTO_JULIA/v1/systemone"
    JULIA_DIR="$MODELS/Julia-1" JULIA_DEVICE="$dev" JULIA_PORT="$PUERTO_JULIA" PYTHONPATH="$PYLIBS" \
      exec "$PY" "$REPO/julia_serve.py"
    ;;
  llamacpp)
    srv="$LLAMACPP/build/bin/llama-server"
    [ -x "$srv" ] || { echo "Falta llama-server. Ejecuta: ./scripts/instalar.sh llamacpp"; exit 1; }
    echo "Julia-1 con llama.cpp -> http://127.0.0.1:$PUERTO_JULIA/v1/systemone"
    LD_LIBRARY_PATH="$LLAMACPP/build/bin" exec "$srv" -m "$MODELS/Julia-1-GGUF/Julia-1-Q8_0.gguf" \
      --host 127.0.0.1 --port "$PUERTO_JULIA" -t "$(nproc)"
    ;;
  *) echo "Uso: $0 gpu|cpu|llamacpp"; exit 1 ;;
esac
