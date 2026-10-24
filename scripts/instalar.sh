#!/usr/bin/env bash
# Instala por partes lo necesario para el vídeo, desde cero y desde este repo.
#
#   ./scripts/instalar.sh gateway    # agentgateway (binario verificado con SHA256)
#   ./scripts/instalar.sh laya       # entorno Python + PyTorch + Laya (se baja solo al arrancar)
#   ./scripts/instalar.sh julia      # descarga Julia-1 y su transformers 5.0.x aparte
#   ./scripts/instalar.sh llamacpp   # opcional: compila llama-server (Julia-1 en CPU)
#   ./scripts/instalar.sh todo       # gateway + laya + julia
#
# Cuidado con el disco: el entorno con PyTorch ocupa ~6-7 GB y los modelos
# ~1 GB mas. Para sacarlos de C: (WSL): MODELS=/mnt/e/models ./scripts/instalar.sh todo
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/entorno.sh"

espacio() { echo; echo ">> Espacio libre:"; df -h "$REPO" "$MODELS" 2>/dev/null | sort -u; }

instalar_gateway() {
  echo "== agentgateway $AGENTGATEWAY_VERSION"
  mkdir -p "$BIN"
  local base="https://github.com/agentgateway/agentgateway/releases/download/$AGENTGATEWAY_VERSION"
  curl -sSL -o "$BIN/agentgateway" "$base/agentgateway-linux-amd64"
  local esperado real
  esperado=$(curl -sSL "$base/agentgateway-linux-amd64.sha256" | awk '{print $1}')
  real=$(sha256sum "$BIN/agentgateway" | awk '{print $1}')
  [ "$esperado" = "$real" ] || { echo "SHA256 NO coincide ($real != $esperado). Aborto."; rm -f "$BIN/agentgateway"; exit 1; }
  chmod +x "$BIN/agentgateway"
  echo "SHA256 verificado: $real"
  "$BIN/agentgateway" --version | head -3
}

crear_venv() {
  if [ ! -x "$PY" ]; then
    echo "== Entorno Python en $VENV"
    python3 -m venv "$VENV"
  fi
}

instalar_laya() {
  crear_venv
  echo "== PyTorch $TORCH_VERSION ($TORCH_VARIANT)"
  "$PY" -m pip install -q --no-cache-dir "torch==$TORCH_VERSION" \
    --index-url "https://download.pytorch.org/whl/$TORCH_VARIANT" --extra-index-url https://pypi.org/simple
  echo "== Laya y servidor"
  "$PY" -m pip install -q --no-cache-dir -r "$REPO/requirements.txt" laya fastapi uvicorn
  "$PY" - <<'PYEOF'
import torch, laya
print("torch", torch.__version__, "| CUDA disponible:", torch.cuda.is_available())
if torch.cuda.is_available():
    x = torch.randn(8, 8, device="cuda"); (x @ x).sum().item()   # falla si la GPU no tiene kernels
    print("GPU:", torch.cuda.get_device_name(0), "-> kernels OK")
PYEOF
}

instalar_julia() {
  crear_venv
  echo "== Julia-1 en $MODELS"
  mkdir -p "$MODELS" "$PYLIBS"
  "$PY" - "$MODELS" <<'PYEOF'
import sys
from huggingface_hub import snapshot_download
m = sys.argv[1]
snapshot_download("SupersonicLabs/Julia-1", local_dir=f"{m}/Julia-1")
snapshot_download("ggml-org/Julia-1-GGUF", local_dir=f"{m}/Julia-1-GGUF", allow_patterns=["*Q8_0.gguf", "README.md"])
print("Julia-1 descargado")
PYEOF
  # El runtime de Julia parchea un metodo interno que solo existe en
  # transformers 5.0.x; se instala aparte y se antepone por PYTHONPATH.
  echo "== transformers 5.0.x en $PYLIBS"
  "$PY" -m pip install -q --no-cache-dir --no-deps --target "$PYLIBS" "transformers>=5.0,<5.1" "tokenizers>=0.22,<=0.23.0"
}

instalar_llamacpp() {
  crear_venv
  echo "== llama.cpp (solo CPU) en $LLAMACPP"
  "$PY" -m pip install -q --no-cache-dir cmake ninja
  [ -d "$LLAMACPP" ] || git clone -q --depth 1 https://github.com/ggml-org/llama.cpp.git "$LLAMACPP"
  PATH="$VENV/bin:$PATH" cmake -S "$LLAMACPP" -B "$LLAMACPP/build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
    -DGGML_NATIVE=ON -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF >/dev/null
  PATH="$VENV/bin:$PATH" cmake --build "$LLAMACPP/build" --target llama-server -j "$(nproc)"
  echo "llama-server: $LLAMACPP/build/bin/llama-server"
}

case "${1:-}" in
  gateway)  instalar_gateway ;;
  laya)     instalar_laya ;;
  julia)    instalar_julia ;;
  llamacpp) instalar_llamacpp ;;
  todo)     instalar_gateway; instalar_laya; instalar_julia ;;
  *) sed -n '2,13p' "${BASH_SOURCE[0]}"; exit 1 ;;
esac
espacio
echo "Listo."
