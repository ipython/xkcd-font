#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd ${DIR}

cat <<EOF > fonts.conf
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>../font/</dir>
  <cachedir>../.font-cache</cachedir>
  <config></config>
</fontconfig>
EOF


RUN_CTXT="docker run -u $(id -u) -v $(pwd)/../:$(pwd)/../ -w $(pwd) -e FONTCONFIG_FILE=$(pwd)/fonts.conf -e LC_ALL=C.UTF-8 ${FONTBUILDER_IMAGE:-ghcr.io/ipython/xkcd-font:fontbuilder}"

${RUN_CTXT} fc-list | grep -i xkcd

SIMPLE_CTXT="${RUN_CTXT} pango-view --backend=ft2 --font \"xkcdScript\" --dpi 150"

NAME=ipsum
CONTENT=$(cat ${NAME}.txt)
${SIMPLE_CTXT} -o ${NAME}.pgm --text "${CONTENT}"
${RUN_CTXT} convert -strip ${NAME}.pgm ${NAME}.png
${RUN_CTXT} rm ${NAME}.pgm


NAME=handwriting
CONTENT=$(cat ${NAME}.txt)
${SIMPLE_CTXT} -o ${NAME}.pgm --text "${CONTENT}"
${RUN_CTXT} convert -strip ${NAME}.pgm ${NAME}.png
${RUN_CTXT} rm ${NAME}.pgm


NAME=kerning
CONTENT=$(cat ${NAME}.txt)
${SIMPLE_CTXT} -o ${NAME}.pgm --text "${CONTENT}"
${RUN_CTXT} convert -strip ${NAME}.pgm ${NAME}.png
${RUN_CTXT} rm ${NAME}.pgm


if [ "$?" == "141" ] ; then
    # Unexplained exit code from the handwriting sample.
    exit 0
fi

${RUN_CTXT} python3 gen_charmap.py
