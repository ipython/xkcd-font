# -*- coding: utf-8 -*-
"""
Generate derived/composed characters: quote aliases, combining diacritical marks,
and all accented Latin letters for European languages.

Reads the base SFD produced by pt4_svg_to_font.py, adds derived glyphs, saves.
"""
import os
import fontforge
import psMat

font_fname = '../font/xkcd-script.sfd'
font = fontforge.open(font_fname)


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


def _place_below(font, base_name, mark_name, gap=10):
    """Compute translation to place mark centered below base."""
    base_bb = font[base_name].boundingBox()
    mark_bb = font[mark_name].boundingBox()
    base_cx = (base_bb[0] + base_bb[2]) / 2
    mark_cx = (mark_bb[0] + mark_bb[2]) / 2
    dx = base_cx - mark_cx
    dy = base_bb[1] - gap - mark_bb[3]
    return psMat.translate(dx, dy)


def _make_cedilla(font, cp, base_name, gap=8):
    if cp in _SKIP_CPS:
        return
    c = font.createMappedChar(cp)
    c.clear()
    c.addReference(base_name)
    c.width = font[base_name].width
    c.addReference('comma', _place_below(font, base_name, 'comma', gap))


def _make_dot_below(font, cp, base_name, gap=15):
    if cp in _SKIP_CPS:
        return
    c = font.createMappedChar(cp)
    c.clear()
    c.addReference(base_name)
    c.width = font[base_name].width
    c.addReference('_dot_below_mark', _place_below(font, base_name, '_dot_below_mark', gap))


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
]:
    c = font.createMappedChar(cp)
    c.clear()
    mark_bb = font[mark.glyphname].boundingBox()
    dy = _ascender_top + _combining_gap - mark_bb[1]
    c.addReference(mark.glyphname, psMat.translate(0, dy))
    c.width = 0


# ---------------------------------------------------------------------------
# Accented character tables
# ---------------------------------------------------------------------------

# Acute: Á É Í Ó Ú Ý / á é í ó ú ý  (í uses dotlessi to avoid dot+acute stack)
# É is regenerated for consistency — the hand-drawn original has a different stroke length.
for cp, base in [
    (0x00C1, 'A'), (0x00C9, 'E'), (0x00CD, 'I'), (0x00D3, 'O'), (0x00DA, 'U'), (0x00DD, 'Y'),
    (0x00E1, 'a'), (0x00E9, 'e'), (0x00ED, 'dotlessi'), (0x00F3, 'o'), (0x00FA, 'u'), (0x00FD, 'y'),
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

# Ring above: Ů / ů
for cp, base in [(0x016E, 'U'), (0x016F, 'u')]:
    _make_accented(font, cp, base, '_ring_above_mark')

# Ď Ť (uppercase): caron above, like other uppercase caron letters.
for cp, base in [(0x010E, 'D'), (0x0164, 'T')]:
    _make_accented(font, cp, base, '_caron_mark')

# ď ť ľ (lowercase) / Ľ (uppercase): raised apostrophe to the right.
_make_dstroke(font, 0x010F, 'd', gap=-30)
_make_dstroke(font, 0x0165, 't', gap=-50)
_make_dstroke(font, 0x013E, 'l', gap=-50, width_extra=80)
_make_dstroke(font, 0x013D, 'L', gap=-50, dy_offset=100, width_extra=80)

# Circumflex: Â Ê Î Ô Û / â ê î ô û  +  Esperanto Ĉ Ĝ Ĥ Ĵ Ŝ  +  Welsh Ŵ Ŷ
for cp, base in [
    (0x00C2, 'A'), (0x00CA, 'E'), (0x00CE, 'I'), (0x00D4, 'O'), (0x00DB, 'U'),
    (0x0108, 'C'), (0x011C, 'G'), (0x0124, 'H'), (0x0134, 'J'), (0x015C, 'S'), (0x0174, 'W'), (0x0176, 'Y'),
    (0x00E2, 'a'), (0x00EA, 'e'), (0x00EE, 'dotlessi'), (0x00F4, 'o'), (0x00FB, 'u'),
    (0x0109, 'c'), (0x011D, 'g'), (0x0125, 'h'), (0x0135, 'j'), (0x015D, 's'), (0x0175, 'w'), (0x0177, 'y'),
]:
    _accented(cp, base, '_circumflex_mark')

# Grave: À È Ì Ò Ù Ỳ / à è ì ò ù ỳ
for cp, base in [
    (0x00C0, 'A'), (0x00C8, 'E'), (0x00CC, 'I'), (0x00D2, 'O'), (0x00D9, 'U'), (0x1EF2, 'Y'),
    (0x00E0, 'a'), (0x00E8, 'e'), (0x00EC, 'dotlessi'), (0x00F2, 'o'), (0x00F9, 'u'), (0x1EF3, 'y'),
]:
    _accented(cp, base, '_grave_mark')

# Tilde: Ã Ñ Õ / ã ñ õ
for cp, base in [
    (0x00C3, 'A'), (0x00D1, 'N'), (0x00D5, 'O'),
    (0x00E3, 'a'), (0x00F1, 'n'), (0x00F5, 'o'),
]:
    _accented(cp, base, '_tilde_mark')

# Dot above: Ċ Ė Ġ İ Ż / ċ ė ġ ż
for cp, base in [
    (0x010A, 'C'), (0x0116, 'E'), (0x0120, 'G'), (0x0130, 'I'), (0x017B, 'Z'),
    (0x010B, 'c'), (0x0117, 'e'), (0x0121, 'g'), (0x017C, 'z'),
]:
    _accented(cp, base, '_dot_above_mark')

# Diaeresis: Ä Ë Ï Ö Ÿ / ä ë ï ö ü ÿ  (Ü skipped — hand-drawn)
for cp, base in [
    (0x00C4, 'A'), (0x00CB, 'E'), (0x00CF, 'I'), (0x00D6, 'O'), (0x0178, 'Y'),
    (0x00E4, 'a'), (0x00EB, 'e'), (0x00EF, 'dotlessi'), (0x00F6, 'o'), (0x00FC, 'u'), (0x00FF, 'y'),
]:
    _accented(cp, base, '_diaeresis_mark')

# Double acute: Ő Ű / ő ű  (Ő skipped — hand-drawn)
for cp, base in [
    (0x0150, 'O'), (0x0170, 'U'),
    (0x0151, 'o'), (0x0171, 'u'),
]:
    _accented(cp, base, '_double_acute_mark')

# Cedilla: Ç Ş Ţ Ģ Ķ Ļ Ņ Ŗ / ç ş ţ ģ ķ ļ ņ ŗ
for cp, base in [
    (0x00C7, 'C'), (0x015E, 'S'), (0x0162, 'T'), (0x0122, 'G'), (0x0136, 'K'), (0x013B, 'L'), (0x0145, 'N'), (0x0156, 'R'),
    (0x00E7, 'c'), (0x015F, 's'), (0x0163, 't'), (0x0123, 'g'), (0x0137, 'k'), (0x013C, 'l'), (0x0146, 'n'), (0x0157, 'r'),
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
# Glyphs imported from xkcd comic images
# ---------------------------------------------------------------------------

_COMIC_CHARS_DIR = os.path.join(os.path.dirname(__file__), '../generated/additional_chars')


def _import_comic_glyph(font, name, svg_path, target_top, weight_delta=0, y_clip=None):
    """Import a pre-cleaned SVG (from pt5_additional_sources.py) and scale it
    so the top of the ink reaches target_top in font units, preserving the
    aspect ratio so any descender falls naturally below baseline.

    weight_delta: passed to changeWeight() after scaling (positive = thicker).
    y_clip: if given, clip the glyph at this y-coordinate using FontForge's
    intersect() against a background rectangle, removing everything below y_clip.
    Use y_clip=0 to clip at the baseline (removes descenders, seats the glyph
    on the baseline with a natural edge rather than a raw image crop).
    """
    g = font.createChar(-1, f'_comic_{name}')
    g.clear()
    g.importOutlines(svg_path)

    # Scale uniformly so the top of the ink reaches target_top
    bb = g.boundingBox()
    scale = target_top / bb[3]
    g.transform(psMat.scale(scale))

    # Translate to add left margin; vertical position follows naturally from scale
    bb = g.boundingBox()
    g.transform(psMat.translate(-bb[0] + 20, 0))

    if weight_delta:
        g.removeOverlap()
        g.changeWeight(weight_delta)

    if y_clip is not None:
        # Clip at y_clip: keep only ink above y_clip.
        # Place a filled rectangle covering [y_clip, +∞] in the background layer,
        # then intersect() keeps only the foreground that overlaps that rectangle.
        # FontForge uses clockwise winding for filled (outer) contours.
        g.removeOverlap()
        g.correctDirection()
        clip_rect = fontforge.contour()
        clip_rect += fontforge.point(-10000, 10000, True)   # top-left
        clip_rect += fontforge.point(10000, 10000, True)    # top-right
        clip_rect += fontforge.point(10000, y_clip, True)   # bottom-right
        clip_rect += fontforge.point(-10000, y_clip, True)  # bottom-left
        clip_rect.closed = True
        bg = fontforge.layer()
        bg += clip_rect
        g.background = bg
        g.intersect()

    g.correctDirection()
    g.removeOverlap()
    g.addExtrema()

    bb = g.boundingBox()
    g.width = int(round(bb[2] + 20))
    return g


# ß/ẞ source: hand-drawn glyph from extras/eszett.png, vectorised by pt0.
_eszett_svg = os.path.join(_COMIC_CHARS_DIR, 'eszett.svg')
if os.path.exists(_eszett_svg):
    # ß  U+00DF  Latin Small Letter Sharp S — scaled to ascender height (like 'b')
    _eszett_glyph = _import_comic_glyph(
        font, 'eszett', _eszett_svg,
        target_top=font['b'].boundingBox()[3] * 0.59,
        weight_delta=23)
    # Snap bottom to baseline so ß sits like a/e
    _bb = _eszett_glyph.boundingBox()
    if _bb[1] < 0:
        _eszett_glyph.transform(psMat.translate(0, -_bb[1]))
    _eszett = font.createMappedChar(0x00DF)
    _eszett.clear()
    for c in _eszett_glyph.foreground:
        _eszett.foreground += c
    _eszett.width = _eszett_glyph.width

    # ẞ  U+1E9E  Latin Capital Letter Sharp S — scaled to capital height (like 'B')
    _cap_eszett_glyph = _import_comic_glyph(
        font, 'eszett_cap', _eszett_svg,
        target_top=font['B'].boundingBox()[3] * 0.72,
        weight_delta=19)
    _bb = _cap_eszett_glyph.boundingBox()
    if _bb[1] < 0:
        _cap_eszett_glyph.transform(psMat.translate(0, -_bb[1]))
    _cap_glyph = font.createMappedChar(0x1E9E)
    _cap_glyph.clear()
    for c in _cap_eszett_glyph.foreground:
        _cap_glyph.foreground += c
    _cap_glyph.width = _cap_eszett_glyph.width


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

font.save(font_fname)
