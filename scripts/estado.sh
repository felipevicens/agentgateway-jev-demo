#!/usr/bin/env bash
# Que esta en marcha y si responde. Util antes de lanzar bench.py.
source "$(dirname "${BASH_SOURCE[0]}")/entorno.sh"
chk() { # nombre puerto ruta
  if [ "$(curl -s -m 2 -o /dev/null -w "%{http_code}" "http://127.0.0.1:$2$3" 2>/dev/null)" != "000" ]; then echo "  OK    $1 (:$2)"; else echo "  --    $1 (:$2) no responde"; fi
}
echo "Servidores:"
chk "gateway" "$PUERTO_GATEWAY" "/"
chk "Laya"    "$PUERTO_LAYA" "/health"
chk "Julia-1" "$PUERTO_JULIA" "/health"
chk "webhook" "$PUERTO_WEBHOOK" "/"
chk "web"     "$PUERTO_WEB" "/api/health"
echo; echo "Laya:"; curl -s -m 2 "127.0.0.1:$PUERTO_LAYA/health" | head -c 220 || true
echo; echo; echo "GPU:"; nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader 2>/dev/null || echo "  (sin nvidia-smi)"
echo; echo "Disco:"; df -h "$REPO" | tail -1
