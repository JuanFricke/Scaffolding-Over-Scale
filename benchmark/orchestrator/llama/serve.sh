#!/usr/bin/env bash
# Serve the local benchmark models (models.ini) with llama-server in router mode.
# Listens on localhost (sandbox-less runs) and on the docker0 bridge (sandboxed runs reach
# it as host.docker.internal); never on the LAN. Foreground; Ctrl-C to stop.
#   LLAMA_SERVER  llama-server binary   (default ~/Projetos/llama.cpp/build/bin/llama-server)
#   MODELS_DIR    directory of the GGUFs (default ~/Modelos)
#   LLAMA_PORT    port                   (default 8089)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
LLAMA_SERVER="${LLAMA_SERVER:-$HOME/Projetos/llama.cpp/build/bin/llama-server}"
MODELS_DIR="${MODELS_DIR:-$HOME/Modelos}"
LLAMA_PORT="${LLAMA_PORT:-8089}"
bridge="$(ip -4 -o addr show docker0 2>/dev/null | awk '{print $4}' | cut -d/ -f1)"
hosts="127.0.0.1${bridge:+,$bridge}"
cd "$MODELS_DIR"
exec "$LLAMA_SERVER" --models-preset "$here/models.ini" --models-max 1 \
    --host "$hosts" --port "$LLAMA_PORT" "$@"
