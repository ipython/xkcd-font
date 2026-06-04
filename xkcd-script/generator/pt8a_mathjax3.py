# -*- coding: utf-8 -*-
"""
Extracts extensible-glyph outline data (emdash, radical, uniE000) from
pt7's SFD and splices it into ../xkcd-mathjax3.js between the GENERATED
markers.  The browser-side cut-and-extend renderer uses those outlines at
runtime, so they have to travel with the font.

Reserves the pt8a_ slot for future MathJax-3-specific derivative work.
"""
import fontforge
import json
import re


BASE_SFD = '../generated/xkcd-script-pt7.sfd'


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
