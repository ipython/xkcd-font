/**
 * xkcd-mathjax — render MathJax 3 CHTML output with xkcd-script fonts and
 * hand-drawn sqrt / fraction-bar overlays.
 *
 * Drop this script on a page that already loads MathJax 3 (CHTML).  It loads
 * the two woff files from URLs resolved relative to its own src, injects the
 * font-override CSS, and hooks MathJax's startup so the initial typeset is
 * post-processed.  Works whether MathJax loads before or after this script.
 *
 * ── Usage (plain HTML) ──────────────────────────────────────────────────────
 *   <!-- 1. Optional MathJax config (tex delimiters, etc) — set FIRST -->
 *   <script>MathJax = { tex: { inlineMath: [['$','$']] } };</script>
 *   <!-- 2. Then this script: it merges its startup hook into MathJax config -->
 *   <script src="path/to/xkcd-mathjax.js"></script>
 *   <!-- 3. Then MathJax itself, async -->
 *   <script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
 *
 * ── Usage (Jupyter / JupyterLab, which ships its own MathJax 3) ─────────────
 *   from IPython.display import HTML, display
 *   display(HTML('<script src="https://your-host/xkcd-mathjax.js"></script>'))
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
        // Fallback: locate any <script> whose src ends in xkcd-mathjax.js
        for (const s of document.scripts) {
            if (s.src && /xkcd-mathjax(\.min)?\.js(\?|$)/.test(s.src)) {
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
                font-family: 'xkcd-script-math';
                src: url('${FONT_BASE}xkcd-script-mathjax.woff') format('woff');
            }
            @font-face {
                font-family: 'xkcd-script';
                src: url('${FONT_BASE}xkcd-script.woff') format('woff');
            }`;
        document.head.appendChild(s);
    }
    _injectFontFaces();

    // ── BEGIN GENERATED GLYPH DATA ──
    const EXTENSIBLE_GLYPHS = {
            emdash: {
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
            radical: {
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
            uniE000: {
                advance: 1020,
                bbox: {xmin: 20.0, ymin: -625.3, xmax: 1000.0, ymax: 1031.7},
                config: {cutXPct: 56, cutYPct: 45, leanDeg: -2.0, unitsPerSeg: 45, amp: 3},
                commands: [
                    ["M", 346.0, 1029.7],
                    ["C", 348.0, 1031.7, 356.0, 1030.7, 363.0, 1028.7],
                    ["C", 366.0, 1027.7, 373.0, 1026.7, 388.0, 1025.7],
                    ["C", 399.0, 1024.7, 412.0, 1024.7, 417.0, 1023.7],
                    ["C", 436.0, 1020.7, 444.0, 1020.7, 469.0, 1018.7],
                    ["C", 485.0, 1017.7, 548.0, 1015.7, 630.0, 1014.7],
                    ["C", 721.0, 1013.7, 785.0, 1012.7, 793.0, 1011.7],
                    ["C", 797.0, 1011.2, 810.0, 1011.0, 822.9, 1011.0],
                    ["C", 835.8, 1011.0, 848.5, 1011.2, 852.0, 1011.7],
                    ["C", 858.4, 1012.4, 892.2, 1013.2, 914.7, 1013.2],
                    ["C", 924.0, 1013.2, 931.4, 1013.0, 934.0, 1012.7],
                    ["C", 946.0, 1011.7, 971.0, 1004.7, 975.0, 1002.7],
                    ["C", 976.0, 1001.7, 979.0, 1000.7, 980.0, 998.7],
                    ["C", 982.0, 995.7, 988.0, 981.7, 991.0, 972.7],
                    ["C", 993.0, 966.7, 996.0, 958.7, 998.0, 953.7],
                    ["L", 1000.0, 949.7],
                    ["L", 996.0, 941.7],
                    ["C", 992.0, 932.7, 987.0, 926.7, 980.0, 923.7],
                    ["C", 978.0, 922.7, 974.0, 920.7, 973.0, 919.7],
                    ["C", 972.0, 918.7, 968.0, 915.7, 965.0, 913.7],
                    ["C", 962.0, 911.7, 958.0, 909.7, 956.0, 908.7],
                    ["C", 952.0, 905.7, 951.0, 905.7, 943.0, 905.7],
                    ["C", 935.0, 905.7, 933.0, 905.7, 926.0, 908.7],
                    ["C", 917.8, 912.2, 907.7, 913.7, 895.8, 913.7],
                    ["C", 890.3, 913.7, 884.3, 913.4, 878.0, 912.7],
                    ["C", 873.0, 912.7, 857.0, 910.7, 842.0, 910.7],
                    ["C", 827.0, 910.7, 809.0, 909.7, 803.0, 909.7],
                    ["C", 796.0, 909.2, 760.5, 909.0, 723.9, 909.0],
                    ["C", 687.2, 909.0, 649.5, 909.2, 638.0, 909.7],
                    ["C", 628.0, 909.7, 590.0, 910.7, 554.0, 910.7],
                    ["C", 518.0, 910.7, 488.0, 912.7, 487.0, 912.7],
                    ["C", 486.0, 912.7, 467.0, 913.7, 443.0, 913.7],
                    ["C", 409.0, 914.7, 398.0, 914.7, 394.0, 915.7],
                    ["C", 388.0, 917.7, 386.0, 916.7, 383.0, 913.7],
                    ["C", 381.0, 911.7, 381.0, 910.7, 380.0, 904.7],
                    ["C", 380.0, 900.7, 378.0, 894.7, 378.0, 891.7],
                    ["C", 377.0, 881.7, 376.0, 852.7, 375.0, 804.7],
                    ["C", 375.0, 779.7, 374.0, 741.7, 373.0, 721.7],
                    ["C", 372.0, 701.7, 370.0, 667.7, 370.0, 647.7],
                    ["C", 370.0, 627.7, 368.0, 605.7, 368.0, 598.7],
                    ["C", 367.0, 586.7, 367.0, 553.7, 365.0, 349.7],
                    ["C", 364.0, 294.7, 364.0, 258.7, 363.0, 235.7],
                    ["C", 362.0, 216.7, 361.0, 190.7, 361.0, 177.7],
                    ["C", 361.0, 164.7, 360.0, 143.7, 359.0, 130.7],
                    ["C", 358.0, 117.7, 357.0, 84.7, 357.0, 57.7],
                    ["C", 356.0, 5.7, 355.0, -12.3, 353.0, -23.3],
                    ["C", 351.0, -34.3, 348.0, -56.3, 348.0, -63.3],
                    ["C", 348.0, -66.3, 347.0, -84.3, 346.0, -103.3],
                    ["C", 345.0, -123.3, 344.0, -142.3, 343.0, -147.3],
                    ["C", 341.0, -161.3, 341.0, -166.3, 340.0, -175.3],
                    ["C", 340.0, -180.3, 339.0, -192.3, 338.0, -202.3],
                    ["C", 337.0, -212.3, 336.0, -227.3, 335.0, -235.3],
                    ["C", 334.0, -246.3, 333.0, -253.3, 331.0, -261.3],
                    ["C", 328.0, -272.3, 328.0, -276.3, 326.0, -298.3],
                    ["C", 325.0, -309.3, 324.0, -315.3, 321.0, -325.3],
                    ["C", 320.0, -330.3, 318.0, -336.3, 317.0, -348.3],
                    ["C", 315.0, -366.3, 314.0, -373.3, 311.0, -383.3],
                    ["C", 309.0, -388.3, 308.0, -393.3, 307.0, -406.3],
                    ["C", 305.0, -427.3, 305.0, -431.3, 302.0, -441.3],
                    ["C", 299.0, -449.3, 299.0, -450.3, 297.0, -469.3],
                    ["C", 295.0, -486.3, 295.0, -490.3, 292.0, -499.3],
                    ["C", 290.0, -504.3, 288.0, -510.3, 287.0, -524.3],
                    ["C", 285.0, -540.3, 285.0, -544.3, 282.0, -550.3],
                    ["C", 280.0, -555.3, 279.0, -561.3, 278.0, -568.3],
                    ["C", 276.0, -582.3, 275.0, -584.3, 272.0, -588.3],
                    ["C", 271.0, -590.3, 269.0, -594.3, 268.0, -597.3],
                    ["C", 267.0, -601.3, 265.0, -603.3, 259.0, -608.3],
                    ["C", 253.0, -613.3, 252.0, -615.3, 248.0, -616.3],
                    ["C", 245.0, -617.3, 241.0, -619.3, 238.0, -620.3],
                    ["C", 231.0, -624.3, 226.0, -625.3, 218.0, -624.3],
                    ["C", 211.0, -624.3, 207.0, -622.3, 203.0, -619.3],
                    ["C", 202.0, -618.3, 199.0, -616.3, 196.0, -615.3],
                    ["C", 193.0, -613.3, 189.0, -612.3, 188.0, -610.3],
                    ["C", 187.0, -608.3, 184.0, -604.3, 182.0, -601.3],
                    ["C", 180.0, -598.3, 177.0, -593.3, 176.0, -591.3],
                    ["C", 175.0, -589.3, 173.0, -586.3, 172.0, -585.3],
                    ["C", 171.0, -584.3, 169.0, -579.3, 167.0, -576.3],
                    ["C", 165.0, -573.3, 163.0, -568.3, 161.0, -566.3],
                    ["C", 159.0, -564.3, 158.0, -562.3, 158.0, -562.3],
                    ["C", 158.0, -560.3, 152.0, -551.3, 150.0, -548.3],
                    ["C", 149.0, -546.3, 147.0, -544.3, 146.0, -541.3],
                    ["C", 145.0, -538.3, 142.0, -535.3, 141.0, -534.3],
                    ["C", 140.0, -533.3, 137.0, -529.3, 136.0, -526.3],
                    ["C", 135.0, -523.3, 132.0, -520.3, 131.0, -518.3],
                    ["C", 130.0, -516.3, 128.0, -513.3, 127.0, -510.3],
                    ["C", 126.0, -507.3, 124.0, -502.3, 122.0, -500.3],
                    ["C", 120.0, -498.3, 117.0, -493.3, 116.0, -490.3],
                    ["C", 115.0, -487.3, 114.0, -483.3, 112.0, -481.3],
                    ["C", 111.0, -479.3, 108.0, -474.3, 107.0, -471.3],
                    ["C", 106.0, -468.3, 104.0, -462.3, 102.0, -460.3],
                    ["C", 100.0, -457.3, 98.0, -454.3, 95.0, -443.3],
                    ["C", 95.0, -442.3, 93.0, -441.3, 92.0, -439.3],
                    ["C", 91.0, -437.3, 89.0, -433.3, 87.0, -427.3],
                    ["C", 86.0, -422.3, 83.0, -416.3, 82.0, -414.3],
                    ["C", 79.0, -410.3, 79.0, -406.3, 77.0, -399.3],
                    ["C", 76.0, -397.3, 74.0, -392.3, 73.0, -390.3],
                    ["C", 71.0, -388.3, 69.0, -382.3, 68.0, -378.3],
                    ["C", 67.0, -373.3, 65.0, -368.3, 64.0, -367.3],
                    ["C", 62.0, -364.3, 59.0, -360.3, 57.0, -355.3],
                    ["C", 56.0, -353.3, 55.0, -349.3, 54.0, -348.3],
                    ["C", 53.0, -347.3, 51.0, -343.3, 49.0, -340.3],
                    ["C", 47.0, -337.3, 45.0, -333.3, 43.0, -331.3],
                    ["C", 41.0, -329.3, 39.0, -326.3, 38.0, -324.3],
                    ["C", 37.0, -322.3, 35.0, -318.3, 33.0, -315.3],
                    ["C", 31.0, -312.3, 29.0, -307.3, 28.0, -305.3],
                    ["C", 27.0, -303.3, 25.0, -299.3, 24.0, -297.3],
                    ["C", 23.0, -295.3, 22.0, -291.3, 21.0, -289.3],
                    ["C", 20.0, -285.3, 20.0, -284.3, 21.0, -281.3],
                    ["C", 22.0, -279.3, 23.0, -277.3, 24.0, -275.3],
                    ["C", 25.0, -273.3, 27.0, -269.3, 29.0, -266.3],
                    ["C", 31.0, -262.3, 33.0, -259.3, 34.0, -258.3],
                    ["C", 35.0, -257.3, 37.0, -255.3, 38.0, -253.3],
                    ["C", 40.0, -248.3, 56.0, -233.3, 61.0, -231.3],
                    ["C", 64.0, -230.3, 65.0, -229.3, 70.0, -230.3],
                    ["C", 76.0, -231.3, 79.0, -232.3, 81.0, -235.3],
                    ["C", 82.0, -236.3, 84.0, -237.3, 86.0, -238.3],
                    ["C", 88.0, -239.3, 92.0, -242.3, 94.0, -244.3],
                    ["C", 96.0, -246.3, 101.0, -249.3, 103.0, -250.3],
                    ["C", 105.0, -252.3, 107.0, -254.3, 108.0, -255.3],
                    ["C", 109.0, -256.3, 111.0, -258.3, 113.0, -259.3],
                    ["C", 115.0, -260.3, 119.0, -264.3, 121.0, -266.3],
                    ["C", 136.0, -281.3, 138.0, -283.3, 140.0, -289.3],
                    ["C", 141.0, -292.3, 143.0, -296.3, 144.0, -297.3],
                    ["C", 145.0, -298.3, 147.0, -303.3, 149.0, -308.3],
                    ["C", 151.0, -313.3, 153.0, -319.3, 155.0, -322.3],
                    ["C", 158.0, -327.3, 159.0, -332.3, 160.0, -337.3],
                    ["C", 160.0, -339.3, 162.0, -342.3, 163.0, -344.3],
                    ["C", 164.0, -346.3, 167.0, -351.3, 168.0, -355.3],
                    ["C", 171.0, -364.3, 171.0, -364.3, 174.0, -368.3],
                    ["C", 175.0, -370.3, 178.0, -374.3, 179.0, -378.3],
                    ["C", 180.0, -382.3, 182.0, -387.3, 183.0, -388.3],
                    ["C", 184.0, -389.3, 187.0, -394.3, 189.0, -399.3],
                    ["L", 192.0, -409.3],
                    ["L", 197.0, -409.3],
                    ["C", 202.0, -409.3, 202.0, -409.3, 202.0, -407.3],
                    ["C", 203.0, -403.3, 205.0, -392.3, 205.0, -383.3],
                    ["C", 206.0, -373.3, 208.0, -358.3, 210.0, -350.3],
                    ["C", 213.0, -341.3, 213.0, -339.3, 214.0, -325.3],
                    ["C", 215.0, -318.3, 216.0, -309.3, 217.0, -306.3],
                    ["C", 218.0, -303.3, 218.0, -298.3, 218.0, -296.3],
                    ["C", 218.0, -294.3, 219.0, -291.3, 220.0, -289.3],
                    ["C", 221.0, -286.3, 224.0, -269.3, 225.0, -248.3],
                    ["C", 226.0, -236.3, 228.0, -220.3, 231.0, -211.3],
                    ["C", 232.0, -206.3, 233.0, -186.3, 234.0, -152.3],
                    ["C", 234.0, -139.3, 235.0, -124.3, 235.0, -120.3],
                    ["C", 235.0, -116.3, 236.0, -108.3, 237.0, -102.3],
                    ["C", 237.0, -96.3, 238.0, -88.3, 239.0, -83.3],
                    ["C", 241.0, -72.3, 243.0, -54.3, 244.0, -38.3],
                    ["C", 244.0, -31.3, 245.0, -19.3, 246.0, -10.3],
                    ["C", 247.0, -1.3, 248.0, 12.7, 248.0, 19.7],
                    ["C", 248.0, 26.7, 249.0, 37.7, 250.0, 43.7],
                    ["C", 252.0, 57.7, 252.0, 83.7, 253.0, 159.7],
                    ["C", 253.0, 193.7, 255.0, 235.7, 256.0, 253.7],
                    ["C", 257.0, 271.7, 258.0, 296.7, 258.0, 308.7],
                    ["C", 258.0, 320.7, 258.0, 336.7, 259.0, 344.7],
                    ["C", 261.0, 362.7, 262.0, 399.7, 263.0, 495.7],
                    ["C", 264.0, 544.7, 264.0, 580.7, 265.0, 603.7],
                    ["C", 266.0, 622.7, 268.0, 650.7, 268.0, 665.7],
                    ["C", 268.0, 680.7, 270.0, 697.7, 270.0, 701.7],
                    ["C", 271.0, 709.7, 272.0, 744.7, 273.0, 821.7],
                    ["C", 274.0, 855.7, 274.0, 873.7, 275.0, 880.7],
                    ["C", 276.0, 885.7, 277.0, 892.7, 277.0, 895.7],
                    ["C", 277.0, 898.7, 278.0, 905.7, 279.0, 909.7],
                    ["C", 280.0, 913.7, 281.0, 925.7, 282.0, 934.7],
                    ["C", 284.0, 956.7, 285.0, 963.7, 289.0, 971.7],
                    ["C", 291.0, 975.7, 293.0, 979.7, 294.0, 981.7],
                    ["C", 295.0, 983.7, 297.0, 985.7, 298.0, 986.7],
                    ["C", 299.0, 987.7, 301.0, 989.7, 302.0, 990.7],
                    ["C", 303.0, 991.7, 309.0, 998.7, 316.0, 1005.7],
                    ["C", 323.0, 1012.7, 330.0, 1019.7, 332.0, 1021.7],
                    ["C", 335.0, 1023.7, 337.0, 1025.7, 340.0, 1026.7],
                    ["C", 342.0, 1027.7, 345.0, 1028.7, 346.0, 1029.7],
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

    // Per-glyph Sx multiplier (relative to the base SURD_NATURAL_SCALE).
    // uniE000 is drawn with thicker strokes than radical; rendering at a
    // smaller Sx thins them AND shrinks the natural pixel height, so Ny
    // extension has somewhere to grow into for in-between surd heights.
    const SURD_SX_FACTOR_PER_GLYPH = {
        radical: 1.0,
        uniE000: 0.80,
    };
    // Downward nudge for the bar (fraction of fontSize), from
    // vinculumRect.top.  Only safe for SHORT single-line radicands
    // (sqrt(π)) that have no superscript/ascender near the bar: there
    // vinculumRect.top leaves the bar floating high, so we pull it down to
    // the character.  For taller radicands (b² superscript, fractions)
    // vinculumRect.top already clears the content and nudging down would
    // drive the bar into the superscript, so the nudge is 0.  uniE000 is
    // always tall; it gets a tiny fixed nudge.
    //
    // The "short" test keys off the VINCULUM height (the radicand box),
    // NOT surdRect.height — the latter is always ≈1.0×fontSize regardless
    // of the radicand, so it can't tell sqrt(π) from sqrt(b²).  Measured
    // ratios: sqrt(π)≈0.77, sqrt(b²)≈0.93, sqrt(b²−4ac)≈0.97 → 0.85 splits
    // the no-ascender case from the superscript cases.
    const SURD_SHORT_THRESHOLD_FRAC = 0.85;
    const SURD_SHORT_NUDGE_FRAC = 0.28;  // radical, short radicands (down)
    // Tall radicals (b² superscript etc): our hand-drawn bar is thicker than
    // MathJax's 1px border, so anchored at vinculumRect.top its lower edge
    // dips into the superscript.  Lift it slightly (negative = up) so the
    // bar clears the ascender.
    const SURD_TALL_NUDGE_FRAC  = 0.10; // radical, tall radicands (down)
    const SURD_E000_NUDGE_FRAC  = 0.10;  // uniE000, any height

    function _pickSurd(targetH_units_at_naturalRadicalScale) {
        const natH = EXTENSIBLE_GLYPHS.radical.bbox.ymax -
                     EXTENSIBLE_GLYPHS.radical.bbox.ymin;
        return targetH_units_at_naturalRadicalScale > natH * TALL_SURD_RATIO
            ? 'uniE000' : 'radical';
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
    function buildSurdSvg(barWidthPx, renderedHeightPx, name, baseSx) {
        const g    = EXTENSIBLE_GLYPHS[name];
        const bb   = g.bbox;
        const natH = bb.ymax - bb.ymin;
        const natW = bb.xmax - bb.xmin;
        // Per-glyph Sx — thinner-stroke glyphs (uniE000) render at a smaller
        // px-per-unit so their drawn strokes don't dominate visually.
        const Sx = baseSx * (SURD_SX_FACTOR_PER_GLYPH[name] || 1.0);
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
    // Horizontal lead-in between the surd's stem corner and the start of
    // the radicand.  For the radical glyph it scales with surd height (the
    // corner region grows with the glyph, so taller radicands like the
    // quadratic formula crowd a fixed gap) but never drops below a
    // fontSize-based floor for short cases.  uniE000's shallow stem needs
    // only a small fixed gap.
    const SURD_LEADING_RADICAL_FRAC = 0.16; // × fontSize
    // uniE000: a moderately tall radicand (quadratic formula) crowds the
    // stem with too little lead-in, but a very tall one (deeply nested)
    // looks over-spaced with a big gap.  So taper leading DOWN as the surd
    // grows: leading = BASE×fontSize − TAPER×surdHeight, clamped at FLOOR.
    const SURD_LEADING_E000_BASE_FRAC   = 0.22; // × fontSize
    const SURD_LEADING_E000_TAPER_FRAC  = 0.045; // × surd height
    const SURD_LEADING_E000_FLOOR_FRAC  = 0.05; // × fontSize
    // Extra bar length past the radicand's right edge for short single-line
    // radicands (fraction of fontSize), so e.g. sqrt(π)'s bar doesn't end
    // abruptly at the glyph.
    const SURD_TRAILING_FRAC = 0.12;
    // Render the bar SVG at this multiple of the CSS border height.  The
    // emdash glyph's bbox is the full visible stroke, so >1× makes the
    // visible bar thicker than the typeset reference.  ~2× matches the
    // density of the previous hand-drawn bar visually.
    const BAR_PIXEL_MULT = 2;

    function replaceSqrtSymbols(root) {
        const scope = root || document;
        scope.querySelectorAll('mjx-msqrt').forEach(msqrt => {
            if (msqrt.dataset.sqrtReplaced) return;
            msqrt.dataset.sqrtReplaced = '1';

            const surd = msqrt.querySelector('mjx-surd');
            if (!surd) return;

            // The radicand's vinculum (a CSS border-top in MathJax's CHTML)
            // gives us the bar's intended width and left edge.
            let vinculumEl = null;
            for (const el of msqrt.querySelectorAll('*')) {
                if (el.closest('mjx-surd')) continue;
                const nearestFrac = el.closest('mjx-mfrac');
                if (nearestFrac && msqrt.contains(nearestFrac)) continue;
                const cs = getComputedStyle(el);
                if (cs.borderTopStyle === 'solid' && parseFloat(cs.borderTopWidth) > 0) {
                    vinculumEl = el; break;
                }
            }

            const surdRect     = surd.getBoundingClientRect();
            const msqrtRect    = msqrt.getBoundingClientRect();
            const vinculumRect = vinculumEl ? vinculumEl.getBoundingClientRect() : null;

            const fontSizePx = parseFloat(getComputedStyle(msqrt).fontSize);
            const Sx = fontSizePx / SURD_NATURAL_SCALE;

            // Glyph pick is based on the radicand height (vincH) in units
            // at the radical's base scale, so deeply-nested expressions
            // (tall vincH) switch to uniE000 while inline/superscript
            // cases stay on radical.
            const _radicandH_initial = vinculumRect ? vinculumRect.height : surdRect.height;
            const glyphName = _pickSurd(_radicandH_initial / Sx);
            const leadingPx  = glyphName === 'radical'
                ? fontSizePx * SURD_LEADING_RADICAL_FRAC
                : Math.max(fontSizePx * SURD_LEADING_E000_FLOOR_FRAC,
                           fontSizePx * SURD_LEADING_E000_BASE_FRAC
                             - _radicandH_initial * SURD_LEADING_E000_TAPER_FRAC);
            // Radicand height comes from the vinculum box; surdRect.height
            // is a constant ≈1.0×fontSize and useless as a height signal.
            const radicandH = _radicandH_initial;
            const isShort    = radicandH <= fontSizePx * SURD_SHORT_THRESHOLD_FRAC;
            const trailingPx = isShort ? fontSizePx * SURD_TRAILING_FRAC : 0;
            const barWidthPx = (vinculumRect ? vinculumRect.width : surdRect.height)
                             + leadingPx + trailingPx;

            // Nudge depends on glyph + isShort.  Compute it before sizing
            // the surd so we can target a uniform tick-below-radicand
            // distance regardless of how far down the bar is nudged.
            const nudgeFrac = glyphName === 'uniE000'
                ? SURD_E000_NUDGE_FRAC
                : (isShort ? SURD_SHORT_NUDGE_FRAC : SURD_TALL_NUDGE_FRAC);
            const nudgePx = fontSizePx * nudgeFrac;

            // Surd's full rendered height — bar top to tick bottom.  We want
            // the tick to land DESCENDER_FRAC×fontSize below the radicand's
            // bottom for all cases; since the bar is at vincTop + nudge,
            // that means rendered = radicandH + descender − nudge.
            const renderedHeightPx = Math.max(
                radicandH + fontSizePx * SURD_DESCENDER_FRAC - nudgePx,
                fontSizePx * SURD_MIN_HEIGHT_FRAC);

            const built = buildSurdSvg(barWidthPx, renderedHeightPx, glyphName, Sx);

            // Anchor the bar-corner junction `leadingPx` to the left of the
            // bar's intended start, and vertically at vinculumRect.top —
            // i.e. where MathJax actually draws the bar.  surdRect.top is
            // a few px above this because the surd character has empty
            // space above its visible bar, and using it put our bar too
            // high above the radicand on inline expressions.
            const barLeft = vinculumRect
                ? vinculumRect.left - msqrtRect.left
                : surdRect.right   - msqrtRect.left;
            const barTop  = vinculumRect
                ? vinculumRect.top  - msqrtRect.top
                : surdRect.top      - msqrtRect.top;
            // nudgePx was already computed above (needed for height calc).
            const svgLeft = barLeft - leadingPx - built.junctionPx.x;
            const svgTop  = barTop  - built.junctionPx.y + nudgePx;

            surd.dataset.xkcdHidden = '1';
            surd.style.visibility = 'hidden';
            if (vinculumEl) { vinculumEl.dataset.xkcdHidden = '1'; vinculumEl.style.borderTopColor = 'transparent'; }
            if (getComputedStyle(msqrt).position === 'static') { msqrt.dataset.xkcdPos = '1'; msqrt.style.position = 'relative'; }

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
        // 'xkcd-script-math' carries only the display-sized large operators
        // (∑, ∏, ∫).  Everything else — letters, Greek, the math italic/bold
        // codepoint aliases, the cdot — lives in 'xkcd-script', which sits
        // next in the fallback chain so MathJax can resolve those codepoints.
        const STACK = "'xkcd-script-math', 'xkcd-script', MJXTEX, MJXTEX-I, MJXTEX-B, MJXTEX-BI, MJXTEX-S1, MJXTEX-S2, MJXTEX-S3, MJXTEX-S4, MJXTEX-A";
        const s = document.createElement('style');
        s.textContent = `
            mjx-container[jax="CHTML"] *,
            mjx-container[jax="CHTML"] *::before {
                font-family: ${STACK} !important;
            }
            /* Inline limits on ∏ and ∫ need extra right margin — MathJax uses
               pre-baked metrics that ignore our wider glyphs. */
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
        return document.fonts.load("1em 'xkcd-script-math'").catch(() => {});
    }

    let _resolveReady;
    const ready = new Promise(res => { _resolveReady = res; });

    function _afterInitialTypeset() {
        return Promise.all([_waitForFont(), _waitForDom()])
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
