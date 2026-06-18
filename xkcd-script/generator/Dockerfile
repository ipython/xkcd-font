FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
        fontforge \
        python3-fontforge \
        potrace \
        pango1.0-tools \
        imagemagick \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Direct deps are listed in requirements.in; requirements.txt is a fully
# resolved lockfile produced by `uv pip compile`. Regenerate after editing
# requirements.in:
#   uv pip compile xkcd-script/generator/requirements.in \
#       -o xkcd-script/generator/requirements.txt --python-version 3.12
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --break-system-packages -r /tmp/requirements.txt
