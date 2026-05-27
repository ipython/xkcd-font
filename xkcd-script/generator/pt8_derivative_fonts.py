# -*- coding: utf-8 -*-
"""
Build derivative font variants by mutating the base SFD produced by pt7.

Each variant gets its own SFD output in ../generated/, which pt9 then
normalises and converts into the committed binary font files.

Currently produces:
  xkcd-script-mathjax-pt8.sfd
    — pt7 + three display-sized large operators (∑, ∏, ∫) overriding the
      inline forms.  Everything else MathJax needs (math italic / bold cmap
      aliases, the cdot, the hand-drawn √ surd) lives in the main
      xkcd-script font (added in pt6) and is reached via font-fallback in
      xkcd-mathjax.js.

To add a new derivative font: write a builder function that mutates an
open SFD in place, then append it to VARIANTS.  pt9 will pick it up
automatically as long as its sfd_in matches what's written here.
"""
import fontforge
import psMat


BASE_SFD = '../generated/xkcd-script-pt7.sfd'

# y-position of the math axis (fraction-bar centre) in xkcd-script font units.
MATH_AXIS = 260


# ---------------------------------------------------------------------------
# MathJax: display-sized large operators
# ---------------------------------------------------------------------------

def add_mathjax_operators(ff_font):
    """Override ∑, ∏, ∫ with display-mode-sized glyphs.

    MathJax CHTML uses the same Unicode codepoints for both inline and
    display-mode large operators — display-mode sizing is achieved via CSS
    font-size scaling plus different glyph metrics in MJXTEX-S1.  Our
    !important font-family override intercepts Size1 usage, so we supply
    glyphs with appropriate metrics here.

    Tuning knobs (adjust and rebuild to iterate):
      MATH_AXIS   — module-level constant; y-position of the math axis.
      OP_WEIGHT   — stroke thinning for ∑/∏ after scale-up (negative = thinner).
      INTEGRAL_H  — display-mode ∫ height in font units.  Current xkcd ∫ is
                    951 (≈1.11 × UPM); Size1 fonts target ≈1.4–1.6 × UPM.
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
               controlled via CSS margin-right in xkcd-mathjax.js instead.
        """
        # Snapshot outlines + width before touching dst; src and dst point to
        # the same glyph when src_cp == dst_cp (e.g. ∫ scaled in place).
        src = ff_font[src_cp]
        src_layer = fontforge.layer()
        for c in src.foreground:
            src_layer += c
        src_width = src.width

        try:
            g = ff_font[dst_cp]
            g.clear()
        except TypeError:
            g = ff_font.createChar(dst_cp, dst_name)

        g.foreground = src_layer
        g.width = src_width

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


# ---------------------------------------------------------------------------
# Variants table
# ---------------------------------------------------------------------------

VARIANTS = [
    ('xkcd-script-mathjax-pt8.sfd', add_mathjax_operators),
]


for out_name, builder in VARIANTS:
    out_path = '../generated/' + out_name
    print(f"=== Building {out_name} ===")
    font = fontforge.open(BASE_SFD)
    builder(font)
    font.save(out_path)
    font.close()
    print(f"  saved {out_path}")
