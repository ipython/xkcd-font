# -*- coding: utf-8 -*-
"""
Extract hand-drawn glyphs from extras/ and convert them to SVG.

Outputs go to ../generated/additional_chars/ and are consumed by pt5_svg_to_font.py.
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


def extract_symbol(arr, y0, y1, x0, x1, name, exclude=None):
    """Crop glyph region, upsample, binarise, run potrace, clean, save SVG.

    exclude: optional list of (y0, y1, x0, x1) regions in full-image coordinates
             to blank out (set to background) before potrace, for removing
             artefacts that cannot be separated by tightening the main crop.
    """
    crop = arr[y0:y1, x0:x1].copy()
    if exclude:
        for ey0, ey1, ex0, ex1 in exclude:
            crop[ey0 - y0:ey1 - y0, ex0 - x0:ex1 - x0] = 255
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
# xkcd 2586 "Greek Letters" — 2x image (889 × 1699 px)
# Symbol column: cols 80–136; coordinates are 2× the 1x bounds.
# ---------------------------------------------------------------------------

GREEK_LETTERS_2586 = {
    # name         y0    y1    x0   x1
    'pi':       ( 144,  172,  80, 136),  # π  U+03C0
    'Delta':    ( 190,  228,  80, 136),  # Δ  U+0394
    'delta':    ( 256,  304,  80, 136),  # δ  U+03B4
    'theta':    ( 334,  372,  80, 136),  # θ  U+03B8
    'phi':      ( 370,  440,  80, 136),  # φ  U+03C6  (y1 extended: clips on bottom)
    'lunate_epsilon': ( 450,  476,  80, 136),  # ϵ  U+03F5
    'upsilon':  ( 500,  534,  35,  86),  # υ  U+03C5  (left half of ν/υ pair row; x1 tightened: comma at col 87)
    'nu':       ( 500,  534,  88, 120),  # ν  U+03BD  (right half of ν/υ pair row)
    'mu':       ( 562,  608,  65, 136),  # μ  U+03BC  (x0 extended: clips on left)
    'Sigma':    ( 636,  678,  65, 136),  # Σ  U+03A3  (x0 extended: clips on left)
    'Pi':       ( 688,  732,  65, 136),  # Π  U+03A0  (x0 extended: clips on left)
    'zeta':     ( 740,  795,  80, 136),  # ζ  U+03B6  (y0 compromise: clears Pi, keeps zeta top)
    'beta':     ( 800,  844,  80, 136),  # β  U+03B2
    'alpha':    ( 872,  902,  80, 115),  # α  U+03B1  (x1 tightened: bit on right)
    'Omega':    ( 958, 1002,  70, 130),  # Ω  U+03A9  (x1 loosened from 115: clips on right)
    'omega':    (1050, 1080,  65, 136),  # ω  U+03C9  (x0 extended: clips on left)
    'sigma':    (1140, 1168,  80, 136),  # σ  U+03C3
    'xi':       (1220, 1266,  80, 136),  # ξ  U+03BE
    'gamma':    (1290, 1336,  80, 136),  # γ  U+03B3
    'rho':      (1362, 1422,  80, 136),  # ρ  U+03C1  (y1 extended: clips on bottom)
    'Xi':       (1472, 1520,  80, 136),  # Ξ  U+039E
    'psi':      (1574, 1630,  65, 136),  # ψ  U+03C8  (x0 extended: clips on left)
}

# Regions (in full-image coords) to blank out before potrace, keyed by glyph name.
# Used when an artefact cannot be excluded by tightening the main crop alone.
GREEK_EXCLUDE_2586 = {
    'upsilon': [(522, 534, 80, 100)],  # comma tail curves into the crop at rows 522-533
}

_greek_image = os.path.join(os.path.dirname(__file__), '2586_greek_letters_2x.png')
print(f'Extracting Greek letters from {_greek_image}...')
arr_greek = np.array(Image.open(_greek_image).convert('L'))
for name, (y0, y1, x0, x1) in GREEK_LETTERS_2586.items():
    extract_symbol(arr_greek, y0, y1, x0, x1, name,
                   exclude=GREEK_EXCLUDE_2586.get(name))


# ---------------------------------------------------------------------------
# Hand-drawn extras (generator/extras/*.png)
# Each file is a full-glyph image (no cropping needed).  RGBA images are
# composited onto white before thresholding so transparent areas read as white.
# A lower upsample factor is used since these images are already high-res.
# ---------------------------------------------------------------------------

EXTRAS_DIR = 'extras'

# Each entry is (output_name, source_filename_stem).
EXTRAS = [
    ('notdef', '1913_i_2x__notdef'),            # .notdef fallback glyph source
    ('square', '2251_alignment_chart_2x__square'),  # □ U+25A1 source
    ('eszett', 'eszett'),                       # ß U+00DF / ẞ U+1E9E source
    ('lambda', '1145_sky_color_2x__lambda'),    # λ U+03BB source
    ('tau', '2520_symbols_2x__tau'),            # τ U+03C4 source
    ('varsigma', '2586_greek_letters_2x__sigma'), # ς U+03C2 source
    ('AElig', '2763_linguistics_gossip_2x__AE'), # Æ U+00C6 source
    ('cedilla', '2034_equations_2x__cedilla.hand-tweaked'),  # hook cedilla mark source
    ('epsilon', '2034_equations_2x__epsilon'),               # ε U+03B5 source
]

print('Extracting hand-drawn extras...')
for name, filename in EXTRAS:
    src_path = os.path.join(EXTRAS_DIR, f'{filename}.png')
    arr_extra = np.array(Image.open(src_path).convert('L'))
    h, w = arr_extra.shape
    extract_symbol(arr_extra, 0, h, 0, w, name)


# ---------------------------------------------------------------------------
# ai_extensions_1.png — hand-drawn ligatures and IPA letters
# Coordinates measured from the 1774×887 px image.
# ---------------------------------------------------------------------------

AI_EXT_1 = {
    # name       y0    y1    x0    x1
    'OElig': (155, 358,  835, 1107),  # Œ  U+0152
    'aelig': (225, 357, 1363, 1515),  # æ  U+00E6
    'oelig': (223, 354, 1582, 1750),  # œ  U+0153
}

_ai_ext_1_image = os.path.join(os.path.dirname(__file__), 'ai_extensions_1.png')
print(f'Extracting ligatures from {_ai_ext_1_image}...')
arr_ai1 = np.array(Image.open(_ai_ext_1_image).convert('L'))
for name, (y0, y1, x0, x1) in AI_EXT_1.items():
    extract_symbol(arr_ai1, y0, y1, x0, x1, name)
