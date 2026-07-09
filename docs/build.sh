#!/usr/bin/env bash
# Assemble the Pages site: docs/ + release assets → $OUT
#
# Env vars:
#   OUT   output directory, relative to repo root (default: _site)
#   TAG   release tag to pull assets from (default: latest)
#   REPO  GitHub repo (default: ipython/xkcd-font)
set -euo pipefail

OUT="${OUT:-build/html}"
TAG="${TAG:-}"
REPO="${REPO:-ipython/xkcd-font}"

DOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DOCS/.." && pwd)"
DEST="$ROOT/$OUT"

rm -rf "$DEST"
mkdir -p "$DEST/assets"
# Copy every doc source except this build script itself.
rsync -a --exclude='build.sh' "$DOCS/" "$DEST/"

download=(gh release download
  --repo "$REPO"
  --dir "$DEST/assets"
  --pattern xkcd-script.otf
  --pattern xkcd-script.ttf
  --pattern xkcd-script.woff
  --pattern xkcd-script.woff2
  --pattern xkcd-mathjax3.js)
[ -n "$TAG" ] && download+=("$TAG")

"${download[@]}"

echo "Site assembled at $DEST"
