"""Generate xkcd-script-mathjax.woff — xkcd-script extended with:
  1. Unicode math italic/bold cmap aliases so MathJax CHTML uses it for letter glyphs.
  2. A hand-drawn U+221A (radical/sqrt) glyph from xkcd comic #2343 (surd only).
  3. A hand-drawn U+E221 (full long sqrt) glyph — the complete surd+bar shape.

Phase A uses fontforge (for correctDirection / removeOverlap cleanup).
Phase B uses fontTools (for cmap aliasing and WOFF output).

Run from repo root:
    docker run --rm -v $(pwd):/work fontbuilder-test \\
        python3 /work/xkcd-script/generator/gen_mathjax_font.py
"""
import os
import tempfile
import fontforge
import psMat
from fontTools.ttLib import TTFont


FONT_IN = '/work/xkcd-script/font/xkcd-script.otf'
FONT_OUT = '/work/xkcd-script/font/xkcd-script-mathjax.woff'

# y-position of the math axis (fraction-bar centre) in xkcd-script font units.
MATH_AXIS = 260


def build_aliases():
    a = {}

    # --- Latin: italic and bold variants ---
    # Math Italic Capital A–Z: U+1D434–U+1D44D
    for i in range(26):
        a[0x1D434 + i] = 0x0041 + i
    # Math Italic Small a–z: U+1D44E–U+1D467 (U+1D455 is a Unicode hole)
    for i in range(26):
        src = 0x1D44E + i
        if src != 0x1D455:
            a[src] = 0x0061 + i
    # Special TeX italic substitutes used where the standard slot is a hole
    a[0x210E] = ord('h')  # PLANCK CONSTANT ℎ → h
    a[0x210F] = ord('h')  # PLANCK CONSTANT OVER TWO PI ℏ → h (no hbar glyph)
    a[0x2113] = ord('l')  # SCRIPT SMALL L ℓ → l
    a[0x03D5] = 0x03C6    # GREEK PHI SYMBOL ϕ → φ (closest available)

    # Math Bold Capital A–Z: U+1D400–U+1D419
    for i in range(26):
        a[0x1D400 + i] = 0x0041 + i
    # Math Bold Small a–z: U+1D41A–U+1D433
    for i in range(26):
        a[0x1D41A + i] = 0x0061 + i

    # Math Bold Italic Capital A–Z: U+1D468–U+1D481
    for i in range(26):
        a[0x1D468 + i] = 0x0041 + i
    # Math Bold Italic Small a–z: U+1D482–U+1D49B
    for i in range(26):
        a[0x1D482 + i] = 0x0061 + i

    # Math Bold digits 0–9: U+1D7CE–U+1D7D7
    for i in range(10):
        a[0x1D7CE + i] = 0x0030 + i

    # --- Greek: italic and bold variants ---
    # Sequence follows the Unicode math Greek blocks exactly, including the
    # capital-theta-symbol slot at position 17 (aliased back to plain theta).
    GREEK_UPPER = [
        0x0391, 0x0392, 0x0393, 0x0394, 0x0395, 0x0396, 0x0397,
        0x0398,                                  # Θ (theta)
        0x0399, 0x039A, 0x039B, 0x039C, 0x039D, 0x039E, 0x039F,
        0x03A0,                                  # Π
        0x03A1,                                  # Ρ
        0x0398,                                  # ϴ capital theta symbol → Θ
        0x03A3,                                  # Σ (skips non-existent 03A2)
        0x03A4, 0x03A5, 0x03A6, 0x03A7, 0x03A8,
        0x03A9,                                  # Ω
    ]
    GREEK_LOWER = [
        0x03B1, 0x03B2, 0x03B3, 0x03B4, 0x03B5, 0x03B6, 0x03B7,
        0x03B8,                                  # θ
        0x03B9, 0x03BA, 0x03BB, 0x03BC, 0x03BD, 0x03BE, 0x03BF,
        0x03C0,                                  # π
        0x03C1,                                  # ρ
        0x03C2,                                  # ς (final sigma)
        0x03C3,                                  # σ
        0x03C4, 0x03C5, 0x03C6, 0x03C7, 0x03C8,
        0x03C9,                                  # ω
    ]

    # Math Italic Capital Greek: U+1D6E2–U+1D6FA (25 chars)
    for i, cp in enumerate(GREEK_UPPER):
        a[0x1D6E2 + i] = cp
    # Math Italic Small Greek: U+1D6FC–U+1D714 (25 chars)
    for i, cp in enumerate(GREEK_LOWER):
        a[0x1D6FC + i] = cp
    # Math Italic Greek variants (∂, ϵ, θ-symbol, κ-symbol, φ-symbol, ρ-symbol, π-symbol)
    a[0x1D715] = 0x2202  # ∂ partial differential
    a[0x1D716] = 0x03F5  # ϵ epsilon symbol
    a[0x1D717] = 0x03B8  # θ theta symbol
    a[0x1D718] = 0x03BA  # κ kappa symbol
    a[0x1D719] = 0x03C6  # φ phi symbol
    a[0x1D71A] = 0x03C1  # ρ rho symbol
    a[0x1D71B] = 0x03C0  # π pi symbol

    # Math Bold Capital Greek: U+1D6A8–U+1D6C0 (25 chars)
    for i, cp in enumerate(GREEK_UPPER):
        a[0x1D6A8 + i] = cp
    # Math Bold Small Greek: U+1D6C2–U+1D6DA (25 chars)
    for i, cp in enumerate(GREEK_LOWER):
        a[0x1D6C2 + i] = cp

    return a


def build_operator_glyphs(ff_font):
    """Create/resize large-operator glyphs to match MathJax Size1 font proportions.

    MathJax CHTML uses the same Unicode codepoints for both inline and display-mode
    large operators — display-mode sizing is achieved via CSS font-size scaling plus
    different glyph metrics in MJXTEX-S1.  Our !important font-family override
    intercepts Size1 usage, so we supply glyphs with appropriate metrics here.

    Tuning knobs (adjust and rebuild to iterate):
      MATH_AXIS   — module-level constant; y-position of the math axis in xkcd-script.
      OP_WEIGHT   — stroke thinning for ∑ and ∏ after scale-up (negative = thinner).
      INTEGRAL_H  — display-mode ∫ height in font units.  Current xkcd ∫ is 951
                    (≈1.11 × UPM); Size1 fonts target ≈1.4–1.6 × UPM.
    """
    upem = ff_font.em  # 856

    OP_WEIGHT = -20
    INTEGRAL_H = round(1.4 * upem)  # ≈ 1198

    def _make_largeop(src_cp, dst_cp, dst_name, target_h, weight=0, rbear=0):
        """Scale src to target_h, optionally thin strokes, centre on MATH_AXIS.

        rbear: right bearing in font units (advance = right glyph edge + rbear).
               Note: MathJax CHTML ignores the font advance width — it pre-bakes
               character widths from its own JS metric tables, so rbear only
               affects non-MathJax uses.  Inline limit spacing in MathJax is
               controlled via CSS margin-right in mathjax-demo.html instead.
        """
        ff_font.selection.select(src_cp)
        ff_font.copy()
        try:
            g = ff_font[dst_cp]
            g.clear()
        except TypeError:
            g = ff_font.createChar(dst_cp, dst_name)
        ff_font.selection.select(dst_cp)
        ff_font.paste()
        g = ff_font[dst_cp]

        bb = g.boundingBox()
        scale = target_h / (bb[3] - bb[1])
        g.transform(psMat.scale(scale))

        if weight != 0:
            g.correctDirection()
            g.removeOverlap()
            g.changeWeight(weight)
            g.correctDirection()
            g.addExtrema()

        # Centre the glyph's y-midpoint on MATH_AXIS so display-mode operators
        # straddle the text baseline and MathJax places limits at expected positions.
        bb2 = g.boundingBox()
        g.transform(psMat.translate(0, MATH_AXIS - (bb2[3] + bb2[1]) / 2))

        bb3 = g.boundingBox()
        g.width = round(bb3[2] + rbear)

        print(f"  U+{dst_cp:04X} ({dst_name}): scale={scale:.3f} weight={weight} "
              f"bounds={g.boundingBox()} advance={g.width}")

    # ∑ (U+2211): Σ scaled to 1.0 × UPM, strokes thinned, centred on math axis
    _make_largeop(0x03A3, 0x2211, 'summation', upem, weight=OP_WEIGHT, rbear=20)
    # ∏ (U+220F): Π scaled to 1.0 × UPM, strokes thinned, centred on math axis
    _make_largeop(0x03A0, 0x220F, 'product',   upem, weight=OP_WEIGHT, rbear=5000)
    # ∫ (U+222B): existing xkcd ∫ scaled to INTEGRAL_H, strokes thinned, centred
    _make_largeop(0x222B, 0x222B, 'integral', INTEGRAL_H, weight=-15,  rbear=5000)


def build_sqrt_glyphs(ff_font):
    """Replace U+221A with hand-drawn surd; add U+E221 as the full long sqrt.

    Source: potrace of 2343_mathematical_symbol_fight_2x__long_sqrt.png
    (170×61 px, potrace space 1700×610 units, Y-up convention).

    Coordinate transform (potrace → font units, UPM=856):
        font_x = round(x_pot * 0.65 + 20)
        font_y = round(y_pot * 1.228 − 101)

    U+221A: surd stroke only (potrace segs 1–11), closed with a straight bar
    cap back to the start — the horizontal overline is handled by CSS in
    mathjax-demo.html.

    U+E221: the complete surd+bar shape (segs 1–16, closes naturally at M).
    Wide advance width so the glyph extends visually to the right.
    """
    SX, OX = 0.65, 20
    SY, OY = 1.228, -101

    def tx(x): return round(x * SX + OX)
    def ty(y): return round(y * SY + OY)

    def draw_surd(pen, close_with_bar):
        """Potrace segs 1–11: the surd tick + ascending stroke."""
        pen.moveTo((tx(845), ty(602)))
        pen.curveTo((tx(844), ty(601)), (tx(727), ty(598)), (tx(586), ty(597)))
        pen.curveTo((tx(377), ty(595)), (tx(327), ty(591)), (tx(316), ty(580)))
        pen.curveTo((tx(305), ty(568)), (tx(269), ty(462)), (tx(254), ty(400)))
        pen.curveTo((tx(237), ty(323)), (tx(165), ty(101)), (tx(160), ty(107)))
        pen.curveTo((tx(156), ty(112)), (tx(142), ty(135)), (tx(129), ty(160)))
        pen.curveTo((tx( 95), ty(224)), (tx( 70), ty(252)), (tx( 55), ty(240)))
        pen.curveTo((tx( 45), ty(232)), (tx( 55), ty(203)), (tx( 97), ty(120)))
        pen.curveTo((tx(127), ty( 59)), (tx(155), ty( 10)), (tx(158), ty( 10)))
        pen.curveTo((tx(172), ty( 10)), (tx(186), ty( 26)), (tx(198), ty( 53)))
        pen.curveTo((tx(208), ty( 76)), (tx(283), ty(325)), (tx(332), ty(500)))
        pen.curveTo((tx(337), ty(519)), (tx(346), ty(539)), (tx(350), ty(544)))
        if close_with_bar:
            pen.lineTo((tx(350), ty(602)))
            pen.closePath()

    def draw_bar(pen):
        """Potrace segs 12–16: bar extending right, closing back to M(845,602)."""
        pen.curveTo((tx( 355), ty(549)), (tx( 656), ty(554)), (tx(1020), ty(555)))
        pen.curveTo((tx(1384), ty(557)), (tx(1684), ty(560)), (tx(1687), ty(563)))
        pen.curveTo((tx(1690), ty(566)), (tx(1689), ty(577)), (tx(1686), ty(587)))
        pen.curveTo((tx(1681), ty(604)), (tx(1658), ty(605)), (tx(1264), ty(605)))
        pen.curveTo((tx(1036), ty(605)), (tx( 847), ty(604)), (tx( 845), ty(602)))
        pen.closePath()

    def draw_serif(pen):
        """Small left serif stroke (potrace path 1)."""
        pen.moveTo((tx(0), ty(467)))
        pen.curveTo((tx( 0), ty(430)), (tx( 3), ty(400)), (tx( 8), ty(400)))
        pen.curveTo((tx(17), ty(400)), (tx(17), ty(516)), (tx( 7), ty(526)))
        pen.curveTo((tx( 3), ty(530)), (tx( 0), ty(503)), (tx( 0), ty(467)))
        pen.closePath()

    # --- U+221A: surd only ---
    g = ff_font[0x221A]
    g.clear()
    pen = g.glyphPen()
    draw_surd(pen, close_with_bar=True)
    draw_serif(pen)
    del pen
    g.correctDirection()
    g.removeOverlap()
    g.addExtrema()
    g.width = 570
    print(f"  U+221A (radical): bounds={g.boundingBox()}, advance={g.width}")

    # --- U+E221: full long sqrt ---
    try:
        glong = ff_font[0xE221]
        glong.clear()
    except TypeError:
        glong = ff_font.createChar(0xE221, 'longsqrt')
    pen2 = glong.glyphPen()
    draw_surd(pen2, close_with_bar=False)
    draw_bar(pen2)
    draw_serif(pen2)
    del pen2
    glong.correctDirection()
    glong.removeOverlap()
    glong.addExtrema()
    glong.width = tx(1750)
    print(f"  U+E221 (longsqrt): bounds={glong.boundingBox()}, advance={glong.width}")


def build_misc_glyphs(ff_font):
    """Create U+22C5 (⋅, cdot): period scaled to 75%, centred on math axis."""
    ff_font.selection.select(ord('.'))
    ff_font.copy()
    try:
        g = ff_font[0x22C5]
        g.clear()
    except TypeError:
        g = ff_font.createChar(0x22C5, 'cdot')
    ff_font.selection.select(0x22C5)
    ff_font.paste()
    g = ff_font[0x22C5]

    TARGET_W = 220
    g.transform(psMat.scale(0.75))
    bb = g.boundingBox()
    cx = (bb[0] + bb[2]) / 2
    cy = (bb[1] + bb[3]) / 2
    g.transform(psMat.translate(TARGET_W / 2 - cx, MATH_AXIS - cy))
    g.correctDirection()
    g.addExtrema()
    g.width = TARGET_W
    print(f"  U+22C5 (cdot): bounds={g.boundingBox()}, advance={g.width}")



# ── Phase A: fontforge — glyph editing ────────────────────────────────────────
_tmp = tempfile.NamedTemporaryFile(suffix='.otf', delete=False)
FONT_TEMP = _tmp.name
_tmp.close()

ff_font = fontforge.open(FONT_IN)
build_operator_glyphs(ff_font)
build_sqrt_glyphs(ff_font)
build_misc_glyphs(ff_font)
ff_font.generate(FONT_TEMP, flags=('opentype',))
ff_font.close()
print(f"Phase A complete: intermediate OTF at {FONT_TEMP}")

# ── Phase B: fontTools — cmap aliases + WOFF output ───────────────────────────
font = TTFont(FONT_TEMP)
base_cmap = font.getBestCmap()
aliases = build_aliases()

added = 0
skipped = 0
for src_cp, dst_cp in sorted(aliases.items()):
    glyph = base_cmap.get(dst_cp)
    if not glyph:
        print(f"  skip U+{dst_cp:04X} ({chr(dst_cp)!r}): no glyph in source font")
        skipped += 1
        continue
    for t in font['cmap'].tables:
        if t.format == 4 and src_cp <= 0xFFFF:
            t.cmap[src_cp] = glyph
        elif t.format == 12:
            t.cmap[src_cp] = glyph
    added += 1

print(f"Added {added} aliases ({skipped} skipped — no source glyph)")

font.flavor = 'woff'
font.save(FONT_OUT)
os.unlink(FONT_TEMP)
print(f"Saved {FONT_OUT}")
