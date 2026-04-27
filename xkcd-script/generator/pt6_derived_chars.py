# -*- coding: utf-8 -*-
"""
Generate derived/composed characters: quote aliases, combining diacritical marks,
accented Latin letters, and Greek aliases and derived glyphs.

Reads the base SFD produced by pt5_svg_to_font.py, adds derived glyphs, saves.
"""
import math
import fontforge
import psMat

font_fname = '../generated/xkcd-script-pt6.sfd'
font = fontforge.open('../generated/xkcd-script-pt5.sfd')


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def extract_top_contours(font, source_cp, n):
    """Return the n topmost contours (by ymin) from a glyph.

    Used to pull hand-drawn marks from composite glyphs (e.g. dots from Ü,
    ring from Å, macron stroke from Ē, acute strokes from Ő).
    source_cp may be an integer codepoint or a glyph name string.
    """
    layer = font[source_cp].foreground
    contours = sorted(layer, key=lambda c: min(p.y for p in c), reverse=True)
    ymins = [min(p.y for p in c) for c in contours]
    thresh = (ymins[n - 1] + ymins[n]) / 2
    return [c for c in contours if min(p.y for p in c) > thresh]


def make_mark(font, name, contours):
    """Create a zero-width mark glyph from contours, centered at x=0."""
    glyph = font.createChar(-1, name)
    glyph.clear()
    layer = fontforge.layer()
    for c in contours:
        layer += c
    glyph.foreground = layer
    bb = glyph.boundingBox()
    glyph.transform(psMat.translate(-((bb[0] + bb[2]) / 2), 0))
    glyph.width = 0
    return glyph


def make_mark_flipped_x(font, name, source_mark_name):
    """Zero-width mark: horizontal mirror of an existing centered mark."""
    glyph = font.createChar(-1, name)
    glyph.clear()
    layer = fontforge.layer()
    for c in font[source_mark_name].foreground:
        layer += c
    glyph.foreground = layer
    glyph.transform(psMat.scale(-1, 1))
    glyph.width = 0
    return glyph


def _make_weighted_mark(font, src_name, scale, weight_delta, mark_glyph_name, flip_y=False):
    """Standalone mark glyph: outlines copied from src_name, scaled, centered at x=0.

    flip_y=True mirrors vertically (e.g. ^ → ˇ for the caron).
    weight_delta adjusts stroke weight after scaling (0 = no adjustment).
    """
    src = font[src_name]
    src_bb = src.boundingBox()
    src_cx = (src_bb[0] + src_bb[2]) / 2
    mark = font.createChar(-1, mark_glyph_name)
    mark.clear()
    layer = fontforge.layer()
    for c in src.foreground:
        layer += c
    mark.foreground = layer
    sy = -scale if flip_y else scale
    mark.transform(psMat.compose(psMat.scale(scale, sy), psMat.translate(-src_cx * scale, 0)))
    if flip_y:
        # Vertical flip negates y, putting the mark below the baseline.
        # Translate back to the original y range so combining characters render above the base.
        mark.transform(psMat.translate(0, scale * (src_bb[1] + src_bb[3])))
    mark.width = 0
    mark.correctDirection()  # flip reverses winding order; restore before changeWeight
    mark.removeOverlap()
    if weight_delta:
        mark.changeWeight(weight_delta)
    mark.simplify()
    return mark


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


def _make_dstroke(font, cp, base_name, gap=5, dy_offset=0, width_extra=0):
    """Czech ď/ť form: base + quoteright at natural size to the upper right (not caron above).

    The apostrophe overhangs the advance width (like italic f in many fonts); the
    advance width is kept close to the base glyph so following letters sit naturally.
    dy_offset shifts the apostrophe vertically (positive = up).
    width_extra adds to the advance width for narrow bases like l/L.
    """
    c = font.createMappedChar(cp)
    c.clear()
    c.addReference(base_name)
    base_width = font[base_name].width
    base_bb = font[base_name].boundingBox()
    apos_bb = font['quoteright'].boundingBox()
    dx = base_width + gap - apos_bb[0]
    dy = base_bb[3] - apos_bb[3] + dy_offset
    c.addReference('quoteright', psMat.translate(dx, dy))
    c.width = base_width + 20 + width_extra
    return c


def _place_below(font, base_name, mark_name, y_adj=10, x_adj=0):
    """Compute translation to place mark below base.

    y_adj: positive = more space (mark lower), negative = closer/overlapping.
    x_adj: positive shifts mark right, negative shifts left.
    """
    base_bb = font[base_name].boundingBox()
    mark_bb = font[mark_name].boundingBox()
    base_cx = (base_bb[0] + base_bb[2]) / 2
    mark_cx = (mark_bb[0] + mark_bb[2]) / 2
    dx = base_cx - mark_cx + x_adj
    dy = base_bb[1] - y_adj - mark_bb[3]
    return psMat.translate(dx, dy)


def _make_cedilla(font, cp, base_name, y_adj=8, mark='comma', x_adj=0):
    if cp in _SKIP_CPS:
        return
    c = font.createMappedChar(cp)
    c.clear()
    c.width = font[base_name].width
    c.addReference(base_name)
    c.addReference(mark, _place_below(font, base_name, mark, y_adj, x_adj))


def _make_macron_below(font, cp, base_name, y_adj=15):
    if cp in _SKIP_CPS:
        return
    c = font.createMappedChar(cp)
    c.clear()
    c.addReference(base_name)
    c.width = font[base_name].width
    c.addReference('_macron_below_mark', _place_below(font, base_name, '_macron_below_mark', y_adj))


def _make_dot_below(font, cp, base_name, y_adj=15):
    if cp in _SKIP_CPS:
        return
    c = font.createMappedChar(cp)
    c.clear()
    c.addReference(base_name)
    c.width = font[base_name].width
    c.addReference('_dot_below_mark', _place_below(font, base_name, '_dot_below_mark', y_adj))


def _make_ogonek(font, cp, base_name):
    if cp in _SKIP_CPS:
        return
    c = font.createMappedChar(cp)
    c.clear()
    c.addReference(base_name)
    c.width = font[base_name].width
    comma_bb = font['comma'].boundingBox()
    base_bb = font[base_name].boundingBox()
    # Rotate comma 180° and position so the tail tip sits at the baseline (y=0)
    # and the right edge of the rotated shape attaches at the base ink right edge.
    # After scale(-1,-1): original left edge → right side, original bottom → top.
    # dx: -comma_bb[0] + dx = base_bb[2]  →  dx = base_bb[2] + comma_bb[0]
    # dy: -comma_bb[1] + dy = 0           →  dy = comma_bb[1]
    # +80 shifts the whole ogonek up so it overlaps the base letter bottom.
    dx = base_bb[2] + comma_bb[0]
    dy = comma_bb[1] + 80
    c.addReference('comma', psMat.compose(psMat.scale(-1, -1), psMat.translate(dx, dy)))


# Codepoints that already exist as hand-drawn glyphs; skip to avoid overwriting.
_SKIP_CPS = frozenset({
    0x00DC,  # Ü — hand-drawn
    0x0150,  # Ő — hand-drawn
    0x0112,  # Ē — hand-drawn
})


def _accented(cp, base_name, mark_name, gap=20, x_adj=0):
    if cp not in _SKIP_CPS:
        _make_accented(font, cp, base_name, mark_name, gap, x_adj)


# ---------------------------------------------------------------------------
# Glyph aliases and re-uses
# ---------------------------------------------------------------------------

# Vertical pipe: re-use the I glyph (same stroke, same weight).
pipe = font.createMappedChar(ord('|'))
pipe.clear()
pipe.addReference('I')
pipe.width = font['I'].width



ref_aliases = [
    (0x0060, 'quoteleft'),    # grave/backtick
    (0x00B4, 'quoteright'),   # acute accent
    (0x201B, 'quoteleft'),    # quotereversed
    (0x201F, 'quotedblleft'), # quotedblreversed
    (0x2032, 'quoteright'),   # prime
    (0x2033, 'quotedbl'),     # doubleprime
    (0x2035, 'quoteleft'),    # backprime
    # Dash aliases
    (0x2011, 'hyphen'),       # non-breaking hyphen
    (0x00AD, 'hyphen'),       # soft hyphen
    (0x2212, 'endash'),       # minus sign
    (0x2012, 'endash'),       # figure dash
    (0x2015, 'emdash'),       # horizontal bar
]
for codepoint, source_name in ref_aliases:
    c = font.createMappedChar(codepoint)
    c.addReference(source_name)
    c.width = font[source_name].width


# ---------------------------------------------------------------------------
# Combining mark glyphs
# ---------------------------------------------------------------------------

# --- Marks sourced from hand-drawn glyphs (correct pen weight by construction) ---

# Acute: rightmost of the two strokes in Ő.
_acute_mark = make_mark(font, '_acute_mark',
    sorted(extract_top_contours(font, 0x0150, 2),
           key=lambda c: sum(p.x for p in c) / len(c), reverse=True)[:1])

# Grave: horizontal mirror of the acute.
_grave_mark = make_mark_flipped_x(font, '_grave_mark', '_acute_mark')

# Ring above: both ring contours (inner + outer circle) from Å.
_ring_mark = make_mark(font, '_ring_above_mark', extract_top_contours(font, 0x00C5, 2))

# Diaeresis: both dots from Ü.
_diaeresis_mark = make_mark(font, '_diaeresis_mark', extract_top_contours(font, 0x00DC, 2))

# Single dot above: one dot from Ü.
_dot_above_mark = make_mark(font, '_dot_above_mark', extract_top_contours(font, 0x00DC, 2)[:1])

# Single dot below: same dot shape, used for Vietnamese dot-below characters.
_dot_below_mark = make_mark(font, '_dot_below_mark', extract_top_contours(font, 0x00DC, 2)[:1])

# Macron below: same stroke as the macron above, used for Semitic transliteration.
_macron_below_mark = make_mark(font, '_macron_below_mark', extract_top_contours(font, 0x0112, 1))
_macron_below_mark.changeWeight(20)


# Hook cedilla: hand-drawn mark from the 2034 equations comic (extras/cedilla).
# Used for French/Turkish/Cameroonian characters (ç ş ţ); the comma-based cedilla
# is kept for Latvian (ģ ķ ļ ņ ŗ) where that shape is traditional.
_hook_cedilla_mark = make_mark(font, '_hook_cedilla_mark',
                               list(font['cedilla'].foreground))
_hook_cedilla_mark.changeWeight(30)
_hook_cedilla_mark.correctDirection()
_hook_cedilla_mark.removeOverlap()
_hook_cedilla_mark.transform(psMat.scale(1.2))

# Macron: topmost stroke from Ē, with weight correction.
_macron_mark = make_mark(font, '_macron_mark', extract_top_contours(font, 0x0112, 1))
_macron_mark.changeWeight(20)

# --- Marks sourced from ASCII glyphs (scaled + weight-corrected) ---

_mark_scale = 0.65

# Caron: asciicircum flipped vertically (^ → ˇ).
_caron_mark = _make_weighted_mark(font, 'asciicircum', _mark_scale, 35, '_caron_mark', flip_y=True)

# Circumflex: asciicircum unflipped.
_circumflex_mark = _make_weighted_mark(font, 'asciicircum', _mark_scale, 35, '_circumflex_mark')

# Tilde.
_tilde_mark = _make_weighted_mark(font, 'asciitilde', _mark_scale, 35, '_tilde_mark')

# Breve: parenleft rotated 90° CCW — the arc gives the right bowl shape for ˘.
_breve_mark = _make_weighted_mark(font, 'parenleft', _mark_scale, 35, '_breve_mark')
_breve_mark.transform(psMat.rotate(math.radians(90)))
_bb = _breve_mark.boundingBox()
_breve_mark.transform(psMat.translate(-(_bb[0] + _bb[2]) / 2, 0))
_breve_mark.transform(psMat.scale(0.5, 1))
_breve_mark.transform(psMat.translate(-220, 0))

# --- Marks composed from existing mark glyphs ---

# dotlessi (U+0131): i without the dot, so í etc. don't stack dot + acute.
_i_layer = font['i'].foreground
_dot_ymin = max(min(p.y for p in c) for c in _i_layer)
_dotlessi_glyph = font.createMappedChar(0x0131)
_dotless_layer = fontforge.layer()
for c in _i_layer:
    if min(p.y for p in c) < _dot_ymin:
        _dotless_layer += c
_dotlessi_glyph.foreground = _dotless_layer
_dotlessi_glyph.width = font['i'].width

# dotlessj (U+0237): j without the dot, for ĵ ǰ etc. to avoid dot + accent stack.
_j_layer = font['j'].foreground
_j_dot_ymin = max(min(p.y for p in c) for c in _j_layer)
_dotlessj_glyph = font.createMappedChar(0x0237)
_dotlessj_layer = fontforge.layer()
for c in _j_layer:
    if min(p.y for p in c) < _j_dot_ymin:
        _dotlessj_layer += c
_dotlessj_glyph.foreground = _dotlessj_layer
_dotlessj_glyph.width = font['j'].width

# Marks above j/dotlessj should be centered over the dot position, not the body centre.
# The body centre is at (bb[0]+bb[2])/2; the dot was further right.
_j_dot_xs = [p.x for c in _j_layer for p in c if min(p.y for p in c) >= _j_dot_ymin]
_j_dot_cx = (min(_j_dot_xs) + max(_j_dot_xs)) / 2
_j_body_bb = _dotlessj_glyph.boundingBox()
_j_body_cx = (_j_body_bb[0] + _j_body_bb[2]) / 2
_j_x_adj = int(round(_j_dot_cx - _j_body_cx))

# longs (U+017F LATIN SMALL LETTER LONG S): dotless j rotated ~175° and placed
# on the baseline.  The descender curve of j becomes the top hook of long s.
_longs_glyph = font.createMappedChar(0x017F)
_longs_glyph.foreground = _dotlessj_glyph.foreground.dup()
_longs_glyph.transform(psMat.rotate(math.radians(175)))
_longs_glyph.addExtrema('only_good_rm')
_, _longs_ymin, _, _ = _longs_glyph.boundingBox()
_longs_glyph.transform(psMat.translate(0, -_longs_ymin))
_longs_glyph.left_side_bearing = 20
_longs_glyph.right_side_bearing = 40

# Double acute: two acute-mark references shifted apart.
_double_acute_mark = font.createChar(-1, '_double_acute_mark')
_double_acute_mark.clear()
_abb = _acute_mark.boundingBox()
_half = (_abb[2] - _abb[0]) / 2 * 1.2
_double_acute_mark.addReference('_acute_mark', psMat.translate(-_half, 0))
_double_acute_mark.addReference('_acute_mark', psMat.translate(_half, 0))
_double_acute_mark.width = 0

# ---------------------------------------------------------------------------
# Register combining Unicode codepoints
# ---------------------------------------------------------------------------

# Position each combining mark so its bottom sits just above the ascender.
# Without GPOS anchors the renderer places marks at their native coordinates,
# so we translate here to ensure they appear above even tall letters like l/L/b/h.
# (Pre-composed glyphs are unaffected — _place_above computes its own dy.)
_ascender_top = font['l'].boundingBox()[3]
_combining_gap = 20

for cp, mark in [
    (0x0300, _grave_mark),
    (0x0301, _acute_mark),
    (0x0302, _circumflex_mark),
    (0x0303, _tilde_mark),
    (0x0304, _macron_mark),
    (0x0307, _dot_above_mark),
    (0x0308, _diaeresis_mark),
    (0x030A, _ring_mark),
    (0x030B, _double_acute_mark),
    (0x030C, _caron_mark),
    (0x0306, _breve_mark),   # ̆  combining breve
]:
    c = font.createMappedChar(cp)
    c.clear()
    mark_bb = font[mark.glyphname].boundingBox()
    dy = _ascender_top + _combining_gap - mark_bb[1]
    c.addReference(mark.glyphname, psMat.translate(0, dy))
    c.width = 0

# Below combining marks share the macron-below shape at different vertical positions.
_descender_bottom = font['p'].boundingBox()[1]
_mb_bb = font['_macron_below_mark'].boundingBox()

# U+0331 ◌̱  COMBINING MACRON BELOW — below the descender.
_c0331 = font.createMappedChar(0x0331)
_c0331.clear()
_c0331.addReference('_macron_below_mark', psMat.translate(0, _descender_bottom - _combining_gap - _mb_bb[3]))
_c0331.width = 0

# U+0332 ◌̲  COMBINING LOW LINE — just below the baseline (underline position).
_c0332 = font.createMappedChar(0x0332)
_c0332.clear()
_c0332.addReference('_macron_below_mark', psMat.translate(0, -_combining_gap - _mb_bb[3]))
_c0332.width = 0

# U+0320 ◌̠  COMBINING MINUS SIGN BELOW — halfway between baseline and descender.
_c0320 = font.createMappedChar(0x0320)
_c0320.clear()
_c0320.addReference('_macron_below_mark', psMat.translate(0, _descender_bottom // 2 - _combining_gap - _mb_bb[3]))
_c0320.width = 0


# ---------------------------------------------------------------------------
# Accented character tables
# ---------------------------------------------------------------------------

# Acute: Á É Í Ó Ú Ý / á é í ó ú ý  (í uses dotlessi to avoid dot+acute stack)
# É is regenerated for consistency — the hand-drawn original has a different stroke length.
for cp, base in [
    (0x00C1, 'A'), (0x00C9, 'E'), (0x00CD, 'I'), (0x00D3, 'O'), (0x00DA, 'U'), (0x00DD, 'Y'),
    (0x00E1, 'a'), (0x00E9, 'e'), (0x00ED, 'dotlessi'), (0x00F3, 'o'), (0x00FA, 'u'), (0x00FD, 'y'),
    (0x0106, 'C'), (0x0107, 'c'),   # Ć ć  Polish/Croatian
    (0x0139, 'L'), (0x013A, 'l'),   # Ĺ ĺ  Slovak
    (0x0143, 'N'), (0x0144, 'n'),   # Ń ń  Polish
    (0x0154, 'R'), (0x0155, 'r'),   # Ŕ ŕ  Slovak
    (0x015A, 'S'), (0x015B, 's'),   # Ś ś  Polish
    (0x0179, 'Z'), (0x017A, 'z'),   # Ź ź  Polish
    (0x1E82, 'W'), (0x1E83, 'w'),   # Ẃ ẃ  Welsh
]:
    _make_accented(font, cp, base, '_acute_mark')

# Caron: uppercase consonants + vowels (gap=20); U slightly tighter (gap=15).
for cp, base in [
    (0x010C, 'C'), (0x011A, 'E'), (0x01CF, 'I'), (0x0147, 'N'), (0x0158, 'R'), (0x0160, 'S'), (0x017D, 'Z'),
    (0x01CD, 'A'), (0x01D1, 'O'),
]:
    _make_accented(font, cp, base, '_caron_mark')
_make_accented(font, 0x01D3, 'U', '_caron_mark', gap=15)

# Caron: lowercase consonants + vowels (gap=8 — lowercase sits lower than caps).
# ǐ keeps gap=40 since dotlessi is short.
for cp, base in [
    (0x010D, 'c'), (0x011B, 'e'), (0x0148, 'n'), (0x0159, 'r'), (0x0161, 's'), (0x017E, 'z'),
    (0x01CE, 'a'), (0x01D2, 'o'), (0x01D4, 'u'),
]:
    _make_accented(font, cp, base, '_caron_mark', gap=8)
_make_accented(font, 0x01D0, 'dotlessi', '_caron_mark', gap=40)
_make_accented(font, 0x01F0, 'uni0237', '_caron_mark', gap=40, x_adj=_j_x_adj)  # ǰ — dotless to avoid dot+caron stack

# Ring above: å Ů / ů
for cp, base in [(0x00E5, 'a'), (0x016E, 'U'), (0x016F, 'u')]:
    _make_accented(font, cp, base, '_ring_above_mark')

# Breve: Ă Ĕ Ğ Ĭ Ŏ Ŭ / ă ĕ ğ ĭ ŏ ŭ  (Romanian, Turkish, Belarusian, Esperanto, transliteration)
for cp, base in [
    (0x0102, 'A'), (0x0114, 'E'), (0x011E, 'G'), (0x012C, 'I'), (0x014E, 'O'), (0x016C, 'U'),
]:
    _make_accented(font, cp, base, '_breve_mark', gap=20)
for cp, base in [
    (0x0103, 'a'), (0x0115, 'e'), (0x011F, 'g'), (0x014F, 'o'), (0x016D, 'u'),
]:
    _make_accented(font, cp, base, '_breve_mark', gap=8)
_make_accented(font, 0x012D, 'dotlessi', '_breve_mark', gap=40)  # ĭ — dotless to avoid dot+breve stack

# Ď Ť (uppercase): caron above, like other uppercase caron letters.
for cp, base in [(0x010E, 'D'), (0x0164, 'T')]:
    _make_accented(font, cp, base, '_caron_mark')

# ď ť ľ (lowercase) / Ľ (uppercase): raised apostrophe to the right.
_make_dstroke(font, 0x010F, 'd', gap=-30)
_make_dstroke(font, 0x0165, 't', gap=-50)
_make_dstroke(font, 0x013E, 'l', gap=-50, width_extra=80)
_make_dstroke(font, 0x013D, 'L', gap=-50, dy_offset=100, width_extra=80)

# ---------------------------------------------------------------------------
# L with stroke: Ł U+0141 / ł U+0142
# ---------------------------------------------------------------------------

def _make_l_crossbar_mark(font, name, bar_width, rotation=0):
    """Scaled hyphen stroke centered at origin (x=0, y=0), zero-width mark.

    rotation: counter-clockwise angle in degrees.
    """
    hyp_bb = font['hyphen'].boundingBox()
    hyp_cx = (hyp_bb[0] + hyp_bb[2]) / 2
    hyp_cy = (hyp_bb[1] + hyp_bb[3]) / 2
    sx = bar_width / (hyp_bb[2] - hyp_bb[0])
    mark = font.createChar(-1, name)
    mark.clear()
    layer = fontforge.layer()
    for c in font['hyphen'].foreground:
        layer += c
    mark.foreground = layer
    mark.transform(psMat.compose(
        psMat.scale(sx, 1.0),
        psMat.translate(-hyp_cx * sx, -hyp_cy),
    ))
    if rotation:
        mark.transform(psMat.rotate(math.radians(rotation)))
        # Re-centre after rotation: the bounding box shifts if the source shape is asymmetric.
        bb = mark.boundingBox()
        mark.transform(psMat.translate(-((bb[0] + bb[2]) / 2), -((bb[1] + bb[3]) / 2)))
    mark.width = 0
    return mark


def _make_lslash(font, cp, base_name, crossbar_name, y_frac, x_center):
    """L-with-stroke: base glyph + crossbar mark at (x_center, y_frac * height)."""
    c = font.createMappedChar(cp)
    c.clear()
    c.addReference(base_name)
    c.width = font[base_name].width
    base_bb = font[base_name].boundingBox()
    target_y = base_bb[1] + (base_bb[3] - base_bb[1]) * y_frac
    c.addReference(crossbar_name, psMat.translate(x_center, target_y))
    return c


_l_crossbar = _make_l_crossbar_mark(font, '_l_crossbar', bar_width=300, rotation=40)

# Ł U+0141 — crossbar at 42% of cap height, centered on the vertical stroke (x≈75)
_make_lslash(font, 0x0141, 'L', '_l_crossbar', y_frac=0.42, x_center=75)
# ł U+0142 — crossbar at 60% of ascender height, l's stroke is at x≈75
_make_lslash(font, 0x0142, 'l', '_l_crossbar', y_frac=0.60, x_center=75)


# ---------------------------------------------------------------------------
# O with stroke: Ø U+00D8 / ø U+00F8
# ---------------------------------------------------------------------------

def _make_oslash(font, cp, base_name, crossbar_name, y_offset=0):
    """O-with-stroke: base glyph + crossbar centered on its bounding box.

    y_offset: shift the crossbar up (positive) or down (negative) from centre.
    """
    c = font.createMappedChar(cp)
    c.clear()
    c.addReference(base_name)
    c.width = font[base_name].width
    base_bb = font[base_name].boundingBox()
    cx = (base_bb[0] + base_bb[2]) / 2
    cy = (base_bb[1] + base_bb[3]) / 2
    c.addReference(crossbar_name, psMat.translate(cx, cy + y_offset))
    return c


# bar_width sized to span the oval diagonal plus a small overhang on each side:
# O: bbox ≈450×580 → diagonal ≈735; o: bbox ≈365×420 → diagonal ≈557
_cap_o_crossbar = _make_l_crossbar_mark(font, '_cap_o_crossbar', bar_width=720, rotation=55)
_lc_o_crossbar = _make_l_crossbar_mark(font, '_lc_o_crossbar', bar_width=558, rotation=55)

_make_oslash(font, 0x00D8, 'O', '_cap_o_crossbar', y_offset=30)  # Ø
_make_oslash(font, 0x00F8, 'o', '_lc_o_crossbar', y_offset=15)   # ø


# ---------------------------------------------------------------------------
# L with middle dot: Ŀ U+013F / ŀ U+0140  (Catalan)
# ---------------------------------------------------------------------------

def _make_l_middot(font, cp, base_name, dot_x=None, gap=35):
    """Catalan L-middot: base glyph + dot at mid-height.

    dot_x: explicit dot-centre x coordinate.  Use for uppercase L where the ink
           right edge (base_bb[2]) is the wide horizontal foot, far from where
           the dot should sit.  If None, falls back to ink-right-edge + gap.
    gap:   extra space added to the right of the dot when computing advance width,
           and the fallback offset from ink right edge when dot_x is None.
    """
    c = font.createMappedChar(cp)
    c.clear()
    c.addReference(base_name)
    base_bb = font[base_name].boundingBox()
    dot_bb = font['_dot_above_mark'].boundingBox()
    dot_cx = (dot_bb[0] + dot_bb[2]) / 2
    dot_cy = (dot_bb[1] + dot_bb[3]) / 2
    target_x = dot_x if dot_x is not None else base_bb[2] + gap
    target_y = (base_bb[1] + base_bb[3]) / 2
    c.addReference('_dot_above_mark', psMat.translate(target_x - dot_cx, target_y - dot_cy))
    # Width: at least as wide as the base letter; wider only if the dot overhangs.
    dot_right = target_x + (dot_bb[2] - dot_bb[0]) / 2 + gap
    c.width = max(font[base_name].width, int(round(dot_right)))
    return c

_make_l_middot(font, 0x013F, 'L', dot_x=font['L'].boundingBox()[0] + 172)  # Ŀ
_make_l_middot(font, 0x0140, 'l', gap=45)  # ŀ


# ---------------------------------------------------------------------------
# D/d/H/h/T/t with stroke (all horizontal bars, rotation=0)
# ---------------------------------------------------------------------------

_bar_300 = _make_l_crossbar_mark(font, '_bar_300', bar_width=300)  # D/d/Ð
_bar_220 = _make_l_crossbar_mark(font, '_bar_220', bar_width=220)  # T/t/h
_bar_480 = _make_l_crossbar_mark(font, '_bar_480', bar_width=480)  # H (spans past both uprights)

# Đ U+0110 — bar through D's left vertical stem (like Ł for L)
_make_lslash(font, 0x0110, 'D', '_bar_300', y_frac=0.50, x_center=145)
# đ U+0111 — bar through d's right ascending stem
_make_lslash(font, 0x0111, 'd', '_bar_300', y_frac=0.78, x_center=360)
# Ħ U+0126 — bar spanning past both H uprights, centred on full glyph width
_make_lslash(font, 0x0126, 'H', '_bar_480', y_frac=0.85, x_center=239)
# ħ U+0127 — bar through h's left ascending stem
_make_lslash(font, 0x0127, 'h', '_bar_220', y_frac=0.85, x_center=70)
# Ŧ U+0166 — bar through T's vertical stem
_make_lslash(font, 0x0166, 'T', '_bar_220', y_frac=0.45, x_center=194)
# ŧ U+0167 — bar through t's stem, below t's existing crossbar
_make_lslash(font, 0x0167, 't', '_bar_220', y_frac=0.35, x_center=148)
# Ð U+00D0 — Eth: like Đ but slightly higher (upper curve of D)
_make_lslash(font, 0x00D0, 'D', '_bar_300', y_frac=0.58, x_center=145)


# ---------------------------------------------------------------------------
# Eng: Ŋ U+014A / ŋ U+014B
# N/n with a comma-shaped hook below the right stem.
# The comma is placed so its top aligns with the baseline (y=0) and its centre
# sits at a fraction of the base glyph's ink width (the right stem).
# ---------------------------------------------------------------------------

_comma_bb = font['comma'].boundingBox()
_comma_cx = (_comma_bb[0] + _comma_bb[2]) / 2

def _make_eng_comma(font, name, y_scale, x_scale=1.0, thin_delta=0):
    """Elongated comma for eng glyphs: y_scale taller, anchored at the hook tip."""
    g = font.createChar(-1, name)
    g.clear()
    layer = fontforge.layer()
    for c in font['comma'].foreground:
        layer += c
    g.foreground = layer
    # Scale, then translate up so the bottom stays fixed.
    g.transform(psMat.compose(psMat.scale(x_scale, y_scale),
                              psMat.translate(0, -(y_scale - 1) * _comma_bb[1])))
    if thin_delta:
        g.removeOverlap()
        g.changeWeight(thin_delta)
    g.width = 0
    return g


_eng_comma_uc = _make_eng_comma(font, '_eng_comma_uc', y_scale=1.5)
_eng_comma_lc = _make_eng_comma(font, '_eng_comma_lc', y_scale=1.3, x_scale=0.85)

_eng_stroke = int(round(0.12 * font.ascent))


def _make_eng(font, cp, base_name, comma_name, x_frac=0.88, x_offset=0, y_offset=0):
    """Eng: base (N/n) + comma hook hanging below the right stem.

    x_frac:   fraction of base ink width for the hook centre.
    x_offset: additional horizontal nudge in font units (negative = left).
    y_offset: vertical nudge of the hook attachment point (positive = up).
    """
    base_bb = font[base_name].boundingBox()
    target_x = base_bb[0] + (base_bb[2] - base_bb[0]) * x_frac + x_offset
    dx = target_x - _comma_cx
    dy = -font[comma_name].boundingBox()[3] + y_offset
    c = font.createMappedChar(cp)
    c.clear()
    c.addReference(base_name)
    c.width = font[base_name].width
    c.addReference(comma_name, psMat.translate(dx, dy))
    return c


_make_eng(font, 0x014A, 'N', '_eng_comma_uc', x_offset=-_eng_stroke // 2 - 10, y_offset=3 * _eng_stroke)  # Ŋ
_make_eng(font, 0x014B, 'n', '_eng_comma_lc', x_offset=-_eng_stroke // 2 + 15, y_offset=int(_eng_stroke * 1.5))  # ŋ


# Circumflex: Â Ê Î Ô Û / â ê î ô û  +  Esperanto Ĉ Ĝ Ĥ Ĵ Ŝ  +  Welsh Ŵ Ŷ
for cp, base in [
    (0x00C2, 'A'), (0x00CA, 'E'), (0x00CE, 'I'), (0x00D4, 'O'), (0x00DB, 'U'),
    (0x0108, 'C'), (0x011C, 'G'), (0x0124, 'H'), (0x0134, 'J'), (0x015C, 'S'), (0x0174, 'W'), (0x0176, 'Y'),
    (0x00E2, 'a'), (0x00EA, 'e'), (0x00EE, 'dotlessi'), (0x00F4, 'o'), (0x00FB, 'u'),
    (0x0109, 'c'), (0x011D, 'g'), (0x0125, 'h'), (0x015D, 's'), (0x0175, 'w'), (0x0177, 'y'),
]:
    _accented(cp, base, '_circumflex_mark')
_make_accented(font, 0x0135, 'uni0237', '_circumflex_mark', x_adj=_j_x_adj)  # ĵ — dotless to avoid dot+circumflex stack

# Grave: À È Ì Ò Ù Ỳ / à è ì ò ù ỳ  + Ẁ ẁ Ǹ ǹ
for cp, base in [
    (0x00C0, 'A'), (0x00C8, 'E'), (0x00CC, 'I'), (0x00D2, 'O'), (0x00D9, 'U'), (0x1EF2, 'Y'),
    (0x00E0, 'a'), (0x00E8, 'e'), (0x00EC, 'dotlessi'), (0x00F2, 'o'), (0x00F9, 'u'), (0x1EF3, 'y'),
    (0x1E80, 'W'), (0x1E81, 'w'),   # Ẁ ẁ  Welsh
    (0x01F8, 'N'), (0x01F9, 'n'),   # Ǹ ǹ  Welsh/Pinyin
]:
    _accented(cp, base, '_grave_mark')

# Tilde: Ã Ñ Õ / ã ñ õ  + Ĩ ĩ Ũ ũ Ẽ ẽ
for cp, base in [
    (0x00C3, 'A'), (0x00D1, 'N'), (0x00D5, 'O'),
    (0x00E3, 'a'), (0x00F1, 'n'), (0x00F5, 'o'),
    (0x0128, 'I'), (0x0129, 'dotlessi'),  # Ĩ ĩ  Portuguese
    (0x0168, 'U'), (0x0169, 'u'),         # Ũ ũ  Portuguese
    (0x1EBC, 'E'), (0x1EBD, 'e'),         # Ẽ ẽ  Portuguese
]:
    _accented(cp, base, '_tilde_mark')

# Dot above: Ċ Ė Ġ İ Ż / ċ ė ġ ż  + Ẇ ẇ
for cp, base in [
    (0x010A, 'C'), (0x0116, 'E'), (0x0120, 'G'), (0x0130, 'I'), (0x017B, 'Z'),
    (0x010B, 'c'), (0x0117, 'e'), (0x0121, 'g'), (0x017C, 'z'),
    (0x1E86, 'W'), (0x1E87, 'w'),   # Ẇ ẇ  Welsh
]:
    _accented(cp, base, '_dot_above_mark')

# Diaeresis: Ä Ë Ï Ö Ÿ / ä ë ï ö ü ÿ  (Ü skipped — hand-drawn)  + Ẅ ẅ
for cp, base in [
    (0x00C4, 'A'), (0x00CB, 'E'), (0x00CF, 'I'), (0x00D6, 'O'), (0x0178, 'Y'),
    (0x00E4, 'a'), (0x00EB, 'e'), (0x00EF, 'dotlessi'), (0x00F6, 'o'), (0x00FC, 'u'), (0x00FF, 'y'),
    (0x1E84, 'W'), (0x1E85, 'w'),   # Ẅ ẅ  Welsh
]:
    _accented(cp, base, '_diaeresis_mark')

# Double acute: Ő Ű / ő ű  (Ő skipped — hand-drawn)
for cp, base in [
    (0x0150, 'O'), (0x0170, 'U'),
    (0x0151, 'o'), (0x0171, 'u'),
]:
    _accented(cp, base, '_double_acute_mark')

# Hook cedilla: Ç Ş Ţ / ç ş ţ  — French/Turkish/Cameroonian
# C/c/S/s: curved base bottom leaves visual space — pull cedilla up to close the gap
_make_cedilla(font, 0x00C7, 'C', mark='_hook_cedilla_mark', y_adj=-15)  # Ç
_make_cedilla(font, 0x00E7, 'c', mark='_hook_cedilla_mark', y_adj=-15)  # ç
_make_cedilla(font, 0x015E, 'S', mark='_hook_cedilla_mark', y_adj=-15)  # Ş
_make_cedilla(font, 0x015F, 's', mark='_hook_cedilla_mark', y_adj=-15)  # ş
_make_cedilla(font, 0x0162, 'T', mark='_hook_cedilla_mark', y_adj=-10, x_adj=-37)  # Ţ
_make_cedilla(font, 0x0163, 't', mark='_hook_cedilla_mark', y_adj=-15, x_adj=40)  # ţ
# Ȩ/ȩ U+0228/U+0229 — E with cedilla (Cameroonian)
_make_cedilla(font, 0x0228, 'E', mark='_hook_cedilla_mark', y_adj=-25)  # Ȩ
_make_cedilla(font, 0x0229, 'e', mark='_hook_cedilla_mark', y_adj=-15)  # ȩ

# Comma cedilla: Ģ Ķ Ļ Ņ Ŗ / ģ ķ ļ ņ ŗ  — Latvian
for cp, base in [
    (0x0122, 'G'), (0x0136, 'K'), (0x013B, 'L'), (0x0145, 'N'), (0x0156, 'R'),
    (0x0123, 'g'), (0x0137, 'k'), (0x013C, 'l'), (0x0146, 'n'), (0x0157, 'r'),
]:
    _make_cedilla(font, cp, base)

# Comma below: Ș ș Ț ț  (Romanian — U+0219/U+021B are the canonical forms;
# U+015F/U+0163 cedilla variants already exist above)
for cp, base in [
    (0x0218, 'S'), (0x0219, 's'),
    (0x021A, 'T'), (0x021B, 't'),
]:
    _make_cedilla(font, cp, base)

# Macron: Ā Ī Ō Ū / ā ī ō ū ē  (Ē skipped — hand-drawn)
for cp, base in [
    (0x0100, 'A'), (0x012A, 'I'), (0x014C, 'O'), (0x016A, 'U'), (0x0112, 'E'),
    (0x0101, 'a'), (0x012B, 'dotlessi'), (0x014D, 'o'), (0x016B, 'u'), (0x0113, 'e'),
]:
    _accented(cp, base, '_macron_mark')


# Ogonek: Ą Ę Į Ų / ą ę į ų
for cp, base in [
    (0x0104, 'A'), (0x0118, 'E'), (0x012E, 'I'), (0x0172, 'U'),
    (0x0105, 'a'), (0x0119, 'e'), (0x012F, 'i'), (0x0173, 'u'),
]:
    _make_ogonek(font, cp, base)

# Dot below: Ạ Ẹ Ị Ọ Ụ Ỵ / ạ ẹ ị ọ ụ ỵ
for cp, base in [
    (0x1EA0, 'A'), (0x1EB8, 'E'), (0x1ECA, 'I'), (0x1ECC, 'O'), (0x1EE4, 'U'), (0x1EF4, 'Y'),
    (0x1EA1, 'a'), (0x1EB9, 'e'), (0x1ECB, 'i'), (0x1ECD, 'o'), (0x1EE5, 'u'), (0x1EF5, 'y'),
]:
    _make_dot_below(font, cp, base)

# Macron below: Ḏ Ḻ Ṉ Ṟ Ṯ Ẕ / ḏ ḻ ṉ ṟ ṯ ẕ  (Semitic transliteration)
for cp, base in [
    (0x1E0E, 'D'), (0x1E3A, 'L'), (0x1E48, 'N'), (0x1E5E, 'R'), (0x1E6E, 'T'), (0x1E94, 'Z'),
    (0x1E0F, 'd'), (0x1E3B, 'l'), (0x1E49, 'n'), (0x1E6F, 't'), (0x1E95, 'z'),
]:
    _make_macron_below(font, cp, base)
_make_macron_below(font, 0x1E5F, 'r', y_adj=45)  # ṟ — r sits low, needs extra gap

# ĳ U+0133 / Ĳ U+0132: Dutch IJ digraph ligatures.
# Position so the ink edges have the same gap as adjacent letters would after kerning (~40 units).
for cp, left, right in [(0x0133, 'i', 'j'), (0x0132, 'I', 'J')]:
    _ij = font.createMappedChar(cp)
    _ij.clear()
    _ij.addReference(left)
    _ink_gap = 0
    _dx = int(round(font[left].boundingBox()[2] + _ink_gap - font[right].boundingBox()[0]))
    _ij.addReference(right, psMat.translate(_dx, 0))
    _ij.width = _dx + font[right].width


# ---------------------------------------------------------------------------
# Greek letter aliases and derived glyphs
# ---------------------------------------------------------------------------

# Uppercase Greek letters visually identical to Latin capitals.
for _cp, _name in [
    (0x0391, 'A'),   # Α Alpha
    (0x0392, 'B'),   # Β Beta
    (0x0395, 'E'),   # Ε Epsilon
    (0x0396, 'Z'),   # Ζ Zeta
    (0x0397, 'H'),   # Η Eta
    (0x0399, 'I'),   # Ι Iota
    (0x039A, 'K'),   # Κ Kappa
    (0x039C, 'M'),   # Μ Mu
    (0x039D, 'N'),   # Ν Nu
    (0x039F, 'O'),   # Ο Omicron
    (0x03A1, 'P'),   # Ρ Rho
    (0x03A4, 'T'),   # Τ Tau
    (0x03A5, 'Y'),   # Υ Upsilon
    # Χ Chi handled separately below (needs weight adjustment)
]:
    _g = font.createMappedChar(_cp)
    _g.clear()
    _g.addReference(_name)
    _g.width = font[_name].width

# Χ (Chi, U+03A7): X thinned to match derived Greek uppercase weight.
_chi_layer = fontforge.layer()
for _c in font['X'].foreground:
    _chi_layer += _c
_g = font.createMappedChar(0x03A7)
_g.clear()
_g.foreground = _chi_layer
_g.removeOverlap()
_g.changeWeight(-15)
_bb = _g.boundingBox()
_g.width = int(round(_bb[2] + 20))

# Lowercase Greek letters visually identical to Latin lowercase.
for _cp, _name in [
    (0x03B9, 'dotlessi'),  # ι iota  (undotted like the Greek letter)
    (0x03BF, 'o'),          # ο omicron
    (0x03BA, 'k'),          # κ kappa
    (0x03C7, 'x'),          # χ chi
]:
    _g = font.createMappedChar(_cp)
    _g.clear()
    _g.addReference(_name)
    _g.width = font[_name].width

# Greek uppercase derived by scaling the corresponding lowercase to capital height.
_cap_height = font['A'].boundingBox()[3]


def _greek_lc_to_uc(font, lc_cp, uc_cp, snap=True, weight_delta=0):
    """Copy a Greek lowercase glyph and scale it to capital height.

    snap=True    → translate so bb[1]=0 then re-scale to cap height.
    snap=False   → keep natural position (for letters like ψ with a descender).
    weight_delta → changeWeight adjustment applied after scaling (negative = thinner).
    """
    src = font[lc_cp]
    src_bb = src.boundingBox()
    if src_bb[3] <= 0:
        return
    uc = font.createMappedChar(uc_cp)
    uc.clear()
    layer = fontforge.layer()
    for c in src.foreground:
        layer += c
    uc.foreground = layer
    uc.transform(psMat.scale(_cap_height / src_bb[3]))
    if snap:
        _bb = uc.boundingBox()
        if _bb[1] != 0:
            uc.transform(psMat.translate(0, -_bb[1]))
            _bb = uc.boundingBox()
            if _bb[3] > 0:
                uc.transform(psMat.scale(_cap_height / _bb[3]))
    if weight_delta:
        uc.correctDirection()
        uc.addExtrema()
        uc.removeOverlap()
        uc.changeWeight(weight_delta)
        _bb = uc.boundingBox()
        if _bb[3] > 0:
            uc.transform(psMat.scale(_cap_height / _bb[3]))
    _bb = uc.boundingBox()
    uc.width = int(round(_bb[2] + 20))


_greek_lc_to_uc(font, 0x03B8, 0x0398)                          # Θ from θ
_greek_lc_to_uc(font, 0x03C6, 0x03A6, weight_delta=-25)        # Φ from φ  (circle shape is sensitive to changeWeight)
_greek_lc_to_uc(font, 0x03C8, 0x03A8, snap=False, weight_delta=-20)  # Ψ from ψ

# Γ (U+0393): L flipped vertically — vertical stroke on left, bar at top.
_L_bb = font['L'].boundingBox()
_g = font.createMappedChar(0x0393)
_g.clear()
_g.addReference('L', psMat.compose(psMat.scale(1, -1), psMat.translate(0, _L_bb[3])))
_g.width = font['L'].width

# Λ (U+039B): V flipped vertically — two diagonals meeting at the top.
_V_bb = font['V'].boundingBox()
_g = font.createMappedChar(0x039B)
_g.clear()
_g.addReference('V', psMat.compose(psMat.scale(1, -1), psMat.translate(0, _V_bb[3])))
_g.width = font['V'].width

# η (eta, U+03B7): n with a straight vertical descender on the right leg.
# A rotated hyphen-bar gives a stroke of matching weight and shape.
# x-scaled to 90% of original thickness so it reads slightly thinner than n's strokes.
_p_desc = abs(font['p'].boundingBox()[1])
_eta_bar = _make_l_crossbar_mark(font, '_eta_bar', bar_width=int(_p_desc * 1.08), rotation=90)
_eta_bar.transform(psMat.scale(0.9, 1))
_eta_bar_bb = _eta_bar.boundingBox()
_n_bb = font['n'].boundingBox()
_eta_leg_x = _n_bb[0] + (_n_bb[2] - _n_bb[0]) * 0.88
_eta_bar_cx = (_eta_bar_bb[0] + _eta_bar_bb[2]) / 2
_g = font.createMappedChar(0x03B7)
_g.clear()
_g.addReference('n')
_g.addReference('_eta_bar', psMat.translate(
    _eta_leg_x - _eta_bar_cx,
    -_eta_bar_bb[3] + _eng_stroke,  # top of bar overlaps baseline by one stroke width
))
_g.width = font['n'].width


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

font.save(font_fname)
