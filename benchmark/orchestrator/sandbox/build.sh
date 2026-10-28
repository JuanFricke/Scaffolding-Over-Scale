#!/usr/bin/env bash
# Build the agent sandbox image on top of the grading image (benchmark/bin/build-image.sh first).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
BASE="${1:-pf-bench:tcc-baseline-v1}"
IMAGE="${2:-pf-bench-agent:tcc-baseline-v1}"
docker image inspect "$BASE" >/dev/null || { echo "missing $BASE: run benchmark/bin/build-image.sh" >&2; exit 1; }
docker build --build-arg BASE="$BASE" -t "$IMAGE" .
echo "built $IMAGE"
