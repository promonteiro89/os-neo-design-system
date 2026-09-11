# Neo Design System — extracted and restructured

The CSS the **ODC portal** ships (your ODC tenant), pulled apart into a readable,
reusable source tree so it can be dropped into your own OutSystems apps.

* **Source:** `https://<odc-tenant>/…/css/NeoDesignSystem.NeoDesignSystem__<hash>.css` — the host lives in the gitignored `odc-tenant` file (copy `odc-tenant.example`), the exact URLs in `tools/stylesheets.txt`
* **Contents:** 907 custom properties (612 light + 295 dark overrides), 1298 rules,
  24 Fusion components, 10 utility families — plus the portal chrome (322 rules) split from
  `prod.unified.css`
* **Unchanged:** the split is lossless — `python3 tools/verify.py` proves every rule and
  every token survives the round trip

```
156 KB  original (minified, single line)
271 KB  dist/neobase.css    everything, in cascade order — this is the paste
 44 KB  dist/neo-tokens.css variables only              (7.9 KB gzipped)
 56 KB  dist/neo-shell.css  portal chrome (separate product)
 61 KB  dist/o11-theme.css  tokens + compat + OSUI bridge — the O11 paste-in
 47 KB  dist/odc-library.css tokens + ODC compat — the ODC paste-in
```

## Start here

For most apps you want **the design language, not the components**:

```bash
cat dist/neo-tokens.css compat/neo-compat.css | pbcopy
```

Paste that into your app's theme stylesheet and every `var(--text-primary)`,
`var(--space-4)`, `var(--heading-1)` becomes available, in light *and* dark. Nothing else
in this repo is required.

Open `demo/index.html` in a browser to see the tokens and components rendered from plain
hand-written HTML — no framework, no OutSystems runtime. For the layout, open
`templates/portal-shell.html` (chrome + page scaffold, geometry verified against the live
portal) or `templates/fusion-layout.html` (page scaffold only), and read
[`docs/layout.md`](docs/layout.md).

## The portal loads 12 stylesheets, not one

Captured from `document.styleSheets` on `/configurations/organization`. All are public — no
auth. `tools/fetch.sh` downloads every one into `reference/raw/`.

| Stylesheet | Size | Owns |
| --- | --- | --- |
| `old-neo-design-system` | 566 KB | `.ds-layout*` — the layout the portal actually uses today (323 rules) — plus `.btn`, `.form-control`, `.card` |
| `outsystems-ui-theme` | 445 KB | OutSystems UI base (3175 rules) |
| **`neo-design-system`** | **156 KB** | **the Fusion components — the one this repo splits** |
| `unified-shell` | 59 KB | `.unified-aside` (nav rail) + `.unified-header` (top bar), 259 rules |
| `font-awesome` | 29 KB | icon font |
| `legacy-neo-theme` | 19 KB | glue and overrides; defines the `--unified-*` variables |
| + 6 smaller | ~32 KB | platform basics, React widgets, the app's own theme |

**9,576 rules / ~1.15 MB total.** Five of those are one **theme inheritance chain**, which is how
the portal is assembled — `OutSystemsUITheme → Legacy_NeoTheme → Old_NeoDesignSystem →
NeoDesignSystem → Configuration_Th`, all but the last inside a single `NeoDesignSystem` UI module
that also holds Blocks, 7 Scripts and Images. They **forked** OutSystems UI into that chain and
restyled ~290 of its classes by hand, because their copy predates the per-channel variable layer;
with OSUI 2.28.0 you get the same result from `compat/neo-osui-bridge.css` instead. The Fusion
components are a **Stencil** library (38 components, light DOM, lazy-loaded chunks). Measurements
and method in [`reference/portal-module.md`](reference/portal-module.md).

Also worth knowing: **the portal does not use `fusion-layout`.**
`/configurations/organization` renders with the previous-generation `ds-layout`, and only two
Fusion components appear on it (`fusion-dropdown-item`, `fusion-empty-state`). Fusion is where
the portal is heading, not where it is — so building on it means visual parity today is
approximate. [`docs/layout.md`](docs/layout.md) has a class-by-class mapping between the two.

That file also corrects a guess in `compat/neo-compat.css`: the portal's real chrome dimensions
are `--unified-aside-width-expanded: 256px` and `--unified-header-height: 56px`. The shim keeps
them at `0px`, which is right for a standalone app with no portal chrome — change them only if
you build equivalent chrome.

## Layout

```
dist/                      flattened, paste-ready (no @import of local files)
  neo.css                  everything, pretty-printed
  neo-tokens.css           tokens only — the file you usually want
  neo-shell.css            portal chrome: top bar + nav rail
  o11-theme.css            one file to paste into an O11 Theme (see docs/o11-theme-module.md)
  o11-theme-utilities.css  the utility classes, minus the ones that collide with OSUI
  o11-theme-components.css the 24 Fusion components, for hand-built markup
  odc-library.css          the ODC equivalent: no O11 adaptation, no bridge
  osui-reskin.css          the portal's own OutSystems UI overrides (423 rules)
  paste/                   paste-ready, pretty-printed: 0-neobase-complete.css + parts
  assets/                  the two logo SVGs the shell references
compat/
  neo-compat.css           shims for the tokens-only path; the 4 spacing/border
                           variables it defines are now also in dist/neobase.css
  neo-shell-compat.css     real chrome dimensions; load last when using the shell
  neo-o11-compat.css       OutSystems 11 adaptation layer
  neo-odc-compat.css       ODC adaptation layer — much shorter, and says why
  neo-osui-bridge.css      maps Neo tokens onto OutSystems UI's variables
src/                       the structured source, one concern per file
  neo.css                  index: @imports every layer in cascade order
  neo-tokens.css           index: @imports the token layer only
  00-tokens/               28 files
    primitives/            _size _palette _typography _opacity      (raw values)
    semantic/              _color _typography _space _elevation _motion _charts
    components/            _alert _avatar _badge _button _tag …      (17 files)
    _dark-theme.css        every [data-theme="dark"] override, grouped like the light files
  01-base/                 fonts, reset, animations, legacy-interop
  02-components/           24 files, one per Fusion component (+ vendor/splide.css)
  03-utilities/            colors, spacing, typography, icons, elevation, motion, …
  04-shell/                portal chrome from prod.unified.css, 8 files
  neo-shell.css            index for the shell layer
templates/
  fusion-layout.html       page scaffold: header, top-info, content, side panel
  portal-shell.html        the complete layout — chrome + scaffold, matches the portal
  osui-neo-skin.html       OutSystems UI widgets re-skinned by the bridge, both themes
  o11-theme-check.html     proves dist/o11-theme.css alone is enough over OutSystems UI
docs/
  layout.md                layout API, modifiers, gotchas, ds-layout -> fusion mapping
  outsystems-11.md         how to build this in an O11 Reactive Web App
  o11-theme-module.md      packaging it as a shared, published O11 theme module
  odc-library.md           the ODC library: release step, consumption, measured results
reference/
  raw/                     all 12 portal stylesheets, untouched
  portal-module.md         how OutSystems package it: theme chain, module contents, Stencil
  osui-collisions.md       Neo utilities vs OutSystems UI: 140 shared class names
  tokens.json              machine-readable: group, light, dark, resolved value, alias flag
  tokens.md               every token as a table, light vs dark vs resolved
  audit.md                 broken references, external dependencies, unused tokens
tools/
  stylesheets.txt          manifest of the 12 portal stylesheet URLs
  fetch.sh                 re-download them all, reporting what changed
  build.py                 split raw CSS -> src/ + dist/ + reference/
  verify.py                prove src/ and dist/ still equal the original
  collisions.py            regenerate the class-collision report
  osui_reskin.py           extract the portal's OutSystems UI re-skin layer
demo/index.html            visual reference, works standalone
```

The token layer is split three ways, which is the part worth understanding:

| Layer | Example | Change these? |
| --- | --- | --- |
| `primitives/` | `--indigo-7: #514dec`, `--size-6: 16px` | Only to rebrand |
| `semantic/` | `--text-primary: var(--neutral-10)`, `--surface-1-hover` | Rarely |
| `components/` | `--button-primary-background-hover: var(--indigo-8)` | Per component tweak |

Consume the semantic and component tokens in your CSS; avoid reaching for primitives
directly, or dark mode stops working (a primitive is a fixed value, a semantic token flips
per theme).

## Using it in an OutSystems app

**1 — Tokens only (recommended).** Paste `dist/neo-tokens.css` + `compat/neo-compat.css`
into the theme's stylesheet (ODC Studio / Service Studio → *Interface* → your Theme → CSS
editor). Then write your own CSS against the variables. Your app inherits the portal's
color, type, spacing and elevation language and will follow it if you re-fetch a newer
version — with zero risk of fighting OutSystems UI.

**2 — Tokens + utilities.** Also paste `src/03-utilities/*.css`. This is the sweet spot for
low-code: the class names go straight into a widget's **Style Classes** property with no
custom CSS at all — `heading-2`, `body-regular-s`, `margin-bottom-4`, `padding-x-6`,
`shadow-2`, `border-radius-2`, `line-clamp line-clamp-2`.

⚠ In an app that also loads OutSystems UI, **omit `colors.css` and `typography.css`** — they
share 40 class names with OutSystems UI whose values differ, and `.text-primary` /
`.text-secondary` mean the opposite thing in each. See
[`reference/osui-collisions.md`](reference/osui-collisions.md).

**3 — Full bundle, including components.** Paste `dist/neobase.css`. Read the gotchas first —
in particular, the CSS gives you no components by itself. There is **no shadow DOM and no
`::part()`** anywhere in the bundle (verified), so the class names are the entire API: you
build the markup, and you toggle the state classes. `demo/index.html` shows an accordion
working with six lines of JavaScript, and a wizard, progress bar, tag, avatar, breadcrumb,
score and spinner working with no JavaScript at all.

**4 — Re-skin OutSystems UI itself (O11).** Add `compat/neo-osui-bridge.css`. Every colour in
OutSystems UI is read through a variable, so this one file makes `.btn`, `.card`, `.table`,
inputs, alerts, badges and tags adopt the Neo language — **including dark mode** — with no widget
CSS touched. Open `templates/osui-neo-skin.html` to see it, and
[`docs/outsystems-11.md`](docs/outsystems-11.md#the-bridge--the-important-part) for the measured
before/after. Needs OutSystems UI 2.28.0+ for full effect; older builds get the base layer only.

**5 — Full portal look, including the chrome.** Add `dist/neo-shell.css` +
`compat/neo-shell-compat.css` (in that order, after Neo) for the top bar and nav rail. This one
has real prerequisites: mandatory `<body>` classes that the portal sets from JavaScript, four
lines of layout glue, and the two logo assets. All of it is documented in
[`docs/layout.md`](docs/layout.md#the-portal-shell), and `templates/portal-shell.html` is a
working reference whose geometry I measured against the live portal — header height, rail width,
content offsets, nav item height, active-item colour and label type all match exactly.

**6 — Package it once, consume it everywhere (O11).** Options 1, 2 and 4 collapsed into a single
file: `dist/o11-theme.css` is the token layer + `compat/neo-o11-compat.css` +
`compat/neo-osui-bridge.css`, concatenated in cascade order, with the reset, the legacy interop,
the component rules and the colliding utility classes all stripped out — `verify.py` asserts each
of those exclusions on every build. Paste it into one Theme with **Base Theme = OutSystemsUI**,
publish that module, and every app consumes it through Manage Dependencies.
[`docs/o11-theme-module.md`](docs/o11-theme-module.md) walks the whole assembly: module kind,
fonts as resources, the dark-mode client action, what to make public, and how to update it later.
`templates/o11-theme-check.html` loads *only* that one file over an OutSystems UI excerpt — every
value it produces matches the bridge's table, in both themes.

Markup pattern, using `fusion-tag` as the example:

```html
<fusion-tag>                                  <!-- optional; { display: contents } -->
  <span class="fusion-tag fusion-tag--choice fusion-tag--selected">
    <span class="fusion-tag__content">
      <span class="fusion-tag__label">Selected</span>
    </span>
  </span>
</fusion-tag>
```

The `fusion-*` element names are unregistered custom elements. Browsers style unknown
elements fine, so they are safe to use as-is — or drop them and keep the classes.

### Dark mode

The bundle themes off an attribute on the root element:

```javascript
document.documentElement.dataset.theme = 'dark';   // or 'light'
```

In OutSystems, run that from an OnReady / OnInitialize client action (a JavaScript node),
and persist the choice in Local Storage. There is no `prefers-color-scheme` support in the
bundle — the switch is entirely manual, which also means you can wire it to a user setting.

## Gotchas

**Don't take `01-base/reset.css` into an existing app.** It sets `html { overflow-y: hidden }`
and `body { height: 100vh; overflow-y: scroll }`, which takes over scrolling and will fight
OutSystems UI's own layout. `dist/neobase.css` includes it; `dist/neo-tokens.css` does not.
One line from it *is* worth copying, though — it holds the real font stack:

```css
html:root { --font-family: "Noto Sans", sans-serif; }
```

Without it you get the primitive value `--font-family: noto sans`, which works but has no
fallback.

**The two `@import` lines for Google Fonts must come first or they are ignored.** CSS
requires `@import` before any rule, so pasting the bundle *below* existing theme CSS
silently kills the font. Better: load the fonts with a `<link>` in the layout, or upload
Noto Sans / Source Code Pro as app resources and write your own `@font-face`. Self-hosting
also avoids the external request, which some environments block outright.

**The bundle expects OutSystems UI to be loaded.** It styles 33 classes it never defines —
`.btn`, `.form-control`, `.avatar`, `.skeleton-box`, `.ds-tabs`, `.metadata-container`,
`.ph`, `.phone`/`.desktop`, … Notably there is **no button CSS here**: `--button-*` tokens
exist, but the `.btn` rules live in OutSystems UI. Full list in `reference/audit.md` §4.

**3 variables are referenced but defined nowhere** — `--icon-default`, `--box-shadow-0` and
`--border-focus-default`. A `var()` with no definition and no fallback makes the browser drop the
whole declaration, so the default icon colour, the carousel arrow shadow and one focus ring
quietly do nothing. Genuine upstream bugs; `compat/neo-compat.css` fixes them.

A further **4** (`--space-s`, `--space-base`, `--space-m`, `--border-size-s`) are *not* bugs —
they belong to OutSystems UI and the legacy Neo theme, so they resolve for free in any
OutSystems app, which is every app that uses OutSystems UI as its base theme. The compat file
still defines them so the bundle works standalone, and its inferred values turned out to match
the owners exactly (8px / 16px / 24px / 1px). `reference/audit.md` §1 and §1b are generated by
cross-referencing all 12 stylesheets, so this stays accurate if upstream changes.

**228 tokens are never used inside the bundle.** Not a bug — that is the public API surface
for your own CSS. Listed in `reference/audit.md` §5 if you want to trim.

**The URL carries a content hash**, so it changes on every ODC update. Nothing here
auto-updates; re-run `tools/fetch.sh` when you want to pick up changes.

## Rebuilding

```bash
./tools/fetch.sh          # re-download all 12 (keeps previous copies, reports what changed)
./tools/fetch.sh neo      # or just the entries matching "neo"
python3 tools/build.py    # regenerate src/, dist/, reference/
python3 tools/verify.py   # prove nothing was lost or altered
```

No dependencies — standard-library Python 3 only. `build.py` deletes and rewrites `src/`
and `dist/` on every run, so treat those as generated: edit `tools/build.py` (or
`compat/neo-compat.css`, which is never touched), never the output.

`verify.py` re-parses everything, re-minifies each rule to a canonical form and compares
the result against the original as a multiset — so a reordered file passes, but a dropped
declaration, a changed value or a mangled selector fails. It caught two real mistakes while
this tree was being built.

## One caveat worth stating

This is the ODC portal's stylesheet, and reusing it across your OutSystems apps is
a reasonable way to stay visually consistent with the platform. Two things to keep in mind:
it is **OutSystems' proprietary product CSS**, not a published design system with a license
— no licence is granted here (see NOTICE), so treat it accordingly; and it is an
**undocumented internal API** — OutSystems can restructure it in any release, which is
exactly why the token layer is the safe thing to depend on and `verify.py` exists to tell
you what moved.
