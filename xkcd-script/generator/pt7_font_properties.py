# -*- coding: utf-8 -*-
"""
Apply font-wide properties: kerning, spacing, and any other metric tweaks.

Reads the SFD produced by pt6_derived_chars.py (which has all glyphs),
applies properties, saves.
"""
import fontforge
import unicodedata

font_fname = '../font/xkcd-script.sfd'
font = fontforge.open(font_fname)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


autokern(font)


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
    cx = (bb[0] + bb[2]) / 2
    glyph.addAnchorPoint('above', 'base', cx, bb[3] + _BASE_GAP)


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

font.save(font_fname)
