# -*- coding: utf-8 -*-
"""
MathJax 3 delta-overlay font.  Starts from the base SFD produced by pt7 and
writes ../generated/xkcd-script-mathjax3-pt8.sfd, which pt9 then subsets to
the WOFF that's loaded alongside xkcd-script in the browser font-stack.

Targets MathJax 3 specifically.  MathJax 4 has additional font-handling
extensibility hooks that may reduce the need for the CSS overrides in
xkcd-mathjax3.js — a separate pt8b_mathjax4.py / xkcd-mathjax4.js pair
would supersede this if/when that work happens.

Does two things:

  1. Overrides ∑ / ∏ / ∫ with display-sized large operators (the inline
     forms in the base font are too small for MathJax display mode).
  2. Extracts extensible-glyph outline data (emdash, radical, uniE000)
     from the SFD and splices it into ../xkcd-mathjax3.js between the
     GENERATED markers.  The browser-side cut-and-extend renderer uses
     those outlines at runtime, so they have to travel with the font.

The U+1D400-block math cmap aliases (math italic / bold / Greek) are NOT
here — they live in pt6 (base font), reached via the font-fallback chain.
Putting them here instead would force this WOFF to ship the source
Latin/Greek outlines too, bloating it.

This file deliberately does NOT carry per-codepoint metric tweaks.
MathJax 3 CHTML uses pre-baked per-codepoint metric tables in its own JS;
it ignores the font's advance widths and OT MATH italic-correction values
at runtime.  Verified empirically: a +400 font-unit advance bump on
math-italic g produced zero visible change in product-rule.png.  All
positional adjustments for MathJax-rendered math therefore live as CSS
overrides in xkcd-mathjax3.js, not here.
"""
import fontforge
import psMat
import json
import re


BASE_SFD = '../generated/xkcd-script-pt7.sfd'
OUT_SFD  = '../generated/xkcd-script-mathjax3-pt8.sfd'

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
               controlled via CSS margin-right in xkcd-mathjax3.js instead.
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


print(f"=== Building {OUT_SFD} ===")
font = fontforge.open(BASE_SFD)
add_mathjax_operators(font)
font.save(OUT_SFD)
font.close()
print(f"  saved {OUT_SFD}")


# ---------------------------------------------------------------------------
# Extensible-glyph data for xkcd-mathjax3.js
# ---------------------------------------------------------------------------
#
# The runtime renderer in xkcd-mathjax3.js takes each glyph's outline, applies
# a coordinate-threshold extension (shift points past cutX by Nx, splice
# jittered cubic sub-segments across the gap; same for cutY along an axis
# optionally tilted by leanDeg), and produces an SVG path sized to the
# requested overlay.  Per-glyph parameters live here so they travel with
# the font: when the font is rebuilt this step regenerates the embedded
# data and the renderer picks up the new shapes without code changes.

EXTENSIBLE_MARKER_BEGIN = '// ── BEGIN GENERATED GLYPH DATA ──'
EXTENSIBLE_MARKER_END   = '// ── END GENERATED GLYPH DATA ──'
MATHJAX_JS = '../xkcd-mathjax3.js'

# cutXPct / cutYPct : cut threshold as % of bbox along that axis
# leanDeg           : Y-extension axis lean from vertical (deg)
# unitsPerSeg       : sub-segment density along the inserted gap
# amp               : jitter amplitude in font units
EXTENSIBLE_CONFIG = {
    'emdash':  {'cutXPct': 50, 'cutYPct': 50, 'leanDeg':  0.0, 'unitsPerSeg': 120, 'amp':  4},
    'radical': {'cutXPct': 70, 'cutYPct': 50, 'leanDeg':  0.0, 'unitsPerSeg':  60, 'amp':  5},
    'uniE000': {'cutXPct': 56, 'cutYPct': 45, 'leanDeg': -2.0, 'unitsPerSeg':  45, 'amp':  3},
}


def _extract_commands(g):
    """Walk a FontForge glyph's foreground contours and emit a list of
    SVG-style commands: ['M',x,y] / ['L',x,y] / ['C',x1,y1,x2,y2,x,y] /
    ['Z'].  xkcd-script outlines are cubic-only so we don't emit Q."""
    cmds = []
    for contour in g.foreground:
        pts = list(contour)
        n = len(pts)
        if n == 0:
            continue
        # Start at an on-curve point so the moveTo lands on the actual path.
        start = 0
        for i, p in enumerate(pts):
            if p.on_curve:
                start = i; break
        pts = pts[start:] + pts[:start]
        cmds.append(['M', round(pts[0].x, 1), round(pts[0].y, 1)])
        i = 1
        while i < n:
            p = pts[i]
            if p.on_curve:
                cmds.append(['L', round(p.x, 1), round(p.y, 1)])
                i += 1
            else:
                # Cubic: two off-curve control points then the next on-curve.
                c1 = pts[i]
                c2 = pts[(i + 1) % n]
                end = pts[(i + 2) % n]
                cmds.append(['C',
                             round(c1.x, 1),  round(c1.y, 1),
                             round(c2.x, 1),  round(c2.y, 1),
                             round(end.x, 1), round(end.y, 1)])
                i += 3
        if contour.closed:
            cmds.append(['Z'])
    return cmds


def _bbox(cmds):
    xs, ys = [], []
    for c in cmds:
        for i in range(1, len(c), 2):
            xs.append(c[i]); ys.append(c[i + 1])
    return {'xmin': min(xs), 'ymin': min(ys),
            'xmax': max(xs), 'ymax': max(ys)}


def _as_js(data):
    """Stable, diff-friendly JS literal: one glyph per top-level key,
    one command per line, numbers as JSON."""
    lines = ['const EXTENSIBLE_GLYPHS = {']
    for name, g in data.items():
        bb  = g['bbox']
        cfg = g['config']
        lines.append('        %s: {' % name)
        lines.append('            advance: %s,' % g['advance'])
        lines.append('            bbox: {xmin: %s, ymin: %s, xmax: %s, ymax: %s},'
                     % (bb['xmin'], bb['ymin'], bb['xmax'], bb['ymax']))
        lines.append('            config: {cutXPct: %s, cutYPct: %s, leanDeg: %s, unitsPerSeg: %s, amp: %s},'
                     % (cfg['cutXPct'], cfg['cutYPct'], cfg['leanDeg'], cfg['unitsPerSeg'], cfg['amp']))
        lines.append('            commands: [')
        for cmd in g['commands']:
            lines.append('                ' + json.dumps(cmd) + ',')
        lines.append('            ],')
        lines.append('        },')
    lines.append('    };')
    return '\n'.join(lines)


def _splice_into_mathjax(js_path, generated):
    with open(js_path, 'r', encoding='utf-8') as f:
        src = f.read()
    pat = re.compile(re.escape(EXTENSIBLE_MARKER_BEGIN) + r'.*?' +
                     re.escape(EXTENSIBLE_MARKER_END), re.DOTALL)
    if not pat.search(src):
        raise SystemExit(
            f"marker block not found in {js_path}; expected lines:\n"
            f"  {EXTENSIBLE_MARKER_BEGIN}\n  {EXTENSIBLE_MARKER_END}")
    block = '%s\n    %s\n    %s' % (
        EXTENSIBLE_MARKER_BEGIN,
        generated.replace('\n', '\n    '),
        EXTENSIBLE_MARKER_END)
    new_src = pat.sub(lambda m: block, src)
    if new_src == src:
        print(f"  {js_path}: unchanged")
        return
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(new_src)
    print(f"  {js_path}: updated")


def export_extensible_glyphs():
    print(f"=== Extracting extensible-glyph data from {BASE_SFD} ===")
    font = fontforge.open(BASE_SFD)
    data = {}
    for name, cfg in EXTENSIBLE_CONFIG.items():
        if name not in font:
            raise SystemExit(f"glyph {name!r} not in {BASE_SFD}")
        g = font[name]
        cmds = _extract_commands(g)
        data[name] = {
            'advance':  g.width,
            'bbox':     _bbox(cmds),
            'config':   cfg,
            'commands': cmds,
        }
        bb = data[name]['bbox']
        print(f"  {name}: advance={g.width} "
              f"bbox=[{bb['xmin']:.0f},{bb['ymin']:.0f},{bb['xmax']:.0f},{bb['ymax']:.0f}] "
              f"cmds={len(cmds)}")
    font.close()
    print(f"=== Splicing into {MATHJAX_JS} ===")
    _splice_into_mathjax(MATHJAX_JS, _as_js(data))


export_extensible_glyphs()
