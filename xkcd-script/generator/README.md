# xkcd-script font generation pipeline

Each script runs in order inside the `fontbuilder` Docker image; `run.sh` orchestrates them and accepts an optional starting step (`./run.sh 5` skips pt1–pt4).

## Stages

| # | Script | What it does |
|---|---|---|
| 1 | `pt1_character_extraction.py` | Extract character strokes from `handwriting_minimal.png` (scikit-image). |
| 2 | `pt2_character_classification.py` | Cluster strokes into lines (k-means, fixed seed). |
| 3 | `pt3_ppm_to_svg.py` | Convert per-character PPM → SVG via `potrace`. |
| 4 | `pt4_additional_sources.py` | Trace extra glyphs from comic panels and `extras/`. |
| 5 | `pt5_svg_to_font.py` | Import SVG glyphs into a FontForge SFD; apply stroke normalisation, weight nudges, math-symbol imports. |
| 6 | `pt6_derived_chars.py` | Build derived/composed glyphs: diacritics, ligatures, Greek, IPA, combining marks, math cmap aliases (U+1D400 block via altuni). |
| 7 | `pt7_font_properties.py` | Apply kerning, GPOS anchors, pin CFF hints and OS/2 metrics. Output is `xkcd-script-pt7.sfd` — the **base** font used for everything downstream. |
| 8 | `pt8_derivatives.py` | Orchestrator. Runs each `pt8X_*.py` derivative step in turn. |
| 9 | `pt9_gen_reprod_font.py` | Scrub the SFD for reproducibility, freeze CFF charstrings, generate committed binaries (otf/ttf/woff). |

## Derivatives (pt8)

`pt7` produces a single kitchen-sink base SFD with everything — Latin, Greek, math symbols and aliases, ligatures, combining marks. Each `pt8X_<name>.py` reads that base and either writes its own derivative SFD or extracts data from it to splice elsewhere; `pt8_derivatives.py` runs them with `runpy`.

Today there is no live derivative font: the sole entry, `pt8a_mathjax3.py`, only extracts extensible-glyph outline data into `../xkcd-mathjax3.js`. The display-sized large operators that used to live in a separate mathjax3 WOFF are now stylistic alternates in the base font (`ss01`).

Because derivatives can only subtract or overlay what pt7 already has, **everything plausibly useful belongs in pt7**. Don't pre-strip pt7 for size — that loses the subtractive option.
