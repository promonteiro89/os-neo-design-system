#!/usr/bin/env node
/**
 * Frame-capture measurement of the theme flash against a REAL deployed ODC app.
 *
 *     node tools/fouc-lab/run-odc.js https://<host>/NeoLayoutCheck/Home [cpu] [repeats]
 *
 * tools/fouc-lab/run.js reconstructs ODC's boot order locally; this runs inside
 * ODC, so the bundle sizes, the injection timing and the OnReady latency are the
 * platform's own. That distinction mattered: the local lab and the platform
 * disagreed, and the platform was right. See docs/theme-flash-on-reload.md.
 *
 * A/B ON ONE APP. Comparing a fixed app against an unfixed app compares two
 * apps. Instead this loads ONE app twice and intercepts NeoDesignSystem's
 * `NeoThemePaint` script on the wire: the "with" run serves it untouched, the
 * "without" run serves an empty body. Everything else — the app, the CSS, the
 * bundle, ODC's boot order — is byte-identical between the two runs.
 *
 * THE VERDICT COMES FROM PAINTED FRAMES. getComputedStyle reports states the
 * browser never paints and gave the opposite answer once already in this
 * investigation.
 */

'use strict';

const { chromium } = require('playwright');

const BASE = process.argv[2];
if (!BASE) {
  console.error('usage: node tools/fouc-lab/run-odc.js <app-url> [cpuThrottle] [repeats]');
  process.exit(2);
}
const CPU = Number(process.argv[3] || 4);
const REPEATS = Number(process.argv[4] || 5);

/** The URL ODC serves the script at, query string and all. */
const THEME_PAINT_JS = /NeoThemePaint[^/]*\.js(\?|$)/i;

/**
 * TWO DISTINCT LIGHT WINDOWS, MEASURED SEPARATELY.
 *
 *   canvas  pure white (255,255,255) — the browser's own canvas, painted before
 *           any stylesheet has applied. Nothing in an ODC app can reach it: the
 *           generated index.html carries only platform files, so at that point
 *           no app or library code exists yet. Reporting it mixed in with the
 *           next number would hide whether the fix did anything.
 *
 *   page    the app's own light page background — stylesheets have applied but
 *           the dark theme has not. THIS is the window the fix exists to close,
 *           and the only number the comparison turns on.
 */
const WHITE = '255,255,255';
const isPageLight = (rgb) => {
  if (rgb === WHITE) return false;
  const [r, g, b] = rgb.split(',').map(Number);
  return (r + g + b) / 3 > 140;
};

/** Decode base64 PNGs through a second page; Node has no PNG decoder. */
async function decode(page, frames) {
  return page.evaluate((list) => Promise.all(list.map((f) => new Promise((res) => {
    const img = new Image();
    img.onload = () => {
      const c = document.createElement('canvas');
      c.width = img.width; c.height = img.height;
      const g = c.getContext('2d');
      g.drawImage(img, 0, 0);
      const [r, gr, b] = g.getImageData(Math.floor(img.width / 2), Math.floor(img.height * 0.7), 1, 1).data;
      res({ t: f.t, rgb: `${r},${gr},${b}` });
    };
    img.onerror = () => res({ t: f.t, rgb: 'decode-error' });
    img.src = 'data:image/png;base64,' + f.data;
  }))), frames);
}

/** Milliseconds the sequence spent on frames matching `pred`. */
function window_(seq, pred) {
  let ms = 0;
  for (let i = 0; i < seq.length; i++) {
    if (!pred(seq[i].rgb)) continue;
    ms += (i + 1 < seq.length ? seq[i + 1].t : seq[i].t) - seq[i].t;
  }
  return ms;
}

async function run(browser, decoder, { disable, os }) {
  const context = await browser.newContext({ viewport: { width: 600, height: 500 }, colorScheme: os });
  const page = await context.newPage();

  let served = false;
  await page.route(THEME_PAINT_JS, async (route) => {
    served = true;
    const res = await route.fetch();
    await route.fulfill({ response: res, body: disable ? '/* disabled for baseline */' : await res.text() });
  });

  // Store the dark preference the way a user would where the app offers a
  // control, otherwise derive the key as TrueShade does: the first path
  // segment, since ODC's /<AppName>/ gives the app name.
  await page.goto(BASE, { waitUntil: 'networkidle' });
  const darkButton = page.getByRole('button', { name: /^Dark$/i });
  if (await darkButton.count()) {
    await darkButton.first().click();
  } else {
    await page.evaluate(() => {
      const seg = location.pathname.split('/').filter(Boolean)[0] || '';
      localStorage.setItem('$OS_' + seg + '$layout-theme', 'dark');
    });
    await page.reload({ waitUntil: 'networkidle' });
  }
  await page.waitForFunction(() => document.documentElement.dataset.theme === 'dark', null, { timeout: 20000 });

  const cdp = await context.newCDPSession(page);
  const frames = [];
  cdp.on('Page.screencastFrame', async (f) => {
    frames.push({ t: Date.now(), data: f.data });
    try { await cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }); } catch (e) {}
  });
  if (CPU > 1) await cdp.send('Emulation.setCPUThrottlingRate', { rate: CPU });
  await cdp.send('Page.startScreencast', { format: 'png', everyNthFrame: 1 });

  const t0 = Date.now();
  await page.reload({ waitUntil: 'commit' }).catch(() => {});
  await page.waitForFunction(() => document.documentElement.dataset.theme === 'dark', null, { timeout: 30000 })
    .catch(() => {});
  await page.waitForTimeout(600);
  await cdp.send('Page.stopScreencast').catch(() => {});

  const read = await decode(decoder, frames.map((f) => ({ t: f.t - t0, data: f.data })));
  await context.close();

  const seq = [];
  for (const f of read) if (!seq.length || seq[seq.length - 1].rgb !== f.rgb) seq.push(f);
  return { seq, served, canvasMs: window_(seq, (c) => c === WHITE), pageMs: window_(seq, isPageLight) };
}

const median = (xs) => {
  const s = [...xs].sort((a, b) => a - b);
  return s.length % 2 ? s[(s.length - 1) / 2] : Math.round((s[s.length / 2 - 1] + s[s.length / 2]) / 2);
};

(async () => {
  const browser = await chromium.launch();
  const decoder = await browser.newPage();
  await decoder.goto('about:blank');

  console.log(`painted frames, CPU x${CPU}, ${REPEATS} reloads per cell, stored choice = dark\n  ${BASE}\n`);
  console.log('  canvas = pure white before any stylesheet (unreachable from an ODC app)');
  console.log('  page   = the light page background before the theme applies (what NeoThemePaint closes)\n');

  for (const os of ['light', 'dark']) {
    console.log(`  --- operating system preference: ${os} ---`);
    for (const [label, disable] of [['without', true], ['with', false]]) {
      const canvas = [], pageW = [];
      let last = null;
      for (let i = 0; i < REPEATS; i++) {
        const r = await run(browser, decoder, { disable, os });
        if (!r.served) throw new Error('NeoThemePaint was never requested — the app is not on a library revision that ships it');
        last = r.seq;
        canvas.push(r.canvasMs); pageW.push(r.pageMs);
      }
      console.log(`  NeoThemePaint ${label.padEnd(8)} canvas ${String(median(canvas)).padStart(4)}ms   page ${String(median(pageW)).padStart(4)}ms` +
                  `   (page runs: ${pageW.join(', ')})`);
      console.log(`  ${' '.repeat(22)}last trail: ${last.map((f) => `${f.rgb}@${f.t}ms`).join('  ->  ')}`);
    }
    console.log('');
  }

  await browser.close();
})().catch((e) => { console.error(e.message); process.exit(1); });
