#!/usr/bin/env bash

IMAGE=pelson/fontbuilder
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd ${DIR}
RUN_CTXT="docker run -u $(id -u) -v $(pwd)/../:$(pwd)/../ -w $(pwd) -e LC_ALL:en_US.UTF-8 ${IMAGE}"

set -x

# Following @pelson's field notes at https://pelson.github.io/2017/xkcd_font/
$RUN_CTXT python pt1_character_extraction.py
$RUN_CTXT python pt2_character_classification.py
$RUN_CTXT python pt3_ppm_to_svg.py
$RUN_CTXT python pt4_svg_to_font.py
$RUN_CTXT python pt5_gen_reprod_font.py 
