#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate one deterministic character-map PNG per Unicode block for xkcd-script.

Each codepoint occupies a fixed grid cell within its block, so successive PNG
diffs immediately show which characters were added or changed.

  White cell  — glyph present in the font
  Red cell    — codepoint is an ordinary printable character but missing from font
  Grey cell   — control / non-printable codepoint (not expected in font)
"""
import os
import re
import unicodedata

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.font_manager import FontProperties
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
OTF  = os.path.join(HERE, '../font/xkcd-script.otf')
OUTDIR = HERE   # PNGs go in samples/ alongside this script

# ---------------------------------------------------------------------------
# Which codepoints does the font contain?
# ---------------------------------------------------------------------------
tt = TTFont(OTF)
present = set(tt.getBestCmap() or {})

# ---------------------------------------------------------------------------
# Codepoint ranges shown in the grid (fixed — defines cell positions).
# Each entry: (first codepoint inclusive, last exclusive, block label).
# Rows are automatically aligned to 16-codepoint boundaries.
# ---------------------------------------------------------------------------
BLOCKS = [
    (0x0020, 0x0080, "Basic Latin"),
    (0x00A0, 0x0100, "Latin-1 Supplement"),
    (0x0100, 0x0180, "Latin Extended-A"),
    (0x0180, 0x0250, "Latin Extended-B"),
    (0x0300, 0x0370, "Combining Diacritical Marks"),
    (0x2018, 0x2040, "General Punctuation"),
    (0x2190, 0x2200, "Arrows"),
    (0x2200, 0x2300, "Mathematical Operators"),
]

COLS = 16
COMBINING_CATS = {'Mn', 'Mc', 'Me'}

# Any font glyphs not covered by the defined blocks go in a catch-all block.
block_covered = set()
for start, end, _ in BLOCKS:
    block_covered.update(range(start, end))
extras = sorted(cp for cp in present if cp not in block_covered)
if extras:
    BLOCKS = list(BLOCKS) + [(None, None, "Non-Latin / Other")]

# ---------------------------------------------------------------------------
# Layout constants (shared across all figures)
# ---------------------------------------------------------------------------
CELL_W   = 0.52   # inches per cell (width)
CELL_H   = 0.50   # inches per cell (height)
LABEL_W  = 0.90   # inches for the row-label column
HEADER_H = 0.32   # inches for the column-header row
LEGEND_H = 0.40   # inches for the legend strip at the bottom
PAD      = 0.035  # gap around each cell (inches)

LEGEND_ITEMS = [
    ('#FFFFFF', '#111111', 'glyph present'),
    ('#FFE0E0', '#CC2222', 'missing (printable)'),
    ('#E6E6E6', '#888888', 'control / non-printable'),
]


def slugify(label):
    return re.sub(r'[^a-z0-9]+', '_', label.lower()).strip('_')


def block_rows(start, end):
    """Return ordered list of (label_or_None, [codepoints]) for a block."""
    rows = []
    row_base = (start // COLS) * COLS
    row_end  = ((end - 1) // COLS + 1) * COLS
    first = True
    for base in range(row_base, row_end, COLS):
        rows.append(list(range(base, base + COLS)))
        first = False
    return rows


def extras_rows():
    """Rows for codepoints not covered by any defined block."""
    return [extras[i:i + COLS] for i in range(0, len(extras), COLS)]


def render_block(label, rows):
    """Render one block as a figure and return it."""
    n_rows = len(rows)
    fig_w  = LABEL_W + COLS * CELL_W
    fig_h  = HEADER_H + n_rows * CELL_H + LEGEND_H

    fig = plt.figure(figsize=(fig_w, fig_h), dpi=150)
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis('off')
    fig.patch.set_facecolor('#F5F5F5')

    fp_xkcd = FontProperties(fname=OTF, size=9.5)
    fp_mono = FontProperties(family='monospace', size=6.5)
    fp_tiny = FontProperties(family='monospace', size=5.5)

    # Column headers 0–F
    for col in range(COLS):
        x = LABEL_W + (col + 0.5) * CELL_W
        y = fig_h - HEADER_H * 0.5
        ax.text(x, y, f'{col:X}',
                ha='center', va='center', fontproperties=fp_mono, color='#888888')

    # Block name — rotated 90°, centred vertically across all rows
    name_x = 0.18
    name_y = fig_h - HEADER_H - (n_rows * CELL_H) / 2
    ax.text(name_x, name_y, label,
            ha='center', va='center', fontproperties=fp_tiny, color='#555555',
            rotation=90)

    # Grid rows
    for row_idx, cps in enumerate(rows):
        y_top    = fig_h - HEADER_H - row_idx * CELL_H
        y_bottom = y_top - CELL_H
        y_center = (y_top + y_bottom) / 2

        hex_tag = f'U+{cps[0]:04X}' if cps else ''
        ax.text(LABEL_W - 0.05, y_center, hex_tag,
                ha='right', va='center', fontproperties=fp_tiny, color='#555555')

        for col, cp in enumerate(cps):
            x_left   = LABEL_W + col * CELL_W
            x_center = x_left + CELL_W / 2

            try:
                cat = unicodedata.category(chr(cp))
            except (ValueError, OverflowError):
                cat = 'Cn'

            is_control = cat in ('Cc', 'Cn', 'Cs')
            is_present = cp in present

            if is_control:
                bg, fg = '#E6E6E6', None
            elif is_present:
                bg, fg = '#FFFFFF', '#111111'
            else:
                bg, fg = '#FFE0E0', '#CC2222'

            rect = mpatches.FancyBboxPatch(
                (x_left + PAD, y_bottom + PAD),
                CELL_W - 2 * PAD, CELL_H - 2 * PAD,
                boxstyle='round,pad=0.01', linewidth=0,
                facecolor=bg, zorder=1)
            ax.add_patch(rect)

            if fg is None:
                continue

            if is_present:
                ch = ('\u25CC' + chr(cp)) if cat in COMBINING_CATS else chr(cp)
                ax.text(x_center, y_center, ch,
                        ha='center', va='center',
                        fontproperties=fp_xkcd, color=fg, zorder=2)
            else:
                ax.text(x_center, y_center, '?',
                        ha='center', va='center',
                        fontproperties=fp_mono, color=fg, fontsize=5.5, zorder=2)

    # Legend
    ly = LEGEND_H / 2
    lx = LABEL_W
    for bg, fg, text in LEGEND_ITEMS:
        swatch = mpatches.FancyBboxPatch(
            (lx, ly - CELL_H * 0.3), CELL_W * 0.7, CELL_H * 0.6,
            boxstyle='round,pad=0.01', linewidth=0, facecolor=bg)
        ax.add_patch(swatch)
        ax.text(lx + CELL_W * 0.85, ly, text,
                ha='left', va='center', fontproperties=fp_tiny, color='#444444')
        lx += CELL_W * 0.7 + len(text) * CELL_W * 0.19 + CELL_W * 0.3

    return fig


# ---------------------------------------------------------------------------
# Render one PNG per block
# ---------------------------------------------------------------------------
for start, end, label in BLOCKS:
    rows = block_rows(start, end) if start is not None else extras_rows()
    if not rows:
        continue
    fig = render_block(label, rows)
    out = os.path.join(OUTDIR, f'charmap_{slugify(label)}.png')
    fig.savefig(out, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'charmap → {out}')
