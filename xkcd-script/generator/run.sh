#!/usr/bin/env bash

IMAGE=${FONTBUILDER_IMAGE:-ghcr.io/ipython/xkcd-font:fontbuilder}
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd ${DIR}
RUN_CTXT="docker run --rm -u $(id -u) -v $(pwd)/../:$(pwd)/../ -w $(pwd) -e LC_ALL=en_US.UTF-8 ${IMAGE}"

FROM=${1:-1}

set -ex

# Following @pelson's field notes at https://pelson.github.io/2017/xkcd_font/
# Pass a part number as the first argument to start from that step, e.g. ./run.sh 6
[ "$FROM" -le 1 ] && $RUN_CTXT python3 pt1_character_extraction.py
[ "$FROM" -le 2 ] && $RUN_CTXT python3 pt2_character_classification.py
[ "$FROM" -le 3 ] && $RUN_CTXT python3 pt3_ppm_to_svg.py
[ "$FROM" -le 4 ] && $RUN_CTXT python3 pt4_additional_sources.py
[ "$FROM" -le 5 ] && $RUN_CTXT python3 pt5_svg_to_font.py
[ "$FROM" -le 6 ] && $RUN_CTXT python3 pt6_derived_chars.py xkcd-script-mono
[ "$FROM" -le 6 ] && $RUN_CTXT python3 pt6_derived_chars.py xkcd-script
[ "$FROM" -le 7 ] && $RUN_CTXT python3 pt7_font_properties.py xkcd-script-mono
[ "$FROM" -le 7 ] && $RUN_CTXT python3 pt7_font_properties.py xkcd-script
[ "$FROM" -le 8 ] && $RUN_CTXT python3 pt8_gen_reprod_font.py xkcd-script-mono
[ "$FROM" -le 8 ] && $RUN_CTXT python3 pt8_gen_reprod_font.py xkcd-script
