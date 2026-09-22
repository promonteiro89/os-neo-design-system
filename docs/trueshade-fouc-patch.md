# TrueShade patch — apply the theme at script evaluation

One addition to `TrueShade.UserScripts.TrueShade`. It removes the visible
wrong-theme flash on reload; measured in `tools/fouc-lab`, the light frame goes
from **255 ms to 6 ms** on a fast boot.

## The change

At the very end of the `Theme` IIFE, immediately after the `Expose public API`
block and before the `Utils` section:

```js
        // Expose public API
        Theme.Initialize = initialize;
        Theme.GetLayoutColorScheme = getLayoutColorScheme;
        Theme.GetStoredLayoutColorScheme = getStoredLayoutColorScheme;
        Theme.SetLayoutColorScheme = setLayoutColorScheme;
        Theme.Dispose = dispose;
        Theme.OnChange = onChange;
        Theme.GetStorageKey = getStorageKey;

        // ---- ADD FROM HERE ----------------------------------------------
        // Apply the stored preference the moment this script evaluates, rather
        // than waiting for Initialize() to be called from a block's OnReady.
        //
        // Why: consumers load this script well before first paint, but call
        // Initialize() from OnReady, which runs after the screen renders. In
        // between, the stylesheets have applied with no data-theme, so the page
        // paints in light and then flips. Moving the write here closes that gap
        // without changing any behaviour:
        //
        //   - ensureSeeded() caches into _rawTheme, so Initialize() reuses it.
        //   - applyTheme() skips the write when the value is unchanged, so
        //     Initialize()'s own call becomes a no-op rather than a second write.
        //   - no event is emitted here; Initialize() still emits 'init' exactly
        //     once, so OnChange subscribers are unaffected.
        //   - Initialize(appName) clears _storageKey and _rawTheme when given an
        //     explicit name, so a key derived here is correctly superseded.
        //
        // The one new side effect is that ensureSeeded() may seed
        // 'system-default' into localStorage earlier than before. It writes the
        // same value Initialize() would have written moments later.
        try {
            applyTheme(ensureSeeded());
        } catch (_) {
            // Storage blocked (private mode, disabled cookies). Leave the
            // attribute alone; Initialize() will try again and fall back.
        }
        // ---- TO HERE -----------------------------------------------------

        // -------------------------
        // Utils
        // -------------------------
```

That is the whole patch. It reuses `ensureSeeded()` and `applyTheme()` rather
than repeating their logic, so the key derivation, the seeding and the
`system-default` resolution stay in one place.

## What it does not fix

A white canvas is painted before any stylesheet applies — roughly 76 ms on a
fast boot, 325 ms on a slow one. No CSS can reach it, because it precedes the
first stylesheet. The only cure is an inline `<script>` in `<head>` setting both
`data-theme` and `color-scheme`, which is what TrueShade's own header comment
recommends.

**That is not available to an ODC app.** ODC's generated `index.html` contains
four platform scripts and two platform stylesheets and nothing app-controlled,
so there is nowhere to put it. Verified against the deployed harness.

Also tested and rejected: a `prefers-color-scheme` fallback shipped inside the
consuming library's own stylesheet. It cannot apply earlier than the stylesheet
that carries it, so it changes nothing that matters, and it is only ever correct
when the OS preference happens to match the stored choice.

## Reproducing the measurement

```bash
# once: TrueShade is not committed here
curl -s "<deployed-app>/scripts/TrueShade.UserScripts.TrueShade__<hash>.js" \
  -o tools/fouc-lab/assets/trueshade.js

LAB_BOOT=50 node tools/fouc-lab/run.js 4
```

The lab reproduces ODC's boot order and reports the colour of every painted
frame. Measure in frames, not `getComputedStyle` — an earlier round of this
investigation reached the opposite conclusion by polling computed style, which
reports values the browser never paints.
