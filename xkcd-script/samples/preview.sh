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


RUN_CTXT="docker run -u $(id -u) -v $(pwd)/../:$(pwd)/../ -w $(pwd) -e FONTCONFIG_FILE=$(pwd)/fonts.conf pelson/fontbuilder"

SIMPLE_CTXT="${RUN_CTXT} pango-view --backend=ft2 --font \"xkcdScript\" --dpi 150" 

NAME=ipsum
CONTENT=$(cat ${NAME}.txt)
${SIMPLE_CTXT} -o ${NAME}.pgm --wrap=word --width=400 --text "${CONTENT}"
${RUN_CTXT} python -c "import skimage.io; skimage.io.imsave('${NAME}.png', skimage.io.imread('${NAME}.pgm'))"
${RUN_CTXT} rm ${NAME}.pgm


NAME=handwriting
CONTENT=$(cat ${NAME}.txt)
${SIMPLE_CTXT} -o ${NAME}.pgm --text "${CONTENT}"
${RUN_CTXT} python -c "import skimage.io; skimage.io.imsave('${NAME}.png', skimage.io.imread('${NAME}.pgm'))"
${RUN_CTXT} rm ${NAME}.pgm


if [ "$?" == "141" ] ; then
    # Unexplained exit code from the handwriting sample.
    exit 0
fi
