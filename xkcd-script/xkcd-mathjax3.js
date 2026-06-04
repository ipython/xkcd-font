/**
 * xkcd-mathjax3 — render MathJax 3 CHTML output with xkcd-script fonts and
 * hand-drawn sqrt / fraction-bar overlays.
 *
 * Drop this script on a page that already loads MathJax 3 (CHTML).  It loads
 * xkcd-script.woff from a URL resolved relative to its own src, injects the
 * font-override CSS, and hooks MathJax's startup so the initial typeset is
 * post-processed.  Works whether MathJax loads before or after this script.
 *
 * ── Usage (plain HTML) ──────────────────────────────────────────────────────
 *   <!-- 1. Optional MathJax config (tex delimiters, etc) — set FIRST -->
 *   <script>MathJax = { tex: { inlineMath: [['$','$']] } };</script>
 *   <!-- 2. Then this script: it merges its startup hook into MathJax config -->
 *   <script src="path/to/xkcd-mathjax3.js"></script>
 *   <!-- 3. Then MathJax itself, async -->
 *   <script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
 *
 * ── Usage (Jupyter / JupyterLab, which ships its own MathJax 3) ─────────────
 *   from IPython.display import HTML, display
 *   display(HTML('<script src="https://your-host/xkcd-mathjax3.js"></script>'))
 *   # Then any subsequent Markdown / Latex cells render with xkcd-script.
 *
 * ── Public API on window.XkcdMathJax ────────────────────────────────────────
 *   refresh(root?)       — re-run sqrt / vinculum overlay placement.  Call
 *                          after any MathJax.typesetPromise() of dynamic
 *                          content.  Idempotent.
 *   ready                — Promise that resolves once the initial typeset and
 *                          first overlay pass have completed.
 *   resetOverlays(root?) — strip overlays + restore hidden elements (used
 *                          internally on resize; exposed for advanced use).
 *
 * ── Configuration (optional) ────────────────────────────────────────────────
 *   Set BEFORE loading this script:
 *     window.XkcdMathJaxConfig = { fontBase: 'https://your-host/fonts/' };
 *   fontBase is prepended to the woff filenames.  If unset, fonts are loaded
 *   relative to this script's own src (assumes font/*.woff sits next to it).
 */
(function () {
    'use strict';

    // ── Locate our own URL so we can resolve sibling woff files ─────────────
    const cfg = window.XkcdMathJaxConfig || {};
    function _scriptBase() {
        if (cfg.fontBase) return cfg.fontBase;
        const cur = document.currentScript;
        if (cur && cur.src) {
            return cur.src.replace(/[^/]*$/, '') + 'font/';
        }
        // Fallback: locate any <script> whose src ends in xkcd-mathjax3.js
        for (const s of document.scripts) {
            if (s.src && /xkcd-mathjax3(\.min)?\.js(\?|$)/.test(s.src)) {
                return s.src.replace(/[^/]*$/, '') + 'font/';
            }
        }
        return 'font/';
    }
    const FONT_BASE = _scriptBase();

    // ── @font-face injection ────────────────────────────────────────────────
    function _injectFontFaces() {
        const s = document.createElement('style');
        s.textContent = `
            @font-face {
                font-family: 'xkcd-script';
                src: url('${FONT_BASE}xkcd-script.woff') format('woff');
            }`;
        document.head.appendChild(s);
    }
    _injectFontFaces();

    // ── BEGIN GENERATED GLYPH DATA ──
    const EXTENSIBLE_GLYPHS = {
            "emdash": {
                advance: 747,
                bbox: {xmin: -4.0, ymin: 194.0, xmax: 727.0, ymax: 294.0},
                config: {cutXPct: 50, cutYPct: 50, leanDeg: 0.0, unitsPerSeg: 120, amp: 4},
                commands: [
                    ["M", 203.0, 276.0],
                    ["C", 326.0, 276.0, 584.0, 282.0, 588.0, 282.0],
                    ["L", 655.0, 282.0],
                    ["C", 662.0, 291.0, 662.0, 291.0, 681.0, 293.0],
                    ["C", 697.0, 294.0, 714.0, 271.0, 719.0, 271.0],
                    ["C", 720.0, 271.0, 722.0, 268.0, 724.0, 264.0],
                    ["C", 727.0, 258.0, 727.0, 256.0, 724.0, 241.0],
                    ["C", 720.0, 218.0, 719.0, 216.0, 708.0, 209.0],
                    ["L", 699.0, 203.0],
                    ["L", 621.0, 202.0],
                    ["C", 529.0, 201.0, 422.0, 198.0, 394.0, 195.0],
                    ["C", 382.0, 194.0, 350.0, 194.0, 315.0, 195.0],
                    ["C", 252.0, 196.0, 195.0, 196.0, 96.0, 195.0],
                    ["C", 43.0, 194.0, 35.0, 195.0, 30.0, 198.0],
                    ["C", 22.0, 203.0, 9.0, 204.0, 3.0, 211.0],
                    ["C", -4.0, 220.0, 0.0, 273.0, 18.0, 273.0],
                    ["C", 20.0, 273.0, 23.0, 273.0, 24.0, 274.0],
                    ["C", 25.0, 275.0, 106.0, 276.0, 203.0, 276.0],
                    ["Z"],
                ],
            },
            "radical": {
                advance: 533,
                bbox: {xmin: -3.0, ymin: -92.0, xmax: 517.0, ymax: 643.0},
                config: {cutXPct: 70, cutYPct: 50, leanDeg: 0.0, unitsPerSeg: 60, amp: 5},
                commands: [
                    ["M", 266.0, 638.0],
                    ["C", 347.0, 607.0, 453.0, 632.0, 483.0, 619.0],
                    ["C", 488.0, 617.0, 492.0, 616.0, 493.0, 616.0],
                    ["C", 497.0, 616.0, 504.0, 605.0, 504.0, 599.0],
                    ["C", 504.0, 587.0, 517.0, 582.0, 511.0, 567.0],
                    ["C", 508.0, 561.0, 482.0, 534.0, 462.0, 540.0],
                    ["C", 421.0, 552.0, 356.0, 532.0, 296.0, 547.0],
                    ["L", 286.0, 550.0],
                    ["L", 284.0, 518.0],
                    ["C", 283.0, 501.0, 282.0, 478.0, 281.0, 467.0],
                    ["C", 278.0, 423.0, 248.0, 214.0, 248.0, 211.0],
                    ["C", 248.0, 208.0, 210.0, -38.0, 196.0, -68.0],
                    ["C", 187.0, -87.0, 174.0, -80.0, 169.0, -85.0],
                    ["C", 162.0, -92.0, 140.0, -88.0, 133.0, -79.0],
                    ["C", 132.0, -78.0, 76.0, 11.0, 58.0, 54.0],
                    ["C", 35.0, 112.0, 25.0, 138.0, 19.0, 143.0],
                    ["C", 17.0, 144.0, 13.0, 149.0, 11.0, 153.0],
                    ["C", -3.0, 180.0, -3.0, 182.0, 7.0, 197.0],
                    ["C", 26.0, 225.0, 34.0, 229.0, 49.0, 219.0],
                    ["C", 70.0, 205.0, 96.0, 180.0, 96.0, 174.0],
                    ["C", 96.0, 168.0, 132.0, 91.0, 132.0, 90.0],
                    ["C", 138.0, 75.0, 141.0, 70.0, 142.0, 73.0],
                    ["C", 142.0, 75.0, 167.0, 227.0, 171.0, 244.0],
                    ["C", 175.0, 264.0, 203.0, 511.0, 203.0, 514.0],
                    ["C", 210.0, 585.0, 210.0, 587.0, 216.0, 595.0],
                    ["C", 216.0, 596.0, 252.0, 643.0, 266.0, 638.0],
                    ["Z"],
                ],
            },
            "radical.tall": {
                advance: 824,
                bbox: {xmin: 20.0, ymin: -458.7, xmax: 804.0, ymax: 865.3},
                config: {cutXPct: 56, cutYPct: 45, leanDeg: -2.0, unitsPerSeg: 45, amp: 3},
                commands: [
                    ["M", 281.0, 864.3],
                    ["C", 283.0, 865.3, 288.0, 865.3, 294.0, 863.3],
                    ["C", 297.0, 862.3, 302.0, 862.3, 314.0, 861.3],
                    ["C", 323.0, 860.3, 334.0, 860.3, 338.0, 859.3],
                    ["C", 353.0, 857.3, 359.0, 856.3, 379.0, 855.3],
                    ["C", 392.0, 854.3, 442.0, 853.3, 508.0, 852.3],
                    ["C", 581.0, 851.3, 631.0, 850.3, 638.0, 849.3],
                    ["C", 641.5, 848.8, 652.0, 848.5, 662.4, 848.5],
                    ["C", 672.8, 848.5, 683.0, 848.8, 686.0, 849.3],
                    ["C", 691.0, 850.0, 717.9, 850.7, 735.7, 850.7],
                    ["C", 743.1, 850.7, 749.0, 850.6, 751.0, 850.3],
                    ["C", 761.0, 849.3, 781.0, 844.3, 784.0, 842.3],
                    ["C", 785.0, 841.3, 787.0, 840.3, 788.0, 839.3],
                    ["C", 790.0, 837.3, 795.0, 825.3, 797.0, 818.3],
                    ["C", 799.0, 813.3, 801.0, 807.3, 803.0, 803.3],
                    ["L", 804.0, 800.3],
                    ["L", 801.0, 793.3],
                    ["C", 797.0, 786.3, 793.0, 782.3, 788.0, 779.3],
                    ["C", 786.0, 778.3, 784.0, 776.3, 783.0, 775.3],
                    ["C", 782.0, 774.3, 779.0, 772.3, 776.0, 771.3],
                    ["C", 774.0, 770.3, 771.0, 768.3, 769.0, 767.3],
                    ["C", 766.0, 765.3, 765.0, 765.3, 758.0, 765.3],
                    ["C", 752.0, 765.3, 751.0, 765.3, 745.0, 767.3],
                    ["C", 738.3, 769.9, 730.3, 771.3, 721.0, 771.3],
                    ["C", 716.3, 771.3, 711.3, 770.9, 706.0, 770.3],
                    ["C", 702.0, 770.3, 689.0, 769.3, 677.0, 769.3],
                    ["C", 665.0, 769.3, 652.0, 768.3, 647.0, 768.3],
                    ["C", 641.0, 767.8, 612.5, 767.5, 583.2, 767.5],
                    ["C", 554.0, 767.5, 524.0, 767.8, 515.0, 768.3],
                    ["C", 507.0, 768.3, 477.0, 769.3, 448.0, 769.3],
                    ["C", 419.0, 769.3, 395.0, 770.3, 394.0, 770.3],
                    ["C", 393.0, 770.3, 377.0, 771.3, 358.0, 771.3],
                    ["C", 331.0, 772.3, 322.0, 771.3, 319.0, 772.3],
                    ["C", 314.0, 773.3, 312.0, 774.3, 310.0, 771.3],
                    ["C", 308.0, 769.3, 308.0, 768.3, 308.0, 763.3],
                    ["C", 308.0, 760.3, 307.0, 756.3, 307.0, 753.3],
                    ["C", 306.0, 745.3, 305.0, 722.3, 304.0, 683.3],
                    ["C", 304.0, 663.3, 303.0, 634.3, 302.0, 618.3],
                    ["C", 301.0, 602.3, 300.0, 574.3, 300.0, 558.3],
                    ["C", 300.0, 542.3, 299.0, 524.3, 299.0, 518.3],
                    ["C", 298.0, 509.3, 298.0, 483.3, 296.0, 320.3],
                    ["C", 295.0, 276.3, 295.0, 247.3, 294.0, 228.3],
                    ["C", 293.0, 213.3, 293.0, 193.3, 293.0, 182.3],
                    ["C", 293.0, 171.3, 292.0, 154.3, 291.0, 144.3],
                    ["C", 291.0, 134.3, 290.0, 108.3, 290.0, 86.3],
                    ["C", 289.0, 44.3, 289.0, 30.3, 287.0, 21.3],
                    ["C", 285.0, 12.3, 282.0, -4.7, 282.0, -9.7],
                    ["C", 282.0, -12.7, 282.0, -27.7, 281.0, -42.7],
                    ["C", 280.0, -58.7, 280.0, -73.7, 279.0, -77.7],
                    ["C", 277.0, -88.7, 276.0, -91.7, 276.0, -99.7],
                    ["C", 276.0, -103.7, 276.0, -113.7, 275.0, -121.7],
                    ["C", 274.0, -129.7, 273.0, -141.7, 272.0, -147.7],
                    ["C", 271.0, -156.7, 271.0, -161.7, 269.0, -168.7],
                    ["C", 267.0, -177.7, 267.0, -179.7, 265.0, -197.7],
                    ["C", 264.0, -206.7, 262.0, -211.7, 260.0, -219.7],
                    ["C", 259.0, -223.7, 259.0, -228.7, 258.0, -237.7],
                    ["C", 257.0, -251.7, 256.0, -257.7, 253.0, -265.7],
                    ["C", 252.0, -269.7, 251.0, -274.7, 250.0, -284.7],
                    ["C", 248.0, -300.7, 247.0, -304.7, 245.0, -312.7],
                    ["C", 243.0, -319.7, 243.0, -319.7, 242.0, -334.7],
                    ["C", 241.0, -347.7, 239.0, -352.7, 237.0, -359.7],
                    ["C", 236.0, -363.7, 235.0, -368.7, 234.0, -379.7],
                    ["C", 233.0, -392.7, 232.0, -394.7, 230.0, -399.7],
                    ["C", 229.0, -403.7, 227.0, -408.7, 226.0, -414.7],
                    ["C", 224.0, -425.7, 224.0, -427.7, 222.0, -430.7],
                    ["C", 221.0, -432.7, 219.0, -435.7, 218.0, -437.7],
                    ["C", 217.0, -441.7, 216.0, -442.7, 211.0, -446.7],
                    ["C", 207.0, -450.7, 205.0, -451.7, 202.0, -452.7],
                    ["C", 200.0, -453.7, 196.0, -454.7, 194.0, -455.7],
                    ["C", 189.0, -458.7, 184.0, -458.7, 178.0, -458.7],
                    ["C", 173.0, -458.7, 170.0, -457.7, 167.0, -455.7],
                    ["C", 166.0, -454.7, 163.0, -452.7, 161.0, -451.7],
                    ["C", 158.0, -450.7, 155.0, -448.7, 154.0, -447.7],
                    ["C", 153.0, -446.7, 151.0, -442.7, 149.0, -440.7],
                    ["C", 147.0, -438.7, 145.0, -435.7, 144.0, -433.7],
                    ["C", 143.0, -431.7, 142.0, -428.7, 141.0, -427.7],
                    ["C", 140.0, -426.7, 138.0, -423.7, 137.0, -420.7],
                    ["C", 136.0, -417.7, 133.0, -414.7, 132.0, -412.7],
                    ["C", 131.0, -410.7, 130.0, -409.7, 130.0, -409.7],
                    ["C", 130.0, -408.7, 126.0, -400.7, 124.0, -398.7],
                    ["C", 123.0, -397.7, 122.0, -394.7, 121.0, -392.7],
                    ["C", 120.0, -390.7, 118.0, -387.7, 117.0, -386.7],
                    ["C", 116.0, -385.7, 114.0, -382.7, 113.0, -380.7],
                    ["C", 112.0, -378.7, 110.0, -374.7, 109.0, -373.7],
                    ["C", 108.0, -372.7, 106.0, -369.7, 105.0, -367.7],
                    ["C", 104.0, -365.7, 102.0, -362.7, 101.0, -360.7],
                    ["C", 100.0, -358.7, 98.0, -354.7, 97.0, -352.7],
                    ["C", 96.0, -349.7, 94.0, -346.7, 93.0, -344.7],
                    ["C", 92.0, -342.7, 90.0, -339.7, 89.0, -336.7],
                    ["C", 88.0, -333.7, 86.0, -330.7, 85.0, -328.7],
                    ["C", 83.0, -325.7, 82.0, -322.7, 80.0, -314.7],
                    ["C", 80.0, -313.7, 79.0, -312.7, 78.0, -311.7],
                    ["C", 77.0, -309.7, 75.0, -306.7, 74.0, -301.7],
                    ["C", 73.0, -297.7, 71.0, -293.7, 70.0, -291.7],
                    ["C", 68.0, -287.7, 66.0, -283.7, 65.0, -278.7],
                    ["C", 65.0, -276.7, 63.0, -273.7, 62.0, -271.7],
                    ["C", 61.0, -269.7, 59.0, -265.7, 58.0, -261.7],
                    ["C", 57.0, -257.7, 56.0, -254.7, 55.0, -253.7],
                    ["C", 53.0, -251.7, 51.0, -247.7, 50.0, -243.7],
                    ["C", 49.0, -241.7, 48.0, -239.7, 47.0, -238.7],
                    ["C", 46.0, -237.7, 44.0, -233.7, 43.0, -231.7],
                    ["C", 42.0, -228.7, 39.0, -225.7, 38.0, -224.7],
                    ["C", 36.0, -223.7, 35.0, -220.7, 34.0, -218.7],
                    ["C", 33.0, -216.7, 32.0, -213.7, 30.0, -211.7],
                    ["C", 28.0, -209.7, 27.0, -206.7, 26.0, -204.7],
                    ["C", 25.0, -202.7, 25.0, -199.7, 24.0, -197.7],
                    ["C", 23.0, -195.7, 22.0, -193.7, 21.0, -191.7],
                    ["C", 20.0, -188.7, 20.0, -187.7, 21.0, -185.7],
                    ["C", 22.0, -183.7, 22.0, -180.7, 23.0, -179.7],
                    ["C", 24.0, -178.7, 26.0, -175.7, 27.0, -172.7],
                    ["C", 28.0, -169.7, 30.0, -167.7, 31.0, -166.7],
                    ["C", 32.0, -165.7, 33.0, -164.7, 34.0, -162.7],
                    ["C", 36.0, -158.7, 49.0, -146.7, 53.0, -144.7],
                    ["C", 55.0, -143.7, 56.0, -143.7, 60.0, -144.7],
                    ["C", 65.0, -145.7, 67.0, -145.7, 69.0, -147.7],
                    ["C", 70.0, -148.7, 72.0, -149.7, 73.0, -150.7],
                    ["C", 75.0, -151.7, 77.0, -152.7, 79.0, -154.7],
                    ["C", 81.0, -156.7, 84.0, -159.7, 86.0, -160.7],
                    ["C", 88.0, -161.7, 89.0, -162.7, 90.0, -163.7],
                    ["C", 91.0, -164.7, 92.0, -166.7, 94.0, -167.7],
                    ["C", 96.0, -168.7, 98.0, -170.7, 100.0, -172.7],
                    ["C", 112.0, -184.7, 114.0, -186.7, 116.0, -191.7],
                    ["C", 117.0, -193.7, 118.0, -196.7, 119.0, -197.7],
                    ["C", 120.0, -198.7, 122.0, -202.7, 123.0, -206.7],
                    ["C", 124.0, -210.7, 127.0, -215.7, 128.0, -217.7],
                    ["C", 130.0, -221.7, 131.0, -225.7, 132.0, -229.7],
                    ["C", 132.0, -230.7, 134.0, -233.7, 135.0, -235.7],
                    ["C", 136.0, -237.7, 137.0, -240.7, 138.0, -243.7],
                    ["C", 140.0, -250.7, 141.0, -251.7, 143.0, -254.7],
                    ["C", 144.0, -255.7, 146.0, -259.7, 147.0, -262.7],
                    ["C", 148.0, -265.7, 150.0, -268.7, 151.0, -269.7],
                    ["C", 152.0, -270.7, 154.0, -275.7, 155.0, -279.7],
                    ["L", 157.0, -286.7],
                    ["L", 161.0, -287.7],
                    ["C", 165.0, -287.7, 166.0, -286.7, 166.0, -285.7],
                    ["C", 167.0, -282.7, 168.0, -273.7, 168.0, -266.7],
                    ["C", 168.0, -258.7, 170.0, -246.7, 172.0, -239.7],
                    ["C", 174.0, -232.7, 175.0, -231.7, 176.0, -220.7],
                    ["C", 177.0, -214.7, 177.0, -207.7, 177.0, -204.7],
                    ["C", 178.0, -201.7, 179.0, -198.7, 179.0, -196.7],
                    ["C", 179.0, -194.7, 180.0, -192.7, 180.0, -191.7],
                    ["C", 181.0, -188.7, 183.0, -175.7, 184.0, -158.7],
                    ["C", 185.0, -148.7, 187.0, -135.7, 189.0, -128.7],
                    ["C", 190.0, -124.7, 190.0, -108.7, 191.0, -81.7],
                    ["C", 191.0, -70.7, 192.0, -59.7, 192.0, -56.7],
                    ["C", 192.0, -53.7, 194.0, -46.7, 194.0, -41.7],
                    ["C", 194.0, -36.7, 195.0, -30.7, 196.0, -26.7],
                    ["C", 198.0, -17.7, 198.0, -3.7, 199.0, 9.3],
                    ["C", 199.0, 14.3, 200.0, 25.3, 201.0, 32.3],
                    ["C", 202.0, 39.3, 202.0, 49.3, 202.0, 55.3],
                    ["C", 202.0, 61.3, 203.0, 70.3, 204.0, 75.3],
                    ["C", 205.0, 86.3, 206.0, 106.3, 207.0, 167.3],
                    ["C", 207.0, 195.3, 208.0, 228.3, 209.0, 243.3],
                    ["C", 210.0, 258.3, 210.0, 278.3, 210.0, 287.3],
                    ["C", 210.0, 296.3, 211.0, 309.3, 212.0, 315.3],
                    ["C", 213.0, 329.3, 213.0, 359.3, 214.0, 436.3],
                    ["C", 215.0, 475.3, 215.0, 505.3, 216.0, 523.3],
                    ["C", 217.0, 538.3, 218.0, 561.3, 218.0, 573.3],
                    ["C", 218.0, 585.3, 220.0, 598.3, 220.0, 601.3],
                    ["C", 221.0, 608.3, 221.0, 637.3, 222.0, 698.3],
                    ["C", 223.0, 725.3, 223.0, 739.3, 224.0, 744.3],
                    ["C", 225.0, 748.3, 226.0, 753.3, 226.0, 756.3],
                    ["C", 226.0, 759.3, 227.0, 764.3, 228.0, 768.3],
                    ["C", 229.0, 772.3, 229.0, 781.3, 230.0, 788.3],
                    ["C", 231.0, 805.3, 233.0, 810.3, 236.0, 817.3],
                    ["C", 238.0, 820.3, 238.0, 823.3, 239.0, 825.3],
                    ["C", 240.0, 827.3, 242.0, 828.3, 243.0, 829.3],
                    ["C", 244.0, 830.3, 245.0, 831.3, 246.0, 832.3],
                    ["C", 247.0, 833.3, 252.0, 839.3, 257.0, 844.3],
                    ["C", 262.0, 849.3, 268.0, 855.3, 270.0, 857.3],
                    ["C", 272.0, 859.3, 274.0, 861.3, 276.0, 862.3],
                    ["C", 278.0, 863.3, 280.0, 863.3, 281.0, 864.3],
                    ["Z"],
                ],
            },
        };
    // ── END GENERATED GLYPH DATA ──

    // ── Cut-and-extend algorithm ───────────────────────────────────────────
    // Self-contained, font-driven: takes a glyph's outline (from
    // EXTENSIBLE_GLYPHS above), shifts every coordinate past a threshold by
    // Nx font units, and stitches jittered cubic sub-segments across the
    // inserted gap.  Run twice (rotating between passes) for 2D extension on
    // the surd.  Algorithm and parameters mirror line-extend-demo.html.

    function _segmentize(commands) {
        const segs = [];
        let cx = 0, cy = 0, sx = 0, sy = 0;
        for (const c of commands) {
            const op = c[0];
            if (op === 'M') {
                sx = cx = c[1]; sy = cy = c[2];
                segs.push({ type:'M', from:[cx,cy], to:[cx,cy] });
            } else if (op === 'L') {
                segs.push({ type:'L', from:[cx,cy], to:[c[1],c[2]] });
                cx = c[1]; cy = c[2];
            } else if (op === 'C') {
                segs.push({ type:'C', from:[cx,cy], to:[c[5],c[6]],
                            ctrl:[[c[1],c[2]],[c[3],c[4]]] });
                cx = c[5]; cy = c[6];
            } else if (op === 'Q') {
                segs.push({ type:'Q', from:[cx,cy], to:[c[3],c[4]],
                            ctrl:[[c[1],c[2]]] });
                cx = c[3]; cy = c[4];
            } else if (op === 'Z') {
                segs.push({ type:'L', from:[cx,cy], to:[sx,sy] });
                segs.push({ type:'Z', from:[sx,sy], to:[sx,sy] });
                cx = sx; cy = sy;
            }
        }
        return segs;
    }

    function _bboxOf(segs) {
        let xmin=Infinity, ymin=Infinity, xmax=-Infinity, ymax=-Infinity;
        for (const s of segs) for (const p of [s.from, s.to, ...(s.ctrl||[])]) {
            if (p[0]<xmin) xmin=p[0]; if (p[0]>xmax) xmax=p[0];
            if (p[1]<ymin) ymin=p[1]; if (p[1]>ymax) ymax=p[1];
        }
        return { xmin, ymin, xmax, ymax };
    }

    // Hand-wobble spectrum: ~700- and ~300-unit periods.  Higher frequencies
    // only surface at fine subdivision and read as jitter, not pen wobble.
    function _noiseAt(x, seed) {
        return Math.sin(x * 0.009 + seed)
             + Math.sin(x * 0.021 + seed * 1.7) * 0.45;
    }

    // Catmull-Rom → cubic bezier — gives smooth curves through the jittered
    // anchors rather than a polyline.
    function _anchorsToCubics(anchors) {
        const out = [];
        const n = anchors.length;
        for (let i = 0; i < n - 1; i++) {
            const P0 = anchors[Math.max(0, i - 1)];
            const P1 = anchors[i];
            const P2 = anchors[i + 1];
            const P3 = anchors[Math.min(n - 1, i + 2)];
            const c1 = [P1[0] + (P2[0] - P0[0]) / 6, P1[1] + (P2[1] - P0[1]) / 6];
            const c2 = [P2[0] - (P3[0] - P1[0]) / 6, P2[1] - (P3[1] - P1[1]) / 6];
            out.push({ type:'C', from:P1, to:P2, ctrl:[c1, c2] });
        }
        return out;
    }

    function _mapSegs(segs, fn) {
        return segs.map(s => {
            const r = { type:s.type, from:fn(s.from), to:fn(s.to) };
            if (s.ctrl) r.ctrl = s.ctrl.map(fn);
            return r;
        });
    }

    function _extend(segs, cut, N, subN, amp, seed) {
        if (!(N > 0)) return segs;
        const shift = x => (x > cut ? x + N : x);
        const gapJitter = x => {
            const t = (x - cut) / N;
            if (t <= 0 || t >= 1) return 0;
            return Math.sin(Math.PI * t) * amp * _noiseAt(x, seed);
        };
        const out = [];
        for (const s of segs) {
            if (s.type === 'M' || s.type === 'Z') {
                out.push({ type:s.type, from:[shift(s.from[0]), s.from[1]],
                                          to:  [shift(s.to[0]),   s.to[1]] });
                continue;
            }
            const crosses = (s.from[0] <= cut && s.to[0] > cut)
                         || (s.from[0] >  cut && s.to[0] <= cut);
            if (!crosses) {
                const seg = { type:s.type,
                              from:[shift(s.from[0]), s.from[1]],
                              to:  [shift(s.to[0]),   s.to[1]] };
                if (s.ctrl) seg.ctrl = s.ctrl.map(p => [shift(p[0]), p[1]]);
                out.push(seg);
                continue;
            }
            const goingRight = s.from[0] < s.to[0];
            const xL = goingRight ? s.from[0] : s.to[0];
            const xR = goingRight ? s.to[0]   : s.from[0];
            const yL = goingRight ? s.from[1] : s.to[1];
            const yR = goingRight ? s.to[1]   : s.from[1];
            const tCut = (cut - xL) / (xR - xL);
            const yCut = yL + tCut * (yR - yL);
            const fromP = [shift(s.from[0]), s.from[1]];
            const toP   = [shift(s.to[0]),   s.to[1]];
            const anchors = [fromP];
            if (goingRight) {
                for (let i = 0; i <= subN; i++) {
                    const x = cut + (i / subN) * N;
                    anchors.push([x, yCut + gapJitter(x)]);
                }
            } else {
                for (let i = 0; i <= subN; i++) {
                    const x = cut + N - (i / subN) * N;
                    anchors.push([x, yCut + gapJitter(x)]);
                }
            }
            anchors.push(toP);
            for (const c of _anchorsToCubics(anchors)) out.push(c);
        }
        return out;
    }

    // Apply per-glyph X then leaning-Y extension and return the extended
    // segments (still in font units, baseline-up).  The Y pass is the same
    // X-extend, run in a frame rotated so the (tilted) extension axis aligns
    // with +x.
    function buildExtendedSegs(glyphName, Nx, Ny, seed) {
        const g = EXTENSIBLE_GLYPHS[glyphName];
        if (!g) throw new Error('unknown extensible glyph: ' + glyphName);
        const cfg = g.config;
        const segs0 = _segmentize(g.commands);
        const bb = g.bbox;
        const w = bb.xmax - bb.xmin, h = bb.ymax - bb.ymin;
        const cutX = bb.xmin + w * (cfg.cutXPct / 100);
        const cutY = bb.ymin + h * (cfg.cutYPct / 100);
        const subNx = Math.max(2, Math.round(Nx / cfg.unitsPerSeg));
        const subNy = Math.max(2, Math.round(Ny / cfg.unitsPerSeg));

        let out = segs0;
        if (Nx > 0) out = _extend(out, cutX, Nx, subNx, cfg.amp, seed);
        if (Ny > 0) {
            const lr = cfg.leanDeg * Math.PI / 180;
            const sL = Math.sin(lr), cL = Math.cos(lr);
            const fwd = p => [-sL * p[0] + cL * p[1], -cL * p[0] - sL * p[1]];
            const inv = p => [-sL * p[0] - cL * p[1],  cL * p[0] - sL * p[1]];
            const refX = (bb.xmin + bb.xmax) / 2;
            const cutRot = fwd([refX, cutY])[0];
            out = _mapSegs(out, fwd);
            out = _extend(out, cutRot, Ny, subNy, cfg.amp, seed + 19);
            out = _mapSegs(out, inv);
        }
        return out;
    }

    function _segsToPath(segs) {
        const f = n => +n.toFixed(2);
        const out = [];
        for (const s of segs) {
            if      (s.type === 'M') out.push(`M${f(s.to[0])} ${f(s.to[1])}`);
            else if (s.type === 'L') out.push(`L${f(s.to[0])} ${f(s.to[1])}`);
            else if (s.type === 'C') out.push(`C${f(s.ctrl[0][0])} ${f(s.ctrl[0][1])} ${f(s.ctrl[1][0])} ${f(s.ctrl[1][1])} ${f(s.to[0])} ${f(s.to[1])}`);
            else if (s.type === 'Q') out.push(`Q${f(s.ctrl[0][0])} ${f(s.ctrl[0][1])} ${f(s.to[0])} ${f(s.to[1])}`);
            else if (s.type === 'Z') out.push('Z');
        }
        return out.join(' ');
    }

    // ── Hand-drawn vinculum (font's emdash, X-extended) ────────────────────
    // Sizes the emdash glyph to (pixelWidth × pixelHeight): pick a font-units-
    // per-pixel scale from pixelHeight, compute the X extension needed to
    // reach pixelWidth, then bake the path.  No y stretching — the emdash's
    // natural stroke shape is preserved.
    function mirrorBarHTML(pixelWidth, pixelHeight) {
        const g = EXTENSIBLE_GLYPHS.emdash;
        const bb = g.bbox;
        const natH = bb.ymax - bb.ymin;
        const natW = bb.xmax - bb.xmin;
        const Sx = pixelHeight / natH;
        const targetW = pixelWidth / Sx;
        const Nx = Math.max(0, targetW - natW);
        const segs = buildExtendedSegs('emdash', Nx, 0, 5);
        const d = _segsToPath(segs);
        const totalW = natW + Nx;
        // viewBox covers (xmin, -ymax, totalW, natH) so SVG y-down matches
        // the path's y-up coords via a -1 y-scale on the inner <g>.
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${pixelWidth}px" height="${pixelHeight}px" viewBox="${bb.xmin} ${-bb.ymax} ${totalW} ${natH}" style="display:block;overflow:visible">
          <g transform="scale(1,-1)" fill="currentColor" stroke="none">
            <path d="${d}"/>
          </g>
        </svg>`;
    }

    // ── Hand-drawn sqrt surd ───────────────────────────────────────────────
    // Picks the natural radical (U+221A) for short stems and switches to the
    // PUA stem-with-shallow-lean (U+E000) once the requested height grows
    // past TALL_SURD_RATIO × the natural radical height — preserving xkcd
    // character at normal size, avoiding the visual collapse at large size.
    const TALL_SURD_RATIO = 1.6;

    // The "short" test keys off the VINCULUM height (the radicand box).
    // surdRect.height is always ≈1.0×fontSize regardless of the radicand,
    // so it can't tell sqrt(π) from sqrt(b²).  Measured ratios:
    // sqrt(π)≈0.77, sqrt(b²)≈0.93, sqrt(b²−4ac)≈0.97 → 0.85 splits the
    // no-ascender case from the superscript cases.
    const SURD_SHORT_THRESHOLD_FRAC = 0.85;

    // Per-glyph parameters.  nudgeFrac is the downward bar offset (fraction
    // of fontSize) from vinculumRect.top — pulls a high-floating bar down
    // to a short radicand, or lifts a thick bar clear of a superscript.
    // leadingPx is the gap between the surd's stem corner and the start of
    // the radicand.
    const SURD_PARAMS = {
        radical: {
            // Short radicands (sqrt(π)) need a big downward nudge to hug
            // the character; tall ones (b² superscript) only need a small
            // one to keep our thicker bar clear of the ascender.
            nudgeFrac: ({isShort}) => isShort ? 0.28 : 0.10,
            leadingPx: ({fontSizePx}) => fontSizePx * 0.16,
        },
        'radical.tall': {
            nudgeFrac: () => 0.10,
            // Taper leading DOWN as the surd grows: a moderately tall
            // radicand (quadratic formula) crowds with too little lead-in,
            // but a very tall one looks over-spaced with a big gap.
            leadingPx: ({fontSizePx, radicandH}) =>
                Math.max(fontSizePx * 0.05,
                         fontSizePx * 0.22 - radicandH * 0.045),
        },
    };

    function _pickSurd(targetH_units_at_naturalRadicalScale) {
        const natH = EXTENSIBLE_GLYPHS.radical.bbox.ymax -
                     EXTENSIBLE_GLYPHS.radical.bbox.ymin;
        return targetH_units_at_naturalRadicalScale > natH * TALL_SURD_RATIO
            ? 'radical.tall' : 'radical';
    }

    // Maximum-y anchor point — for a surd this is the top of the bar near
    // the stem corner.  Must be computed AFTER extension because Y extension
    // shifts everything above the cut upward; the pre-extension max-y point
    // ends up inside the stem and stops being the visible bar top.
    function _surdJunctionFromSegs(segs) {
        let bestX = 0, bestY = -Infinity;
        for (const s of segs) for (const p of [s.from, s.to, ...(s.ctrl || [])]) {
            if (p[1] > bestY) { bestY = p[1]; bestX = p[0]; }
        }
        return { x: bestX, y: bestY };
    }

    // Build the surd SVG given target dimensions in pixels (bar pixel width,
    // total surd pixel height) and a font-units-per-pixel scale Sx.  Returns
    // { html, junctionPx } so the caller can position the overlay so the
    // junction lands at a chosen on-screen point.
    // Caller passes the resolved glyphName and the exact pixel height we
    // want the rendered glyph to be (bar-top to tick-bottom).  No more
    // implicit descender compensation — the caller sizes around the
    // radicand and a target descender directly.
    function buildSurdSvg(barWidthPx, renderedHeightPx, name, Sx) {
        const g    = EXTENSIBLE_GLYPHS[name];
        const bb   = g.bbox;
        const natH = bb.ymax - bb.ymin;
        const targetH_units = renderedHeightPx / Sx;

        // Bar width: the natural bar extends from the source-glyph junction
        // to bb.xmax.  We compute Nx from that span (pre-extension) but the
        // anchor point used for placement is taken from the *extended* segs
        // below — Y extension moves the bar's top upward.
        const natJct = (function () {
            let bx = 0, by = -Infinity;
            for (const c of g.commands) {
                const i = (c[0] === 'C') ? 5 : (c[0] === 'Q') ? 3 :
                          (c[0] === 'M' || c[0] === 'L') ? 1 : -1;
                if (i < 0) continue;
                if (c[i + 1] > by) { by = c[i + 1]; bx = c[i]; }
            }
            return { x: bx, y: by };
        })();
        const naturalBarW = bb.xmax - natJct.x;
        const targetBarW  = barWidthPx / Sx;
        const Nx = Math.max(0, targetBarW - naturalBarW);
        const Ny = Math.max(0, targetH_units - natH);

        const segs = buildExtendedSegs(name, Nx, Ny, 5);
        const d = _segsToPath(segs);
        const eb = _bboxOf(segs);
        const jct = _surdJunctionFromSegs(segs);
        const margin = 20;
        const vbX = eb.xmin - margin;
        const vbY = -(eb.ymax + margin);
        const vbW = (eb.xmax - eb.xmin) + 2 * margin;
        const vbH = (eb.ymax - eb.ymin) + 2 * margin;

        const widthPx  = vbW * Sx;
        const heightPx = vbH * Sx;

        // Junction in SVG pixel coords (relative to the svg's left/top corner).
        const junctionPx = {
            x: (jct.x - vbX) * Sx,
            y: (-jct.y - vbY) * Sx,
        };

        // Returns the SVG markup without positioning styles; caller wraps it
        // in a positioned container after computing where junctionPx should
        // land on screen.
        const svg = `<svg class="xkcd-overlay" xmlns="http://www.w3.org/2000/svg"
            width="${widthPx}px" height="${heightPx}px" viewBox="${vbX} ${vbY} ${vbW} ${vbH}"
            style="display:block;overflow:visible;pointer-events:none;">
          <g transform="scale(1,-1)" fill="currentColor" stroke="none">
            <path d="${d}"/>
          </g>
        </svg>`;
        return { svg, junctionPx, widthPx, heightPx, glyphName: name };
    }

    // ── Replacement passes ──────────────────────────────────────────────────
    // Scale for the surd glyph (px per font unit).  Smaller scale → thinner
    // strokes (since the glyph's stroke thickness in font units scales with
    // Sx) and longer Ny extension is used to reach the requested surd
    // height.  490 produced about a 1.5×fontSize natural radical but the
    // strokes were too thick; 850 gives thinner strokes at the cost of more
    // stem extension on natural-height surds.
    const SURD_NATURAL_SCALE = 850;
    // How far below the radicand's bottom we want the surd's tick to
    // extend (fraction of fontSize).  Picked so the surd visually
    // encloses the radicand with the hand-drawn tick descender.
    const SURD_DESCENDER_FRAC = 0.45;
    // Floor on the rendered surd height (fraction of fontSize) — safety
    // for very small radicands.
    const SURD_MIN_HEIGHT_FRAC = 1.0;
    // Extra bar length past the radicand's right edge for short single-line
    // radicands (fraction of fontSize), so e.g. sqrt(π)'s bar doesn't end
    // abruptly at the glyph.
    const SURD_TRAILING_FRAC = 0.12;
    // Render the bar SVG at this multiple of the CSS border height.  The
    // emdash glyph's bbox is the full visible stroke, so >1× makes the
    // visible bar thicker than the typeset reference.  ~2× matches the
    // density of the previous hand-drawn bar visually.
    const BAR_PIXEL_MULT = 2;

    // The radicand's vinculum (a CSS border-top in MathJax's CHTML) gives
    // us the bar's intended width and left edge.
    function _findVinculum(msqrt) {
        for (const el of msqrt.querySelectorAll('*')) {
            if (el.closest('mjx-surd')) continue;
            const nearestFrac = el.closest('mjx-mfrac');
            if (nearestFrac && msqrt.contains(nearestFrac)) continue;
            const cs = getComputedStyle(el);
            if (cs.borderTopStyle === 'solid' && parseFloat(cs.borderTopWidth) > 0) {
                return el;
            }
        }
        return null;
    }

    // Resolve everything the surd builder needs: which glyph, base Sx,
    // bar width, rendered height, leading gap, and downward nudge.  All
    // size decisions key off the radicand height (the vinculum box) and
    // fontSize.
    function _planSurd({fontSizePx, radicandH, vinculumWidth}) {
        const Sx = fontSizePx / SURD_NATURAL_SCALE;
        const glyphName = _pickSurd(radicandH / Sx);
        const params = SURD_PARAMS[glyphName];
        const isShort = radicandH <= fontSizePx * SURD_SHORT_THRESHOLD_FRAC;

        const leadingPx  = params.leadingPx({fontSizePx, radicandH});
        const trailingPx = isShort ? fontSizePx * SURD_TRAILING_FRAC : 0;
        const barWidthPx = vinculumWidth + leadingPx + trailingPx;
        const nudgePx    = fontSizePx * params.nudgeFrac({isShort});

        // Surd's full rendered height — bar top to tick bottom.  We want
        // the tick to land DESCENDER_FRAC×fontSize below the radicand's
        // bottom for all cases; since the bar is at vincTop + nudge,
        // that means rendered = radicandH + descender − nudge.
        const renderedHeightPx = Math.max(
            radicandH + fontSizePx * SURD_DESCENDER_FRAC - nudgePx,
            fontSizePx * SURD_MIN_HEIGHT_FRAC);

        return {glyphName, Sx, barWidthPx, renderedHeightPx, leadingPx, nudgePx};
    }

    function replaceSqrtSymbols(root) {
        const scope = root || document;
        scope.querySelectorAll('mjx-msqrt').forEach(msqrt => {
            if (msqrt.dataset.sqrtReplaced) return;
            msqrt.dataset.sqrtReplaced = '1';

            const surd = msqrt.querySelector('mjx-surd');
            const vinculumEl = surd && _findVinculum(msqrt);
            if (!surd || !vinculumEl) return;

            const msqrtRect    = msqrt.getBoundingClientRect();
            const vinculumRect = vinculumEl.getBoundingClientRect();
            const fontSizePx   = parseFloat(getComputedStyle(msqrt).fontSize);

            const plan = _planSurd({
                fontSizePx,
                radicandH: vinculumRect.height,
                vinculumWidth: vinculumRect.width,
            });
            const built = buildSurdSvg(plan.barWidthPx, plan.renderedHeightPx,
                                       plan.glyphName, plan.Sx);

            // Anchor the bar-corner junction `leadingPx` to the left of the
            // bar's intended start, and vertically at vinculumRect.top —
            // i.e. where MathJax actually draws the bar.
            const barLeft = vinculumRect.left - msqrtRect.left;
            const barTop  = vinculumRect.top  - msqrtRect.top;
            const svgLeft = barLeft - plan.leadingPx - built.junctionPx.x;
            const svgTop  = barTop  - built.junctionPx.y + plan.nudgePx;

            surd.dataset.xkcdHidden = '1';
            surd.style.visibility = 'hidden';
            vinculumEl.dataset.xkcdHidden = '1';
            vinculumEl.style.borderTopColor = 'transparent';
            if (getComputedStyle(msqrt).position === 'static') {
                msqrt.dataset.xkcdPos = '1';
                msqrt.style.position = 'relative';
            }

            msqrt.insertAdjacentHTML('beforeend',
                `<div class="xkcd-overlay" style="position:absolute;left:${svgLeft}px;top:${svgTop}px;pointer-events:none;">${built.svg}</div>`);
        });
    }

    function replaceVinculums(root) {
        const scope = root || document;
        scope.querySelectorAll('mjx-container[jax="CHTML"]').forEach(container => {
            container.querySelectorAll('*').forEach(el => {
                if (el.dataset.xkcdHidden) return;
                if (el.closest('mjx-surd')) return;
                const cs = getComputedStyle(el);
                if (cs.borderTopStyle !== 'solid' || parseFloat(cs.borderTopWidth) <= 0) return;
                const barH = Math.max(parseFloat(cs.borderTopWidth), 1);
                el.dataset.xkcdHidden = '1';
                el.style.borderTopColor = 'transparent';

                if (getComputedStyle(container).position === 'static')
                    { container.dataset.xkcdPos = '1'; container.style.position = 'relative'; }

                const containerRect = container.getBoundingClientRect();
                const elRect        = el.getBoundingClientRect();
                const renderedH = barH * BAR_PIXEL_MULT;
                // Centre the rendered bar on the original border-top line.
                const left = elRect.left - containerRect.left;
                const top  = (elRect.top - containerRect.top) + (barH / 2) - (renderedH / 2);

                container.insertAdjacentHTML('beforeend',
                    `<div class="xkcd-overlay" style="position:absolute;left:${left}px;top:${top}px;pointer-events:none;">${mirrorBarHTML(elRect.width, renderedH)}</div>`);
            });
        });
    }

    function resetOverlays(scope) {
        const root = scope || document;
        root.querySelectorAll('.xkcd-overlay').forEach(el => el.remove());
        root.querySelectorAll('[data-xkcd-hidden]').forEach(el => {
            el.style.visibility = '';
            el.style.borderTopColor = '';
            delete el.dataset.xkcdHidden;
        });
        root.querySelectorAll('[data-xkcd-pos]').forEach(el => {
            el.style.position = '';
            delete el.dataset.xkcdPos;
        });
        root.querySelectorAll('[data-sqrt-replaced]').forEach(el => {
            delete el.dataset.sqrtReplaced;
        });
    }

    // ── Font-override CSS (after MathJax's own CSS, so !important wins) ─────
    let _fontOverrideInjected = false;
    function injectFontOverride() {
        if (_fontOverrideInjected) return;
        _fontOverrideInjected = true;
        // MJXZERO first matches MathJax's own .TEX-S1 rule: it's a zero-metric
        // font that keeps the line-box clean, so only MathJax's explicit ::before
        // padding governs vertical positioning of large operators.  xkcd-script
        // still wins as the actual glyph source via cmap fallback.
        const STACK = "MJXZERO, 'xkcd-script', MJXTEX, MJXTEX-I, MJXTEX-B, MJXTEX-BI, MJXTEX-S1, MJXTEX-S2, MJXTEX-S3, MJXTEX-S4, MJXTEX-A";
        const s = document.createElement('style');
        s.textContent = `
            mjx-container[jax="CHTML"] *,
            mjx-container[jax="CHTML"] *::before {
                font-family: ${STACK} !important;
            }
            /* Display-mode large operators (∑ ∏ ∫): swap in the .disp
               stylistic alternates from xkcd-script via ss01.  Inline
               operators keep the base letter-sized glyphs.  !important
               because the font-family override above is !important and a
               plain font-feature-settings would otherwise lose to MathJax's
               CHTML defaults. */
            /* MathJax CHTML uses the Size1 metric (class TEX-S1) for both
               inline and display ∑/∏/∫, just at different CSS font-sizes.
               Apply ss01 to all of them so MathJax always sees the
               display-sized .disp variant — its own font-size scaling
               handles inline vs display sizing.  Non-MathJax users still
               see the letter-sized base glyph because they don't trigger
               this CSS rule. */
            mjx-container[jax="CHTML"] mjx-mo,
            mjx-container[jax="CHTML"] mjx-mo * {
                font-feature-settings: "ss01" on !important;
            }
            /* Breathing room around inline math containers so they don't
               crowd surrounding sentence text. */
            mjx-container[jax="CHTML"]:not([display="true"]) {
                margin: 0 0.2em !important;
            }
            /* Inline limits on ∑ ∏ ∫ need extra right margin — MathJax uses
               pre-baked metrics that ignore our wider .disp glyphs. */
            mjx-container[jax="CHTML"]:not([display="true"]) mjx-mo:has(.mjx-c2211),
            mjx-container[jax="CHTML"]:not([display="true"]) mjx-mo:has(.mjx-c220F),
            mjx-container[jax="CHTML"]:not([display="true"]) mjx-mo:has(.mjx-c222B) {
                margin-right: 0.4em !important;
            }
            /* ∑ italic-correction was designed for slanted MJXTEX; nudge back
               our upright ∑'s over-script in display mode. */
            mjx-container[jax="CHTML"][display="true"] mjx-munderover:has(.mjx-c2211) mjx-over {
                margin-left: -0.15em !important;
            }
            /* xkcd capitals are narrower than MJXTEX-I metrics so \\hat (U+02C6)
               sits too far right; nudge it back. */
            mjx-container[jax="CHTML"] mjx-mover mjx-over:has(.mjx-c2C6) {
                margin-left: -0.10em !important;
            }
            /* Drop the italic-correction padding on f-as-superscript-base so
               the prime lines up against our upright f. */
            mjx-container[jax="CHTML"] mjx-msup mjx-base mjx-mi:has(.mjx-c1D453) {
                padding-right: 0 !important;
            }
            /* Italic g descender crowds the following '(' — small nudge. */
            mjx-container[jax="CHTML"] mjx-mi:has(.mjx-c1D454) {
                margin-right: 0.05em;
            }`;
        document.head.appendChild(s);
    }

    // ── Public refresh: idempotent overlay pass ─────────────────────────────
    function refresh(root) {
        injectFontOverride();
        replaceSqrtSymbols(root);
        replaceVinculums(root);
    }

    // ── Startup orchestration ──────────────────────────────────────────────
    // We need to run a refresh once MathJax has done its first typeset, then
    // again after every subsequent typesetPromise.  Three cases:
    //   1. MathJax not loaded yet, no startup.ready hook installed → we install
    //      one that does the initial typeset + refresh.
    //   2. MathJax not loaded yet but someone else owns startup.ready → we
    //      wrap their hook so ours runs after theirs (Jupyter sometimes does).
    //   3. MathJax already loaded → await startup.promise, refresh.
    // In all cases we expose `XkcdMathJax.ready` as a promise for callers.

    function _waitForDom() {
        return document.readyState === 'loading'
            ? new Promise(res => document.addEventListener('DOMContentLoaded', res, { once: true }))
            : Promise.resolve();
    }

    function _waitForFont() {
        // Pass a text including ∑/∏/∫ so the FontFaceSet wait covers the
        // codepoints + their ss01 substitutions actually rendered by MathJax.
        return document.fonts.load("1em 'xkcd-script'", "A∑∏∫").catch(() => {});
    }

    let _resolveReady;
    const ready = new Promise(res => { _resolveReady = res; });

    function _afterInitialTypeset() {
        return Promise.all([_waitForFont(), _waitForDom()])
            .then(() => { injectFontOverride(); })  // before typeset so ss01 + STACK affect MathJax's box metrics
            .then(() => MathJax.typesetPromise())
            .then(() => { refresh(); _resolveReady(); });
    }

    function _hookStartup() {
        const prevReady = (window.MathJax && window.MathJax.startup && window.MathJax.startup.ready) || null;
        window.MathJax = window.MathJax || {};
        window.MathJax.startup = window.MathJax.startup || {};
        // Don't auto-typeset; we'll do it ourselves after fonts + DOM are ready.
        if (window.MathJax.startup.typeset !== false) window.MathJax.startup.typeset = false;
        window.MathJax.startup.ready = function () {
            if (prevReady) prevReady();
            else MathJax.startup.defaultReady();
            _afterInitialTypeset();
        };
    }

    if (window.MathJax && window.MathJax.startup && window.MathJax.startup.promise) {
        // Case 3: MathJax already loaded.  Don't re-typeset (the host page
        // probably already did) — just await whatever's in flight and refresh.
        window.MathJax.startup.promise
            .then(() => Promise.all([_waitForFont(), _waitForDom()]))
            .then(() => { injectFontOverride(); refresh(); _resolveReady(); });
    } else {
        // Cases 1 + 2: install / wrap startup.ready before MathJax loads.
        _hookStartup();
    }

    // ── Resize: BCR coordinates change, so re-place overlays ────────────────
    let _resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(_resizeTimer);
        _resizeTimer = setTimeout(() => {
            resetOverlays();
            refresh();
        }, 150);
    });

    // ── Public API ──────────────────────────────────────────────────────────
    window.XkcdMathJax = { refresh, resetOverlays, ready };
})();
