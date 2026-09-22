#!/usr/bin/env node
/**
 * Frame-capture measurement of the dark-mode reload flash on a deployed ODC app.
 *
 *     node tools/fouc-lab/run-odc.js https://<host>/NeoLayoutCheck/Home [cpu] [repeats]
 *
 * A/B ON ONE APP. Loads the app twice per cell and intercepts the app's own
 * `ThemePaint` script (NeoLayoutCheck.UserScripts.ThemePaint.js) on the wire:
 * "with" serves it untouched, "without" serves an empty body. Everything else —
 * the app, the stylesheets, ODC's boot order — is byte-identical.
 *
 * TWO INSTRUMENT LESSONS, BOTH LEARNED THE HARD WAY:
 *
 *   1. Painted frames, not getComputedStyle, which reports states the browser
 *      never paints.
 *   2. Mean luminance of the WHOLE frame, not one pixel. An earlier version
 *      sampled one pixel at 70% of the height, which on this screen sits on a
 *      content surface, and it reported colours unrelated to the theme. That
 *      probe is what produced a wrong "stylesheet ordering" diagnosis.
 *      "The screen looks white" is a whole-frame property.
 *
 * Two light states are reported separately, because only one is the script's
 * job: the pure white canvas (mean luminance ~255) before anything paints, and
 * the light theme (~246) painted while the stored choice is dark.
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

const THEME_PAINT_JS = /UserScripts\.ThemePaint[^/]*\.js(\?|$)/i;

const isWhite = (l) => l >= 252;              // the canvas, nothing painted yet
const isLight = (l) => l > 140 && l < 252;    // the light theme, painted by mistake

/** Decode base64 PNGs through a second page; Node has no PNG decoder. */
async function luminance(page, frames) {
  return page.evaluate((list) => Promise.all(list.map((f) => new Promise((res) => {
    const img = new Image();
    img.onload = () => {
      const c = document.createElement('canvas');
      c.width = img.width; c.height = img.height;
      const g = c.getContext('2d');
      g.drawImage(img, 0, 0);
      const d = g.getImageData(0, 0, img.width, img.height).data;
      let sum = 0, n = 0;
      for (let i = 0; i < d.length; i += 16) { sum += 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2]; n++; }
      res({ t: f.t, l: Math.round(sum / n) });
    };
    img.onerror = () => res({ t: f.t, l: -1 });
    img.src = 'data:image/png;base64,' + f.data;
  }))), frames);
}

function spent(seq, pred) {
  let ms = 0;
  for (let i = 0; i < seq.length; i++) {
    if (!pred(seq[i].l)) continue;
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

  // Store dark the way TrueShade keys it: the first path segment is the app name.
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await page.evaluate(() => {
    const seg = location.pathname.split('/').filter(Boolean)[0] || '';
    localStorage.setItem('$OS_' + seg + '$layout-theme', 'dark');
  });
  await page.reload({ waitUntil: 'networkidle' });

  // Record when the script's marker appears, relative to the navigation.
  await page.addInitScript(() => {
    (function tick() {
      if (document.documentElement && document.documentElement.dataset.neoThemePaint && !window.__paintAt) {
        window.__paintAt = Math.round(performance.now());
      }
      if (!window.__paintAt) setTimeout(tick, 4);
    })();
  });

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
  await page.waitForTimeout(800);
  await cdp.send('Page.stopScreencast').catch(() => {});
  const paintAt = await page.evaluate(() => window.__paintAt || null).catch(() => null);
  const firstPaint = await page.evaluate(() => {
    const e = performance.getEntriesByName('first-paint')[0];
    return e ? Math.round(e.startTime) : null;
  }).catch(() => null);

  const read = await luminance(decoder, frames.map((f) => ({ t: f.t - t0, data: f.data })));
  await context.close();

  const seq = [];
  for (const f of read) if (!seq.length || Math.abs(seq[seq.length - 1].l - f.l) > 6) seq.push(f);
  return { seq, served, paintAt, firstPaint, whiteMs: spent(seq, isWhite), lightMs: spent(seq, isLight) };
}

const median = (xs) => {
  const s = xs.filter((x) => x != null).sort((a, b) => a - b);
  if (!s.length) return null;
  return s.length % 2 ? s[(s.length - 1) / 2] : Math.round((s[s.length / 2 - 1] + s[s.length / 2]) / 2);
};

(async () => {
  const browser = await chromium.launch();
  const decoder = await browser.newPage();
  await decoder.goto('about:blank');

  console.log(`painted frames, CPU x${CPU}, ${REPEATS} reloads per cell, stored choice = dark`);
  console.log(`  ${BASE}`);
  console.log('  white = mean frame luminance >=252 (canvas)   light = 140-252 (light theme painted by mistake)\n');

  for (const os of ['light', 'dark']) {
    console.log(`  --- operating system preference: ${os} ---`);
    for (const [label, disable] of [['without', true], ['with', false]]) {
      const w = [], l = [], at = [], fp = [];
      let last = null;
      for (let i = 0; i < REPEATS; i++) {
        const r = await run(browser, decoder, { disable, os });
        if (!r.served) throw new Error('ThemePaint was never requested — is it in the app root\'s RequiredScripts?');
        w.push(r.whiteMs); l.push(r.lightMs); at.push(r.paintAt); fp.push(r.firstPaint); last = r.seq;
      }
      const tot = w.map((x, i) => x + l[i]);
      console.log(`  ThemePaint ${label.padEnd(8)} white ${String(median(w)).padStart(4)}ms  light ${String(median(l)).padStart(4)}ms  ` +
                  `total ${String(median(tot)).padStart(4)}ms   ran at ${label === 'with' ? median(at) + 'ms' : '-'}  first-paint ${median(fp)}ms`);
      console.log(`  ${' '.repeat(19)}trail: ${last.map((f) => `L${f.l}@${f.t}ms`).join(' -> ')}`);
    }
    console.log('');
  }
  await browser.close();
})().catch((e) => { console.error(e.message); process.exit(1); });
