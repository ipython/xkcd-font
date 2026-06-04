#!/usr/bin/env bash
# Regenerate the MathJax sample PNGs inside the pinned Docker image.
# `git diff` / `git status` after running shows what changed; CI runs this
# script and then `git diff --exit-code` over the PNG paths.
#
# Environment:
#   SAMPLES_IMAGE   Image to use (default: locally built xkcd-mathjax-samples)
#   NO_BUILD=1      Skip `docker build` (use only if the image exists locally)
#
# The repo root is bind-mounted into the container so generate.js can serve
# the live xkcd-mathjax3.js and woff files via its embedded static server.

set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "${DIR}/../../.." && pwd )"
IMAGE="${SAMPLES_IMAGE:-xkcd-mathjax-samples}"

if [ -z "${NO_BUILD:-}" ]; then
    docker build -t "${IMAGE}" "${DIR}"
fi

# Mount the repo at /work (matches the Dockerfile WORKDIR layout) and run as
# the host user so any written files (samples PNGs, README, .diff/) end up
# owned correctly.
docker run --rm \
    -u "$(id -u):$(id -g)" \
    -v "${REPO_ROOT}:/work" \
    -w /work/xkcd-script/samples/mathjax3 \
    "${IMAGE}" "$@"
