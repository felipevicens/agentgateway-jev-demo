# Variables comunes de los scripts. Se carga con `source`, no se ejecuta.
# Todo se puede cambiar exportando la variable antes de lanzar el script.
#
#   MODELS=/mnt/e/models ./scripts/instalar.sh todo     # modelos fuera de C:
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

VENV="${VENV:-$REPO/.venv-local}"       # entorno Python (torch, laya, fastapi...)
BIN="${BIN:-$REPO/bin}"                 # agentgateway y llama-server
MODELS="${MODELS:-$REPO/models}"        # Julia-1 (safetensors y GGUF) y cache de HF
PYLIBS="${PYLIBS:-$REPO/pylibs/tf50}"   # transformers 5.0.x solo para Julia-1
LLAMACPP="${LLAMACPP:-$REPO/llama.cpp}" # fuentes y build de llama.cpp (opcional)
export HF_HOME="${HF_HOME:-$MODELS/hf}" # cache de Hugging Face (Laya se baja aqui)

# Puertos: 4000 gateway, 8000 webhook, 8100 Laya, 8200 Julia-1, 3000 web.
PUERTO_GATEWAY=4000; PUERTO_WEBHOOK=8000; PUERTO_LAYA=8100; PUERTO_JULIA=8200
PUERTO_WEB="${PUERTO_WEB:-3000}"

# "cu126" es la ultima rueda de PyTorch que incluye GPUs Maxwell (GTX 900);
# vale tambien para Pascal en adelante. "cpu" si no hay GPU.
TORCH_VARIANT="${TORCH_VARIANT:-cu126}"
TORCH_VERSION="${TORCH_VERSION:-2.14.1}"
AGENTGATEWAY_VERSION="${AGENTGATEWAY_VERSION:-v1.6.0}"

PY="$VENV/bin/python"

# Si $1 esta ocupado, lo libera (los modelos locales comparten puertos).
liberar_puerto() {
  local pid
  pid=$(ss -ltnp 2>/dev/null | grep ":$1 " | grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2 || true)
  if [ -n "$pid" ]; then echo "Liberando el puerto $1 (pid $pid)"; kill "$pid"; sleep 2; fi
}

necesita_venv() {
  [ -x "$PY" ] || { echo "No existe el entorno $VENV. Ejecuta antes: ./scripts/instalar.sh laya"; exit 1; }
}
