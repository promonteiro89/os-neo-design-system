# The ODC library

Created in the ODC tenant on 2026-09-03 via the OutSystems MCP.

| | |
| --- | --- |
| Name | `NeoDesignSystem` |
| Asset key | `9243697a-362a-45fa-928e-1a3db861b488` |
| Asset type | `LowCodeLibrary` |
| Portfolio | `92a07136-28b5-47e9-b4c7-42c903251ac2` |
| Environment key | `1298b590-a960-431a-844f-a192494a2887` |
| Revision | **123**, published 2026-09-10 — `LayoutHeader.Collapsed` wired to the collapsed classes. **Not tagged** |
| Last released | **0.1.88**, tag on revision 121 — what every consumer's pin still resolves to |
| Theme | `NeoBase`, Base Theme = `OutSystemsUI`, public |
| Publish result | `outcome: success`, 0 validation errors, 6 warnings |
| Build type | Released library — consumable once a tag is cut |

Revisions 122 (72 descriptions) and 123 (this fix) are **published but untagged**,
so nothing in them has reached a consumer. `context_*` indexes the released tag,
which is why it still reports 0.1.88 for this library.

**The theme carries the full token layer** — all 911 declarations of
`dist/neobase.css` (historically `dist/odc-library.css`, delivered over MCP in 6 chunks) and verified
against the local file. Nothing is left to paste by hand.

---

## Verified: an ODC library *can* hold themes

This was an open question in [`o11-theme-module.md`](o11-theme-module.md) and it is now settled from
the tenant itself. A brand UI library (anonymised here as `BrandUI`) is a `LowCodeLibrary` containing **14 themes**:

```
OutSystemsUI  (aa93104f-…)
├── BrandUI_Base            bb6b66c1-…   206,739 chars of CSS
│   └── (12 per-brand variant themes, ~46,900 chars each)
└── DEPRECATED_BrandUI                    120,139 chars
```

All 14 are public. `BrandUI_Base` carries the tokens (`--font-size-h1`, `--font-line-height-*`,
`--extended-yellow-50..900`, `--others-focus`, …) and pulls its assets the same way this repo
recommends for fonts — `@import url(/BrandUI/…icons.css)` and `/BrandUI/opensans.css`, i.e.
resources served from the library's own directory. Its grid is
`{"type":"Inherited","columns":12,"gutterWidth":20}`.

So the base-plus-variants pattern is not just idiomatic, it is already the tenant's house pattern —
one library, a base theme on `OutSystemsUI`, one derived theme per brand.

Note this does **not** contradict the O11 guide: an **O11** Library module cannot hold UI elements,
while an **ODC** library plainly can. Different products, different rules.

## The decision worth making before going further

`NeoDesignSystem` was created as a **separate library** because that touches nothing existing. The
alternative is a 15th theme inside `BrandUI` — `BrandUI_Neo`, Base Theme `BrandUI_Base`.

| | Separate library (what exists now) | Theme inside `BrandUI` |
| --- | --- | --- |
| Blast radius | none — nothing references it yet | a new revision of a library at rev 111 that apps depend on |
| Fits house pattern | no, a second design system | yes, exactly |
| Design language | keeps OutSystems' Neo look distinct from the organisation's brands | mixes an OutSystems product look into the brand library |
| Inherits brand base | no | yes, whether you want it or not |

Neo is the *ODC portal's* design language, not one of the organisation's brands, so a separate library is defensible
for internal/admin tooling that should look like the platform. If instead the goal is "another brand
skin", it belongs in `BrandUI`. Nothing is locked in — the library can be deleted, and this repo
regenerates either target.

## How the CSS got in, and how it was verified

The MCP has no file-upload path for theme CSS: `mentor_request_upload` mints a presigned URL and the
bytes upload fine (HTTP 200), but `mentor_prompt` rejects the resulting `attachmentRefs` with
`One or more tool arguments are invalid`. The only working channel is the prompt itself, so the file
went across in **6 chunks** split at top-level rule boundaries, appended in order.

Two things to know if you repeat this:

* **Mentor's self-reported counts drift.** Its running character counts landed within 6 of expected
  end-to-end (48,124 vs 48,130 — exactly the inter-chunk newlines it declined to add), but its
  declaration counts were off by +1 to +7 on every intermediate report. Do not treat them as proof.
* **It injects indentation.** Chunk 1 came back 1,108 characters over: +4 spaces on each of 277
  non-blank lines. Harmless — CSS ignores leading whitespace, and `@import` still parses — but it is
  not byte-verbatim. Telling it explicitly not to re-indent stopped it on later chunks.

The Context Service never indexed the library (`context_themes` returns 0 rows for it through two
publishes), so byte-level readback was not available. Verification was done instead on structural
fingerprints, all read back from the stored stylesheet and all matching the local file:

| Check | `dist/neobase.css` | Stored |
| --- | --- | --- |
| `:root {` blocks | 30 | 30 |
| `[data-theme="dark"]:root` | 1 | 1 |
| `/* ---- ` section headers | 29 | 29 |
| custom-property declaration lines | 911 | 911 |
| `--chart-cyan-hover` in light | `var(--data-visualization-cyan-9)` | matches |
| `--chart-cyan-hover` in dark | `var(--data-visualization-cyan-7)` | matches |
| `--data-visualization-purple-9` in dark | `#d6d1ff` | matches |
| last non-empty line | `-----… */` | matches |

The two different `--chart-cyan-hover` values are the load-bearing check: light resolves to cyan-9
and dark to cyan-7, so both blocks are present *and* distinct. A regenerated-from-memory stylesheet
would not reproduce that asymmetry, and a truncated one would have lost the dark half entirely.

Whitespace is the one known divergence: leading indentation differs from the repo file in places.
If you want them byte-identical, paste `dist/neobase.css` over the theme in ODC Studio — the
repo stays the source of truth either way.

## Revision 4: the layout Blocks

The library stopped being a token dump at revision 4. It now contains:

**Layout CSS** — `src/02-components/layout.css`, 86 rules, appended to the theme. Verified
afterwards: 64,753 chars / 1,831 lines / **916** declarations = the previous 912 plus the 4 layout
locals (`--layout-content-max-width` ×2, `--icon-size-base`, `--side-panel-viewport-offset`), with
the token layer and dark block confirmed intact.

Two upstream rules are deliberately **omitted**, and this one matters:

```css
body:has(fusion-layout) #reactContainer {
  height: calc(100% - var(--unified-header-height) - var(--unified-banner-height)) !important;
  margin-left: var(--unified-aside-width-expanded);
}
```

Those offset content for the **ODC portal's** own nav rail and top bar. The `--unified-*` variables
do not exist in a customer app, and an invalid `var()` does not get ignored — it makes the property
compute to `auto`. With `!important` that beats OutSystems UI's `#reactContainer { height: 100% }`
and would silently break full-height layout on every screen holding a `fusion-layout`.

**Three public Blocks:**

| Block | Inputs | Placeholders |
| --- | --- | --- |
| `Layout_Neo` | `ScrollType` ("page"/"section"/"section-column"), `LayoutType` ("narrow"/"widescreen"), `ReserveSidePanelSpace` | `Header`, `TopInfo`, `Content`, `SidePanel` |
| `LayoutHeader` | `Collapsed` | `Breadcrumbs`, `Title`, `SupportText`, `Actions`, `Description`, `Metadata` |
| `Section` | `StickyHeader`, `StickyFooter` | `Title`, `Subtitle`, `Actions`, `Content`, `Footer` |

`Section`'s header and footer wrap their placeholders in a Container carrying the Extended Property
`slot`, because the stylesheet hides them unless they contain `div[slot] .ph:not(:empty)`. That is
also why `Title` and `Subtitle` are **Placeholders rather than Expressions bound to inputs** — a
placeholder emits a `.ph` element and an Expression does not, so an Expression-based title would
leave the header permanently hidden.

**Five public client actions**, each a pass-through to TrueShade so consumers take one dependency:

| Action | Delegates to |
| --- | --- |
| `InitTheme` | `Initialize` — call from the consuming screen's or layout block's OnReady |
| `SetTheme(Theme)` | `SetLayoutColorScheme` |
| `ToggleTheme` | `GetLayoutColorScheme` then `SetLayoutColorScheme` with the opposite |
| `UseSystemTheme` | `SetLayoutColorScheme("system-default")` |
| `GetTheme` → `Theme` | `GetLayoutColorScheme` |

### Don't reinvent what OutSystems UI already has

Checked against the OutSystemsUI stylesheet **in this tenant** (503,800 chars, 1,486 distinct
classes, 157 `osui-*` patterns), not against assumptions:

| OutSystems UI already provides | Neo-only, worth adding |
| --- | --- |
| accordion (`osui-accordion`), tag, pagination, carousel (+`splide`), dropdown, progress bar (+`progress-circle`), avatar, spinner, wizard (`osui-wizard`), counter/badge, side panel (`osui-sidebar`), icon | empty-state, collapsible, logo, brand, filter-row, code-snippet, illustration, display-html, page-title, breadcrumb, score |

That is **62.8 KB skipped, 36.4 KB worth adding** instead of the 90 KB of remaining component CSS.
`score` is on the add list because OutSystems UI's `rating` is a star rating, a different thing from
Neo's coloured score badge.

Revision 5 adds the first five: `page-title`, `score`, `empty-state`, `logo`, `brand`,
`display-html` (8,329 chars, 0 new custom properties — they only consume tokens).

### How the portal actually re-skins OutSystems UI

This corrects the approach twice over, and it came from checking the portal rather than reasoning
about it.

The portal does **not** re-tint OutSystems UI through variables. It ships **direct class overrides**
in its `Old_NeoDesignSystem` theme, pointing OutSystems UI's widgets at Neo's own tokens:

```css
.btn         { background-color: var(--button-background-default);
               border-radius: var(--border-radius-2); box-shadow: var(--shadow-0);
               color: var(--button-text-default); font: var(--actions-base);
               height: var(--component-size-base); … }
.btn-primary { background-color: var(--button-primary-background-default);
               border-color: var(--button-primary-border-default);
               color: var(--button-primary-text-default) }
```

Those `--button-*` tokens are already in our theme, so this is cheap to replicate — and it explains
a measurement I could not reconcile earlier: overriding `--color-primary` **and**
`--background-color-primary`, at `:root` and inline on the element, left `.btn-primary` stubbornly at
`#1068eb`, even though `.btn-primary`'s only matching rule is
`background-color: var(--background-color-primary, var(--color-primary))`. Whatever the cause, the
variable route demonstrably does not work here and the portal does not rely on it.

**So `compat/neo-osui-bridge.css` is the wrong tool for ODC** — not because half of it is inert, as
I said earlier, but because the portal solves this a different way entirely.

[`tools/osui_reskin.py`](../tools/osui_reskin.py) extracts that layer reproducibly into
`dist/osui-reskin.css`: **464 rules, 64 KB**. It excludes third-party widget internals bundled into
the portal's theme (flatpickr alone is 186 rules, vscomp 112) and the portal's own `.ds-*` /
`.fusion-*` components, keeping only OutSystems UI's real widgets — `.btn` (72 rules), `.table` (58),
`.list` (53), `.button-group-item` (45), `.form-control` (43), `.dropdown` (40), `.checkbox` (20),
`.alert` (14), `.switch` (14), `.tag` (11) and the rest.

**Undefined-variable audit**, the check the layout CSS taught me to run. The re-skin uses 186
distinct variables; 7 are not in our theme, all without fallbacks. Measured in a live ODC app:

| Variable | Verdict |
| --- | --- |
| `--color-neutral-0` / `-2` / `-9`, `--space-s` | **OutSystems UI provides them** — `#ffffff`, `#f1f3f5`, `#272b30`, `8px`. No shim needed. |
| `--color-brand-blue` | Shimmed with the portal's own values from `legacy-neo-theme.css`: `#0077b3` light, `#38bdff` dark. |
| `--input-border-error`, `--input-height` | Referenced but defined **nowhere in any of the 12 portal stylesheets** — broken upstream too. Mapped to Neo's nearest equivalents and marked as inferences. |

### Pushing CSS through Mentor: the WAF blocks SVG data URIs

Worth recording even though the icons are now Images rather than data URIs, because it will bite
anyone pushing CSS with inline SVG through this MCP.

A percent-encoded `data:image/svg+xml,%3Csvg…xmlns=…` in a `mentor_prompt` body gets the whole
request rejected at the CDN:

```
403 ERROR — The request could not be satisfied. Request blocked.
Generated by cloudfront (CloudFront)
```

The WAF reads it as an XSS attempt. An earlier attempt failed less obviously — the run went
`status: not_found` mid-flight with no error, and three content checks confirmed nothing landed.
Base64 passes, because it carries no markup literals.

A related lesson: **Mentor's character counts are not trustworthy.** In this session it twice
reported the appended block's stats when asked for the whole stylesheet's, and once reported 34,897
characters for a stylesheet that was ~73,000. Verify with content checks — "does the stylesheet
contain this exact string" — never with sizes.

### The theme is complete at revision 10

Pasted in ODC Studio (revision 9) and finished over MCP (revision 10). Verified by content check,
not by size:

| Layer | Marker checked | Present |
| --- | --- | --- |
| tokens | `--surface-1-default` | yes |
| layout | `.fusion-layout__main-content` | yes |
| OutSystems UI re-skin | `.btn-primary{background-color:var(--button-primary-background-default)` | yes |
| re-skin shims | `--color-brand-blue` | yes |
| components | `.fusion-code-snippet`, `.fusion-collapsible`, `.fusion-illustration` | yes |
| utilities | `margin-bottom-4`, `shadow-2` | yes |
| paste markers | `PASTE 1/2/3 HERE` | gone, as intended |

**180,183 characters.** Images `icchevrondownxl` and `icsortablexl` are in the library and the three
icon rules reference them — 2 chevron, 1 sortable, zero inline-encoded values.

### The re-skin works — measured

`NeoReskinCheck` (`fbaa5049-b5fd-4d0f-8455-df091fc29912`) was created after the 0.1.5 release, so it
bound to revision 12 automatically. Served NeoBase: **148,445 characters**, `.btn-primary` override
present.

Computed styles on stock OutSystems UI widgets:

| | light | dark |
| --- | --- | --- |
| `.btn-primary` background | **#514dec** (indigo-7) | **#5252f2** (indigo-6 dark) |
| `.btn-primary` text | #ffffff | #ffffff |
| `.btn` default | #ffffff / #181a1f | #181a1f / #f9fafb |
| body | #f9fafb / #181a1f | #181a1f / #f9fafb |
| `.btn` radius / height / font | 8px / 40px / 14px Noto Sans | same |

Before the re-skin, `.btn-primary` was OutSystems UI's own `#1068eb` in both themes. It is now Neo's
indigo and it inverts. Radius `8px` is `--border-radius-2`, height `40px` is `--component-size-base`,
so the geometry tokens are landing too, not just the colour.

**The one widget that did not change, and why.** The Login screen's input stays transparent with an
OutSystems UI grey border in both themes. That is not a gap in the re-skin — it is a specificity
loss to an OutSystems UI pattern:

```
[OutSystemsUI] .animated-label-input .form-control[data-input] { background: transparent }   (0,3,1)
[NeoBase]      .form-control[data-input] { background-color: var(--input-background-default) } (0,2,1)
```

The template's Login screen uses the animated-label input, whose rule is one class more specific and
deliberately transparent. On an ordinary screen with a plain Input widget the Neo rule wins.

**Checked against the portal, and deliberately left alone.** `animated-label-input` appears in only
one of the 12 portal stylesheets — `outsystems-ui-theme.css`, 27 times. The portal's own re-skin
layer, `old-neo-design-system.css`, contains **zero** rules for it. So the portal renders these
inputs exactly as OutSystems UI does:

```css
.animated-label-input .form-control[data-input] {
  background-color: transparent;
  border-bottom: var(--border-size-s) solid var(--color-neutral-5);
}
.animated-label-input .form-control[data-input]:focus {
  border-bottom: var(--border-size-s) solid var(--color-primary);
}
```

Those are OutSystems UI's base variables, and the portal never remaps them, so its animated-label
inputs carry OutSystems UI's grey too. Our behaviour is therefore a faithful replica, not a gap —
adding an override here would make us diverge *from* the portal. Left unchanged on purpose.

Re-check with `grep -l animated-label-input reference/raw/*.css` after any `tools/fetch.sh`; if
`old-neo-design-system.css` ever starts appearing in that list, the portal has changed its mind and
the override should be ported.

Also worth knowing: `OutSystemsUI.OutSystemsUI.extra` loads **after** NeoBase in the cascade, so
anything it declares beats the theme at equal specificity. It is the platform-generated
`ThemeGrid_*` file, so it rarely matters — but it is the first place to look if an override loses.

### Formatting, and the real image path

Two corrections after seeing the theme in ODC Studio.

**The re-skin went in minified.** `tools/osui_reskin.py` used the repo's `minify()`, so 423 rules
arrived as one-rule-per-line running hundreds of characters wide — fine for a served asset, wrong
for a stylesheet a person opens and maintains. It now uses `render()`. Longest line is down from
~1,900 to 188 characters, and the 25 lines still over 120 are long selectors that are that long in
the source.

**The image path is absolute, not relative.** The portal's published CSS shows
`url(../img/NeoDesignSystem.icchevrondownxl__<hash>.svg?<hash>)`, so that is the form I generated
and I flagged it as needing confirmation. ODC Studio shows the resolved reality:

```css
background-image: url(/NeoDesignSystem/img/NeoDesignSystem.icchevrondownxl.svg);
```

An absolute module path, no hash. The generator now emits exactly that, so the open question is
closed.

`dist/neobase.css` is the whole stylesheet — tokens, ODC compat, layout, both component batches,
the re-skin, the utilities and the OutSystems UI palette bridge — in cascade order. Select all in
the theme editor and paste it over what is there. Nothing else needs pasting.

### The WAF also blocks `../` in a prompt body

Already recorded that a percent-encoded SVG data URI gets a CloudFront `403 Request blocked`. Two
further attempts narrowed it: the block still fired with every base64 and `data:` literal removed.
The remaining trigger was **`url(../img/…)`** — `../` reads as a path-traversal signature.

The way through is to describe the path rather than type it: spell out "two periods, a slash, img, a
slash" and let Mentor assemble the literal. That worked first time. Worth knowing for any CSS with
relative asset paths.

### One file, not a marker-and-chunk pile

The theme once carried three `PASTE n HERE` markers because pushing ~105 KB through `mentor_prompt`
costs a round trip per ~9 KB and failed twice on transport. `dist/neobase.css` replaced that whole
arrangement with a single ordered artifact, and `dist/paste/` plus `tools/paste_bundle.py` were
deleted along with `dist/neo.css`, `dist/neo.min.css` and `dist/odc-library.css` — roughly 14,000
lines of build output nobody pasted any more.

Regenerate everything with `tools/build_all.sh`, which runs the five steps in dependency order and
ends with `tools/neobase.py`. That last step is the one that produces the paste.

Revision 8 replaced the partial re-skin push with those markers — verified afterwards that
`--color-brand-blue` is gone, all three markers are present, and `--surface-1-default` and
`.fusion-layout__main-content` are still there.

### Still missing

Being explicit, because the library is not finished:

* **~20 component CSS files, ~90 KB** — dropdown (26.5 KB), illustration (13.6), code-snippet (7.4),
  pagination, tag, carousel, side-panel, wizard, avatar, empty-state, progress-bar, accordion, icon,
  collapsible, breadcrumb, score, loading-spinner, page-title, logo, filter-row, brand, counter,
  display-html.
* **The safe utility subset, ~19 KB** — spacing, elevation, radius, motion, icons, helpers, cursor,
  transform. Still excluding `colors.css` and `typography.css`, which collide with OutSystems UI.
* **Blocks for the components OutSystems UI has no equivalent of** — `fusion-wizard`, `fusion-score`,
  `fusion-empty-state`, `fusion-page-title`.

Each CSS batch is one Mentor round trip with the content transcribed through a prompt, which is why
this arrives in stages rather than all at once.

## A library must be RELEASED, not just published

This is the step that blocks everything else, and nothing in the MCP surface performs it.

`mentor_publish` is a 1-Click-Publish equivalent: it produces a **Debug** build. A library becomes
visible to other apps only once it has a **Release** build. Until then it is invisible to Manage
Dependencies *and* to the Context Service — which is why `context_themes` returns zero rows for it
and why Mentor reports the library "does not exist in this tenant" when asked to consume it. The
theme's `Public` flag is not the problem; ours was `true` from the start.

Check which you have:

```
build_list  asset_key=<library key>  revision=<n>
```

```json
{"builds":[{"buildType":"Debug","status":"Finished","assetRevision":2, ...}]}
```

One Debug build and no Release build means not consumable. There is no `publish_start` on this
tenant's tool surface (only the read-only `publish_status` and `publish_logs`), and `deploy_start`
cannot substitute — it *promotes* an existing Release build to another environment and resolves
"the latest finished Release build", so with only a Debug build it has nothing to source.

**Release the library from ODC Portal / ODC Studio.** Then confirm with `build_list` that a build
with `buildType: "Release"` has reached `status: "Finished"` before trying to consume it.

Diagnostic note: an earlier version of this document blamed "catalogue propagation delay" for the
empty `context_themes` results. That was wrong — the cause was the missing Release build.

## Consuming it

1. ODC Studio → your app → **Manage Dependencies** → `NeoDesignSystem` → select the `NeoBase` theme.
2. Set the app's theme to `NeoBase`, or create an app theme with **Base Theme = NeoBase**.
3. Dark mode: `document.documentElement.dataset.theme = 'dark'` from a client action on load. There
   is no `prefers-color-scheme` support in the bundle — see
   [`o11-theme-module.md`](o11-theme-module.md#5-dark-mode) for the client-action shape, which is the
   same in ODC.

## Verified end to end in a running ODC app

`NeoThemeCheck` (`400074fb-49b2-49fb-8d6a-7c35e2b423ad`, revision 1) consumes the library, sets its
theme to `NeoBase`, and is live as `NeoThemeCheck` on the dev environment. Mentor resolved the
dependency with 0 errors and 0 warnings. Computed styles measured in the browser:

| | light | dark |
| --- | --- | --- |
| Neo surface background | `#ffffff` | `#24262c` (neutral-1 dark) |
| Neo surface text | `#181a1f` | `#f9fafb` |
| Neo surface border | `#e3e7eb` (neutral-2) | `#2f323a` (neutral-2 dark) |
| Neo brand background | `#514dec` (indigo-7) | `#5252f2` (indigo-6 dark) |
| border radius / font / size | `8px` / Noto Sans / `14px` | same |
| `--heading-1` | `600 30px/40px "Noto Sans", …` | same |
| **OSUI Primary button** | `#1068eb` | **`#1068eb` — unchanged** |
| **OSUI input** | `#ffffff` | **`#ffffff` — unchanged** |
| **page (body)** | `#f3f6f8` | **`#f3f6f8` — unchanged** |

Every Neo token inverts correctly. The composite `font` shorthand resolves, and it picks up the real
font stack from the compat layer rather than the bare `noto sans` primitive — proof the last chunk
landed and wins the cascade.

The three unchanged rows are the honest limitations, both now documented in
[`compat/neo-odc-compat.css`](../compat/neo-odc-compat.css):

* **The OutSystems UI bridge works only HALF way on ODC.** An earlier version of this document said
  it "does not work" — that was too strong, and the correction matters. Measured: **zero**
  `--background-color-*` declarations in any `:root` across all 8 stylesheets, so the bridge's 25
  per-channel mappings are inert. But ODC's OutSystems UI *does* have the base layer
  (`--color-primary` = `#1068eb`, `--color-neutral-9` = `#272b30`,
  `--color-background-body` = `#f3f6f8`), and the bridge carries **30 base-layer `--color-*`
  mappings** too — including `--color-primary: var(--indigo-7)` and
  `--color-background-body: var(--page-background)`. Those would take effect. So adding the full
  bridge on ODC would re-skin OSUI buttons, neutrals and the page, just not the per-channel
  refinements. It is still excluded from `dist/neobase.css` by default because that is a much
  larger visual change than the token layer alone — but it is an option, not a dead end.
* ~~The page background is yours to apply.~~ **Fixed in revision 3** — see below.

Reproduce with the app open:

```javascript
const g = t => getComputedStyle(document.documentElement).getPropertyValue(t).trim() || '(EMPTY)';
document.documentElement.dataset.theme = 'dark';
[g('--surface-1-default'), g('--text-primary'), g('--background-color-primary')]
```

`NeoThemeCheck` is disposable — delete it once you have seen the numbers.

## Revision 3: page surface + TrueShade

**Page surface.** The theme now carries, appended via MCP and verified at 912 declarations:

```css
:root { --color-background-body: var(--page-background); }
body   { background-color: var(--page-background); color: var(--text-primary); }
```

Two mechanisms on purpose. OutSystems UI paints the body with
`background-color: var(--background-color-body, var(--color-background-body))`, so mapping its own
variable makes that rule theme itself with no override and no specificity fight — on ODC the
per-channel half is absent, so the fallback is what resolves. The explicit `body` rule also carries
the text colour, which is **not** optional: OSUI's body text is `--color-neutral-9` (`#272b30`) in
both themes, and on a `#181a1f` page that is unreadable. Background and foreground have to move
together.

**TrueShade handles the switch, with no adapter.** Verified against TrueShade 1.5.1 in the live
harness: it sets **`data-theme` on `<html>`** — exactly the hook Neo's dark block uses.

```
html lang="en-US" dir="ltr" data-theme="light"
localStorage["$OS_NeoThemeCheck$layout-theme"] = "system-default"
window.TrueShade present
```

Clicking the harness's toggle gave `data-theme=dark`, persisted `dark` to localStorage, and moved
Neo's tokens with it — surface `#24262c`, text `#f9fafb`, brand `#5252f2`. No glue code.

| Need | Call |
| --- | --- |
| initialise (screen OnReady) | `TrueShade.Initialize(ApplicationName: "")` |
| toggle | `TrueShade.SetLayoutColorScheme("dark"` / `"light")` |
| follow the OS | `TrueShade.SetLayoutColorScheme("system-default")` |
| read effective theme | `TrueShade.GetLayoutColorScheme()` |
| read raw preference | `TrueShade.GetStoredLayoutColorScheme()` |

`Initialize` also seeds the preference, applies the theme, and registers OS-level and cross-tab
listeners — so "follow the system" and multi-tab sync come free. Worth having, because Neo's CSS has
no `prefers-color-scheme` rules at all. Pass an explicit `ApplicationName` to share one preference
across several front-ends; omit it and the key derives as `$OS_<ModuleName>$layout-theme`.

Replaces the hand-written `SetTheme`/`ToggleTheme` JavaScript that
[`o11-theme-module.md`](o11-theme-module.md#5-dark-mode) still describes — on ODC, prefer TrueShade.

### VERIFIED in the released library

`NeoThemeCheck2` (`2ac92d60-ff89-4127-97cf-288a215f4c2e`) was created *after* the 0.1.1 release, so
its dependency bound to **0.1.1 / revision 3** automatically. The served theme and the measured body:

```
served NeoBase: 37,793 chars, 912 declarations
  has --color-background-body: true
  has body rule: true
```

| | body background | body text | `--color-background-body` |
| --- | --- | --- | --- |
| light | `rgb(249,250,251)` = **#f9fafb** | `rgb(24,26,31)` = **#181a1f** | **#f9fafb** |
| dark | `rgb(24,26,31)` = **#181a1f** | `rgb(249,250,251)` = **#f9fafb** | **#181a1f** |

Exactly the token values, inverting correctly. Both mechanisms work: the mapped OSUI variable
resolves through to `--page-background`, and the explicit `body` rule carries the text colour.

### End-to-end, in the updated consumer

`NeoThemeCheck` on 0.1.1 (revision 4), driven by its real TrueShade button:

| | dark | light |
| --- | --- | --- |
| `data-theme` | `dark` | `light` |
| **body** | **#181a1f** / #f9fafb | **#f9fafb** / #181a1f |
| Neo surface | #24262c / #f9fafb | #ffffff / #181a1f |
| Neo brand | #5252f2 (indigo-6 dark) | #514dec (indigo-7) |
| OSUI Primary button | #1068eb | #1068eb — unchanged, as expected |

The page now themes with the rest of it, in both directions, and the OSUI button staying put is the
documented consequence of leaving the bridge out.

Two things that cost time and are worth remembering:

* **A pending client-side version upgrade makes the app behave like the old build.** After the
  republish the console showed `[VersionsManager] New application version detected, starting upgrade
  from '…' to '…'` and the toggle did nothing. A reload fixed it. Check the console before
  concluding a change did not work.
* **Synthetic ref-clicks may not reach OutSystems' React handlers.** A coordinate/ref click appeared
  to do nothing, while `element.click()` on the same button worked immediately
  (`light → dark`, persisted). That was a test-harness artifact, not an app defect — worth knowing
  when driving an ODC app from a browser tool.

### The pinning gotcha — worth knowing for every future release

A **new** consumer binds to the latest released version on its own. An **existing** consumer does
not, and this bit us: after the library was released as 0.1.1, `NeoThemeCheck` was refreshed in ODC
Studio and republished (revision 2 → 3), yet two independent checks showed it had not moved —

* the served stylesheet still had **911** declarations, no `--color-background-body`, ending at the
  `--font-family` rule (that is revision 2 content), and its URL hash was unchanged, which rules out
  browser caching since the hash is content-derived;
* reading the model, the reference was still `0.1.0` / producer revision `2` /
  `IsFixedVersion: True`.

So republishing a consumer does **not** move a pinned reference, and at least in this case neither
did a plain Refresh. Check the reference explicitly — in Manage Dependencies the version the
consumer resolves has to end up as the new one — and confirm it landed rather than assuming. The
quickest confirmation is from the running app's console:

```javascript
const l = [...document.querySelectorAll('link[rel=stylesheet]')].find(x => x.href.includes('NeoBase'));
fetch(l.href).then(r => r.text()).then(t =>
  console.log(t.length, (t.match(/--[\w-]+\s*:/g) || []).length, t.includes('color-background-body')));
```

912 declarations and `true` means the consumer is on 0.1.1 or later; 911 and `false` means it is
still on 0.1.0.

**MCP cannot do the refresh.** Mentor reports the Model API sandbox has no `ResolveModuleSignature`
event wired, which `RefreshDependency(IGlobalKey)` needs, and the alternative
`RefreshDependenciesUsingSignatureBinary` path needs the producer eSpace object, which is not
reachable. It has to be done in ODC Studio.

## What is deliberately not in the theme

That check covered tokens + [`compat/neo-odc-compat.css`](../compat/neo-odc-compat.css) only.
Excluded, with reasons in that file: the reset (takes over scrolling), the legacy interop, the
component rules, and the OutSystems UI bridge — the bridge needs OutSystems UI's per-channel
variable layer, which is unverified on ODC's build. `tools/verify.py` asserts each exclusion.

To add the components or utilities later, paste `dist/o11-theme-components.css` or
`dist/o11-theme-utilities.css` after it; both apply unchanged in ODC.

## Reproducing / extending via MCP

```
auth_status → env_list → app_list --search neo
mentor_start_session
mentor_create_asset  assetType=Library  name=…  portfolioKey=…
mentor_prompt        "create a public theme … base theme OutSystemsUI"
mentor_prompt        chunk 1 of N   (replace the stylesheet)
mentor_prompt        chunk n of N   (append; say "do not inject indentation")
mentor_prompt        diagnostic: read back structural fingerprints
mentor_publish       → publicationKey
publish_status       → poll to outcome: success
mentor_close_session
```

To edit it again later, start a fresh session and `mentor_load_asset` with the asset key — the
session above is closed, so the library is not held open against ODC Studio.

Two gotchas met along the way: a library has no runtime deployment, so `env_app` reports
`has no deployment in environment` — that is expected, not a failed publish; and `context_themes`
returns nothing for a freshly published library until the Context Service indexes it.

---

## Revision 14: the `ph` class, and why every auto-hide rule was misfiring

Found by building the [`NeoLayoutCheck`](#the-layout-harness) harness and measuring it. Two
independent defects, one root cause each. Both were invisible in the CSS and only showed up in a
running app.

### 1. ODC does not emit a `ph` class — the portal's developers type it

Neo hides empty regions with rules that key on a `ph` class:

```css
.fusion-layout-section-structure__header:not(:has(div[slot] .ph:not(:empty))) { display: none }
.fusion-layout__top-info:has(> .ph:empty)                                     { display: none }
.fusion-empty-state__heading:has(> .ph:empty)                                 { display: none }
```

Sixteen rules in the flattened bundle depended on it. **Not one of them ever matched**, because the live
page contained zero `.ph` elements. An ODC Placeholder renders as a bare div:

```html
<div id="b3-Title">…</div>        <!-- filled -->
<div id="b4-Subtitle"></div>      <!-- empty: :empty is true -->
```

The `ph` class is not runtime output. It is a **Style Class the portal's developers set on the
Placeholder widget itself** — confirmed on the ODC portal, where a placeholder renders as:

```html
<div class="ds-input-with-icons-icons ph" data-test-id="ds-input-with-icons-icons" id="b4-Icons">
```

`id="b4-Icons"` is the placeholder named `Icons`; `ds-input-with-icons-icons ph` is hand-authored.
So the convention is: **every Placeholder in a Neo Block gets Style Class `ph`** (the portal adds a
BEM class alongside it; our containers already carry the BEM classes, so `ph` alone suffices).

The failure modes were opposite and both bad:

| Rule shape | Without `ph` | Effect |
| --- | --- | --- |
| `:not(:has(… .ph:not(:empty)))` | never satisfied → always hides | **section headers and footers vanished even when filled** |
| `:has(> .ph:empty)` | never matches → never hides | empty regions kept their padding |

The first is the silent one. A `Section` with a perfectly good title rendered as content only, and
nothing in Service Studio or the publish log said a word.

Fixed in revision 14 by setting Style Class `ph` on all 15 placeholders across `Layout_Neo`,
`LayoutHeader` and `Section`. **The CSS was not changed** — it was correct all along, and keeping it
byte-identical to the portal's is the point.

### 2. A Placeholder swallows the layout's flex gap

`.fusion-layout__main-content` is `display: flex; gap: var(--space-6)`. In the portal the sections
are its direct children, so the 24px applies between them. Through a Block it cannot be:

```
.fusion-layout__main-content     display:flex; gap:24px   ← one child only
└── div#b1-Content .ph                                     ← the Placeholder
     ├── .fusion-layout-section-structure
     └── .fusion-layout-section-structure                  ← measured gap: 0px
```

A Placeholder always renders a real div, so consecutive sections sat flush. One rule in the compat
layer promotes them back to flex items:

```css
.fusion-layout__main-content > .ph { display: contents; }
```

Measured after the fix: **24px**, matching the portal. This is an ODC adaptation, not a deviation —
it makes OutSystems markup produce the portal's geometry rather than changing the geometry.

### The layout harness

App `NeoLayoutCheck` (`743285c2-1b80-4d11-8f29-c85d619a227b`,
`NeoLayoutCheck/Home` on the dev environment, Home screen is Anonymous). One `Layout_Neo`
holding a `LayoutHeader` with all six placeholders filled, an `alert alert-info` in `TopInfo`, and
two `Section` blocks — the first fully filled, the second with `Subtitle`, `Actions` and `Footer`
deliberately empty so auto-hide is observable. Measured against the live portal:

| Property | Portal | Harness | |
| --- | --- | --- | --- |
| `.fusion-layout__main-content` max-width | 1384px | 1384px | ok |
| `.fusion-layout__main-content` padding | 16px 32px | 16px 32px | ok |
| `.fusion-layout__main-content` gap | 24px | 24px | ok |
| gap between consecutive sections | 24px | 0px → **24px** | fixed in rev 14 |
| header title | 600 30px/40px Noto Sans | same | ok |
| section headers when filled | visible | hidden → **visible** | fixed in rev 14 |
| section footer when empty | `display: none` | `display: none` | ok |
| `.btn-primary` | #514dec light / #5252f2 dark | same | ok |
| page surface | #f9fafb light / #181a1f dark | same | ok |
| body text | #181a1f light / #f9fafb dark | same | ok |
| `data-theme` on `<html>` | set | set (TrueShade) | ok |

Re-measured on the deployed 0.1.7 build (not a patched page): 20 `.ph` elements where there were
none, `.fusion-layout__main-content > .ph` present in the served stylesheet and computing to
`display: contents`, 24px between sections, both section headers `flex`, section two's footer
`none`. Toggling dark and back leaves every geometry value unchanged.

### One measurement trap worth knowing

Reading a colour straight after clicking the theme toggle gave `#514dec` in dark — the light value —
which looks exactly like a broken dark override. It was not. The browser pane was backgrounded
(`window.innerWidth === 0`), so rAF was paused and the `background-color` transition stayed frozen at
its start value. `getComputedStyle` happily returns that frozen intermediate.

The token itself read `#5252f2` on the same element in the same call, which is the tell: **when a
custom property and the property that consumes it disagree, suspect a transition, not the cascade.**
Kill transitions before measuring colour:

```js
document.head.appendChild(Object.assign(document.createElement('style'),
  { textContent: '*,*::before,*::after{transition:none!important;animation:none!important}' }));
```

---

## Revision 15: the application shell, and a class name we cannot copy

Two findings, both triggered by the same question — why a harness page built from the layout Blocks
looks nothing like the ODC portal.

### 1. `ph` is Phosphor's class. Copying the portal's convention destroys all text.

Revision 14 set Style Class `ph` on every Placeholder because that is verbatim what the portal does:

```html
<div class="ds-layout-header-breadcrumbs page-header-breadcrumbs ph" id="b1-b1-Breadcrumbs">
```

In a stock ODC app that is catastrophic. The app loads Phosphor's icon stylesheet, which claims the
same class as its own base:

```css
.ph { font-family: Phosphor }   /* + font-variant: discretionary-ligatures */
```

Every string under a placeholder was then rendered by an icon font whose lowercase codepoints are
ligature triggers. Measured on a 30px heading: lowercase `abcdef` was **0px** wide with `ph`, **90px**
without. Only capitals survived, which is exactly what the screenshots showed.

The portal escapes this because it does not load Phosphor **at all** — verified on
the portal: zero rules in the entire cascade claim `.ph`. The convention is portal-safe, not
ODC-safe.

Revision 15 renames the marker to `neo-ph` in both the Blocks and the 19 selectors that use it. This
is a **forced deviation** from the portal's CSS and is documented in `compat/neo-odc-compat.css`
section 7. Behaviour is unchanged; only the token differs. Do not rename it back.

The rename is applied by `rename_ph_marker()` in the build pipeline, not by editing
`src/02-components/*.css` — those files are regenerated from the raw portal CSS on every build, so an
edit there silently disappears. `src/` stays a faithful replica; only what we paste is adapted.

### 2. The top bar and nav rail are NOT part of an OutSystems app

This is why the two pages look unrelated. The portal's DOM:

```
body.is-aside-expanded.osx.is-unified-desktop.desktop
  div.unified-aside      ← left nav rail   ⎫
  div.unified-header     ← top bar         ⎬ OUTSIDE #reactContainer
  div.unified-icons      ← svg sprite      ⎭
  div#reactContainer
      └── div.ds-layout … #b1-b1-BaseLayout   ← the OutSystems app begins here
```

The chrome is injected **around** the application by the platform host (`prod.unified.css`, from
UnifiedExperienceMenuServices — a different product from the Neo bundle). An app deployed to
an app on the dev runtime is not running inside that host and can never inherit it. Everything the
library shipped up to revision 14 lives inside `#reactContainer`; measuring `.fusion-layout__main-content`
and calling it a portal match was measuring the wrong scope.

Revision 15 re-implements the chrome as Blocks. This works because **both roots are
`position: fixed`** — `.unified-header` at `top:0; height:56px`, `.unified-aside` at
`top:56px; height:calc(100vh - 56px)` — so emitting the same markup from inside the app lands in the
same place as the host's own.

| Block | Emits | Notes |
| --- | --- | --- |
| `ShellHeader` | `.unified-header` | logo, portfolio dropdown, buttons, avatar |
| `ShellAside` | `.unified-aside` | menu header, primary and secondary sections |
| `AsideSection` | `.unified-aside-section` | no parameters — wrapper around an `Items` placeholder |
| `AsideItem` | `.unified-aside-item` | `Label`, `IsActive`, `Level`, `OnClick` |
| `AppShell` | plain wrapper | Header / Aside / Content placeholders; calls `InitShell` on ready |
| `IconSprite` | `.unified-icons.neo-icon-sprite` | `SpriteMarkup` (Text, mandatory); injected on `OnReady` |
| `Icon` | `svg.pds-icon` | `Name`, `Size`, `IdPrefix`; injected on `OnReady` |

CSS ships inside `dist/neobase.css` — `compat/neo-shell-compat.css` (the three
`--unified-*` dimensions the chrome uses but never defines) followed by `dist/neo-shell.css`
(all 8 files: host-integration, header, aside, banner, tooltip, toast, misc, animations).

### The shell is driven by body classes, not media queries

45 rules key off `.is-aside-expanded` alone, and the responsive variants are set from JavaScript by
the host — there is no CSS-only fallback. Two client actions reproduce that contract:

* `InitShell(AsideExpanded)` — sets `is-unified-desktop|tablet|phone` from viewport width, applies
  `is-aside-expanded`, and registers a `resize` listener once.
* `ToggleAside()` — toggles `is-aside-expanded`.

The app's layout root must also carry `neo-layout-shield`, which is what
`.is-unified-desktop .neo-layout-shield { padding-left: var(--unified-aside-width-expanded) }` offsets
past the rail. Revision 15 adds that class to `Layout_Neo`'s root container.

### Logos

`.unified-header-logo` is painted by CSS `background-image`, theme-switched on `[data-theme]`. The two
SVGs are in `dist/assets/` as `outsystems-logo--light.svg` / `outsystems-logo--dark.svg` and must be
imported as library Images under those names. **They are OutSystems' logo** — swap them for your own
brand mark; nothing else needs to change.

---

## Revision 19: what the nav rail is actually made of

Measured on the live portal after the shell first rendered. Three corrections, all found by
comparing the live portal's DOM against ours rather than by reading CSS.

### The header is `sticky`, not `fixed`

`prod.unified.css` declares `.unified-header { position: fixed }`; the live portal **computes
`sticky`**, so a rule we never captured wins. This is structural, not cosmetic: `fixed` takes the bar
out of flow, so nothing pushes the app content down and the page renders underneath it. `sticky`
keeps the 56px box in flow — which is exactly what puts the portal's `#reactContainer` at top 56 with
no padding or margin anywhere in the chain:

```
body                 0,0    1934x523   padding 0
div.unified-header   0,0    1934x56    position: sticky   ← occupies flow
div#reactContainer   0,56   1934x467   margin 0, padding 0
```

Rendered from a Block the header sits in the same flow position (first child, before the content
placeholder), so `sticky` reproduces the offset for free. Measured after: header `0,0 1600x56`,
layout `0,56`, main content left `256`.

### `--unified-banner-height` is used but only conditionally defined

`.screen-container:has(.ds-layout)` sizes itself with
`calc(100vh - var(--unified-header-height) - var(--unified-banner-height))`. The banner height is
only set when a banner is present, and **one undefined term voids the whole `calc()`**. Defaulted to
`0px`.

### Group headings are AsideItems, not a title element

The nav rail has exactly two item variants, and both are `.unified-aside-item`:

| Class | Role | Label typography |
| --- | --- | --- |
| `unified-aside-item--level0` | group heading | uppercase, 600 12px/16px Noto Sans, `#949ca8` |
| `unified-aside-item--level1` | navigation entry | normal |

with `is-open` and `is-active` as state. Live portal class sets, verbatim:

```
unified-aside-item unified-aside-item--level0 is-open
unified-aside-item unified-aside-item--level1 is-active
```

So a heading is an item whose label is styled down — there is no separate heading widget.
`AsideSection.Title` (which rendered `.unified-aside-menu-extra-title`) is not what the portal uses
for these; that element has no styling in the bundle, which is why the group labels first rendered as
plain 14px body text. **Removed in revision 38** — `AsideSection` now takes no parameters at all.

**And a bug of my own:** the `AsideItem` class expression emitted `--level-1` (stray hyphen) and
skipped the class entirely at Level 0, so *neither* variant ever matched. Fixed to always emit
`unified-aside-item--level<N>` with no hyphen, plus a new `IsOpen` parameter.

### Primary and secondary panels overlap by design

Both are `position: absolute; top: 0` in the same box, and the portal does this deliberately —
`.unified-aside-secondary.is-open` is the submenu sliding over the primary menu. Anything left in
`Primary` while the secondary is open is simply hidden underneath. Every navigation group on the
portal's admin pages lives in the **secondary** panel under the "Management" heading.

`is-open` was originally hardcoded into `ShellAside` from a snapshot of the live DOM, which pinned
the primary panel permanently invisible. It is now a `SecondaryOpen` parameter.

---

## The nav rail's two item variants, settled

Measured 2026-09-03 on the portal's `/usersaccess/` page at 1440x900, light theme, against the
harness at the same viewport and theme. This closes the question the earlier revisions kept
half-answering.

A group heading is **not** a distinct widget and **not** a `is-open` state. It is a level-0 item
carrying an **attribute**:

```css
.unified-aside-item--level0[data-children="true"] {
  margin-bottom: var(--space-2);   /* 8px */
  margin-left:   var(--space-1);   /* 4px */
  text-transform: uppercase;
}
.unified-aside-item--level0[data-children="true"] .unified-aside-item-label {
  color: var(--text-secondary);
}
```

That attribute is the whole difference. Without it a level-0 item gets `--text-primary`, no
uppercase, and no left inset — which is exactly how the harness rendered.

| | Group heading | Navigation entry |
| --- | --- | --- |
| class | `unified-aside-item--level0` | `unified-aside-item--level1` |
| attribute | `data-children="true"` | none |
| label font | `600 12px/16px Noto Sans` | `500 14px/24px Noto Sans` |
| label colour | `--text-secondary` | `--text-primary` |
| transform | uppercase | none |
| box | left 12, width 228 | left 8, width 232 |
| margin | `0 0 8px 4px` | `0 0 4px` |
| padding | `16px 4px 0 0` | `0` |

### Verified matching at 1440x900, light

| | Portal | Harness |
| --- | --- | --- |
| header background | `#ffffff` | `#ffffff` |
| nav rail background | `#f9fafb` | `#f9fafb` |
| nav entry box | left 8, width 232 | left 8, width 232 |
| item height | 32px | 32px |

Dark theme was verified separately: page `#181a1f`, header `rgb(36,38,44)`, rail `#181a1f`, item text
`#f9fafb`, `.btn-primary` `#5252f2` — all matching.

### Still to do

1. `AsideItem` — add a `HasChildren` Boolean that emits the Extended Property `data-children="true"`.
   Without it the heading variant cannot be expressed at all.
2. Harness — headings become `AsideItem(Level=0, HasChildren=True)`; the eleven entries become
   `Level=1`. They currently all render as `--level0`, which is why they read as headings.
3. ~~Retire `AsideSection.Title` / `.unified-aside-menu-extra-title`~~ — **done, revision 38.** The
   parameter, its container and its Expression are gone; a scan across every block in every flow
   returns zero instances of the class. The one consumer had its `Title=""` argument stripped first,
   while the parameter still existed, so the removal cost a single release rather than a stale-argument
   error in Studio.
4. `.unified-aside-menu-header-title` renders `14px/21px` system font here vs `14px/24px Noto Sans`
   on the portal — not yet diagnosed.

Note the portal's nav entries on this page carry **no icons**, so the earlier note about missing
icons was wrong for this view — nothing to add there.

---

## Revision 21: the shell matches, and the base font was never applied

Final verification of the deployed build at 1440x900, light theme, against
the portal's `/usersaccess/` page at the same viewport and theme.

| Property | Portal | Harness |
| --- | --- | --- |
| header box / background | `0,0 1440x56` / `#ffffff` | same |
| nav rail box / background | `0,56 256x…` / `#f9fafb` | same |
| heading box | left 12, width 228 | left 12, width 228 |
| heading margin / padding | `0 0 8px 4px` / `16px 4px 0 0` | same |
| heading label | 600 12px/16px Noto Sans, `rgb(104,111,125)`, uppercase | same |
| nav entry box | left 8, width 232 | left 8, width 232 |
| nav entry margin / padding | `0 0 4px` / `0` | same |
| nav entry label | 500 14px/24px Noto Sans, `rgb(24,26,31)` | same |
| menu header title | 14px/24px Noto Sans | same |
| item height | 32px | 32px |

Plus the page-level geometry, unchanged from revision 14: main content max-width 1384px, padding
`16px 32px`, 24px between sections, both section headers `flex`, section two's footer `none`.

Dark verified separately: page `#181a1f`, header `rgb(36,38,44)`, rail `#181a1f`, item text
`#f9fafb`, `.btn-primary` `#5252f2`.

### `--font-family` was defined but never applied

The last discrepancy was the nav's menu header title: `14px/21px` system font here against
`14px/24px` Noto Sans on the portal. The cause was not that element. `--font-family` was declared on
`:root` and **never used**, so every element without an explicit font rule inherited the browser's
default stack. It only surfaced on that one label because each of its neighbours carries a class that
sets a font outright — `.unified-aside-item-label`, `.fusion-layout-header__title` and so on.

The portal's `.unified-aside-menu-header-title` has no font declaration at all; it simply inherits.
One line fixes it and every other inheriting element at once:

```css
body { font: var(--body-regular-base); }   /* 400 14px/24px Noto Sans */
```

Worth remembering when adding a component: if it looks right, it is probably because its own class
sets a font, not because the cascade is healthy underneath it.

### Measurement traps, collected

Three of the same species bit during this work. All three produce a confident, wrong reading:

| Symptom | Cause | Tell |
| --- | --- | --- |
| `.btn-primary` reads the light colour in dark | pane backgrounded, rAF paused, `background-color` transition frozen at its start value | the custom property read correct on the same element in the same call |
| nav rail reads `0 w1440` right after a resize | `.unified-aside` has `transition: width ease-out 0.3s`, caught mid-animation from the phone breakpoint | `getComputedStyle().width` said `256px` throughout |
| first screenshot after a publish is blank or stale | capture fired before paint settled | the DOM query in the same batch returned the full, correct tree |

**When `getBoundingClientRect()` and `getComputedStyle()` disagree, believe the computed value and
re-measure once settled.** For colour, kill transitions first:

```js
document.head.appendChild(Object.assign(document.createElement('style'),
  { textContent: '*,*::before,*::after{transition:none!important;animation:none!important}' }));
```

### A note on propagation

The revision-21 CSS was live in `NeoLayoutCheck` **without refreshing the app's dependency or
republishing it** — released theme CSS is served from the library at runtime. Block *structure*
changes still need the dependency moved and the app republished; CSS-only changes do not.

### The consumer's version pin — measured 2026-09-04

"Move the dependency" above is not something an agent can do. A consuming app's
reference carries `IsFixedVersion: True` and a **specific** version — `NeoLayoutCheck`
sat on `NeoDesignSystem` 0.1.19 / revision 35 while the library was released at
0.1.21 / revision 37. Releasing the library does not move that pin.

The mentor API cannot move it either, and fails **silently**:

- "Refresh the dependency on the library" is accepted for every element, reports no
  errors, and returns `revision: None` for all of them. The pin does not change.
- Passing an explicit `revision: 37` is ignored the same way — accepted on all 17
  elements, `revision: None` returned, pin unchanged.
- Mentor's own summary says "refreshed to the latest revision, no validation errors",
  so **its success message is not evidence**.

This cost a full round trip: two reported-successful refreshes left the harness
running the pre-rework blocks, so every runtime measurement taken afterwards was
measuring the old build while looking like a defect in the new one.

**Rule.** After releasing the library, read back the consumer's recorded version
before believing any runtime measurement. Bumping the pin is a human step:
ODC Studio → open the consumer → Manage Dependencies → select the library → change
the version (or drop the fixed pin) → refresh → 1-Click Publish.

Note the asymmetry with the paragraph above: theme CSS reaches consumers at runtime
with no refresh at all, while Block structure needs a pin bump that only a person can
perform. Same library, two different propagation models.

---

## Code quality: descriptions on public elements

ODC's Code Quality tab flags **Missing descriptions on public element or parameter**.
It is not exposed over MCP — `context_actions` shows an action's own `description`
but the payload carries no description field for *parameters*, and
`context_screens` returns 0 rows for a library, so blocks are invisible to it.
Auditing this needs a Mentor session.

Audited 2026-09-10 at revision 121 / tag 0.1.88. Before the fix:

| | State |
| --- | --- |
| Library description | present |
| Client actions | 5 of 7 described; `InitShell` and `ToggleAside` had none |
| Client action parameters | none described |
| Blocks | public, none described |
| Block input/output parameters | none described |
| Events and their input parameters | none described (e.g. `AppShell.OnThemeChange`, its `Raw` and `Effective` inputs) |
| Structures | `PageItem`, `SkeletonRow` — no descriptions, but both `isPublic: false`, so the rule does not reach them |

### Fixed at revision 122

72 descriptions set over one Mentor session (metadata only — no logic, markup or
CSS touched): 14 blocks (`ShellHeader` had none; 4 skeleton/dropdown blocks
already did), 38 block input parameters, 4 events (`OnThemeChange`, `OnClick`
x2, `OnNavigate`, `OnChange`), 5 event input parameters (`Raw`, `Effective`,
`NewStartIndex`, `SearchTerm`), 2 client actions (`InitShell`, `ToggleAside`),
3 action parameters, 2 structures and their 4 attributes. Re-audit came back
NONE REMAINING; publish `outcome: success`, 0 validation errors.

**Two things this does not do.** Revision 122 is published but **not tagged**, and
`context_*` indexes the last released tag — every row still comes back stamped
`0.1.88` with `description: null` for `InitShell`. So the MCP cannot confirm the
fix, and a consumer will not see the descriptions until a new version is
released and its pin bumped.

### The Code Quality tab is on a schedule — it lags the fix

Checked in the portal at `/codequality/codequality?tab=findings`, filtered to
NeoDesignSystem, a few hours after publishing revision 124:

- **Missing descriptions on public element or parameter — Medium, 28 open.**
- Every finding is dated 2 to 6 days ago. **None postdates the fix.**
- Header: *"Last analysis summary (Sep 10, 2026, 10:56 AM): no new findings
  detected"* and *"Next analysis in 5 hours"* — the 10:56 run predates the
  16:19 UTC publish of revision 122.

So the tab is **not** a live check. It re-analyses roughly daily; a fix
published after a run does not show until the next one. The header even says
"Powered by Mentor", which is why Mentor's own re-audit and the tab agree in
substance but not in timing.

The 28 flagged items are blocks and block parameters, e.g. `Pagination`,
`Avatar`, `Badge`, `SearchInput`, `Icon`, and `SkeletonBox.ExtendedClass`,
`Skeleton.IsLoading`, `DropdownEmpty.IsOpen`, `SkeletonTable.Rows`,
`DropdownItem.Title`. That is fewer than the 72 descriptions set at revision
122, so the rule counts a narrower set than block + parameter + event + event
parameter + structure + attribute — the fix should more than cover it.

**Do not use "Mark all open as resolved" to clear this.** It marks the findings
resolved without the analyser having verified anything, which hides the debt
instead of confirming it is gone. Let the next scheduled run reassess.

### Also open: Visible disabled button (High)

Unrelated, higher severity than the descriptions, and not previously noticed:

| Severity | Pattern | Category | Count |
| --- | --- | --- | --- |
| High | Visible disabled button | Security | 2 |

**Fixed at revision 125.** Both disabled Buttons were replaced with Containers
that carry the same style classes verbatim
(`fusion-pagination__button fusion-pagination__button--ellipsis`), the same
`"..."` Expression, and `aria-hidden="true"` — no OnClick, no Enabled, no
tabindex, so they render as plain non-focusable `<div>`s. Renamed
`EllipsisDesktop` / `EllipsisPhone` and `EllipsisExprDesktop` /
`EllipsisExprPhone` (Mentor created them as `...Btn...2` because the originals
still existed at creation time).

The tag swap is safe because every `.fusion-pagination__button` declaration is
tag-agnostic — `background-color`, `border: 0`, `border-radius`, `color`,
`cursor`, `display: inline-flex`, `font`, `height`, `width`, `outline: 0` — so a
`div` renders identically to the `button`.

**Two side effects worth knowing.**

1. *A knock-on dead action.* The two Buttons' OnClick was a `NoOp` screen action,
   private to `Pagination`. Deleting them orphaned it and **added** an
   unused-action warning (2 → 3). `NoOp` was then deleted too, taking the count
   back to 2. Mentor initially reported all 3 warnings as pre-existing, which was
   wrong; it retracted when challenged with the revision-124 count. Removing a
   widget can create new dead code — always re-read the warning count against
   the previous revision's, not against the model's own claim.
2. *A small, deliberate divergence from the portal.* The portal's CSS excludes
   `--ellipsis` and `[disabled]` **separately**
   (`:not(.fusion-pagination__button--ellipsis):not([disabled])`), which implies
   the portal's own ellipsis is a `button` that is NOT disabled — focusable, but
   inert on click. Ours is now a `div`: visually identical, but not focusable at
   all. That is a strict a11y improvement and it is what clears the finding, so
   it is intentional rather than a replication miss.

   The one visual difference while it was disabled was the cursor —
   `.fusion-pagination__button[disabled]` is specificity (0,2,0) and beat
   `--ellipsis` at (0,1,0), forcing `cursor: not-allowed` over the portal's
   `cursor: default`. The colour was never wrong: `--button-icon-disabled` ->
   `--button-text-disabled` -> `--text-disabled` -> `--neutral-6`, the same
   value `--ellipsis` resolves to.

The original finding, for the record — both were the pagination ellipsis
buttons:
`Pagination > PaginationRoot > DesktopButtons > PageListDesktop >
PageItemWrapperDesktop > IfEllipsisDesktop > True > EllipsisBtnDesktop`, and the
same path under `PhoneButtons` / `EllipsisBtnPhone`. A disabled-but-visible
button is a real usability and a11y problem: it is focusable-looking, conveys an
affordance that does not exist, and the ellipsis is a label, not a control.

### The 7 pre-existing warnings — audited at revision 122, now 6

Unrelated to descriptions, and five of them matter more:

| Warning | On | Verdict |
| --- | --- | --- |
| unused input parameter | `Icon.IdPrefix` | dead |
| unused input parameter | `LayoutHeader.Collapsed` | **bug — fixed at revision 123** |
| unused input parameter | `Layout_Neo.ScrollType` | dead |
| unused input parameter | `Layout_Neo.LayoutType` | dead, half-recoverable |
| unused input parameter | `Layout_Neo.ReserveSidePanelSpace` | dead |
| Google Fonts URL not cached for offline | `NeoBase` — Noto Sans | advisory |
| Google Fonts URL not cached for offline | `NeoBase` — Source Code Pro | advisory |

Four of those five were genuinely dead and were **deleted at revision 124**:
`Icon.IdPrefix`, `Layout_Neo.ScrollType`, `Layout_Neo.LayoutType`,
`Layout_Neo.ReserveSidePanelSpace`. Publish `outcome: success`, 0 errors,
warnings down to the 2 Google Fonts notices.

### `LayoutHeader.Collapsed` — the warning was RIGHT; another session wired it

The platform flagged it as an unused input parameter. **It is not unused.** It
drives two widget style expressions:

    pageHeaderWrapper: "page-header-wrapper " + If(Collapsed, "page-header-collapsed", "page-header-is-relative")
    pageHeaderTitle:   "page-header-title" + If(Collapsed, " page-header-title-collapsed", "")

Corroborated against the CSS independently of the model: `dist/neobase.css`
carries 2 rules for `.page-header-wrapper`, **11 for `.page-header-collapsed`**
(including `position: fixed` and `box-shadow: var(--overflow-shadow)`), 1 for
`.page-header-is-relative`, 16 for `.page-header-title` and 3 for
`.page-header-title-collapsed`. Deleting the parameter would have broken the
sticky collapsed page header outright.

**CORRECTION.** I first read this as a platform false positive — that ODC's
analysis does not traverse style-property expressions. That was wrong, and the
release wizard's revision list is what disproved it:

    125  Pagination ellipsis: replace disabled Buttons with non-...   18:03
    124  Remove 4 unused block input parameters (Icon.IdPrefix, ...   17:41
    123  Wire LayoutHeader.Collapsed to page-header-collapsed / ...   17:33
    122  Add descriptions to all public elements and parameters       17:19

**Revision 123 wired it.** A second session, spawned to analyse these five
parameters, went ahead and connected `Collapsed` to the two style expressions at
17:33. My session loaded the asset after that and found the references — which
existed because that session had just created them, eight minutes earlier. At
revision 121, when the Code Quality analysis ran, the parameter genuinely was
unread and the warning was correct.

The real lesson is about concurrency, not the analyser: **when another session
may have touched the asset, a reference you find proves nothing about when it
appeared.** Check `app_revisions` for gaps and read the publish messages in the
release wizard, which is the only place the per-revision comment is visible.
Grepping the CSS did confirm the classes are real (`.page-header-collapsed` has
11 rules) — so the wiring is correct and worth keeping — but it could never have
told me whether the parameter was wired before or after the warning was raised.

**One fact explains four of the five.** The layout blocks no longer emit the
`fusion-layout*` classes these parameters were designed to concatenate into
([`o11-theme-module.md`](o11-theme-module.md) still documents that design). Read
off the model at revision 122:

| Block | Root container Style Classes, verbatim |
| --- | --- |
| `Layout_Neo` | `"layout nds-layout neo-layout-shield-phone neo-layout-shield-tablet"` — a literal |
| `LayoutHeader` | `"page-header-wrapper page-header-is-relative"` — a literal |
| `Icon` | one `AdvancedHtml` `<i>`, `"ph ph-" + Name + " pds-icon" + If(Size = "", "", " icon-" + Size)` |

That matches `tools/neobase.py`, which drops `layout.css` from the shipped theme
— so `dist/neobase.css` carries **0** occurrences of `fusion-layout--scroll-type`,
`fusion-layout--type--`, `reserve-side-panel-space` or
`fusion-layout-header--collapsed`. The parameters are residue of the pre-rewrite
design.

Per parameter:

- **`Icon.IdPrefix`** — dead. The block renders a Phosphor *font* icon by class
  name and produces no `<svg>`/`<use href="#…">`, so there is no sprite id for a
  prefix to precede. The mechanism [`icons.md`](icons.md) describes is gone.
- **`Layout_Neo.ScrollType`** — dead, with nothing to wire to. The legacy
  `nds-layout` family has no scroll-type modifier at all.
- **`Layout_Neo.LayoutType`** — dead, half-recoverable. One of its two documented
  values has a live target: `.nds-layout.layout-widescreen .theme-grid-container
  { max-width: 2352px }`. There is no `narrow` equivalent in the shipped sheet.
- **`Layout_Neo.ReserveSidePanelSpace`** — dead; the region it modified is gone.
  `Layout_Neo`'s placeholders are `Header`, `TopInfo`, `Content` — no `SidePanel`,
  and no container with any side-panel class. The theme's 31
  `.layout-right-sidepanel` rules exist, but nothing in the library renders that
  element.

**`NeoLayoutCheck` passes all five, and none is load-bearing.** One `Layout_Neo`
(screen `Home`, inside `AppShell` → Content) with `ScrollType`, `LayoutType` and
`ReserveSidePanelSpace` all `null`; one `LayoutHeader` (`LayoutHeader2`, in
`Layout_Neo` → Header) with `Collapsed = "False"`, the default written out; every
`Icon` placement passes `null` for `IdPrefix`. So no consumer *depends* on a
value — but the harness would still fail to compile against a version with these
removed, once its pin is bumped.

### `LayoutHeader.Collapsed` was the one real bug — fixed at revision 123

The shipped theme *does* carry the target: 14 rules on `.page-header-collapsed`
(including an unscoped `position: fixed` one), 5 on
`.page-header-title-collapsed`, plus
`.page-header-wrapper:has(.page-header-title-collapsed)`. The block simply never
emitted either class. Two Style Classes expressions, no logic, no CSS:

```
pageHeaderWrapper  "page-header-wrapper " + If(Collapsed, "page-header-collapsed", "page-header-is-relative")
pageHeaderTitle    "page-header-title" + If(Collapsed, " page-header-title-collapsed", "")
```

Published as revision 123, `outcome: success`, 0 errors — and the validation
warning count dropped 7 → 6, which is the independent confirmation that the
parameter is now read. **Not tagged**, so consumers still see 0.1.88 until a
version is released and their pin bumped.

Caveat worth knowing before using it: the portal drives this from a scroll
handler, so a static Boolean input gets you the styling, not the behaviour — the
consumer has to toggle it.

The remaining four are best batched into one deliberate breaking release rather
than removed one at a time; a public-surface removal costs a consumer republish
per pin bump either way.

**Self-hosting the two fonts is not worth it on the strength of the warning.** A
library Resource URL will not work — ODC leaves pasted theme-CSS urls verbatim,
so it 404s silently — leaving base64 inlining as the only route (precedent:
`dist/o11-phosphor/`, a 147 KB woff2 shipped inline). Six faces would add roughly
150–250 KB of base64 to a 345 KB sheet and need regenerating on every weight
change. The `--font-family` token already carries a full system fallback stack,
so the page stays legible if Google is unreachable. Do it only for genuinely
offline rendering, to drop the third-party request for privacy reasons, or to
kill the render delay from a blocking `@import`.

**Anything added to this library's public surface needs a description at the same
time.** Nothing in the build or publish pipeline enforces it — the publish
reports 0 validation errors either way, so it only surfaces in the portal's Code
Quality tab, after the fact.


---

## Released as 0.1.89

Revision 125, released 2026-09-10 18:08, superseding 0.1.88 (revision 121).
Contains revisions 122-125: the descriptions, the `Collapsed` wiring, the four
parameter removals and the pagination ellipsis fix.

**It is a breaking release.** Four public block input parameters are gone, so a
consumer that sets any of `Icon.IdPrefix`, `Layout_Neo.ScrollType`,
`Layout_Neo.LayoutType` or `Layout_Neo.ReserveSidePanelSpace` fails to compile
once its pin moves to 0.1.89. `NeoLayoutCheck` is the only consumer listed on
the library's Consumers tab. The version number does not signal this — the tenant
convention is sequential patch bumps and the wizard prefilled 0.1.89; 0.2.0
would have carried the signal better.

---

## Verified on the harness at 0.1.89

`NeoLayoutCheck` revision 171, pin bumped to 0.1.89, checked live at
`NeoLayoutCheck` on the dev environment.

**Pagination ellipsis — confirmed fixed.** Both ellipsis elements:

| | |
| --- | --- |
| tag | `DIV` (was `BUTTON`) |
| `aria-hidden` | `true` |
| `tabIndex` | `-1` — not in the tab order |
| `disabled` attribute | absent |
| computed `cursor` | `default` — the portal's value, no longer `not-allowed` |
| size | 32x32, identical to the numbered buttons |

Renders as `< 1 2 3 4 ... 7 >` with the ellipsis dimmed and aligned. The one
disabled button left in the strip is `--prev` on page 1, which is a real control
that is genuinely unavailable — correct, and it was never part of the finding.

**`LayoutHeader.Collapsed` — wiring confirmed.** The live wrapper carries
`page-header-wrapper page-header-is-relative`, i.e. the `If(Collapsed, ...)`
False branch, so the expression evaluates. Forcing the True branch produces
`position: relative -> fixed`, width `1193px -> 1457px` (full-bleed) and the
title dropping from `30px/40px` to `20px/32px`. The CSS behind it is real.

Note that **nothing in the harness sets `Collapsed`** — the Users page does not
even scroll (`scrollHeight` == `innerHeight`), so the collapsed state is never
reached in normal use here. The True branch was verified by applying the classes
by hand, not by driving the parameter.

### Referenced-but-undefined custom properties

Found while checking the collapsed header. `dist/neobase.css` references **20
custom properties by `var()` that are never defined anywhere in the file**:

- **11 with no fallback**, so the whole declaration is silently dropped:
  `--color-neutral-9` (3 refs), `--color-neutral-2` (3), `--surface-1` (3),
  `--color-neutral-0` (2), `--border-size-none` (2), `--time-to-live` (2),
  `--time-m`, `--linear`, `--hidden-label`, `--font-size-xxs`, `--footer-size`.
- **9 with a fallback**, which are harmless by design — the fallback is the
  intended value: the slider and range-slider track dimensions,
  `--fusion-layout-sticky-top-offset`, `--progress-rate`,
  `--fusion-dropdown-empty-trigger-background`.

`--color-neutral-N` and `--surface-1` are a **different naming scheme** from the
tree's own `--neutral-N`, which suggests those rules were captured from a portal
version whose token names have since changed. Unconfirmed.

This is the opposite of the 236 defined-but-unreferenced tokens, and the
dangerous direction: an unreferenced token is inventory a consumer can use, but
an undefined reference is a declaration that never applies. `tools/verify.py`
does not catch it — it proves the split is lossless against the source, and
these references are broken in the source too.

## The collapsed header's last two misalignments

Two visible defects survived the sticky-bar work: the title read 4px high and
the Invite button sat 43px left of the portal's. Both were found by reading the
portal's DOM and computed styles rather than by inference, and both had the
same root cause — a rule or an element we had put in the wrong place.

### `.page-title-content` — the element was already there

Measured on the portal, the chain above the title is:

```
.page-header-content                    flex, align-items: normal
  div.page-title-content                block, align-self: CENTER, height 32
    div.OSBlockWidget                   inline
      .page-header-title                flex, height 32
```

`align-self: center` on `.page-title-content` is what centres the 32px title
inside the 40px row. Ours rendered `y72->104`, the portal `y76->108`.

The fix needed **no structural change at all**: our `LayoutHeader` already
renders the element (`b91-pageTitleContent`, class `page-title-content`). The
rule was simply never extracted — `.page-title-content { align-self: center;
min-width: 0 }` lives in `old-neo-design-system.css`, outside
`extract_legacy_layout.py`'s `.ds-layout` / `.main` whitelist, so the class was
in our markup with nothing behind it. Without `align-self` the wrapper
stretches to the row's full 40px and the shorter title lands at its top.

Added verbatim to `compat/neo-odc-compat.css` section 32.

### `min-width-m text-align-right` was on the wrong element

The portal's actions area is three elements, not one:

```
div.page-header-actions.ph            display: flex        min-width: auto
  div.min-width-m.text-align-right    display: BLOCK       min-width: 150px
    div                               display: block
      button.btn.btn-primary          inline-flex -> pushed right by
                                      text-align on a block parent
```

Our `LayoutHeader` had all three classes collapsed onto the **placeholder**,
which is `display: flex`. `text-align` does nothing to a flex item, so the
button sat at flex-start — exactly `150 - 107 = 43px` left of the portal's
position. The 150px floor was real, the alignment mechanism was not.

Fixed structurally, in two places:

- **Library** (revision 145): the `Actions` placeholder's class list is now
  `page-header-actions neo-ph` only, matching the portal's
  `page-header-actions ph`. Positioning classes are the consumer's job, as they
  are in the portal.
- **Harness** (revision 189): a `Container` named `InviteUserBtnWrapper` with
  class `min-width-m text-align-right` now wraps the button. The Model API
  refuses to reparent, so the button was recreated inside the container and the
  original deleted — `btn btn-primary`, `Enabled: True`, `OnClick -> Primary`,
  label Expression `InviteUserLabel` = "Invite user", all preserved.

We deliberately did **not** add a `.page-header-actions { justify-content:
flex-end }` override. It would have produced the same pixels while encoding a
rule the portal does not have, and the next person diffing the two stylesheets
would have had to rediscover why.

The portal's third, unnamed `div` between the wrapper and the button carries no
styling — one wrapper is geometrically identical, so the harness has one.

### Which `.min-width-m` wins

The portal loads two conflicting declarations at equal specificity:

| sheet | file | value |
|---|---|---|
| 9 | `NeoDesignSystem.Legacy_NeoTheme` | `min-width: 24px` |
| 12 | `usersaccess.Users_Th` | `min-width: 150px` |

The later sheet wins, so 150px is correct — established by reading the computed
value on the portal (`min-width: 150px` on the wrapper), not by assuming the
order of `tools/stylesheets.txt`, which is grouped by purpose and is **not** the
document's load order.
