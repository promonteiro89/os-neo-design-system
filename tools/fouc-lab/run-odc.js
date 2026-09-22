#!/usr/bin/env node
/**
 * Frame-capture measurement against a REAL deployed ODC app.
 *
 *     node tools/fouc-lab/run-odc.js https://<host>/ThemeFlashLab [cpuThrottle] [repeats]
 *
 * tools/fouc-lab/run.js reconstructs ODC's boot order locally from measurements;
 * this runs the same measurement inside ODC itself, so the bundle sizes, the
 * injection timing and the OnReady latency are the platform's own.
 *
 * A/B ON ONE APP, ONE LINE APART. Comparing a patched app against an unpatched
 * app would compare two different apps. Instead this loads ONE app twice and
 * intercepts TrueShade's script on the wire: the "patched" run inserts the
 * candidate line into the response body, the "unpatched" run serves it
 * untouched. Everything else — the app, the CSS, the bundle, ODC's boot order —
 * is byte-identical between the two runs.
 *
 * If the app is already pinned to a patched library revision the interception
 * is a no-op for the patched run and a removal for the unpatched one; either
 * direction is handled, and the run asserts which one it took.
 *
 * As in run.js, the verdict comes from PAINTED FRAMES. getComputedStyle reports
 * states the browser never paints, and gave the opposite answer once already.
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

/** Matches the URL ODC serves the library's script at, query string and all. */
const TRUESHADE_JS = /TrueShade[^/]*\.js(\?|$)/i;

/** The candidate line, and the anchor it is inserted after. */
const CALL = 'applyTheme(ensureSeeded());';
const ANCHOR = /(Theme\.GetStorageKey\s*=\s*getStorageKey;)/;

function patch(body) {
  if (body.includes(CALL)) return { body, state: 'already-patched' };
  if (!ANCHOR.test(body)) return { body, state: 'anchor-missing' };
  return { body: body.replace(ANCHOR, `$1\ntry { ${CALL} } catch (_) { }`), state: 'patched-on-wire' };
}

/**
 * Candidate 2: the patch, plus a `color-scheme` write on the root element.
 *
 * The pure-white canvas is painted by the browser before any stylesheet
 * applies, so no CSS rule can reach it. `color-scheme` set from script can —
 * but only if the script evaluates before that first paint. Whether it does is
 * exactly what this variant measures.
 */
function patchScheme(body) {
  const base = patch(body);
  if (base.state === 'anchor-missing') return base;
  const call = "try { var _r = resolve(ensureSeeded()); document.documentElement.style.colorScheme = _r; } catch (_) { }";
  return { body: base.body.replace(ANCHOR, `$1\n${call}`), state: base.state + '+scheme' };
}

/**
 * Candidate 3: the patch, plus an INLINE background on the root element.
 *
 * Why this exists. Measurement showed the light frame is painted while
 * data-theme is ALREADY dark, because the only stylesheet that knows what
 * [data-theme="dark"] means — NeoBase — is not yet live, while OutSystemsUI's
 * light background is. Setting the attribute earlier therefore cannot help.
 * An inline style needs no stylesheet at all, so it is the only write that can
 * beat the cascade. Injected here for measurement; the fix itself belongs in
 * the design system, which is what knows these colours.
 */
function patchInline(body) {
  const base = patch(body);
  if (base.state === 'anchor-missing') return base;
  const call = "try { if (resolve(ensureSeeded()) === 'dark') {" +
    " var s = document.createElement('style');" +
    " s.textContent = 'html,body{background-color:#181a1f !important;color:#f9fafb}';" +
    " document.head.appendChild(s);" +
    " document.documentElement.style.colorScheme = 'dark'; } } catch (_) { }";
  return { body: base.body.replace(ANCHOR, `$1\n${call}`), state: base.state + '+inline' };
}

function unpatch(body) {
  if (!body.includes(CALL)) return { body, state: 'already-unpatched' };
  return { body: body.split(CALL).join('/* removed for baseline */;'), state: 'unpatched-on-wire' };
}

/**
 * TWO DISTINCT LIGHT WINDOWS, MEASURED SEPARATELY.
 *
 *   canvas  pure white (255,255,255) — the browser's own canvas, painted before
 *           any stylesheet has applied. No CSS and no JS inside the app can
 *           reach it; only an inline <head> script setting color-scheme can,
 *           and ODC's generated index.html has nowhere to put one. The patch
 *           is not expected to move this number, and reporting it mixed in
 *           with the next one would hide whether the patch did anything.
 *
 *   page    the app's own light page background — the stylesheets have applied
 *           but data-theme has not been set yet. THIS is the window the patch
 *           exists to close, and the only number the comparison turns on.
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

async function run(browser, decoder, { transform, os }) {
  const context = await browser.newContext({ viewport: { width: 600, height: 500 }, colorScheme: os });
  const page = await context.newPage();

  let state = null;
  await page.route(TRUESHADE_JS, async (route) => {
    const res = await route.fetch();
    const out = transform(await res.text());
    state = out.state;
    await route.fulfill({ response: res, body: out.body });
  });

  // First load: let the app boot, then store the dark preference. Prefer
  // clicking the app's own control, so the storage key is TrueShade's rather
  // than one guessed here; fall back to deriving the key the way TrueShade
  // does for apps that expose no such button.
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
  return { seq, state, canvasMs: window_(seq, (c) => c === WHITE), pageMs: window_(seq, isPageLight) };
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
  console.log('  canvas = pure white before any stylesheet (no fix can reach it)');
  console.log('  page   = the app\'s light background before data-theme is set (what the patch targets)\n');

  for (const os of ['light', 'dark']) {
    console.log(`  --- operating system preference: ${os} ---`);
    for (const [label, transform] of [['unpatched', unpatch], ['patched', patch], ['patch+scheme', patchScheme], ['patch+inline', patchInline]]) {
      const canvas = [], pageW = [];
      let state = null, last = null;
      for (let i = 0; i < REPEATS; i++) {
        const r = await run(browser, decoder, { transform, os });
        if (r.state === null) throw new Error('TrueShade\'s script was never requested — wrong URL, or the app does not use it');
        if (String(r.state).startsWith('anchor-missing')) throw new Error('the served script has no `Theme.GetStorageKey = getStorageKey;` to insert after');
        state = r.state; last = r.seq;
        canvas.push(r.canvasMs); pageW.push(r.pageMs);
      }
      console.log(`  ${label.padEnd(12)} [${state.padEnd(24)}] canvas ${String(median(canvas)).padStart(4)}ms   page ${String(median(pageW)).padStart(4)}ms` +
                  `   (page runs: ${pageW.join(', ')})`);
      console.log(`  ${' '.repeat(12)}  last trail: ${last.map((f) => `${f.rgb}@${f.t}ms`).join('  ->  ')}`);
    }
    console.log('');
  }

  await browser.close();
})().catch((e) => { console.error(e.message); process.exit(1); });
