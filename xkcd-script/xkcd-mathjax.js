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

    // ── Hand-drawn wibble helpers ───────────────────────────────────────────
    // Deterministic pseudo-random in [-1, 1]; seed decorrelates independent
    // segments (e.g. the two mirrored halves of a fraction bar).
    function _wibbleRand(seed) {
        const r = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
        return (r - Math.floor(r)) * 2 - 1;
    }

    // Width of the reflection-flat zone in path units (~3px in typical bars).
    const _FLAT_HALF_PATH = 12;

    function _taperWindow(t, reflT, taperT) {
        if (reflT == null) return 1;
        return Math.min(1, Math.abs(t - reflT) / taperT);
    }

    function _spliceFlatZone(anchors, reflT, segDx, naturalY) {
        if (reflT == null || reflT <= 0 || reflT >= 1) return;
        const flatHalf = _FLAT_HALF_PATH / Math.abs(segDx);
        if (flatHalf >= 0.5 || reflT - flatHalf <= 0 || reflT + flatHalf >= 1) return;
        const flatY = naturalY(reflT);
        for (let i = anchors.length - 1; i >= 0; i--) {
            const t = anchors[i].t;
            if (t > reflT - flatHalf && t < reflT + flatHalf) anchors.splice(i, 1);
        }
        anchors.push({ t: reflT - flatHalf, y: flatY });
        anchors.push({ t: reflT + flatHalf, y: flatY });
        anchors.sort((a, b) => a.t - b.t);
    }

    function _emitLineDeltas(anchors, dx) {
        const parts = [];
        for (let i = 0; i < anchors.length - 1; i++) {
            const segDx = (anchors[i + 1].t - anchors[i].t) * dx;
            const segDy = anchors[i + 1].y - anchors[i].y;
            parts.push(`${(+segDx.toFixed(1))} ${(+segDy.toFixed(1))}`);
        }
        return parts.join(' ');
    }

    // Replace a relative `dx,dy` line with N jittered sub-segments.  reflT/
    // taperT suppress jitter near a known reflection point (mirrored render).
    function wibbleLine(dx, dy, n, amp, seed, reflT, taperT) {
        const anchors = [];
        for (let i = 0; i <= n; i++) {
            const t = i / n;
            const w = (i === 0 || i === n) ? 0
                    : Math.sin(Math.PI * t) * _taperWindow(t, reflT, taperT);
            const j = _wibbleRand(seed * 7.0 + i + 1) * amp * w;
            anchors.push({ t, y: t * dy + j });
        }
        _spliceFlatZone(anchors, reflT, dx, t => t * dy);
        return _emitLineDeltas(anchors, dx);
    }

    // Subdivide a relative cubic into N jittered sub-cubics by sampling the
    // curve at t=i/n.  Final anchor stays on the original endpoint so
    // downstream commands continue correctly.
    function wibbleCubic(p1, p2, p3, n, amp, seed, reflT, taperT) {
        const sample = t => {
            const u = 1 - t;
            return [
                3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0],
                3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1],
            ];
        };
        const anchors = [];
        for (let i = 0; i <= n; i++) {
            const t = i / n;
            const xy = (i === 0) ? [0, 0] : sample(t);
            const w = (i === 0 || i === n) ? 0
                    : Math.sin(Math.PI * t) * _taperWindow(t, reflT, taperT);
            const j = _wibbleRand(seed * 11.0 + i) * amp * w;
            anchors.push({ t, x: xy[0], y: xy[1] + j });
        }
        if (reflT != null && reflT > 0 && reflT < 1) {
            const flatHalf = _FLAT_HALF_PATH / Math.abs(p3[0]);
            if (flatHalf < 0.5 && reflT - flatHalf > 0 && reflT + flatHalf < 1) {
                const flatY = sample(reflT)[1];
                for (let i = anchors.length - 1; i >= 0; i--) {
                    const t = anchors[i].t;
                    if (t > reflT - flatHalf && t < reflT + flatHalf) anchors.splice(i, 1);
                }
                const left  = sample(reflT - flatHalf);
                const right = sample(reflT + flatHalf);
                anchors.push({ t: reflT - flatHalf, x: left[0],  y: flatY });
                anchors.push({ t: reflT + flatHalf, x: right[0], y: flatY });
                anchors.sort((a, b) => a.t - b.t);
            }
        }
        const out = [];
        const f = v => +v.toFixed(1);
        for (let i = 0; i < anchors.length - 1; i++) {
            const cur = anchors[i];
            const nxt = anchors[i + 1];
            const dx = nxt.x - cur.x;
            const dy = nxt.y - cur.y;
            out.push(`${f(dx/3)},${f(dy/3)} ${f(2*dx/3)},${f(2*dy/3)} ${f(dx)},${f(dy)}`);
        }
        return out.join(' ');
    }

    // ── Hand-drawn vinculum (mirrored half-path approach) ───────────────────
    const BAR_ORIGINAL_PATH = `M408 592
c-52 -2 -90 -8 -96 -15
-5 -7 -20 -48 -32 -92
-12 -44 -35 -123 -51 -175
-15 -52 -35 -121 -44 -153
-9 -31 -20 -57 -23 -57
-4 0 -18 23 -31 51
-35 73 -60 102 -76 89
-18 -15 88 -225 113 -225
13 0 25 24 49 100
47 149 68 219 99 331
l28 102
400 5
c221 3 522 6 670 6
148 0 271 2 273 5
3 3 3 12 -1 21
-5 14 -65 16 -598 13
-326 -2 -632 -4 -680 -6
z`;

    const BAR_BASE_W  = 170;
    const BAR_PATH_H  = 61;
    const BAR_LEFT_X  = 79;
    const BAR_VB_H    = 8;

    function buildBarPath(delta, seed, reflX) {
        const d       = delta * 10;
        const forward = 400 + d;
        const r       = (1278 + d) / 1278;
        const f1      = x => +(x * r).toFixed(1);
        const segCount = Math.max(6, Math.round(forward / 60));
        const amp      = 2.75;
        const fwdEndX      = 436 + forward + 942;
        const bottomStartX = 436;
        const top1StartX   = fwdEndX;
        const top2StartX   = fwdEndX - 598 * r;
        const taperT = 0.30;
        const reflBottom = reflX != null ? (reflX - bottomStartX) / forward    : null;
        const reflTop1   = reflX != null ? (reflX - top1StartX)   / (-598 * r) : null;
        const reflTop2   = reflX != null ? (reflX - top2StartX)   / (-680 * r) : null;
        const bottom = wibbleLine(forward, 5, segCount, amp, seed, reflBottom, taperT);
        const top1   = wibbleCubic([f1(-5), 14],   [f1(-65), 16],   [f1(-598), 13],
                                   5, amp, seed + 31, reflTop1, taperT);
        const top2   = wibbleCubic([f1(-326), -2], [f1(-632), -4],  [f1(-680), -6],
                                   5, amp, seed + 53, reflTop2, taperT);
        return BAR_ORIGINAL_PATH
            .replace(/400 5/, bottom)
            .replace(/-5 14 -65 16 -598 13/, top1)
            .replace(/-326 -2 -632 -4 -680 -6/, top2);
    }

    // Mirrored hand-drawn bar of given pixel dimensions.  Both halves render
    // the same path; same seed keeps the join continuous, and buildBarPath
    // tapers jitter and inserts a flat segment exactly at the reflection x.
    function mirrorBarHTML(pixelWidth, pixelHeight) {
        const Sx      = pixelHeight / BAR_VB_H;
        const halfPt  = pixelWidth / 2 / Sx / 3;
        const maxHalf = BAR_BASE_W - BAR_LEFT_X;
        const delta   = Math.max(0, halfPt - maxHalf);
        const totalW  = BAR_BASE_W + delta;
        const cx      = totalW - halfPt;
        const path    = buildBarPath(delta, 5, cx * 10);
        const svgH    = pixelHeight * 3;
        const hw      = pixelWidth / 2;
        const sx      = hw / halfPt;
        const sy      = svgH / BAR_VB_H;
        const a       =  0.1 * sx;
        const d       = -0.1 * sy;
        const e       = -cx * sx;
        const f       =  BAR_PATH_H * sy;
        const matR    = `matrix(${a},0,0,${d},${e},${f})`;
        const matL    = `matrix(${-a},0,0,${d},${hw - e},${f})`;
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${pixelWidth}px" height="${svgH}px" style="display:block">
          <svg x="0" y="0" width="${hw}" height="${svgH}">
            <path transform="${matL}" d="${path}" fill="currentColor" stroke="none"/>
          </svg>
          <svg x="${hw}" y="0" width="${hw}" height="${svgH}">
            <path transform="${matR}" d="${path}" fill="currentColor" stroke="none"/>
          </svg>
        </svg>`;
    }

    // ── Hand-drawn sqrt surd ────────────────────────────────────────────────
    const BAR_TOP_SVG_Y      = 1;
    const SURD_HEIGHT_SVG    = 656;
    const SVG_CONTENT_H      = 659;
    const BAR_JUNC_SVG_X     = 150.4;
    const BAR_NAT_SVG_W      = 188.2;
    const SURD_GAP_SVG       = 60;
    const SURD_BAR_NUDGE_SVG = 40;
    const SURD_BAR_NUDGE_PX  = 2;

    const SURD_PATH = `m 1320,3691 c -8,-6 -17,-8 -21,-6 -6,4 -140,-124 -164,-156 -5,-8 -23,-31 -38,-52 -32,-43 -46.3589,-214.6662 -67,-412 -21,-234 -89,-3429 -124,-3680 -30.43312,-217.37946 -45.22736,-513.5633 -54,-690 -34.12704,-184.7142 -42.94822,-375.7902 -82,-560 -5,-22 -16,-96 -26,-165 -9,-69 -20,-133 -23,-143 -5,-13 -19,12 -50,87 -24,58 -46,106 -50,108 -5,2 -25,48 -46,103 -51.37238,134.5467 -85,187.2366 -85,214 0,30 -132,155 -240,228 -76,51 -117,30 -215,-112 -40,-57 -44,-94 -16,-145 11,-19 28,-53 40,-76 36.056956,-72.1139 54.23868,-33.8922 165,-319 26,-66 59,-149 73,-185 33,-81 136,-281 173,-335 26,-39 94,-151 159,-265 98.64586,-208.7933 330.01201,-101.8829 368,-19 41,87 69,230 162,804 5,33 30,177 54,320 25,143 45,274 45,290 1,17 9,77 20,135 11,58 8,136 11,175 15,164 36,553 60,690 16,89 67,3152 76,3300 3,55 10,173 17,261 l 11,161 51,-13 c 124,-31 1699,-37 1882,-24 186,13 237,7 310,-15 37,-11 47,-10 85,7 24,10 46,22 49,26 3,5 26,21 52,37 34,21 52,42 63,69 16,38 15,41 -9,89 -14,27 -26,60 -26,73 0,28 -37,84 -56,84 -6,0 -31,9 -54,19 -39,17 -66,19 -359,16 -451,-4 -1904,7 -2091,79 -8,3 -22,2 -30,-3 z`;

    const _f = x => +x.toFixed(1);

    function buildSurdPath(dw, dh, wibbleAmp) {
        const hDownScale = (3680 + dh) / 3680;
        const hUpScale   = (3300 + dh) / 3300;
        const wFwdScale  = (1882 + dw) / 1882;
        const wRetScale  = (2091 + dw) / 2091;
        const amp = wibbleAmp != null ? wibbleAmp : 30;
        const fwdReplacement = wibbleCubic(
            [124  * wFwdScale, -31],
            [1699 * wFwdScale, -37],
            [1882 * wFwdScale, -24],
            6, amp, 5);
        const retReplacement = wibbleCubic(
            [-451  * wRetScale, -4],
            [-1904 * wRetScale,  7],
            [-2091 * wRetScale, 79],
            6, amp, 23);
        return SURD_PATH
            .replace(`-21,-234 -89,-3429 -124,-3680`,
                     `-21,${_f(-234*hDownScale)} -89,${_f(-3429*hDownScale)} -124,${_f(-3680*hDownScale)}`)
            .replace(`16,89 67,3152 76,3300`,
                     `16,${_f(89*hUpScale)} 67,${_f(3152*hUpScale)} 76,${_f(3300*hUpScale)}`)
            .replace(`124,-31 1699,-37 1882,-24`, fwdReplacement)
            .replace(`-451,-4 -1904,7 -2091,79`, retReplacement);
    }

    // ── Replacement passes ──────────────────────────────────────────────────
    function replaceSqrtSymbols(root) {
        const scope = root || document;
        scope.querySelectorAll('mjx-msqrt').forEach(msqrt => {
            if (msqrt.dataset.sqrtReplaced) return;
            msqrt.dataset.sqrtReplaced = '1';

            const surd = msqrt.querySelector('mjx-surd');
            if (!surd) return;

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

            const Sx     = parseFloat(getComputedStyle(msqrt).fontSize) / SURD_HEIGHT_SVG * 1.5;
            const W_bar  = vinculumRect ? vinculumRect.width : surdRect.height;
            const dh     = (surdRect.height / Sx - SURD_HEIGHT_SVG) * 10;
            const dw     = (W_bar / Sx + SURD_GAP_SVG - BAR_NAT_SVG_W) * 10;

            const vbW = 400 + dw * 0.1;
            const vbH = SVG_CONTENT_H + dh * 0.1 + 20;

            const vincLeft = vinculumRect
                ? vinculumRect.left - msqrtRect.left
                : surdRect.right   - msqrtRect.left;
            const svgLeft = vincLeft - (BAR_JUNC_SVG_X + SURD_GAP_SVG) * Sx;
            const svgTop  = (surdRect.top - msqrtRect.top) - (BAR_TOP_SVG_Y - SURD_BAR_NUDGE_SVG) * Sx + SURD_BAR_NUDGE_PX;

            surd.dataset.xkcdHidden = '1';
            surd.style.visibility = 'hidden';
            if (vinculumEl) { vinculumEl.dataset.xkcdHidden = '1'; vinculumEl.style.borderTopColor = 'transparent'; }
            if (getComputedStyle(msqrt).position === 'static') { msqrt.dataset.xkcdPos = '1'; msqrt.style.position = 'relative'; }

            // Short bars look better dead-straight; wibble on a ~10px stretch
            // reads as a kink rather than hand-drawn texture.
            const wibbleAmp = W_bar < 40 ? 0 : Math.min(60, 1.0 / (0.1 * Sx));
            msqrt.insertAdjacentHTML('beforeend',
                `<svg class="xkcd-overlay" xmlns="http://www.w3.org/2000/svg"
                    width="${vbW * Sx}px" height="${vbH * Sx}px" viewBox="0 0 ${vbW} ${vbH}"
                    style="position:absolute;overflow:visible;left:${svgLeft}px;top:${svgTop}px;pointer-events:none;">
                  <g transform="matrix(0.1,0,0,-0.1,0,370)" fill="currentColor" stroke="none">
                    <path d="${buildSurdPath(dw, dh, wibbleAmp)}"/>
                  </g>
                </svg>`);
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
                const left = elRect.left - containerRect.left;
                const top  = elRect.top  - containerRect.top - 1.5 * barH;

                container.insertAdjacentHTML('beforeend',
                    `<div class="xkcd-overlay" style="position:absolute;left:${left}px;top:${top}px;pointer-events:none;">${mirrorBarHTML(elRect.width, barH)}</div>`);
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
