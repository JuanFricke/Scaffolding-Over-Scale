#!/usr/bin/env bash
# Build the evaluation image once from the Dockerfile at a ref of PF_REPO (private subject repo),
# so every run is graded with the same PHP/extension set regardless of what the
# task's base commit shipped.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

TAG="${1:-$BENCH_DEFAULT_TAG}"
IMAGE="${2:-pf-bench:$TAG}"

command -v docker >/dev/null || die "docker not found"
git -C "$PF_REPO" rev-parse --verify --quiet "${TAG}^{commit}" >/dev/null || die "ref not found: $TAG"

# docker build reads the build context as a tar stream from stdin ("-"); -f is relative to it.
git -C "$PF_REPO" archive "$TAG" | docker build -t "$IMAGE" -f docker/Dockerfile -
echo "built $IMAGE from $TAG"
