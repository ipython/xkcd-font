#!/usr/bin/env node
/**
 * Render PNG samples of MathJax CHTML formulae through xkcd-mathjax.js.
 * Overwrites the committed PNGs in this directory.  Use `git diff` /
 * `git status` to see what changed.
 */

const fs = require('fs');
const path = require('path');
const http = require('http');
const url = require('url');
const { chromium } = require('playwright');

const HERE = __dirname;
const REPO_ROOT = path.resolve(HERE, '..', '..', '..');
const FORMULAS = JSON.parse(fs.readFileSync(path.join(HERE, 'formulas.json'), 'utf8'));

// Pixels of whitespace padding around each formula (CSS pixels; effective
// raster padding is PAD * DEVICE_SCALE).
const PAD = 16;
// Output raster density.  Layout (font-size, line-height, clip box) stays
// identical to a real 22px render; only the bitmap resolution doubles.
const DEVICE_SCALE = 2;

// ── Per-formula HTML (served inline; no separate template file) ─────────────
function renderTemplate(tex, display) {
    const json = s => JSON.stringify(s);
    return `<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
    html, body { margin:0; padding:0; background:#fff;
                 font-family:'xkcd-script', sans-serif;
                 font-size:22px; line-height:1.6; color:#111; }
    #m { display:inline-block; padding:4px; }
</style>
<script>
    MathJax = { tex: { inlineMath:  [['$','$'], ['\\\\(','\\\\)']],
                       displayMath: [['$$','$$'], ['\\\\[','\\\\]']] } };
</script>
<script src="/xkcd-script/xkcd-mathjax.js"></script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
</head><body>
<div id="m"></div>
<script>
    document.getElementById('m').textContent =
        ${display ? `'$$' + ${json(tex)} + '$$'` : `'$' + ${json(tex)} + '$'`};
    window.__xkcdReady = false;
    XkcdMathJax.ready.then(() => { window.__xkcdReady = true; });
</script>
</body></html>`;
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
                res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8',
                                     'Cache-Control': 'no-store' });
                res.end(renderTemplate(parsed.query.tex || '',
                                       parsed.query.display === '1'));
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

// ── Render one formula → PNG buffer ──────────────────────────────────────────
async function renderOne(page, baseUrl, entry) {
    const display = entry.display ? '1' : '0';
    await page.goto(`${baseUrl}/sample?tex=${encodeURIComponent(entry.tex)}&display=${display}`,
                    { waitUntil: 'load' });
    await page.waitForFunction(() => window.__xkcdReady === true, null,
                               { timeout: 15000 });
    await page.evaluate(() => document.fonts.ready);

    const box = await page.locator('mjx-container').first().boundingBox();
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

    for (const entry of FORMULAS) {
        const buf = await renderOne(page, baseUrl, entry);
        fs.writeFileSync(path.join(HERE, `${entry.name}.png`), buf);
        console.log(`wrote ${entry.name}.png`);
    }

    await browser.close();
    server.close();
    console.log(`\n${FORMULAS.length} sample${FORMULAS.length === 1 ? '' : 's'} written.`);
})().catch(e => { console.error(e); process.exit(2); });
