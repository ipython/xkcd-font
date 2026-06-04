#!/usr/bin/env node
/**
 * Render PNG samples of MathJax CHTML formulae through xkcd-mathjax3.js.
 * Overwrites the committed PNGs in this directory.  Use `git diff` /
 * `git status` to see what changed.
 *
 * formulas.yaml shape: top-level keys are output-PNG basenames; each maps
 * to `{ formulas: [...], cellWidth?, cellHeight? }`.  Single-formula
 * groups render with a tight bbox (as before).  Multi-formula groups
 * render in a fixed-size CSS grid so that editing one formula does not
 * shift the rendered position of its siblings.
 */

const fs = require('fs');
const path = require('path');
const http = require('http');
const url = require('url');
const yaml = require('js-yaml');
const { chromium } = require('playwright');

const HERE = __dirname;
const REPO_ROOT = path.resolve(HERE, '..', '..', '..');
const GROUPS = yaml.load(fs.readFileSync(path.join(HERE, 'formulas.yaml'), 'utf8'));

// Pixels of whitespace padding around each formula (CSS pixels; effective
// raster padding is PAD * DEVICE_SCALE).
const PAD = 16;
// Output raster density.  Layout (font-size, line-height, clip box) stays
// identical to a real 22px render; only the bitmap resolution doubles.
const DEVICE_SCALE = 2;
// Grid-cell defaults for multi-formula groups (override per group in yaml).
const DEFAULT_CELL_W = 560;
const DEFAULT_CELL_H = 72;

// Build the per-group MathJax bootstrap.  Each YAML group may carry a
// `mathjax:` block declaring which TeX-input packages to load and
// whether equation tagging should be enabled — e.g.
//
//     amscd-commutative-diagram:
//       mathjax: { packages: [amscd] }
//
//     align-eqref:
//       mathjax: { packages: [ams], tags: ams }
//
// Groups that omit `mathjax:` get the bare default (no extras, no
// tagging).  Loading packages per-group keeps each sample as close as
// possible to the minimal MathJax surface its formulae actually need.
function head(group) {
    const mj = group.mathjax || {};
    const packages = mj.packages || [];
    const tags = mj.tags;
    const load = packages.map(p => `[tex]/${p}`);
    const tex = {
        inlineMath:  [['$', '$'], ['\\(', '\\)']],
        displayMath: [['$$', '$$'], ['\\[', '\\]']],
    };
    if (packages.length) tex.packages = { '[+]': packages };
    if (tags) tex.tags = tags;
    const config = { loader: { load }, tex };
    return `<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
    html, body { margin:0; padding:0; background:#fff;
                 font-family:'xkcd-script', sans-serif;
                 font-size:22px; line-height:1.6; color:#111; }
</style>
<script>window.MathJax = ${JSON.stringify(config)};</script>
<script src="/xkcd-script/xkcd-mathjax3.js"></script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
</head><body>`;
}

function readyScript() {
    return `<script>
    window.__xkcdReady = false;
    XkcdMathJax.ready.then(() => { window.__xkcdReady = true; });
</script>
</body></html>`;
}

// Set each cell's text content via DOM rather than embedding LaTeX directly
// in HTML — avoids any quirks around how MathJax's TeX input scanner reads
// entity-encoded characters (&, <, >) that appear naturally in math.
function setTextScript(idToTex) {
    const lines = Object.entries(idToTex).map(
        ([id, tex]) => `    document.getElementById(${JSON.stringify(id)}).textContent = ${JSON.stringify(tex)};`
    );
    return `<script>\n${lines.join('\n')}\n</script>`;
}

function renderSingle(group) {
    return `${head(group)}
<div id="m" style="display:inline-block;padding:4px"></div>
${setTextScript({m: group.formulas[0].tex})}
${readyScript()}`;
}

function renderGrid(group, cellW, cellH) {
    const formulas = group.formulas;
    // Each cell wraps its content in an inner <div> so the flex container has
    // a single flex item.  Without the wrapper, flex blockifies the cell's
    // direct children — text runs and the <mjx-container> become separate
    // flex items each centered independently by `align-items: center`, which
    // discards MathJax's `vertical-align` and drops the math baseline below
    // the text baseline.  The wrapper preserves a normal inline formatting
    // context inside, so baselines align as they do in a real browser page.
    const cells = formulas
        .map((_, i) => `<div class="cell"><div class="content" id="c${i}"></div></div>`)
        .join('\n');
    const idToTex = Object.fromEntries(formulas.map((f, i) => [`c${i}`, f.tex]));
    return `${head(group)}
<style>
    #grid { display: grid;
            grid-template-columns: ${cellW}px;
            grid-template-rows: repeat(${formulas.length}, ${cellH}px);
            width: ${cellW}px; }
    #grid .cell { padding: 0 32px; box-sizing: border-box;
                  display: flex; align-items: center;
                  overflow: visible; }
    #grid .content { width: 100%; }
</style>
<div id="grid">${cells}</div>
${setTextScript(idToTex)}
${readyScript()}`;
}

function renderGroup(group) {
    if (group.formulas.length === 1 && !group.cellHeight && !group.cellWidth) {
        return { html: renderSingle(group), selector: 'mjx-container' };
    }
    const cellW = group.cellWidth  || DEFAULT_CELL_W;
    const cellH = group.cellHeight || DEFAULT_CELL_H;
    return { html: renderGrid(group, cellW, cellH), selector: '#grid' };
}

// ── Static server: inline HTML at /sample, files from repo root elsewhere ────
const MIME = {
    '.js':   'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.css':  'text/css; charset=utf-8',
    '.woff': 'font/woff', '.woff2': 'font/woff2',
    '.otf':  'font/otf',  '.ttf':   'font/ttf',
    '.png':  'image/png', '.svg':   'image/svg+xml',
};

function startServer() {
    return new Promise(resolve => {
        const server = http.createServer((req, res) => {
            const parsed = url.parse(req.url, true);
            if (parsed.pathname === '/sample') {
                const key = parsed.query.key;
                const group = GROUPS[key];
                if (!group) { res.writeHead(404); res.end('unknown group'); return; }
                const { html } = renderGroup(group);
                res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8',
                                     'Cache-Control': 'no-store' });
                res.end(html);
                return;
            }
            const safe = path.normalize(decodeURIComponent(parsed.pathname))
                             .replace(/^([/\\])+/, '');
            const filePath = path.join(REPO_ROOT, safe);
            if (!filePath.startsWith(REPO_ROOT)) {
                res.writeHead(403); res.end('forbidden'); return;
            }
            fs.readFile(filePath, (err, data) => {
                if (err) { res.writeHead(404); res.end('not found'); return; }
                res.writeHead(200, {
                    'Content-Type': MIME[path.extname(filePath).toLowerCase()]
                                    || 'application/octet-stream',
                    'Cache-Control': 'no-store',
                });
                res.end(data);
            });
        });
        server.listen(0, '127.0.0.1', () => resolve(server));
    });
}

// ── Render one group → PNG buffer ────────────────────────────────────────────
async function renderOne(page, baseUrl, key, group) {
    await page.goto(`${baseUrl}/sample?key=${encodeURIComponent(key)}`,
                    { waitUntil: 'load' });
    await page.waitForFunction(() => window.__xkcdReady === true, null,
                               { timeout: 15000 });
    // Iterate document.fonts.ready until the set stops growing.  MathJax CHTML
    // requests fallback fonts (MJXTEX-* for codepoints xkcd-script doesn't
    // cover) lazily during paint — a single fonts.ready check resolves before
    // those late requests start, leaving operators like =, ≥, ≤ unrendered
    // when we screenshot.  Poll across rAF until the FontFaceSet size is
    // stable across two consecutive ticks.
    await page.evaluate(async () => {
        const raf = () => new Promise(r => requestAnimationFrame(r));
        let prev = -1;
        for (let i = 0; i < 20; i++) {
            await document.fonts.ready;
            await raf();
            const size = document.fonts.size;
            if (size === prev) return;
            prev = size;
        }
    });

    const { selector } = renderGroup(group);
    const box = await page.locator(selector).first().boundingBox();
    const clip = {
        x: Math.max(0, Math.floor(box.x) - PAD),
        y: Math.max(0, Math.floor(box.y) - PAD),
        width:  Math.ceil(box.width)  + 2 * PAD,
        height: Math.ceil(box.height) + 2 * PAD,
    };
    return await page.screenshot({ clip });
}

// ── Main ─────────────────────────────────────────────────────────────────────
(async () => {
    const server = await startServer();
    const baseUrl = `http://127.0.0.1:${server.address().port}`;

    const browser = await chromium.launch();
    const context = await browser.newContext({
        viewport: { width: 1200, height: 600 },
        deviceScaleFactor: DEVICE_SCALE,
    });
    const page = await context.newPage();

    const keys = Object.keys(GROUPS);
    for (const key of keys) {
        const buf = await renderOne(page, baseUrl, key, GROUPS[key]);
        fs.writeFileSync(path.join(HERE, `${key}.png`), buf);
        console.log(`wrote ${key}.png`);
    }

    await browser.close();
    server.close();
    console.log(`\n${keys.length} group${keys.length === 1 ? '' : 's'} written.`);
})().catch(e => { console.error(e); process.exit(2); });
