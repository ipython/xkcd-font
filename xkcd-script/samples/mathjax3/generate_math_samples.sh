#!/usr/bin/env bash
# Regenerate the MathJax sample PNGs using the pinned official Playwright image.
# `git diff` / `git status` after running shows what changed; CI runs this
# script and then `git diff --exit-code` over the PNG paths.
#
# The repo root is bind-mounted so generate.js can serve the live
# xkcd-mathjax3.js and woff files from the working tree.
#
# The Playwright image version must stay in sync with the `playwright` package
# version in package.json.

set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "${DIR}/../../.." && pwd )"
PLAYWRIGHT_VERSION="v1.49.1-noble"

docker run --rm \
    -u "$(id -u):$(id -g)" \
    -v "${REPO_ROOT}:/work" \
    -w /work/xkcd-script/samples/mathjax3 \
    "mcr.microsoft.com/playwright:${PLAYWRIGHT_VERSION}" \
    bash -c 'npm ci && node generate.js "$@"' -- "$@"
