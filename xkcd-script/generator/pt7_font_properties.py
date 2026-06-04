# -*- coding: utf-8 -*-
"""
Apply font-wide properties: kerning, spacing, and any other metric tweaks.

Reads the SFD produced by pt6_derived_chars.py (which has all glyphs),
applies properties, saves.
"""
import fontforge
import unicodedata

font_fname = '../generated/xkcd-script-pt7.sfd'
font = fontforge.open('../generated/xkcd-script-pt6.sfd')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_char(c):
    """Return the base letter for an accented character (e.g. É → E).

    Characters without a Unicode canonical decomposition (e.g. ø, ł) are
    handled via the manual table below.
    """
    _no_decomp = {
        'ø': 'o', 'Ø': 'O',
        'ł': 'l', 'Ł': 'L',
        'đ': 'd', 'Đ': 'D',
        'ħ': 'h', 'Ħ': 'H',
        'ŧ': 't', 'Ŧ': 'T',
        'ð': 'd', 'Ð': 'D',
    }
    if c in _no_decomp:
        return _no_decomp[c]
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


# ---------------------------------------------------------------------------
# Kerning
# ---------------------------------------------------------------------------

def autokern(font):
    all_glyphs = [glyph.glyphname for glyph in font.glyphs()
                  if not glyph.glyphname.startswith(' ')]
    ligatures = [name for name in all_glyphs if name[0] != '_' and '_' in name]
    upper_ligatures = [ligature for ligature in ligatures if ligature.upper() == ligature]
    lower_ligatures = [ligature for ligature in ligatures if ligature.lower() == ligature]

    caps = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    lower = list('abcdefghijklmnopqrstuvwxyz')
    roman = caps + lower

    font.addLookup('kerning', 'gpos_pair', (), [['kern', [['latn', ['dflt']]]]])
    font.addLookupSubtable('kerning', 'kern')

    def kern(sep, left, right, damper=None, **kwargs):
        """Wraps font.autoKern: expands accented variants and leading/trailing ligatures."""
        def expand(chars, left_side):
            expanded = _expand_with_variants(font, chars)
            seen = set(expanded)
            for glyph in font.glyphs():
                name = glyph.glyphname
                if name[0] == '_' or '_' not in name:
                    continue
                parts = name.split('_')
                # Left side: ligature's right edge (last component) determines spacing.
                # Right side: ligature's left edge (first component) determines spacing.
                anchor = parts[-1] if left_side else parts[0]
                if anchor in seen and name not in seen:
                    expanded.append(name)
                    seen.add(name)
            return expanded
        lefts = expand(left, left_side=True)
        rights = expand(right, left_side=False)
        font.autoKern('kern', sep, lefts, rights, **kwargs)
        if damper and damper != 1.0:
            for l in lefts:
                tuples = font[l].getPosSub('kern')
                new_table = []
                for tup in tuples:
                    if tup[1] == 'Pair' and tup[2] in rights:
                        font[l].addPosSub('kern', *(tup[2:5] + (int(tup[5] * damper),) + tup[6:]))

    def getkern(left, right):
        c = font[left]
        tuples = c.getPosSub('kern')
        for tup in tuples:
            if tup[1] == 'Pair' and tup[2] == right:
                return tup[5]
        return None

    a = font['_pad_space'].width
    a = max(a - 20, 0)

    # The same combination will be overwritten, so the one written last will take effect.
    # autoKern looks at the outline, so even if you change the padding, it absorbs all of it.
    # Use `+a` when you want to link the spacing after kerning to the padding.
    kern(150, ['/', '\\'], ['/', '\\'])
    # lowercase-lowercase
    kern(60+a, ['s'], set(lower) - {'i', 'j', 'f', 't', 'x'}, onlyCloser=True, damper=0.75) # loosen by damper
    # Overwrite sf and st. (From experience, it is often just right to adopt the larger of the two
    # separation required by the glyphs on the left and right.)
    kern(80+a, set(lower) - {'i', 'j'}, ['f', 't'], onlyCloser=True, damper=0.75)
    kern(90+a, set(lower) - {'i', 'j'}, ['x'], onlyCloser=True, damper=0.75) # kx is fine, fx is tight
    kern(80+a, ['x'], set(lower) - {'i', 'j'}, onlyCloser=True, damper=0.75)
    kern(100+a, ['f', 't'], set(lower) - {'i', 'j'}, onlyCloser=True, damper=0.75) # oveerwrite fx
    # including uppercase
    # Set *Y altogether first: CY, OY, etc. will have appropriate values set in the latter part.
    kern(105, roman, ['Y', 'T'], onlyCloser=True, damper=0.75)
    kern(100, caps, ['f'], onlyCloser=True, damper=0.75)
    # F/E are separated from T/J so they can use a tighter target gap.
    kern(110, ['F'], set(roman) - {'j'}, onlyCloser=True, damper=0.75) # keep FO≈-60
    # Since F and z mesh together and the kerning becomes too large,
    # reuse the kerning value of one of the round letterforms.
    diff_Fo_Fz = getkern('F', 'o') - getkern('F', 'z')
    kern(110 + int(diff_Fo_Fz / 0.75), ['F'], ['z'], onlyCloser=True, damper=0.75)
    kern(90, ['E'], set(roman) - {'j'}, onlyCloser=True, damper=0.75) # keep ES≈-30
    kern(45, ['E'], ['V'], onlyCloser=True, touch=True)
    kern(115, ['T', 'J'], set(roman) - {'j'}, onlyCloser=True, damper=0.75) # keep Tr≈-105
    kern(105, ['Y'], set(roman) - {'j'}, onlyCloser=True, damper=0.75)
    # C: loosen from the default (was too tight for Cj).
    # Compared to E, the lower curve of C tends to come close to the next character,
    # but this is considered an intentional design.
    kern(60, ['C'], set(roman) - {'j'}, onlyCloser=True, damper=0.75) # keep CK≈-15
    kern(25, ['C'], ['V'], onlyCloser=True, touch=True)
    kern(60, ['O'], set(roman) - {'j'}, onlyCloser=True, damper=0.75) # loosen
    kern(100, ['P'], set(roman) - {'j'}, onlyCloser=True, damper=0.75)
    diff_Po_Pe = getkern('P', 'o') - getkern('P', 'e')
    kern(100 + int(diff_Po_Pe / 0.75), ['P'], ['e'], onlyCloser=True, damper=0.75)
    kern(35, ['L'], set(roman) - {'j'}, onlyCloser=True, touch=True)


autokern(font)
font.removeGlyph(font['_pad_space'])


# ---------------------------------------------------------------------------
# Mark-to-base GPOS: position combining diacritical marks above base glyphs
# ---------------------------------------------------------------------------

font.addLookup('above', 'gpos_mark2base', (), [['mark', [['latn', ['dflt']]]]])
font.addLookupSubtable('above', 'above_sub')
font.addAnchorClass('above_sub', 'above')

# Combining mark codepoints registered in pt6, paired with their private glyph names.
# The anchor sits at the bottom-centre of each combining mark glyph, adjusted by
# a per-mark y offset: positive = mark sits lower (less gap), negative = higher (more gap).
_COMBINING = [
    (0x0300, '_grave_mark', 0),
    (0x0301, '_acute_mark', 0),
    (0x0302, '_circumflex_mark', 300),  # was too high
    (0x0303, '_tilde_mark', 270),  # was too high
    (0x0304, '_macron_mark', -90),  # was too low
    (0x0307, '_dot_above_mark', -30),  # too low → raise
    (0x0308, '_diaeresis_mark', 0),
    (0x030A, '_ring_above_mark', 45),  # could be a little closer
    (0x030B, '_double_acute_mark', 0),
    (0x030C, '_caron_mark', 280),  # was too high
]

for cp, private_name, y_offset in _COMBINING:
    mark_glyph = font[cp]
    # Use the private mark glyph's bbox (the encoded glyph is a composite whose
    # bbox FontForge may not resolve; the private mark is a plain outline).
    bb = font[private_name].boundingBox()
    cx = (bb[0] + bb[2]) / 2
    mark_glyph.addAnchorPoint('above', 'mark', cx, bb[1] + y_offset)

# j's dot is to the right of the body centre; combining marks should sit above the dot.
_j_layer = font['j'].foreground
_j_dot_ymin = max(min(p.y for p in c) for c in _j_layer)
_j_dot_xs = [p.x for c in _j_layer for p in c if min(p.y for p in c) >= _j_dot_ymin]
_j_dot_cx = (min(_j_dot_xs) + max(_j_dot_xs)) / 2
_J_BASE_NAMES = frozenset({'j', 'uni0237'})

# Base anchors at top-centre + gap for every letter in the font.
_BASE_GAP = 20
for glyph in font.glyphs():
    if glyph.unicode < 0:
        continue
    if unicodedata.category(chr(glyph.unicode))[0] != 'L':
        continue
    bb = glyph.boundingBox()
    if bb[2] <= bb[0]:  # empty / unresolved composite
        continue
    cx = _j_dot_cx if glyph.glyphname in _J_BASE_NAMES else (bb[0] + bb[2]) / 2
    glyph.addAnchorPoint('above', 'base', cx, bb[3] + _BASE_GAP)


# ---------------------------------------------------------------------------
# Mark-to-base GPOS: position combining cedilla below base glyphs
# ---------------------------------------------------------------------------

font.addLookup('below', 'gpos_mark2base', (), [['mark', [['latn', ['dflt']]]]])
font.addLookupSubtable('below', 'below_sub')
font.addAnchorClass('below_sub', 'below')

# Mark anchor at top-centre of the combining cedilla glyph.
_c0327 = font[0x0327]
_c0327_bb = _c0327.boundingBox()
_c0327.addAnchorPoint('below', 'mark', (_c0327_bb[0] + _c0327_bb[2]) / 2, _c0327_bb[3])

# Base anchors at bottom-centre of ɛ and Ɛ, pulled up by 15 units to match the
# y_adj=-15 overlap used in the precomposed cedilla glyphs (avoids a rendering gap).
_BELOW_BASES = {0x025B, 0x0190}  # ɛ  Ɛ
for glyph in font.glyphs():
    if glyph.unicode not in _BELOW_BASES:
        continue
    bb = glyph.boundingBox()
    if bb[2] <= bb[0]:
        continue
    glyph.addAnchorPoint('below', 'base', (bb[0] + bb[2]) / 2, bb[1] + 15)


# ---------------------------------------------------------------------------
# CFF hinting zones and OS/2 metrics
# ---------------------------------------------------------------------------
# FontForge auto-computes these by scanning all glyph tops and stem widths.
# Adding non-Latin scripts shifts the cluster centroids and silently changes
# hinting, which alters the rendered pixel positions of Latin letters.  Pin
# all values here (derived from the Latin+diacritic glyph set) so the
# hinting is stable regardless of how many non-Latin glyphs are added.
font.private['BlueValues'] = (-10, 20, 411, 441, 573, 603)
font.private['OtherBlues'] = (-241, -190)
font.private['BlueScale'] = 0.0208333
font.private['BlueShift'] = 16
font.private['StdHW'] = 74
font.private['StdVW'] = 76
font.private['StemSnapH'] = (53, 61, 70, 74, 78, 83, 87, 172, 220)
font.private['StemSnapV'] = (60, 70, 76, 80, 85)

# sxHeight / sCapHeight: used by text renderers for optical sizing.
# Same issue — adding Greek glyphs shifts the auto-computed values.
font.os2_xheight = 338
font.os2_capheight = 592


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

font.save(font_fname)
