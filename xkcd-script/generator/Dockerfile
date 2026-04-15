FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
        fontforge \
        python3-fontforge \
        potrace \
        pango1.0-tools \
        imagemagick \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages \
        scikit-image scipy matplotlib parse
