#!/usr/bin/env node
/**
 * Browser tests against the deployed ODC app.
 *
 *     node tools/test_browser.js            run everything
 *     node tools/test_browser.js -v         also log each step
 *     node tools/test_browser.js --headed   watch it happen
 *
 * Exits non-zero on failure.
 *
 * WHY THIS EXISTS. tools/test.py proves the repo builds what it says it builds.
 * tools/test_runtime.py proves the deployed app is SERVING that. Neither one
 * executes a page, so neither can tell you a component still works: a dropdown
 * that no longer opens, a handler bound twice by a re-render, an empty state
 * that lost its second line, a validation rule that stopped marking fields.
 * Those only fail when something uses the component, which is what this does.
 *
 * This is the repository's only dependency. It needs Playwright and a browser:
 *
 *     npm install
 *     npx playwright install chromium
 *
 * CONFIGURATION. Same as tools/test_runtime.py — the app's base URL comes from
 * the gitignored `odc-app` file (copy odc-app.example) or $ODC_APP.
 *
 * SELECTORS. Every selector below was read off the running page, not assumed.
 * Two are worth knowing because they look like bugs and are not:
 *
 *   - the password eye is #PasswordEye on VerifyEmail and #PasswordEyeIcon on
 *     Login. behaviour/password-reveal.js accepts either, so the test does too.
 *   - the dropdown trigger is NOT a tab stop. Tabbing into the dropdown lands
 *     in its search input, because the component opens on focus and hands
 *     keyboard control to virtual-select. That contract is asserted below.
 */

'use strict';

const fs = require('fs');
const path = require('path');

let chromium;
try {
  ({ chromium } = require('playwright'));
} catch (e) {
  console.error('Playwright is not installed.\n' +
                '  npm install && npx playwright install chromium');
  process.exit(2);
}

const ROOT = path.dirname(__dirname);
const VERBOSE = process.argv.includes('-v') || process.argv.includes('--verbose');
const HEADED = process.argv.includes('--headed');

const SCREENS = ['Home', 'Login', 'SignUp', 'VerifyEmail', 'ResetPassword'];

function baseUrl() {
  if (process.env.ODC_APP) return process.env.ODC_APP.replace(/\/+$/, '');
  const f = path.join(ROOT, 'odc-app');
  if (fs.existsSync(f)) {
    for (const line of fs.readFileSync(f, 'utf8').split('\n')) {
      const t = line.trim();
      if (t && !t.startsWith('#')) return t.replace(/\/+$/, '');
    }
  }
  return null;
}

// ---------------------------------------------------------------------------

const results = { passed: 0, failures: [] };

function ok(name, detail = '') {
  results.passed++;
  console.log(`  OK   ${name.padEnd(46)} ${detail}`);
}

function fail(name, detail) {
  results.failures.push([name, detail]);
  console.log(`  FAIL ${name.padEnd(46)} ${detail}`);
}

async function check(name, fn) {
  try {
    const detail = await fn();
    ok(name, detail || '');
  } catch (e) {
    fail(name, e.message.replace(/\s+/g, ' ').slice(0, 150));
  }
}

function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

/** Open a page, recording console errors and failed requests from the start. */
async function openPage(context, url) {
  const page = await context.newPage();
  const consoleErrors = [];
  const failedRequests = [];
  page.on('console', (m) => {
    if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 120));
  });
  page.on('pageerror', (e) => consoleErrors.push('pageerror: ' + e.message.slice(0, 120)));
  page.on('response', (r) => {
    if (r.status() >= 400) {
      failedRequests.push(`${r.status()} ${r.url().split('/').pop().slice(0, 60)}`);
    }
  });
  await page.goto(url, { waitUntil: 'networkidle', timeout: 45000 });
  return { page, consoleErrors, failedRequests };
}

// ---------------------------------------------------------------------------
// checks
// ---------------------------------------------------------------------------

/**
 * Every screen renders without a console error or a failed request.
 *
 * A fresh page per screen matters: the console buffer is per page, so reusing
 * one would attribute an earlier screen's error to a later one.
 */
async function checkScreensAreClean(context, base) {
  for (const screen of SCREENS) {
    await check(`${screen} loads clean`, async () => {
      const { page, consoleErrors, failedRequests } = await openPage(context, `${base}/${screen}`);
      const bodyText = await page.evaluate(() => document.body.innerText.trim().length);
      await page.close();
      assert(bodyText > 0, 'rendered an empty body');
      assert(consoleErrors.length === 0, `console: ${consoleErrors[0]}`);
      assert(failedRequests.length === 0, `request: ${failedRequests[0]}`);
      return 'no console errors, no failed requests';
    });
  }
}

/**
 * The dropdown opens, closes, and survives being toggled twice.
 *
 * Toggling twice is the re-entry test: ODC re-runs a block's OnReady on every
 * render, and a script that bound per run would stack handlers, so one click
 * would fire the toggle twice and the popover would end up back where it
 * started. Ending CLOSED after open-then-close is what proves single binding.
 */
async function checkDropdownOpensAndCloses(context, base) {
  await check('dropdown opens and closes', async () => {
    const { page } = await openPage(context, `${base}/VerifyEmail`);
    const state = () => page.evaluate(() => ({
      root: document.querySelector('.dropdown-empty')?.classList.contains('is--open'),
      pop: document.querySelector('.dropdown-empty-popover')?.classList.contains('is--open'),
      visible: (() => {
        const e = document.querySelector('.dropdown-empty-popover');
        if (!e) return false;
        return e.getBoundingClientRect().height > 0 && getComputedStyle(e).opacity !== '0';
      })(),
    }));

    const before = await state();
    assert(before.root === false, 'started open');

    await page.click('.dropdown-empty-trigger');
    await page.waitForTimeout(400);
    const open = await state();
    assert(open.root && open.pop, 'clicking the trigger did not set is--open');
    assert(open.visible, 'popover has is--open but is not visible');

    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
    const closed = await state();
    assert(closed.root === false && closed.pop === false, 'Escape did not close it');

    await page.close();
    return 'click opens, Escape closes, single-bound';
  });
}

/**
 * Searching for something that does not exist shows the portal's TWO-line
 * empty state, not OutSystemsUI's one-liner.
 *
 * This is the check that would have caught the regression where the block
 * forwarded OptionalConfigs.NoResultsText straight through and the portal text
 * was replaced by "There are no options to show."
 */
async function checkDropdownEmptyState(context, base) {
  await check('dropdown empty state is the portal one', async () => {
    const { page } = await openPage(context, `${base}/VerifyEmail`);
    await page.click('.dropdown-empty-trigger');
    await page.waitForTimeout(300);
    await page.fill('.vscomp-search-input', 'zzzqqqxx');
    await page.waitForTimeout(500);

    const found = await page.evaluate(() => {
      const e = [...document.querySelectorAll('.vscomp-no-search-results')]
        .find((n) => n.offsetParent !== null);
      if (!e) return null;
      return {
        text: e.innerText.replace(/\s+/g, ' ').trim(),
        helper: !!e.querySelector('.vscomp-no-search-results-helper-text'),
      };
    });
    await page.close();

    assert(found, 'no visible no-results element');
    assert(/No results found/i.test(found.text),
           `first line was "${found.text.slice(0, 60)}"`);
    assert(found.helper, 'the helper line is missing — this is the OSUI one-liner');
    return 'two lines, with the helper text';
  });
}

/**
 * Tabbing into the dropdown opens it and lands in its search input.
 *
 * The trigger is deliberately not a tab stop. virtual-select owns arrow keys,
 * type-ahead and Enter, and only while focus is inside its search box, so the
 * component opens on focus and hands over. If this breaks, the keyboard path
 * dies silently while the mouse path keeps working.
 */
async function checkDropdownKeyboardEntry(context, base) {
  await check('dropdown opens on keyboard focus', async () => {
    const { page } = await openPage(context, `${base}/VerifyEmail`);
    await page.evaluate(() => document.body.focus());

    let landed = null;
    for (let i = 0; i < 12 && !landed; i++) {
      await page.keyboard.press('Tab');
      await page.waitForTimeout(120);
      const inSearch = await page.evaluate(() =>
        !!document.activeElement &&
        document.activeElement.classList.contains('vscomp-search-input'));
      if (inSearch) landed = i + 1;
    }
    const isOpen = await page.evaluate(() =>
      document.querySelector('.dropdown-empty')?.classList.contains('is--open'));
    await page.close();

    assert(landed, 'tabbing never reached the dropdown search input');
    assert(isOpen, 'focus reached the search input but the dropdown is not open');
    return `open, focus in search after ${landed} tabs`;
  });
}

/**
 * The password reveal toggles the input between password and text.
 *
 * The eye's id differs per screen (#PasswordEye on VerifyEmail,
 * #PasswordEyeIcon on Login) and behaviour/password-reveal.js accepts either.
 */
async function checkPasswordReveal(context, base, screen) {
  await check(`${screen}: password reveal toggles`, async () => {
    const { page } = await openPage(context, `${base}/${screen}`);
    const eye = await page.evaluate(() =>
      document.getElementById('PasswordEye') ? '#PasswordEye'
        : (document.getElementById('PasswordEyeIcon') ? '#PasswordEyeIcon' : null));
    assert(eye, 'no password eye element found');

    const before = await page.getAttribute('#PasswordInput', 'type');
    assert(before === 'password', `input started as "${before}"`);

    await page.click(eye);
    await page.waitForTimeout(250);
    const shown = await page.getAttribute('#PasswordInput', 'type');

    await page.click(eye);
    await page.waitForTimeout(250);
    const hidden = await page.getAttribute('#PasswordInput', 'type');
    await page.close();

    assert(shown === 'text', `first click left it as "${shown}"`);
    assert(hidden === 'password', `second click left it as "${hidden}"`);
    return `${eye}, password -> text -> password`;
  });
}

/**
 * Submitting an empty form marks the invalid fields.
 *
 * Asserts the class the CSS actually keys off. A validation that runs but never
 * sets .not-valid looks identical to one that did not run at all.
 */
async function checkValidationOnSubmit(context, base, screen, submitSelector) {
  await check(`${screen}: submit marks invalid fields`, async () => {
    const { page } = await openPage(context, `${base}/${screen}`);
    const before = await page.evaluate(() => document.querySelectorAll('.not-valid').length);
    assert(before === 0, `${before} fields were already marked before submitting`);

    await page.click(submitSelector);
    await page.waitForTimeout(900);
    const after = await page.evaluate(() => document.querySelectorAll('.not-valid').length);
    await page.close();

    assert(after > 0, 'submitting an empty form marked nothing invalid');
    return `${after} field(s) marked`;
  });
}


/**
 * The checkbox is the same size at every viewport.
 *
 * OutSystemsUI enlarges checkboxes for touch — `.tablet [data-checkbox],
 * .phone [data-checkbox] { 32px }` — at a specificity our `.checkbox` rule
 * cannot beat. The portal ships its own override putting it back to --size-7,
 * and that override was being dropped by the reskin extractor, because its
 * selector carries no class the whitelist recognises: `[data-checkbox]` is an
 * attribute, and the only classes present are the viewport ones.
 *
 * Desktop looked right, which is exactly why it went unnoticed.
 */
async function checkCheckboxSizeIsStable(context, base) {
  await check('checkbox size is viewport-independent', async () => {
    const sizes = {};
    for (const [name, width, height] of
         [['desktop', 1280, 900], ['tablet', 768, 1024], ['phone', 375, 812]]) {
      const page = await context.newPage();
      await page.setViewportSize({ width, height });
      await page.goto(`${base}/VerifyEmail`, { waitUntil: 'networkidle', timeout: 45000 });
      sizes[name] = await page.evaluate(() => {
        const el = document.getElementById('TermsCheckbox');
        return el ? Math.round(el.getBoundingClientRect().width) : null;
      });
      await page.close();
      assert(sizes[name], `${name}: no TermsCheckbox found`);
    }
    const distinct = [...new Set(Object.values(sizes))];
    assert(distinct.length === 1,
           `desktop ${sizes.desktop}px, tablet ${sizes.tablet}px, phone ${sizes.phone}px`);
    return `${distinct[0]}px at desktop, tablet and phone`;
  });
}


/**
 * Clicking a sortable column header sorts the table and marks the header.
 *
 * Sorting is the platform's, driven by each header's Sort Attribute — clearing
 * that attribute kills sorting outright while leaving the header looking
 * identical. The `sorted` class is appended by TableRecords, so asserting BOTH
 * the class and a changed row order distinguishes "the platform ran the sort"
 * from "a class was painted on".
 *
 * The sort is over the whole dataset, not the visible page: names that were not
 * on page 1 before appear after, which is why this compares first cells rather
 * than expecting a permutation.
 */
async function checkTableSorting(context, base) {
  await check('Home: table sorts on header click', async () => {
    const { page } = await openPage(context, `${base}/Home`);
    await page.waitForTimeout(1200);

    const firstCells = () => page.evaluate(() =>
      [...document.querySelectorAll('tbody tr')].slice(0, 5)
        .map((r) => (r.querySelector('td')?.innerText || '').replace(/\s+/g, ' ').trim()));

    const headers = await page.$$('thead th.sortable');
    assert(headers.length > 0, 'no sortable headers — has the Sort Attribute been cleared?');

    const before = await firstCells();
    assert(before.length > 0, 'the table rendered no rows');

    await headers[0].click();
    await page.waitForTimeout(1000);
    const after = await firstCells();
    const marked = await page.evaluate(() =>
      document.querySelectorAll('thead th.sorted').length);
    await page.close();

    assert(marked > 0, 'no header gained the `sorted` class');
    assert(JSON.stringify(before) !== JSON.stringify(after),
           'the header was marked sorted but the rows did not move');
    return `${headers.length} sortable headers, order changed`;
  });
}

/**
 * Pagination pages the table, moves its active marker, and bounds its arrows.
 *
 * This strip is our own library block, not OutSystemsUI's: its window is
 * hand-built because OSUI's is wrong on middle pages. So the interesting
 * assertion is not page 2, it is that the window RE-CENTRES — on page 1 it
 * shows 1-4 and the last page, and by page 4 it has expanded to reach both
 * ends. A window frozen at "1 2 3 4 ... 7" would still pass a page-2-only test.
 */
async function checkPagination(context, base) {
  await check('Home: pagination pages and re-centres', async () => {
    const { page } = await openPage(context, `${base}/Home`);
    await page.waitForTimeout(1200);

    const snap = () => page.evaluate(() => ({
      first: (document.querySelector('tbody tr td')?.innerText || '')
               .replace(/\s+/g, ' ').trim(),
      rows: document.querySelectorAll('tbody tr').length,
      prev: document.querySelector('[id$=PrevButton]')?.disabled,
      next: document.querySelector('[id$=NextButton]')?.disabled,
      win: [...document.querySelectorAll('[id*=PageBtnDesktop]')]
             .filter((b) => b.offsetParent !== null)
             .map((b) => (b.innerText || '').trim()),
      active: [...document.querySelectorAll('[id*=PageBtnDesktop]')]
                .filter((b) => b.offsetParent !== null
                            && b.className.includes('--active'))
                .map((b) => (b.innerText || '').trim()),
    }));

    const goTo = async (n) => {
      for (const h of await page.$$('[id*=PageBtnDesktop]')) {
        if (!(await h.isVisible())) continue;
        if ((await h.innerText()).trim() === n) {
          await h.click();
          await page.waitForTimeout(1000);
          return true;
        }
      }
      return false;
    };

    const p1 = await snap();
    assert(p1.prev === true, 'Prev is enabled on the first page');
    assert(p1.next === false, 'Next is disabled on the first page');
    assert(p1.active[0] === '1', `active page is "${p1.active[0]}", not 1`);
    const last = p1.win[p1.win.length - 1];

    assert(await goTo('2'), 'page 2 was not in the window');
    const p2 = await snap();
    assert(p2.active[0] === '2', 'clicking 2 did not move the active marker');
    assert(p2.first !== p1.first, 'the rows did not change');
    assert(p2.prev === false, 'Prev is still disabled on page 2');

    const mid = String(Math.max(2, Math.ceil(Number(last) / 2)));
    assert(await goTo(mid), `middle page ${mid} was not in the window`);
    const pm = await snap();
    assert(pm.win.length >= p1.win.length,
           `window did not re-centre: page 1 showed ${p1.win.join(',')}, `
           + `page ${mid} shows ${pm.win.join(',')}`);

    assert(await goTo(last), `last page ${last} was not in the window`);
    const pl = await snap();
    await page.close();
    assert(pl.next === true, 'Next is still enabled on the last page');
    assert(pl.prev === false, 'Prev is disabled on the last page');
    return `${last} pages, window ${p1.win.join(',')} -> ${pm.win.join(',')}`;
  });
}

/**
 * Dark mode flips the tokens, and going back to light restores them.
 *
 * The bundle themes off an attribute on the root element; there is no
 * prefers-color-scheme support, so this is the only switch. Asserting the round
 * trip matters as much as the flip: a rule that hardcodes a dark value rather
 * than overriding a token would pass the first half and fail the second.
 */
async function checkDarkTheme(context, base) {
  await check('dark theme flips tokens, and back', async () => {
    const { page } = await openPage(context, `${base}/Login`);
    const read = () => page.evaluate(() => ({
      theme: document.documentElement.dataset.theme || '',
      bodyBg: getComputedStyle(document.body).backgroundColor,
      text: getComputedStyle(document.documentElement)
              .getPropertyValue('--text-primary').trim(),
      surface: getComputedStyle(document.documentElement)
                 .getPropertyValue('--surface-1-default').trim(),
    }));
    const setTheme = (t) =>
      page.evaluate((v) => { document.documentElement.dataset.theme = v; }, t);

    await setTheme('light');
    await page.waitForTimeout(250);
    const light = await read();

    await setTheme('dark');
    await page.waitForTimeout(250);
    const dark = await read();

    await setTheme('light');
    await page.waitForTimeout(250);
    const back = await read();
    await page.close();

    assert(dark.text !== light.text && dark.surface !== light.surface,
           'the token values did not change in dark');
    assert(dark.bodyBg !== light.bodyBg, 'the page background did not change');
    assert(back.text === light.text && back.surface === light.surface
             && back.bodyBg === light.bodyBg,
           'returning to light did not restore the light values');
    return `${light.surface} <-> ${dark.surface}`;
  });
}


/**
 * A well-formed email on SignUp navigates to VerifyEmail; a malformed one does
 * not, and marks the field.
 *
 * The rejection cases are the point. The first version of this validation
 * required a dot somewhere after the @ and nothing more, so "a@b." sailed
 * through to VerifyEmail — a happy-path-only test would have called that
 * working. Each case below is asserted in BOTH directions: navigating when it
 * should not is a failure, and so is refusing to.
 */
async function checkSignUpNavigatesOnValidEmail(context, base) {
  // Every rejection here was a real hole in an earlier version of this
  // validation. The first attempt was a chain of Index/Substr tests and it
  // accepted all eight of them; the check is now a single regex in a JS node.
  const CASES = [
    ['someone@example.com', true],
    ['first.last@sub.example.co.uk', true],
    ['a+tag@example.com', true],
    ["o'brien@example.com", true],
    ['', false],
    ['   ', false],
    ['notanemail', false],
    ['@example.com', false],
    ['a@b', false],
    ['a@b.', false],
    ['a@.com', false],
    ['a b@example.com', false],          // space in the local part
    ['a@ex ample.com', false],           // space in the domain
    ['a@@example.com', false],           // doubled @
    ['a@b@c.com', false],                // two @
    ['a@example..com', false],           // consecutive dots
    ['.a@example.com', false],           // leading dot in the local part
    ['a@-example.com', false],           // domain label starting with a hyphen
    ['a@example.c', false],              // single-character TLD
  ];
  await check('SignUp: valid email goes to VerifyEmail', async () => {
    const wrong = [];
    for (const [email, shouldNavigate] of CASES) {
      const page = await context.newPage();
      await page.goto(`${base}/SignUp`, { waitUntil: 'networkidle', timeout: 45000 });
      if (email) await page.fill('#EmailInput', email);
      await page.click('#ContinueButton');
      await page.waitForTimeout(1400);
      const navigated = /VerifyEmail/.test(page.url());
      const marked = await page.evaluate(() =>
        document.querySelectorAll('.not-valid').length);
      await page.close();

      if (navigated !== shouldNavigate) {
        wrong.push(`${JSON.stringify(email)} navigated=${navigated}`);
      } else if (!shouldNavigate && marked === 0) {
        wrong.push(`${JSON.stringify(email)} was rejected but not marked invalid`);
      }
    }
    assert(wrong.length === 0, wrong.join('; '));
    return `${CASES.length} addresses, ${CASES.filter((c) => c[1]).length} accepted`;
  });
}


/**
 * The portal chrome renders, at the portal's dimensions.
 *
 * The shell is a separate layer that has to be concatenated LAST, after the
 * components, icons and utilities — the same order the portal loads it in. Get
 * that wrong and the header and aside still render, still carry their classes,
 * and are simply the wrong size, which is invisible unless something measures
 * it. 56px and 256px are the portal's own chrome dimensions.
 *
 * The background assertions are the second half: a transparent header means the
 * shell layer's rules did not land at all, even though the markup is there.
 */
async function checkShellChrome(context, base) {
  await check('shell header and aside render', async () => {
    const { page } = await openPage(context, `${base}/Home`);
    await page.waitForTimeout(800);
    const shell = await page.evaluate(() => {
      const read = (sel) => {
        const e = document.querySelector(sel);
        if (!e) return null;
        const r = e.getBoundingClientRect();
        const c = getComputedStyle(e);
        return { w: Math.round(r.width), h: Math.round(r.height),
                 bg: c.backgroundColor, position: c.position };
      };
      return {
        header: read('.unified-header'),
        aside: read('.unified-aside'),
        asideItems: document.querySelectorAll('.unified-aside a, .unified-aside [class*=item]').length,
      };
    });
    await page.close();

    assert(shell.header, 'no .unified-header on the page');
    assert(shell.aside, 'no .unified-aside on the page');
    assert(shell.header.h === 56,
           `header is ${shell.header.h}px tall, the portal's is 56`);
    assert(shell.aside.w === 256,
           `aside is ${shell.aside.w}px wide, the portal's is 256`);
    assert(!/rgba\(0, 0, 0, 0\)|transparent/.test(shell.header.bg),
           'header has no background — the shell layer did not land');
    assert(!/rgba\(0, 0, 0, 0\)|transparent/.test(shell.aside.bg),
           'aside has no background — the shell layer did not land');
    assert(shell.asideItems > 0, 'the aside rendered no items');
    return `header ${shell.header.h}px, aside ${shell.aside.w}px, `
         + `${shell.asideItems} items`;
  });
}


/**
 * Reloading with dark stored must never paint the light theme.
 *
 * Guarded by the app's `ThemePaint` Script, listed in the app root's
 * RequiredScripts — the same mechanism the ODC Portal uses with its per-app
 * `Layout` script. It paints the stored theme's colour on <body> at app init,
 * before the stylesheets apply. Without it, the screen spends ~370ms in the
 * light theme after the white canvas and before the shell sets data-theme.
 *
 * TWO INSTRUMENT RULES, both learned by getting this wrong:
 *
 *   - PAINTED FRAMES, not getComputedStyle, which reports values the browser
 *     never paints.
 *   - MEAN LUMINANCE OF THE WHOLE FRAME, not one pixel. A single probe at 60-70%
 *     of the height sits on a content surface here and reported colours
 *     unrelated to the theme; it produced a wrong diagnosis once already.
 *
 * The pure white canvas (mean ~255) is NOT a failure. It precedes all app code,
 * and ODC's generated index.html carries nothing app-controlled. The portal has
 * it too. What must never appear is the light THEME (mean ~246), i.e. a frame
 * that is light but not blank.
 */
async function checkNoThemeFlash(context, base) {
  const WHITE = 252;    // at or above: the blank canvas, nothing painted yet
  const DARK = 140;     // at or below: dark theme
  await check('dark reload paints no light-theme frame', async () => {
    const page = await context.newPage();
    await page.setViewportSize({ width: 500, height: 400 });
    await page.goto(`${base}/Home`, { waitUntil: 'networkidle', timeout: 45000 });

    const key = await page.evaluate(() => {
      const seg = location.pathname.split('/').filter(Boolean)[0] || '';
      return '$OS_' + seg + '$layout-theme';
    });
    await page.evaluate((k) => localStorage.setItem(k, 'dark'), key);
    await page.reload({ waitUntil: 'networkidle', timeout: 45000 });

    const cdp = await context.newCDPSession(page);
    const frames = [];
    cdp.on('Page.screencastFrame', async (f) => {
      frames.push(f.data);
      try { await cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }); } catch (e) {}
    });
    // Throttled so the window a fast machine would hide is actually observable.
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
    await cdp.send('Page.startScreencast', { format: 'png', everyNthFrame: 1 });
    await page.reload({ waitUntil: 'networkidle', timeout: 45000 });
    await page.waitForTimeout(600);
    await cdp.send('Page.stopScreencast').catch(() => {});

    // Node cannot decode PNG, so hand each frame to a blank page and average
    // its luminance through a canvas.
    const decoder = await context.newPage();
    await decoder.goto('about:blank');
    const lum = await decoder.evaluate((list) => Promise.all(list.map((d) => new Promise((res) => {
      const img = new Image();
      img.onload = () => {
        const c = document.createElement('canvas');
        c.width = img.width; c.height = img.height;
        const g = c.getContext('2d');
        g.drawImage(img, 0, 0);
        const px = g.getImageData(0, 0, img.width, img.height).data;
        let sum = 0, n = 0;
        for (let i = 0; i < px.length; i += 16) { sum += 0.2126 * px[i] + 0.7152 * px[i + 1] + 0.0722 * px[i + 2]; n++; }
        res(Math.round(sum / n));
      };
      img.onerror = () => res(-1);
      img.src = 'data:image/png;base64,' + d;
    }))), frames);
    await decoder.close();
    await page.close();

    assert(lum.length > 0, 'no frames were captured');
    const seq = lum.filter((l, i) => i === 0 || Math.abs(l - lum[i - 1]) > 6).map((l) => 'L' + l);
    const flashed = lum.filter((l) => l > DARK && l < WHITE).length;
    assert(flashed === 0,
           `${flashed} frame(s) painted the light theme while dark was stored — `
           + `is ThemePaint in the app root's RequiredScripts? sequence: ${seq.join(' -> ')}`);
    return `${lum.length} frames, no light-theme frame (${seq.join(' -> ')})`;
  });
}

// ---------------------------------------------------------------------------

(async () => {
  const base = baseUrl();
  if (!base) {
    console.error('No app configured.\n' +
      '  copy odc-app.example to odc-app and put your app URL in it,\n' +
      '  or set ODC_APP=https://your-env.outsystems.app/YourApp');
    process.exit(2);
  }
  console.log(`app: ${base}`);

  const browser = await chromium.launch({ headless: !HEADED });
  const context = await browser.newContext();

  console.log('\nscreens');
  await checkScreensAreClean(context, base);

  console.log('\ndropdown');
  await checkDropdownOpensAndCloses(context, base);
  await checkDropdownEmptyState(context, base);
  await checkDropdownKeyboardEntry(context, base);

  console.log('\nresponsive');
  await checkCheckboxSizeIsStable(context, base);

  console.log('\nshell');
  await checkShellChrome(context, base);

  console.log('\ntable');
  await checkTableSorting(context, base);
  await checkPagination(context, base);

  console.log('\ntheme');
  await checkDarkTheme(context, base);
  await checkNoThemeFlash(context, base);

  console.log('\nforms');
  await checkPasswordReveal(context, base, 'Login');
  await checkPasswordReveal(context, base, 'VerifyEmail');
  await checkValidationOnSubmit(context, base, 'Login', '#LoginButton');
  await checkValidationOnSubmit(context, base, 'VerifyEmail', '#AgreeButton');
  await checkValidationOnSubmit(context, base, 'SignUp', '#ContinueButton');
  await checkValidationOnSubmit(context, base, 'ResetPassword', '#ResetButton');

  console.log('\nnavigation');
  await checkSignUpNavigatesOnValidEmail(context, base);

  await browser.close();

  console.log();
  if (results.failures.length) {
    console.log(`FAILED: ${results.failures.length} of ` +
                `${results.passed + results.failures.length} checks`);
    for (const [name, detail] of results.failures) {
      console.log(`  ${name.padEnd(46)} ${detail}`);
    }
    process.exit(1);
  }
  console.log(`All ${results.passed} checks passed.`);
  process.exit(0);
})().catch((e) => {
  console.error('\nthe run itself failed:', e.message);
  process.exit(1);
});
