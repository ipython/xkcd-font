# -*- coding: utf-8 -*-
"""
Convert hand-drawn SVG glyphs into the base xkcd-script SFD font file.

Reads per-character SVG files produced by pt3_ppm_to_svg.py and additional
comic-sourced SVGs produced by pt4_additional_sources.py, scales and positions
each glyph to fit the EM, applies per-line scale corrections, and saves the
result as xkcd-script.sfd.

Derived characters (diacriticals, aliases) are added in pt6_derived_chars.py.
Font-wide properties (kerning) are applied in pt7_font_properties.py.
"""
from __future__ import division
import base64
import fontforge
import os
import glob
import parse
import unicodedata

fnames = sorted(glob.glob('../generated/characters/char_*.svg'))

characters = []
for fname in fnames:
    # Sample filename: char_L2_P2_x378_y1471_x766_y1734_RQ==?.svg

    pattern = 'char_L{line:d}_P{position:d}_x{x0:d}_y{y0:d}_x{x1:d}_y{y1:d}_{b64_str}.svg'
    result = parse.parse(pattern, os.path.basename(fname))
    chars = tuple(base64.b64decode(result['b64_str']).decode('utf-8'))
    bbox = (result['x0'], result['y0'], result['x1'], result['y1'])
    characters.append([result['line'], result['position'], bbox, fname, chars])


def basic_font():
    font = fontforge.font()
    font.familyname = font.fontname = 'XKCD'
    font.encoding = "UnicodeFull"

    font.version = '1.0';
    font.weight = 'Regular';
    font.fontname = 'xkcdScript'
    font.familyname = 'xkcd Script'
    font.fullname = 'xkcd-Script-Regular'
    font.copyright = 'Copyright (c) ipython/xkcd-font contributors, Creative Commons Attribution-NonCommercial 3.0 License'
    # As per guidelines in https://fontforge.github.io/fontinfo.html, xuid is no longer needed.
    font.uniqueid = -1

    font.em = 1024;
    font.ascent = 768;
    font.descent = 256;

    # We create a ligature lookup table.
    font.addLookup('ligatures', 'gsub_ligature', (), [['liga',
                                                       [['latn',
                                                         ['dflt']]]]])
    font.addLookupSubtable('ligatures', 'liga')

    return font


from contextlib import contextmanager
import tempfile
import shutil
import os


@contextmanager
def tmp_symlink(fname):
    """
    Create a temporary symlink to a file, so that applications that can't handle
    unicode filenames don't barf (I'm looking at you font-forge)

    """
    target = tempfile.mktemp(suffix=os.path.splitext(fname)[1])
    fname = os.path.normpath(os.path.abspath(fname))
    try:
        os.symlink(fname, target)
        yield target
    finally:
        if os.path.exists(target):
            os.remove(target)


def create_char(font, chars, fname):
    if len(chars) == 1:
        # A single unicode character, so I create a character in the font for it.

        # Because I'm using an old & narrow python (<3.5) I need to handle the unicode
        # characters that couldn't be converted to ordinals (so I kept them as integers).
        if isinstance(chars[0], int):
            c = font.createMappedChar(chars[0])
        else:
            c = font.createMappedChar(ord(chars[0]))
    else:
        # Multiple characters - this is a ligature. We need to register this in the
        # ligature lookup table we created. Not all font-handling libraries will do anything
        # with ligatures (e.g. matplotlib doesn't at vn <=2)
        char_names = [charname(char) for char in chars]
        ligature_name = '_'.join(char_names)
        ligature_tuple = tuple([character.encode('ascii') for character in chars])
        ligature_tuple = tuple([character for character in char_names])

        c = font.createChar(-1, ligature_name)

        c.addPosSub('liga', ligature_tuple)

    c.clear()

    # Use the workaround to have non-unicode filenames.
    with tmp_symlink(fname) as tmp_fname:
        # At last, bring in the SVG image as an outline for this glyph.
        c.importOutlines(tmp_fname)

    return c


baseline_chars = ['a' 'e', 'm', 'A', 'E', 'M', '&', '@', '.', u'≪', u'É']
caps_chars = ['S', 'T', 'J', 'k', 't', 'l', 'b', 'd', '1', '2', u'3', u'≪', '?', '!']

line_stats = {}
for line, position, bbox, fname, chars in characters:
    if len(chars) == 1:
        this_line = line_stats.setdefault(line, {})
        char = chars[0]
        if char in baseline_chars:
            this_line.setdefault('baseline', []).append(bbox[3])
        if char in caps_chars:
            this_line.setdefault('cap-height', []).append(bbox[1])


import numpy as np
import psMat

# Normalise each line's cap-height/baseline span to the median across all lines.
# This corrects for lines where the writing was larger or smaller than average,
# so glyphs from all lines get the same scale treatment.
_spans = {line: np.mean(s['baseline']) - np.mean(s['cap-height'])
          for line, s in line_stats.items()
          if 'baseline' in s and 'cap-height' in s}
_top_ratio = 600 / (600 + 256)
_full_glyph_sizes = {line: span / _top_ratio for line, span in _spans.items()}
_median_full_glyph_size = np.median(list(_full_glyph_sizes.values()))


def scale_glyph(char, char_bbox, baseline, cap_height):
    # TODO: The code in this function is convoluted - it can be hugely simplified.
    # Essentially, all this function does is figure out how much
    # space a normal glyph takes, then looks at how much space *this* glyph takes.
    # With that magic ratio in hand, I now look at how much space the glyph *currently*
    # takes, and scale it to the full EM. On second thoughts, this function really does
    # need to be convoluted, so maybe the code isn't *that* bad...

    font = char.font

    # Get hold of the bounding box information for the imported glyph.
    import_bbox = c.boundingBox()
    import_width, import_height = import_bbox[2] - import_bbox[0], import_bbox[3] - import_bbox[1]

    # Note that timportOutlines doesn't guarantee glyphs will be put in any particular location,
    # so translate to the bottom and middle.

    target_baseline = char.font.descent
    top = char.font.ascent
    top_ratio = top / (top + target_baseline)

    y_base_delta_baseline = char_bbox[3] - baseline

    width, height = char_bbox[2] - char_bbox[0], char_bbox[3] - char_bbox[1]

    # This is the scale factor that font forge will have used for normal glyphs...
    scale_factor = (top + target_baseline) / (cap_height - baseline)
    glyph_ratio = (cap_height - baseline) / height

    # A nice glyph size, in pixels. NOTE: In pixel space, cap_height is smaller than baseline, so make it positive.
    full_glyph_size = -(cap_height - baseline) / top_ratio

    to_canvas_coord_from_px = full_glyph_size / font.em

    anchor_ratio = (top + target_baseline) / height

    # pixel scale factor
    px_sf = (top + target_baseline) / font.em

    frac_of_full_size = (height / full_glyph_size)
    import_frac_1000 = font.em / import_height

    t = psMat.scale(frac_of_full_size * import_frac_1000)
    c.transform(t)


def translate_glyph(c, char_bbox, cap_height, baseline):
    # Put the glyph in the middle, and move it relative to the baseline.

    # Compute the proportion of the full EM that cap_height - baseline should consume.
    top_ratio = c.font.ascent / (c.font.ascent + c.font.descent)

    # In the original pixel coordinate space, compute how big a nice full sized glyph
    # should be.
    full_glyph_size = -(cap_height - baseline) / top_ratio

    # We know that the scale of the glyph is now good. But it is probably way off in terms of x & y, so we
    # need to fix up its position.
    glyph_bbox = c.boundingBox()
    # No matter where it is currently, take the glyph to x=0 and a y based on its positioning in
    # the original handwriting sample.
    t = psMat.translate(-glyph_bbox[0], -glyph_bbox[1] + ((baseline - char_bbox[3]) * c.font.em / full_glyph_size))
    c.transform(t)

    # Put horizontal padding around the glyph. I choose a number here that looks reasonable,
    # there are far more sophisticated means of doing this (like looking at the original image,
    # and calculating how much space there should be).
    space = 20
    scaled_width = glyph_bbox[2] - glyph_bbox[0]
    c.width = int(round(scaled_width + 2 * space))
    t = psMat.translate(space, 0)
    c.transform(t)


def charname(char):
    # Give the fontforge name for the given character.
    return fontforge.nameFromUnicode(ord(char))


# ---------------------------------------------------------------------------
# Font creation and base glyph processing
# ---------------------------------------------------------------------------

font = basic_font()
font.ascent = 600

# Pin line metrics so FontForge doesn't recompute them from bounding boxes during generate().
font.os2_typoascent = 855; font.os2_typoascent_add = False
font.os2_typodescent = -270; font.os2_typodescent_add = False
font.os2_typolinegap = 77
font.os2_winascent = 855; font.os2_winascent_add = False
font.os2_windescent = 270; font.os2_windescent_add = False
font.hhea_ascent = 855; font.hhea_ascent_add = False
font.hhea_descent = -270; font.hhea_descent_add = False
font.hhea_linegap = 77

# Per-character size scaling applied after changeWeight, to fine-tune individual glyphs
# that end up slightly too large despite correct stroke weight.
_per_char_size = {
    ('q',): 0.92,
    ('x',): 0.83,
}

# Pick out particular glyphs that are more pleasant than their latter alternatives.
special_choices = {('C', ): dict(line=4),
                   ('G',): dict(line=4),
                   # Get rid of the "as" ligature - it's not very good.
                   ('a', 's'): dict(line=None),
                   # A nice tall I.
                   ('I', ): dict(line=4),
                   }

for line, position, bbox, fname, chars in characters:
    if chars in special_choices:
        spec = special_choices[chars]
        spec_line = spec.get('line', any)
        if spec_line is not any and spec_line != line:
            continue

    c = create_char(font, chars, fname)

    # Get the linestats for this character.
    line_features = line_stats[line]

    scale_glyph(
        c, bbox,
        baseline=np.mean(line_features['baseline']),
        cap_height=np.mean(line_features['cap-height']))

    translate_glyph(
        c, bbox,
        baseline=np.mean(line_features['baseline']),
        cap_height=np.mean(line_features['cap-height']))

    # Correct for lines written at a significantly different scale than the median.
    # - Too large (fgs high): chars scaled down → thin strokes → fatten with changeWeight.
    # - Too small (fgs low): chars scaled up → thick/large glyphs → shrink with scale().
    _line_fgs = _full_glyph_sizes.get(line)
    if _line_fgs:
        if _line_fgs > _median_full_glyph_size * 1.10:
            _scale_correction = _line_fgs / _median_full_glyph_size
            _estimated_stroke = 0.12 * font.ascent
            _delta = int(round(_estimated_stroke * (_scale_correction - 1)))
            c.removeOverlap()
            c.changeWeight(_delta)
        elif _line_fgs < _median_full_glyph_size * 0.90:
            _scale_correction = _line_fgs / _median_full_glyph_size
            _estimated_stroke = 0.12 * font.ascent
            # Scale by 1.4 to compensate for the restore-scale partially undoing the thinning.
            _delta = int(round(_estimated_stroke * (_scale_correction - 1) * 1.4))
            _bb_before = c.boundingBox()
            _h_before = _bb_before[3] - _bb_before[1]
            c.removeOverlap()
            c.changeWeight(_delta)
            _bb_after = c.boundingBox()
            _h_after = _bb_after[3] - _bb_after[1]
            if _h_after > 0:
                _restore = _h_before / _h_after
                c.transform(psMat.scale(_restore))
                c.width = int(round(c.width * _restore))

    # Per-character size adjustments: scale about the baseline (origin) to reduce
    # overall size while preserving stroke weight gained from changeWeight above.
    _size_scale = _per_char_size.get(chars)
    if _size_scale is not None:
        c.transform(psMat.scale(_size_scale))
        c.width = int(round(c.width * _size_scale))

    # Simplify, then put the vertices on rounded coordinate positions.
    c.simplify()
    c.round()

c = font.createMappedChar(32)
c.width = 256


# ---------------------------------------------------------------------------
# Glyphs imported from xkcd comic images
# ---------------------------------------------------------------------------

_COMIC_CHARS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../generated/additional_chars')


def _scan_stroke_width(g, y_lo, y_hi, n=8):
    """Rough stroke-width estimate via horizontal line scanning.

    Samples n evenly-spaced y values in [y_lo, y_hi].  At each y, finds all
    x-crossings of the contour edges (polyline approximation between consecutive
    points) and records the minimum gap between consecutive crossings.  Returns
    the median of those per-y minimums — approximating the typical thinnest
    visible stroke in the scan band.
    """
    results = []
    for k in range(n):
        y = y_lo + (y_hi - y_lo) * (k + 0.5) / n
        xs = []
        for contour in g.foreground:
            pts = list(contour)
            for i in range(len(pts)):
                p1, p2 = pts[i], pts[(i + 1) % len(pts)]
                if (p1.y - y) * (p2.y - y) < 0:
                    t = (y - p1.y) / (p2.y - p1.y)
                    xs.append(p1.x + t * (p2.x - p1.x))
        xs.sort()
        gaps = [xs[j + 1] - xs[j] for j in range(len(xs) - 1)]
        if gaps:
            results.append(min(gaps))
    if not results:
        return None
    results.sort()
    return results[len(results) // 2]


def _import_comic_glyph(font, name, svg_path, target_top, weight_delta=0):
    """Import a pre-cleaned SVG (from pt4_additional_sources.py) and scale it
    so the top of the ink reaches target_top in font units, preserving the
    aspect ratio so any descender falls naturally below baseline.

    weight_delta: if non-zero, apply changeWeight() after scaling.
    """
    g = font.createChar(-1, f'_comic_{name}')
    g.clear()
    g.importOutlines(svg_path)

    bb = g.boundingBox()
    g.transform(psMat.scale(target_top / bb[3]))

    bb = g.boundingBox()
    g.transform(psMat.translate(-bb[0] + 20, 0))

    if weight_delta:
        g.correctDirection()
        g.simplify(0.25)  # tight tolerance: reduce redundant points before overlap resolution
        g.removeOverlap()
        g.changeWeight(weight_delta)

    g.correctDirection()
    # round() before removeOverlap() avoids a FontForge "endpoint intersection"
    # bug that fires when two spline curves meet exactly at a fractional-
    # coordinate point on the sweep line.
    g.round()
    g.removeOverlap()
    g.addExtrema()

    bb = g.boundingBox()
    g.width = int(round(bb[2] + 20))
    return g


# Greek letters vectorised by pt4 from xkcd comic images.
# Each entry: (svg_name, unicode_cp, ref_char_for_height, baseline_snap)
# baseline_snap=True  → translate so bb[1]=0 (letters that sit on the baseline).
# baseline_snap=False → leave at natural import coords; descender positioning
#                        is handled separately via _GREEK_DESCENDER_FRAC.
_GREEK = [
    ('pi',      0x03C0, 'a', True),
    ('Delta',   0x0394, 'A', True),
    ('delta',   0x03B4, 'b', True),
    ('theta',   0x03B8, 'b', True),
    ('phi',     0x03C6, 'a', True),
    ('epsilon', 0x03B5, 'a', True),
    ('upsilon', 0x03C5, 'a', True),
    ('nu',      0x03BD, 'a', True),
    ('mu',      0x03BC, 'a', False),
    ('Sigma',   0x03A3, 'A', True),
    ('Pi',      0x03A0, 'A', True),
    ('zeta',    0x03B6, 'b', False),
    ('beta',    0x03B2, 'b', False),
    ('alpha',   0x03B1, 'a', True),
    ('Omega',   0x03A9, 'A', True),
    ('omega',   0x03C9, 'a', True),
    ('sigma',   0x03C3, 'a', True),
    ('xi',      0x03BE, 'b', False),
    ('gamma',   0x03B3, 'a', False),
    ('rho',     0x03C1, 'a', False),
    ('Xi',      0x039E, 'A', True),
    ('psi',     0x03C8, 'a', False),
    ('lambda',  0x03BB, 'b', True),
    ('tau', 0x03C4, 'a', True),
    ('varsigma', 0x03C2, 'a', True),
]

# Letters with genuine descenders: fraction of the crop height that is the
# body (above baseline).  Remaining fraction becomes the descender below y=0.
# Estimated from pixel proportions in the 2× source image crop.
_GREEK_DESCENDER_FRAC = {
    'mu': 0.61,
    'beta': 0.75,
    'rho': 0.67,
}

# Measure target stroke width from 'l' — a clean vertical stroke with no
# ambiguity from curves or bowls.
_l_bb = font['l'].boundingBox()
_target_stroke = _scan_stroke_width(
    font['l'],
    _l_bb[1] + (_l_bb[3] - _l_bb[1]) * 0.2,
    _l_bb[1] + (_l_bb[3] - _l_bb[1]) * 0.8,
)

# Glyphs dominated by horizontal strokes: the horizontal scan in
# _scan_stroke_width measures bar *lengths* rather than stroke thickness,
# producing a grossly over-estimated value and a large negative delta that
# massively thins the letter.  Skip stroke normalisation for these.
_GREEK_NO_STROKE_NORM = {'epsilon', 'Xi', 'Sigma'}

# Per-letter changeWeight nudge applied after all positioning and stroke
# normalisation.  Positive = thicker, negative = thinner.
_GREEK_WEIGHT_NUDGE = {
    'Sigma':   15,
    'mu':      15,
    'epsilon': 15,
    'psi':    -15,
    'lambda':  10,
}

for _name, _cp, _ref, _snap in _GREEK:
    _svg = os.path.join(_COMIC_CHARS_DIR, f'{_name}.svg')
    _target_top = font[_ref].boundingBox()[3]
    _g = _import_comic_glyph(font, _name, _svg, target_top=_target_top)
    _desc_frac = _GREEK_DESCENDER_FRAC.get(_name)
    if _desc_frac is not None:
        # Seat the body in [0, target_top] and let the descender fall below y=0.
        # baseline_y is the font-unit y that corresponds to the baseline inside
        # the imported glyph.
        _bb = _g.boundingBox()
        _baseline_y = _bb[3] - _desc_frac * (_bb[3] - _bb[1])
        _g.transform(psMat.translate(0, -_baseline_y))
        _bb = _g.boundingBox()
        if _bb[3] > 0:
            _g.transform(psMat.scale(_target_top / _bb[3]))
            _g.width = int(round(_g.boundingBox()[2] + 20))
    elif _snap:
        # Seat the glyph on the baseline: translate so bb[1]=0 then re-scale to
        # restore target_top.  Handles both positive bb[1] (sub-baseline
        # whitespace in the source crop) and negative bb[1] (ink that slightly
        # undercuts the baseline).
        _bb = _g.boundingBox()
        if _bb[1] != 0:
            _g.transform(psMat.translate(0, -_bb[1]))
            _bb = _g.boundingBox()
            if _bb[3] > 0:
                _g.transform(psMat.scale(_target_top / _bb[3]))
                _g.width = int(round(_g.boundingBox()[2] + 20))
    # Normalise stroke width AFTER all positioning so that snap/descender
    # re-scales do not alter the final stroke width.
    if _target_stroke is not None and _name not in _GREEK_NO_STROKE_NORM:
        _measured = _scan_stroke_width(_g, _target_top * 0.15, _target_top * 0.85)
        if _measured and _measured > 0:
            _delta = int(round(_target_stroke - _measured))
            if abs(_delta) > 3:
                _g.correctDirection()
                _g.addExtrema()
                _g.removeOverlap()
                _g.changeWeight(_delta)
                _bb2 = _g.boundingBox()
                if _bb2[3] > 0:
                    _g.transform(psMat.scale(_target_top / _bb2[3]))
                    _bb2 = _g.boundingBox()
                    _g.transform(psMat.translate(-_bb2[0] + 20, 0))
                    _g.width = int(round(_g.boundingBox()[2] + 20))
    # Per-letter weight nudge (applied last so it overrides normalisation).
    _nudge = _GREEK_WEIGHT_NUDGE.get(_name)
    if _nudge:
        _g.correctDirection()
        _g.addExtrema()
        _g.removeOverlap()
        _g.changeWeight(_nudge)
        _bb2 = _g.boundingBox()
        if _bb2[3] > 0:
            _g.transform(psMat.scale(_target_top / _bb2[3]))
            _bb2 = _g.boundingBox()
            _g.transform(psMat.translate(-_bb2[0] + 20, 0))
            _g.width = int(round(_g.boundingBox()[2] + 20))
    _ch = font.createMappedChar(_cp)
    _ch.clear()
    for c in _g.foreground:
        _ch.foreground += c
    _ch.width = _g.width


# ¸ U+00B8 CEDILLA — hand-drawn hook shape from extras/cedilla.png.
_cedilla_svg = os.path.join(_COMIC_CHARS_DIR, 'cedilla.svg')
_cedilla_src = _import_comic_glyph(font, 'cedilla', _cedilla_svg,
                                   target_top=font['comma'].boundingBox()[3])
_ch = font.createMappedChar(0x00B8)
_ch.clear()
for c in _cedilla_src.foreground:
    _ch.foreground += c
_ch.width = _cedilla_src.width


# ß (U+00DF) and ẞ (U+1E9E) — hand-drawn source from extras/eszett.png.
# The same SVG is imported twice at different scales for the two case forms.
_eszett_svg = os.path.join(_COMIC_CHARS_DIR, 'eszett.svg')

_eszett_glyph = _import_comic_glyph(
    font, 'eszett', _eszett_svg,
    target_top=font['b'].boundingBox()[3] * 0.59,
    weight_delta=23)
_bb = _eszett_glyph.boundingBox()
if _bb[1] < 0:
    _eszett_glyph.transform(psMat.translate(0, -_bb[1]))
_ch = font.createMappedChar(0x00DF)
_ch.clear()
for c in _eszett_glyph.foreground:
    _ch.foreground += c
_ch.width = _eszett_glyph.width

_cap_eszett_glyph = _import_comic_glyph(
    font, 'eszett_cap', _eszett_svg,
    target_top=font['B'].boundingBox()[3] * 0.72,
    weight_delta=19)
_bb = _cap_eszett_glyph.boundingBox()
if _bb[1] < 0:
    _cap_eszett_glyph.transform(psMat.translate(0, -_bb[1]))
_ch = font.createMappedChar(0x1E9E)
_ch.clear()
for c in _cap_eszett_glyph.foreground:
    _ch.foreground += c
_ch.width = _cap_eszett_glyph.width


# Æ/æ/Œ/œ — hand-drawn sources from ai_extensions_1.png.
# Œ is capital height; æ and œ are x-height.
for _name, _cp, _ref in [
    ('AElig', 0x00C6, 'A'),  # Æ — capital
    ('OElig', 0x0152, 'O'),  # Œ — capital
    ('aelig', 0x00E6, 'a'),  # æ — lowercase
    ('oelig', 0x0153, 'o'),  # œ — lowercase
]:
    _svg = os.path.join(_COMIC_CHARS_DIR, f'{_name}.svg')
    _target_top = font[_ref].boundingBox()[3]
    _g = _import_comic_glyph(font, _name, _svg, target_top=_target_top, weight_delta=20)
    _bb = _g.boundingBox()
    if _bb[1] != 0:
        _g.transform(psMat.translate(0, -_bb[1]))
        _bb = _g.boundingBox()
        if _bb[3] > 0:
            _g.transform(psMat.scale(_target_top / _bb[3]))
            _g.width = int(round(_g.boundingBox()[2] + 20))
    _ch = font.createMappedChar(_cp)
    _ch.clear()
    for c in _g.foreground:
        _ch.foreground += c
    _ch.width = _g.width


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

font_fname = '../generated/xkcd-script-pt5.sfd'

if not os.path.exists(os.path.dirname(font_fname)):
    os.makedirs(os.path.dirname(font_fname))
if os.path.exists(font_fname):
    os.remove(font_fname)
font.save(font_fname)
