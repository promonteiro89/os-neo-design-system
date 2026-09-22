# The dark-mode flash on reload

Reloading with dark stored shows white, then the light page, then dark. This is
what that is, measured against the deployed harness rather than reasoned about.

**The short version: TrueShade cannot fix it, and neither can the timing of the
`data-theme` write. The light frame is painted while `data-theme` is already
`dark`.**

## What the frames show

`tools/fouc-lab/run-odc.js` reloads the deployed app with the screencast
running and reports the colour of every painted frame. It loads *one* app twice
and rewrites TrueShade's script on the wire, so each candidate differs from the
baseline by one line and nothing else — same app, same bundle, same timings.

Four reloads per cell, CPU throttled 4x, `NeoLayoutCheck/Home`, dark stored,
median milliseconds spent painting the light page background:

| variant | OS light | OS dark | what it changes |
|---|---|---|---|
| unpatched | 372 ms | 373 ms | — |
| `applyTheme(ensureSeeded())` at script eval | 367 ms | 383 ms | sets `data-theme` ~120 ms earlier |
| the same, plus `color-scheme` | 369 ms | 368 ms | also darkens the UA canvas |
| the same, plus an injected background rule | **8 ms** | **15 ms** | paints dark without waiting for NeoBase |

The first two candidates do nothing. The third removes the flash.

## Why the obvious fix does nothing

Polling `data-theme`, the computed body background and `document.styleSheets`
through a single boot, with the `data-theme` patch applied:

```
  456ms  data-theme=dark   body-bg=rgba(0, 0, 0, 0)     neobase-not-live
  469ms  data-theme=dark   body-bg=rgb(243, 246, 248)   neobase-not-live
  472ms  first-paint
  594ms  data-theme=dark   body-bg=rgb(24, 26, 31)      neobase-live
```

`data-theme` is already `dark` at 456 ms. The first frame is painted at 472 ms
and it is light. The background only turns dark at 594 ms, when NeoBase's
stylesheet enters the cascade.

That is the whole story. `[data-theme="dark"]` is meaningless until the sheet
that defines it is live. OutSystemsUI's stylesheet is live before NeoBase's —
both arrive within a millisecond of each other (110 KB and 78 KB, `responseEnd`
457 ms and 458 ms), but NeoBase takes ~125 ms longer to become live — so for
that window the page is styled by OutSystemsUI alone, which is light.

Setting the attribute sooner cannot help, because nothing is listening to it
yet. This is why the local lab in `tools/fouc-lab/run.js` disagreed: it loads
one small stylesheet that is live the moment it arrives, so there is no window
in which the attribute is set and the rules are missing.

## What does work

Anything that paints the dark background **without needing NeoBase to be live**.
The measured candidate injects a two-declaration `<style>` at script-evaluation
time:

```css
html, body { background-color: #181a1f !important; color: #f9fafb }
```

372 ms → 8 ms. A residual 6–25 ms light frame remains, which is the gap between
OutSystemsUI going live and this rule being appended.

This belongs in **NeoDesignSystem**, not TrueShade: it is the design system that
knows these colours, and TrueShade has no business hardcoding an app's palette.
Two shapes are worth trying, in this order:

1. **A tiny separate stylesheet** carrying only the page-background tokens for
   both themes. Rules, not script; it should go live almost immediately because
   it is ~1 KB rather than 78 KB. Whether ODC injects it early enough is an
   empirical question — measure it, do not assume.
2. **An early script** that appends the rule above when the stored preference
   resolves to dark. This is what was measured, so it is known to work, but it
   duplicates a colour that otherwise lives only in the tokens.

## What cannot be fixed at all

A pure white canvas precedes every stylesheet — **~370 ms on the harness,
unchanged by every candidate above**, including `color-scheme`. It is painted
before any app or library code exists: the platform's two `<head>` stylesheets
are live at ~150 ms and say nothing about colour, and everything else, CSS and
script alike, arrives together at ~455 ms.

The only cure is an inline `<script>` in `<head>`, which is what TrueShade's own
header comment recommends. **That is not available to an ODC app.** The
generated `index.html` contains four platform scripts and two platform
stylesheets and nothing app-controlled. Verified against the deployed harness.

## Reproducing

```bash
node tools/fouc-lab/run-odc.js https://<host>/NeoLayoutCheck/Home 4 4
```

Measure in frames, not `getComputedStyle`. An earlier round of this
investigation reached the opposite conclusion by polling computed style, which
reports values the browser never paints — and a later round reached the
opposite conclusion again from a local reconstruction that was faithful to
ODC's *timings* but not to its *stylesheet count*.
