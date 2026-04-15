# -*- coding: utf-8 -*-
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


def _base_char(c):
    """Return the base letter for an accented character (e.g. É → E)."""
    decomp = unicodedata.decomposition(c)
    if decomp and not decomp.startswith('<'):
        return chr(int(decomp.split()[0], 16))
    return c


def _expand_with_variants(font, chars):
    """Expand a list of base chars/glyph-names to include accented variants in the font.

    Multi-character glyph names (ligatures) are passed through unchanged — only
    single-character entries are eligible for variant expansion.
    """
    single_chars = set(c for c in chars if len(c) == 1)
    # Convert single chars to FontForge glyph names (e.g. '/' → 'slash').
    result = [fontforge.nameFromUnicode(ord(c)) if len(c) == 1 else c for c in chars]
    seen = set(result)
    for glyph in font.glyphs():
        if glyph.unicode < 0:
            continue
        c = chr(glyph.unicode)
        if _base_char(c) in single_chars and c not in single_chars:
            name = glyph.glyphname
            if name not in seen:
                result.append(name)
                seen.add(name)
    return result


def autokern(font):
    all_glyphs = [glyph.glyphname for glyph in font.glyphs()
                  if not glyph.glyphname.startswith(' ')]
    ligatures = [name for name in all_glyphs if '_' in name]
    upper_ligatures = [ligature for ligature in ligatures if ligature.upper() == ligature]
    lower_ligatures = [ligature for ligature in ligatures if ligature.lower() == ligature]

    # Expand the broad letter lists to include accented variants from the outset,
    # so every rule that references `caps`, `lower`, or `all_chars` covers them too.
    caps = _expand_with_variants(font, list('ABCDEFGHIJKLMNOPQRSTUVWXYZ') + upper_ligatures)
    lower = _expand_with_variants(font, list('abcdefghijklmnopqrstuvwxyz') + lower_ligatures)
    all_chars = caps + lower

    font.addLookup('kerning', 'gpos_pair', (), [['kern', [['latn', ['dflt']]]]])
    font.addLookupSubtable('kerning', 'kern')

    def kern(sep, left, right, **kwargs):
        """Wraps font.autoKern: expands accented variants and leading/trailing ligatures."""
        def expand(chars, left_side):
            expanded = _expand_with_variants(font, chars)
            seen = set(expanded)
            for glyph in font.glyphs():
                name = glyph.glyphname
                if '_' not in name:
                    continue
                parts = name.split('_')
                # Left side: ligature's right edge (last component) determines spacing.
                # Right side: ligature's left edge (first component) determines spacing.
                anchor = parts[-1] if left_side else parts[0]
                if anchor in seen and name not in seen:
                    expanded.append(name)
                    seen.add(name)
            return expanded
        font.autoKern('kern', sep, expand(left, left_side=True), expand(right, left_side=False), **kwargs)

    kern(150, ['/', '\\'], ['/', '\\'])

    kern(175, ['r'], ['i'], minKern=35)
    kern(180, ['r'], ['g', 'x'], minKern=35)
    kern(100, ['r'], lower, minKern=50)
    kern(60, ['s'], lower, minKern=50)
    # f has a long right-arm; kern slightly tighter than default but don't overdo it.
    kern(75, ['f'], lower, minKern=40)
    # g has a round left side; nudge preceding glyphs in a little.
    # Letters with open/diagonal right sides need a looser target before g.
    kern(115, list('EKLPRYkz'), ['g'], minKern=30)
    kern(75, lower, ['g'], minKern=30)
    kern(75, caps, ['g'], minKern=30)
    # x has diagonal strokes that leave visual space on its left side.
    kern(90, lower, ['x'], minKern=40)
    # H has tall verticals that sit naturally close to j's descender.
    kern(150, ['H'], ['j'], minKern=35)
    # Raise separation so Jj doesn't get pulled too close.
    kern(220, all_chars, ['j'], minKern=35)
    # F/E are separated from T/J so they can use a tighter target gap.
    kern(130, ['F'], all_chars)
    kern(140, ['E'], ['V', 'W', 'Y'])
    kern(100, ['E'], all_chars)
    kern(120, ['T', 'J'], ['R'])
    kern(150, ['T', 'J'], all_chars)
    # C: loosen from the default (was too tight for Ct/Cf/Cj).
    kern(65, ['C'], all_chars)
    kern(60, ['O'], all_chars)


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

# Special case - add a vertial pipe by re-using an I, and stretching it a bit.
for line, position, bbox, fname, chars in characters:
    if chars == (u'I',) and line == 4:
        characters.append([4, None, bbox, fname, ('|',)])

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

# Add reference glyphs for quote-like characters that share the same visual shape.
ref_aliases = [
    (0x0060, 'quoteleft'),    # grave/backtick
    (0x00B4, 'quoteright'),   # acute accent
    (0x201B, 'quoteleft'),    # quotereversed
    (0x201F, 'quotedblleft'), # quotedblreversed
    (0x2032, 'quoteright'),   # prime
    (0x2033, 'quotedbl'),     # doubleprime
    (0x2035, 'quoteleft'),    # backprime
]
for codepoint, source_name in ref_aliases:
    c = font.createMappedChar(codepoint)
    c.addReference(source_name)
    c.width = font[source_name].width

# --- Combining diacritics and Czech accented characters ---

# Build weight-corrected mark glyphs for acute and caron.
# Scaling thins strokes; changeWeight restores them to match the font's pen weight.
_mark_scale = 0.65
_stroke = int(round(0.12 * font.ascent))
_weight_delta = 0

def _make_weighted_mark(font, src_name, scale, weight_delta, mark_glyph_name, flip_y=False):
    """
    Standalone mark glyph: outlines copied from src_name, scaled, centered at x=0,
    then weight-corrected so strokes match the rest of the font.
    flip_y=True mirrors vertically (e.g. ^ → ˇ for the caron).
    """
    src = font[src_name]
    src_bb = src.boundingBox()
    src_cx = (src_bb[0] + src_bb[2]) / 2
    mark = font.createChar(-1, mark_glyph_name)
    mark.clear()
    _layer = fontforge.layer()
    for _c in src.foreground:
        _layer += _c
    mark.foreground = _layer
    sy = -scale if flip_y else scale
    mark.transform(psMat.compose(psMat.scale(scale, sy), psMat.translate(-src_cx * scale, 0)))
    mark.width = 0
    mark.correctDirection()  # flip reverses winding order; restore before changeWeight
    mark.removeOverlap()
    if weight_delta:
        mark.changeWeight(weight_delta)
    mark.simplify()
    return mark

_acute_mark = _make_weighted_mark(font, 'quoteright', _mark_scale, _weight_delta, '_acute_mark')
_caron_mark = _make_weighted_mark(font, 'asciicircum', _mark_scale, _weight_delta, '_caron_mark', flip_y=True)

# Register as combining diacritics at their Unicode codepoints.
for _cp, _mark in [(0x0301, _acute_mark), (0x030C, _caron_mark)]:
    _c = font.createMappedChar(_cp)
    _c.addReference(_mark.glyphname)
    _c.width = 0

# Combining ring above (U+030A): extract ring contours from Å.
# Å is a single drawn glyph; the ring sits above y=580, clear of the A body.
# The ring keeps its original stroke weight — it was drawn with the same pen.
_ring_xs = []
_ring_indices = []
for _i, _contour in enumerate(font['Aring'].foreground):
    if min(p.y for p in _contour) > 580:
        _ring_indices.append(_i)
        _ring_xs.extend(p.x for p in _contour)
_ring_cx = (min(_ring_xs) + max(_ring_xs)) / 2

_ring_glyph = font.createMappedChar(0x030A)
_ring_layer = fontforge.layer()
for _i, _contour in enumerate(font['Aring'].foreground):
    if _i in _ring_indices:
        _ring_layer += _contour
_ring_glyph.foreground = _ring_layer
_ring_glyph.transform(psMat.translate(-_ring_cx, 0))
_ring_glyph.width = 0
_ring_name = _ring_glyph.glyphname

# dotlessi (U+0131): i without the dot, so í etc. don't stack dot + acute.
# The dot is the topmost contour of i (highest ymin); all others form the stem.
_i_layer = font['i'].foreground
_dot_ymin = max(min(p.y for p in _c) for _c in _i_layer)
_dotless_layer = fontforge.layer()
for _contour in _i_layer:
    if min(p.y for p in _contour) < _dot_ymin:
        _dotless_layer += _contour
_dotlessi_glyph = font.createMappedChar(0x0131)
_dotlessi_glyph.foreground = _dotless_layer
_dotlessi_glyph.width = font['i'].width

def _place_above(font, base_name, mark_name, gap=20, x_adj=0):
    """Compute translation to place a pre-sized mark centered above base by bounding box."""
    base_bb = font[base_name].boundingBox()
    mark_bb = font[mark_name].boundingBox()
    base_cx = (base_bb[0] + base_bb[2]) / 2
    mark_cx = (mark_bb[0] + mark_bb[2]) / 2
    dx = base_cx - mark_cx + x_adj
    dy = base_bb[3] + gap - mark_bb[1]
    return psMat.translate(dx, dy)

def _make_accented(font, cp, base_name, mark_name, gap=20, x_adj=0):
    """Accented glyph: base reference + pre-sized mark placed above by bounding-box centering."""
    c = font.createMappedChar(cp)
    c.clear()
    c.addReference(base_name)
    c.width = font[base_name].width
    c.addReference(mark_name, _place_above(font, base_name, mark_name, gap, x_adj))
    return c

def _make_dstroke(font, cp, base_name, gap=5):
    """Czech ď/ť form: base + quoteright at natural size to the upper right (not caron above)."""
    c = font.createMappedChar(cp)
    c.clear()
    c.addReference(base_name)
    base_width = font[base_name].width
    base_bb = font[base_name].boundingBox()
    apos_bb = font['quoteright'].boundingBox()
    dx = base_width + gap - apos_bb[0]
    dy = base_bb[3] - apos_bb[3]
    c.addReference('quoteright', psMat.translate(dx, dy))
    c.width = int(round(base_width + gap + (apos_bb[2] - apos_bb[0]) + 15))
    return c

# Acute: Á É Í Ó Ú Ý / á é í ó ú ý  (í uses dotlessi to avoid dot+acute stack)
# É is regenerated for consistency — the hand-drawn original has a different stroke length.
for _cp, _base in [
    (0x00C1, 'A'), (0x00C9, 'E'), (0x00CD, 'I'), (0x00D3, 'O'), (0x00DA, 'U'), (0x00DD, 'Y'),
    (0x00E1, 'a'), (0x00E9, 'e'), (0x00ED, 'dotlessi'), (0x00F3, 'o'), (0x00FA, 'u'), (0x00FD, 'y'),
]:
    _make_accented(font, _cp, _base, _acute_mark.glyphname)

# Caron: Č Ě Ň Ř Š Ž / č ě ň ř š ž  (ď/ť handled separately below)
for _cp, _base in [
    (0x010C, 'C'), (0x011A, 'E'), (0x0147, 'N'), (0x0158, 'R'), (0x0160, 'S'), (0x017D, 'Z'),
    (0x010D, 'c'), (0x011B, 'e'), (0x0148, 'n'), (0x0159, 'r'), (0x0161, 's'), (0x017E, 'z'),
]:
    _make_accented(font, _cp, _base, _caron_mark.glyphname)

# Ring above: Ů / ů  (ring weight matches Å — drawn with the same pen)
for _cp, _base in [(0x016E, 'U'), (0x016F, 'u')]:
    _make_accented(font, _cp, _base, _ring_name)

# Ď Ť (uppercase): caron above, like other uppercase caron letters
for _cp, _base in [(0x010E, 'D'), (0x0164, 'T')]:
    _make_accented(font, _cp, _base, _caron_mark.glyphname)

# ď ť (lowercase): raised apostrophe to the right — tall descenders leave no room above
for _cp, _base in [(0x010F, 'd'), (0x0165, 't')]:
    _make_dstroke(font, _cp, _base)

autokern(font)

font_fname = '../font/xkcd-script.sfd'

if not os.path.exists(os.path.dirname(font_fname)):
    os.makedirs(os.path.dirname(font_fname))
if os.path.exists(font_fname):
    os.remove(font_fname)
font.save(font_fname)

