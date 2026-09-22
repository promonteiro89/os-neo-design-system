#!/usr/bin/env node
/**
 * FOUC lab runner.
 *
 *     node tools/fouc-lab/run.js
 *
 * Serves tools/fouc-lab over http and, for each candidate fix, records the
 * PAINTED frames with CDP's screencast and reports the colour of every frame
 * until the page settles.
 *
 * WHY PAINTED FRAMES AND NOT getComputedStyle. Polling computed style reports
 * states the user never sees: a stylesheet can apply, and be superseded, before
 * the browser paints at all. An earlier round of this investigation called a
 * candidate a failure on that basis, when the light value it saw was never on
 * screen. Only frames prove what a person actually sees.
 *
 * Frames arrive as base64 PNGs, which Node cannot decode on its own, so each is
 * handed to a second page and read back through a canvas.
 */

'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = __dirname;
const REPO = path.dirname(path.dirname(ROOT));

/**
 * The lab runs against the real stylesheets and the real TrueShade, but none of
 * them are committed: two are large vendor files already living elsewhere in
 * this repo, and the third belongs to another app. Assemble them on demand.
 */
function ensureAssets() {
  const dir = path.join(ROOT, 'assets');
  fs.mkdirSync(dir, { recursive: true });
  const copies = [
    ['osui.css', path.join(REPO, 'reference', 'raw', 'outsystems-ui-theme.css')],
    ['neobase.css', path.join(REPO, 'dist', 'neobase.css')],
  ];
  for (const [name, src] of copies) {
    const dst = path.join(dir, name);
    if (!fs.existsSync(dst)) {
      if (!fs.existsSync(src)) throw new Error('missing source for ' + name + ': ' + src);
      fs.copyFileSync(src, dst);
    }
  }
  if (!fs.existsSync(path.join(dir, 'trueshade.js'))) {
    throw new Error('tools/fouc-lab/assets/trueshade.js is missing.\n' +
      '  Fetch it from a deployed app that references TrueShade, e.g.\n' +
      '  curl -s "<app>/scripts/TrueShade.UserScripts.TrueShade__<hash>.js" -o tools/fouc-lab/assets/trueshade.js');
  }
}
const PORT = 8899;
const TYPES = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript' };

function serve() {
  return new Promise((resolve) => {
    const s = http.createServer((req, res) => {
      const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '') || 'index.html';
      const file = path.join(ROOT, rel);
      if (!file.startsWith(ROOT) || !fs.existsSync(file)) { res.writeHead(404); return res.end(); }
      res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
      fs.createReadStream(file).pipe(res);
    });
    s.listen(PORT, () => resolve(s));
  });
}

/** Read the centre pixel of each base64 PNG, using the browser as the decoder. */
async function decode(page, frames) {
  return page.evaluate((list) => Promise.all(list.map((f) => new Promise((res) => {
    const img = new Image();
    img.onload = () => {
      const c = document.createElement('canvas');
      c.width = img.width; c.height = img.height;
      const g = c.getContext('2d');
      g.drawImage(img, 0, 0);
      const [r, gr, b] = g.getImageData(Math.floor(img.width / 2), Math.floor(img.height * 0.6), 1, 1).data;
      res({ t: f.t, rgb: `${r},${gr},${b}` });
    };
    img.onerror = () => res({ t: f.t, rgb: 'decode-error' });
    img.src = 'data:image/png;base64,' + f.data;
  }))), frames);
}

const LIGHTISH = (rgb) => {
  const [r, g, b] = rgb.split(',').map(Number);
  return (r + g + b) / 3 > 140;            // anything pale enough to read as a flash
};

async function runVariant(browser, decoder, fix, cpu, os) {
  const page = await browser.newPage({ viewport: { width: 500, height: 400 }, colorScheme: os });
  const cdp = await page.context().newCDPSession(page);
  const BOOT = process.env.LAB_BOOT || '300';
  await page.goto(`http://localhost:${PORT}/index.html?fix=${fix}&theme=dark&boot=${BOOT}&init=${process.env.LAB_INIT||'250'}`);
  await page.waitForSelector('html[data-lab-settled]', { timeout: 15000 }).catch(() => {});

  const frames = [];
  cdp.on('Page.screencastFrame', async (f) => {
    frames.push({ t: Date.now(), data: f.data });
    try { await cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }); } catch (e) {}
  });

  if (cpu > 1) await cdp.send('Emulation.setCPUThrottlingRate', { rate: cpu });
  await cdp.send('Page.startScreencast', { format: 'png', everyNthFrame: 1 });

  const t0 = Date.now();
  await page.reload({ waitUntil: 'commit' }).catch(() => {});
  await page.waitForSelector('html[data-lab-settled]', { timeout: 20000 }).catch(() => {});
  await page.waitForTimeout(400);
  await cdp.send('Page.stopScreencast').catch(() => {});
  await page.close();

  const read = await decode(decoder, frames.map((f) => ({ t: f.t - t0, data: f.data })));
  const seq = [];
  for (const f of read) if (!seq.length || seq[seq.length - 1].rgb !== f.rgb) seq.push(f);
  const flashed = seq.some((f) => LIGHTISH(f.rgb));
  return { fix, frames: read.length, flashed, seq };
}

(async () => {
  ensureAssets();
  const server = await serve();
  const browser = await chromium.launch();
  const decoder = await browser.newPage();
  await decoder.goto('about:blank');

  const cpu = Number(process.argv[2] || 4);
  console.log(`painted frames per variant, CPU x${cpu}, stored choice = dark, boot=${process.env.LAB_BOOT||300}ms\n`);

  for (const os of ['light', 'dark']) {
    console.log(`\n  --- operating system preference: ${os} ---`);
    for (const fix of ['none', 'selfapply', 'cssbundle', 'combo', 'headscheme']) {
      const r = await runVariant(browser, decoder, fix, cpu, os);
      const trail = r.seq.map((f) => `${f.rgb}@${f.t}ms`).join('  ->  ');
      console.log(`  ${fix.padEnd(11)} light frame: ${r.flashed ? 'YES' : 'no '}   ${trail}`);
    }
  }

  await browser.close();
  server.close();
})();
