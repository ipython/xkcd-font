# -*- coding: utf-8 -*-
"""
Extract hand-drawn glyphs from extras/ and convert them to SVG.

Outputs go to ../generated/additional_chars/ and are consumed by pt6_derived_chars.py.
"""
import os
import subprocess
import tempfile
import numpy as np
from PIL import Image
import fontforge

OUT_DIR = '../generated/additional_chars'
os.makedirs(OUT_DIR, exist_ok=True)

UPSAMPLE = 12   # upscale factor before potrace; higher = more curve detail
THRESHOLD = 160  # pixel value below which a pixel is considered ink


def _clean_potrace_svg(raw_svg_path, clean_svg_path):
    """Remove potrace artefacts from raw_svg_path and write clean_svg_path.

    Potrace always emits a background rectangle covering the full canvas, plus
    occasional single-pixel noise specks.  We load the SVG into FontForge,
    drop those contours, and re-export so that pt6 receives a file containing
    only the actual ink outlines.

    Filtering rules (applied in order):
      1. Background rectangle: <= 12 control points AND spans > 80% of the
         full bounding box in both axes.
      2. Noise specks: bbox smaller than 10% of the remaining ink extent in
         both axes simultaneously.
    """
    scratch = fontforge.font()
    g = scratch.createChar(-1, 'tmp')
    g.importOutlines(raw_svg_path)

    # Pass 1: drop background rectangle
    full_bb = g.boundingBox()
    full_w = full_bb[2] - full_bb[0]
    full_h = full_bb[3] - full_bb[1]
    pass1 = fontforge.layer()
    for c in g.foreground:
        cb = c.boundingBox()
        span_w = (cb[2] - cb[0]) / full_w if full_w else 0
        span_h = (cb[3] - cb[1]) / full_h if full_h else 0
        if len(list(c)) <= 12 and span_w > 0.8 and span_h > 0.8:
            continue
        pass1 += c
    g.foreground = pass1

    # Pass 2: drop noise specks relative to ink extent
    ink_bb = g.boundingBox()
    ink_w = ink_bb[2] - ink_bb[0]
    ink_h = ink_bb[3] - ink_bb[1]
    ink = fontforge.layer()
    for c in pass1:
        cb = c.boundingBox()
        if (cb[2] - cb[0]) < ink_w * 0.10 and (cb[3] - cb[1]) < ink_h * 0.10:
            continue
        ink += c
    g.foreground = ink

    scratch.save(clean_svg_path + '.sfd')  # FontForge can't export single-glyph SVG directly
    # Export via generate — write to a temp SFD then export the glyph as SVG
    g.export(clean_svg_path)
    os.remove(clean_svg_path + '.sfd')


def extract_symbol(arr, r0, r1, c0, c1, name):
    """Crop glyph region, upsample, binarise, run potrace, clean, save SVG."""
    crop = arr[r0:r1, c0:c1]
    big = Image.fromarray(crop).resize(
        (crop.shape[1] * UPSAMPLE, crop.shape[0] * UPSAMPLE),
        Image.BILINEAR)
    binary = (np.array(big) >= THRESHOLD).astype(np.uint8) * 255

    with tempfile.TemporaryDirectory() as tmp:
        png_path = os.path.join(tmp, f'{name}.png')
        pbm_path = os.path.join(tmp, f'{name}.pbm')
        raw_svg  = os.path.join(tmp, f'{name}_raw.svg')
        Image.fromarray(binary, mode='L').save(png_path)
        subprocess.check_call(['convert', png_path, '-threshold', '50%', pbm_path])
        subprocess.check_call(['potrace', '-s', pbm_path, '-o', raw_svg])
        svg_path = os.path.join(OUT_DIR, f'{name}.svg')
        _clean_potrace_svg(raw_svg, svg_path)

    print(f'  wrote {svg_path}')
    return svg_path


# ---------------------------------------------------------------------------
# Hand-drawn extras (generator/extras/*.png)
# Each file is a full-glyph image (no cropping needed).  RGBA images are
# composited onto white before thresholding so transparent areas read as white.
# A lower upsample factor is used since these images are already high-res.
# ---------------------------------------------------------------------------

EXTRAS_DIR = 'extras'

EXTRAS = [
    'eszett',   # ß U+00DF / ẞ U+1E9E source
]

print('Extracting hand-drawn extras...')
for name in EXTRAS:
    src_path = os.path.join(EXTRAS_DIR, f'{name}.png')
    arr_extra = np.array(Image.open(src_path).convert('L'))
    h, w = arr_extra.shape
    extract_symbol(arr_extra, 0, h, 0, w, name)

