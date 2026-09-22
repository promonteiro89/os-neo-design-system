# The dark-mode flash on reload

Reloading with dark stored used to show white, then the light theme, then dark.
This is what the ODC Portal does about it, how that was found, and the
replication — measured on the deployed harness, not reasoned about.

## The fix, as the portal does it

Each portal app carries its own copy of a tiny **Script** element called
`Layout`, and lists it in the **app root's `RequiredScripts`**. ODC compiles
that list into the app's initialisation — the portal's bundle index reads:

```js
executeRequiredScripts: [ "scripts/apps.UserScripts.Layout.js" ]
```

so the script runs at app init, before any screen loads and before the
stylesheets are live. It is 305 bytes:

```js
const storedTheme = localStorage.getItem("layout-theme");
if (!!storedTheme) {
    if (storedTheme == "light") document.body.style.backgroundColor = "#F9FAFB"
    else                        document.body.style.backgroundColor = "#181A1F"
} else {
    document.body.style.backgroundColor = "#F9FAFB"
}
```

A client action later hands back to the stylesheets with
`document.body.style.removeProperty("background-color")`. The portal's
authentication app has the same script with a different dark colour.

The replication is `behaviour/theme-paint.js`, installed in NeoLayoutCheck as
the Script `ThemePaint` in the app root's `RequiredScripts`. The harness's bundle
index now compiles to the same shape:

```js
executeRequiredScripts: [ "scripts/NeoLayoutCheck.UserScripts.ThemePaint.js" ]
```

It differs from the portal's in three deliberate ways: it reads TrueShade's key
(`$OS_<AppName>$layout-theme`) rather than the portal's unprefixed one, it
resolves `system-default` through `prefers-color-scheme`, and it hands back to
the stylesheets on its own once NeoBase is live and `data-theme` is set, so
there is no removal action to wire.

## Result

`tools/fouc-lab/run-odc.js`, five reloads per cell, CPU throttled 4x, dark
stored, median milliseconds, measured by intercepting `ThemePaint` on the wire
so both columns are the same app:

| OS preference | without `ThemePaint` | with `ThemePaint` |
|---|---|---|
| light | 400 white + **369 light theme** = 769 | 282 white + **0 light theme** = 282 |
| dark | 448 white + **381 light theme** = 829 | 285 white + **0 light theme** = 285 |

The script evaluates at 426-448 ms, before first paint, so the first content
frame is already dark. It also trims the white window, because the inline body
colour is itself the first paint.

The ~283 ms of white that remains precedes all app code: ODC's generated
`index.html` carries only platform files, and the portal has the same window.

`tools/test_browser.js` guards this: `dark reload paints no light-theme frame`
fails when `ThemePaint` is blocked (mutation-tested).

## Installing it in another app

NeoDesignSystem holds the canonical copy as the Script `NeoThemePaint`, but apps
cannot reference it. Setting it public is rejected by ODC's validator:

```
(Error) Invalid app (type: IScript, location: /NeoDesignSystem/NeoThemePaint)
The app uses 'Public Property of UI Elements', which is not supported on this version.
```

So, like the portal, each app keeps its own copy. If a later platform version
supports public Scripts, flip the library copy to public and have apps reference
it instead.

1. In the consuming app, create a Script element and paste
   `behaviour/theme-paint.js` into it.
2. Select the app root and add that Script to its **RequiredScripts**.
3. Publish. Check the bundle index contains `executeRequiredScripts` naming it.

## How it was found

The early write was invisible to every JavaScript hook — prototype setters on
`style`, `setProperty`, `cssText`, `setAttribute` all caught nothing. A DevTools
DOM breakpoint on `body` attribute changes caught it immediately, with the file
and line: `authentication.UserScripts.Layout.js:8`, top-level. Comparing request
initiators then showed why it is early: the portal's script is loaded by
`executeRequiredScripts` from the app's bundle index, while a library block's
script goes through `loadResources → scheduleCustomJsLoading`.

## What did not work, and why

| attempt | effect | why |
|---|---|---|
| TrueShade applies the theme at script evaluation | none | setting `data-theme` earlier measured 776 ms vs 784 ms |
| `color-scheme` from script | none | the canvas is painted before any app code |
| library Script in `AppShell`/`Layout_Login` `RequiredScripts` | none | downloads at 413 ms, evaluates at 818 ms when the block renders — after first paint. Removed from both blocks |
| make the library's Script public, reference it from the app | rejected | "'Public Property of UI Elements' ... not supported on this version" |
| paint `html` only | none | `body` computes to `rgb(249,250,251)` at that moment, not the transparent `reset.css` declares, and covers it |
| paint `html` and `body`, early | 784 → 383 ms | the right idea; the app-level registration is what makes it early in production |

## Instrument lessons

Two earlier write-ups in this repo reached wrong conclusions from bad
instruments, and both are worth knowing before measuring anything visual here.

- **Measure painted frames, not `getComputedStyle`.** Computed style reports
  states the browser never paints.
- **Measure the whole frame, not one pixel.** A probe at 70% of the height sits
  on a content surface on this screen. It reported colours unrelated to the
  theme and produced a confident, wrong "stylesheet ordering" diagnosis. Mean
  luminance of the whole frame is what "the screen looks white" means.

The local lab in `tools/fouc-lab/run.js` reconstructs ODC's boot order and is
useful for fast iteration, but it disagreed with the platform on this question
and the platform was right. Confirm on a deployed app with `run-odc.js`.
