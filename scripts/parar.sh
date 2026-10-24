#!/usr/bin/env bash
# Para los servidores del vídeo (gateway, webhook, Laya y Julia-1).
source "$(dirname "${BASH_SOURCE[0]}")/entorno.sh"
for p in "$PUERTO_GATEWAY" "$PUERTO_WEBHOOK" "$PUERTO_LAYA" "$PUERTO_JULIA" "$PUERTO_WEB"; do liberar_puerto "$p"; done
echo "Hecho."
