const { chromium } = require('playwright');
const BASE = 'https://mc-dev.outsystems.app/NeoLayoutCheck/Home';
const PAINT_JS = /NeoThemePaint[^/]*\.js(\?|$)/i;
const TRUESHADE_JS = /TrueShade[^/]*\.js(\?|$)/i;
// Mean luminance above this reads as a light screen. Dark theme settles around
// 40-50; the light page and the white canvas both sit far above it.
const isLightScreen = (mean) => Number(mean) > 140;
async function decode(page, frames) {
  return page.evaluate((list) => Promise.all(list.map((f) => new Promise((res) => {
    const img = new Image();
    img.onload = () => {
      const c = document.createElement('canvas');
      c.width = img.width; c.height = img.height;
      const g = c.getContext('2d'); g.drawImage(img, 0, 0);
      // Mean luminance of the WHOLE frame. A single sample point is fragile:
      // at 70% height this screen shows a content surface, not the page
      // background, so a pixel probe reported colours that had nothing to do
      // with the theme. "The screen looks white" is a whole-frame property.
      const d = g.getImageData(0, 0, img.width, img.height).data;
      let sum = 0, n = 0;
      for (let i = 0; i < d.length; i += 16) { sum += 0.2126*d[i] + 0.7152*d[i+1] + 0.0722*d[i+2]; n++; }
      res({ t: f.t, rgb: String(Math.round(sum / n)) });
    };
    img.onerror = () => res({ t: f.t, rgb: 'x' });
    img.src = 'data:image/png;base64,' + f.data;
  }))), frames);
}
function win(seq, pred) { let ms=0; for (let i=0;i<seq.length;i++){ if(!pred(seq[i].rgb)) continue; ms += (i+1<seq.length?seq[i+1].t:seq[i].t)-seq[i].t; } return ms; }
const median = xs => { const s=[...xs].sort((a,b)=>a-b); return s.length%2?s[(s.length-1)/2]:Math.round((s[s.length/2-1]+s[s.length/2])/2); };

async function run(browser, decoder, mode, paintSrc) {
  const ctx = await browser.newContext({ viewport: { width: 600, height: 500 }, colorScheme: 'light' });
  const p = await ctx.newPage();
  // Always neutralise the real (late) NeoThemePaint so only the variable varies.
  await p.route(PAINT_JS, r => r.fulfill({ status: 200, contentType: 'text/javascript', body: '/* disabled */' }));
  const EARLY = {
    // (b) set data-theme at script-evaluation time and nothing else
    attr: "try{var k='$OS_'+(location.pathname.split('/').filter(Boolean)[0]||'')+'$layout-theme';"
        + "var v=localStorage.getItem(k)||'system-default';"
        + "var d=v==='dark'||(v==='system-default'&&matchMedia('(prefers-color-scheme: dark)').matches);"
        + "document.documentElement.dataset.theme=d?'dark':'light';}catch(e){}",
    // (c) our shipped script, injected so that it evaluates early
    paint: paintSrc,
    // (d) the same idea but painting BODY as well as HTML. body's computed
    // background is rgb(249,250,251) at 441ms despite reset.css declaring it
    // transparent, so an html-only paint is covered over and invisible.
    body: "try{var k='$OS_'+(location.pathname.split('/').filter(Boolean)[0]||'')+'$layout-theme';"
        + "var v=localStorage.getItem(k)||'system-default';"
        + "var d=v==='dark'||(v==='system-default'&&matchMedia('(prefers-color-scheme: dark)').matches);"
        + "if(d){var st=document.createElement('style');"
        + "st.textContent='html,body{background-color:#181a1f !important;color:#f9fafb !important}';"
        + "(document.head||document.documentElement).appendChild(st);}}catch(e){}",
  };
  if (mode !== 'off') {
    await p.route(TRUESHADE_JS, async (route) => {
      const res = await route.fetch();
      await route.fulfill({ response: res, body: (await res.text()) + '\n;' + EARLY[mode] });
    });
  }
  await p.goto(BASE, { waitUntil: 'networkidle' });
  await p.evaluate(() => { const s = location.pathname.split('/').filter(Boolean)[0]||''; localStorage.setItem('$OS_'+s+'$layout-theme','dark'); });
  await p.reload({ waitUntil: 'networkidle' });

  const cdp = await ctx.newCDPSession(p);
  const frames = [];
  cdp.on('Page.screencastFrame', async f => { frames.push({t:Date.now(),data:f.data}); try{await cdp.send('Page.screencastFrameAck',{sessionId:f.sessionId});}catch(e){} });
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  await cdp.send('Page.startScreencast', { format:'png', everyNthFrame:1 });
  const t0 = Date.now();
  await p.reload({ waitUntil: 'commit' }).catch(()=>{});
  await p.waitForFunction(() => document.documentElement.dataset.theme === 'dark', null, {timeout:30000}).catch(()=>{});
  await p.waitForTimeout(600);
  await cdp.send('Page.stopScreencast').catch(()=>{});
  const read = await decode(decoder, frames.map(f => ({ t: f.t-t0, data: f.data })));
  await ctx.close();
  const seq = []; for (const f of read) if (!seq.length || Math.abs(Number(seq[seq.length-1].rgb) - Number(f.rgb)) > 6) seq.push(f);
  return { seq, pageMs: win(seq, isLightScreen) };
}

(async () => {
  const paintSrc = require('fs').readFileSync('behaviour/theme-paint.js', 'utf8');
  const browser = await chromium.launch();
  const decoder = await browser.newPage(); await decoder.goto('about:blank');
  console.log('What actually closes the flash? (the real, late NeoThemePaint is disabled in every run)');
console.log('metric: mean frame luminance; >140 counts as a light screen\n');
  for (const [label, mode] of [
    ['baseline (nothing early)', 'off'],
    ['data-theme set early', 'attr'],
    ['theme-paint.js early (html)', 'paint'],
    ['html AND body early', 'body'],
  ]) {
    const runs = []; let last = null;
    for (let i=0;i<3;i++) { const r = await run(browser, decoder, mode, paintSrc); runs.push(r.pageMs); last = r.seq; }
    console.log(`  ${label.padEnd(28)} page light ${String(median(runs)).padStart(4)}ms   (runs: ${runs.join(', ')})`);
    console.log(`  ${' '.repeat(28)} trail: ${last.map(f=>`L${f.rgb}@${f.t}ms`).join('  ->  ')}`);
  }
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
