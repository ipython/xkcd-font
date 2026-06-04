# Image for generating / verifying the MathJax sample renders.
#
# Based on Microsoft's official Playwright image so Chromium, its system
# dependencies, and the font-rendering stack (fontconfig, libfreetype,
# noto/dejavu fallbacks) are pinned to a known good combination.
#
# Tag must match the `playwright` version in package.json so that the
# Chromium bundled in this image matches the API client used by generate.js.

FROM mcr.microsoft.com/playwright:v1.49.1-noble

# Everything happens under /work; the runner script bind-mounts the repo
# root here so the static server can serve xkcd-mathjax3.js and the woff
# files from the live working tree.
WORKDIR /work/xkcd-script/samples/mathjax3

# Pre-warm node_modules in the image so cold runs don't re-fetch every time.
# The COPY brings in only the install manifests so this layer is invalidated
# only when deps actually change.
COPY package.json package-lock.json* ./
# `npm ci` requires a lockfile; fall back to `npm install` if missing so an
# initial `docker build` works before the lockfile has been committed.
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# The remaining sources (template.html, formulas.json, generate.js, etc) are
# read from the bind mount at run time so editing on the host doesn't require
# rebuilding the image.

ENTRYPOINT ["node", "generate.js"]
