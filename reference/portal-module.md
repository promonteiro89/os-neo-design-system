# How OutSystems themselves package it

Measured on the live portal (`https://<odc-tenant>/configurations/organization`), 2026-08-03.
Everything below is read out of the runtime — `document.styleSheets`, `performance.getEntriesByType`,
`customElements`, and the served asset bodies. Nothing here comes from Service Studio, so the
interpretations are flagged where they are inferences.

## The load order is the answer

`link[rel=stylesheet]` in DOM order, with live rule counts from the CSSOM:

| # | File | Rules | What it is |
| --- | --- | --- | --- |
| 0 | `_Basic` | 42 | platform |
| 1 | `OutSystemsReactWidgets` | 93 | platform |
| 2 | `font-awesome.min` | 672 | platform |
| 3 | `UnifiedExperienceCommonLib.UnifiedExpTools.UnifiedExperienceChangePassword` | 1 | a **Block**'s CSS |
| 4 | `NeoDesignSystem.NeoDesignSystem.Illustration` | 0 | a **Block**'s CSS (empty) |
| 5 | `NeoDesignSystem.OutSystemsUITheme` | 3160 | **theme** — forked OutSystems UI |
| 6 | `NeoDesignSystem.Legacy_NeoTheme` | 147 | **theme** — brand utilities, `--unified-*` |
| 7 | `NeoDesignSystem.Old_NeoDesignSystem` | 3646 | **theme** — the `ds-*` generation |
| 8 | `NeoDesignSystem.NeoDesignSystem` | 1300 | **theme** — Fusion tokens + components |
| 9 | `configurations.Configuration_Th` | 69 | **theme** — the consuming app's own |
| 10 | `configurations.Configuration_Th.extra` | 77 | platform-generated `ThemeGrid_*` |
| 11 | `prod.unified.css` | 318 | the shell, a Resource from another app |

The filename convention decodes as `<Module>.<Element>`, with a third segment for elements inside a
module: `<Module>.<Block>` for block CSS, `<Module>.<Theme>` for theme CSS,
`<Module>.<Script>` under `/scripts/`, `<Module>.<Image>` under `/img/`.

**Six themes load on one screen, base-first — so it is one inheritance chain:**

```
OutSystemsUITheme → Legacy_NeoTheme → Old_NeoDesignSystem → NeoDesignSystem → Configuration_Th
   (forked OSUI)      brand utils        the ds-* system       Fusion tokens     the app's own
```

A screen has exactly one theme and the platform emits its whole ancestry, base first — that is the
only thing that explains five theme stylesheets in this order. Confirm it in Service Studio by
opening each theme's **Base Theme** property.

This is the same shape as the chain in [`docs/o11-theme-module.md`](../docs/o11-theme-module.md),
one link longer: they keep two design-system generations live simultaneously, and the consuming app
still gets its own thin theme at the end (69 + 77 rules — almost nothing, which is the point).

## `NeoDesignSystem` is a UI module, not a library

The module contains, all under the `NeoDesignSystem.` prefix:

* **4 Themes** — `OutSystemsUITheme`, `Legacy_NeoTheme`, `Old_NeoDesignSystem`, `NeoDesignSystem`
* **Blocks** — at least `Illustration`, which gets its own (empty) CSS file
* **7 Scripts** — see below
* **Images** — e.g. `DEPRECATED_NotResponsiveDark.svg`, `DEPRECATED_NotResponsiveLight.svg`

Themes and Blocks in the same module as scripts and images is a UI-capable module, which settles the
open question in the assembly guide: a design-system module *is* how OutSystems ships this, and it
holds UI elements.

The two `DEPRECATED_NotResponsive{Dark,Light}` images are a nice fossil: the previous generation
shipped light and dark as **separate** assets, where the current one switches on `[data-theme]`.

## They forked OutSystems UI rather than inheriting from it

`NeoDesignSystem.OutSystemsUITheme` is a 3,160-rule copy sitting *inside* their own module. The real
`OutSystemsUI` module is consumed — its `UserScripts.OutSystemsUI` script loads — but its theme is
**not** in the chain. So the CSS was taken as a copy.

It is also an older OutSystems UI than the 2.28.0 you have. Measured in that file:

| | portal's fork | your OSUI 2.28.0 |
| --- | --- | --- |
| `--background-color-*` per-channel layer | **0** declarations | present |
| `--color-neutral-0..10` base scale | 11 | 11 |
| custom properties total | 221 | 221 |

No per-channel layer means **the portal cannot re-skin OutSystems UI through variables the way
`compat/neo-osui-bridge.css` does.** So they do it the other way — by overriding classes directly:

| Layer | Rules | Custom props | Own classes | Classes shared with OSUI |
| --- | --- | --- | --- | --- |
| `OutSystemsUITheme` (fork) | 3160 | 221 | 1431 | — |
| `Legacy_NeoTheme` | 147 | 147 | 312 | 23 (7%) |
| `Old_NeoDesignSystem` | 3646 | 54 | 1516, of which 240 `ds-*` | 293 (19%) |
| `NeoDesignSystem` (Fusion) | 1300 | **671** | 1030, of which 330 `fusion-*` | 184 (18%) |

The 54 → 671 jump in custom properties between the two generations is the whole story of the
rewrite: `Old_NeoDesignSystem` restyles `.btn`, `.card`, `.alert`, `.avatar`, `.tabs` and ~290 other
OutSystems UI classes by hand; `NeoDesignSystem` defines a token system instead.

**Consequence for us:** the bridge is not what the portal does, and it is the better option in a
modern app. ~200 variable mappings against OSUI 2.28's per-channel layer get the same result as
their ~3,600 rules of hand overrides, and survive an OutSystems UI upgrade. Keep using it.

## The JavaScript side

Seven Scripts in the module (`/configurations/scripts/NeoDesignSystem.UserScripts.<name>.js`),
sizes as served (gzipped) / raw:

| Script | Raw | What it actually is |
| --- | --- | --- |
| `OutSystemsNDS` | 385 KB | the in-house bundle: component behaviour, scroll/resize/render |
| `purify_min` | 25 KB | DOMPurify (vendored) |
| `Core` | 12.5 KB | `@floating-ui/core` — `computePosition`, `flip`, `offset`, `autoPlacement` |
| `DOM` | 10 KB | `@floating-ui/dom` — `getClippingRect`, `autoUpdate` |
| `ContentObserver` | 6 KB | mutation-observer helper |
| `HasBottomSpace` | 1.3 KB | one predicate, `hasBottomSpace` |
| `Helpers` | 346 B | misc |

Third-party libraries are vendored as individual Script elements rather than bundled — each one is a
separate element you could copy into your own module the same way.

## Fusion is a Stencil library

`/configurations/fusiondesignsystem.esm__<hash>.js`, loaded as `<script type="module">`, 9 KB. It is
built with **Stencil**: `bootstrapLazy` / `registerInstance` / `patchBrowser` / `promiseResolve` are
all present, it declares 38 components, and it lazy-loads per-component chunks (`p-fa31dcdf.entry.js`,
`p-4890f72e.entry.js` — only two on this screen, because only two Fusion components are used).

Stencil injects a `<style data-styles>` block containing its two tells:

```css
slot-fb { display: contents }  slot-fb[hidden] { display: none }
ds-app-icon, ds-avatar, …, fusion-wizard-step { visibility: hidden }
.hydrated { visibility: inherit }
```

The full registry — 31 `fusion-*` plus 7 `ds-*`:

```
fusion-accordion fusion-accordion-item fusion-avatar fusion-brand fusion-breadcrumb-item
fusion-carousel fusion-code-snippet fusion-collapsible fusion-collapsible-core fusion-counter
fusion-display-html fusion-dropdown-empty fusion-dropdown-item fusion-empty-state
fusion-filter-row fusion-icon fusion-illustration fusion-layout fusion-layout-header
fusion-layout-section-structure fusion-loading-spinner fusion-logo fusion-page-title
fusion-pagination fusion-progress-bar fusion-score fusion-side-panel fusion-tag
fusion-wizard fusion-wizard-section fusion-wizard-step

ds-app-icon ds-avatar ds-column-chart ds-icon ds-skeleton-loader ds-tree-item-type-1 ds-tree-view
```

Two things this confirms and one it adds:

* **No shadow DOM** — `document.querySelectorAll('*')` finds zero `shadowRoot`s on the page. Stencil
  is running in light-DOM mode, which is exactly why every component style has to live in the global
  theme stylesheet, and why the class names are the whole API.
* `fusion-button` is **not** registered — buttons really do come from OutSystems UI, as the token/rule
  split in `reference/audit.md` §4 already implied.
* **New:** the components are `visibility: hidden` until Stencil adds `.hydrated`. If you ever load
  the ESM bundle in your own app, un-hydrated elements are invisible rather than unstyled — a very
  different failure mode from hand-writing the markup, where no such rule exists.

## Placeholders and slots, as rendered

58 `.ph` elements on the page, **37 of them empty** — so the platform emits a placeholder's wrapper
whether or not it has content, which is precisely what the bundle's `:has(> .ph:empty)` auto-hide
rules need. All 58 are `div`s, and the id is `<block-instance>-<PlaceholderName>`:

```html
<div class="ds-layout-header-breadcrumbs page-header-breadcrumbs ph" id="b1-b1-Breadcrumbs">
```

That id pattern makes the layout blocks' placeholder API readable straight off the DOM:

| Block | Placeholders |
| --- | --- |
| header (`b1-b1`) | `Breadcrumbs`, `SupportTextLeft`, `SupportTextRight`, `Actions`, `Description`, `Metadata` |
| layout (`b1-b2`) | `MainContentTitle`, `MainContentDescription`, `MainContentAction`, `MainContentFooter`, `PageTopInfo`, `PageFilters`, `SearchFilter` |
| nested component blocks | `Title`, `Type`, `Heading`, `Action`, `Actions`, `SecondaryActions`, `Helper`, `HelperText` |

**26 of the 58 sit inside a `[slot]` container** — 39 `[slot]` elements in total, with values like
`slot="type"`, `slot="title"`, `slot="aux-text"`. That is how content is fed to the Stencil
components in light DOM, and it is set from Service Studio as an **Extended Property** on a Container.
Three placeholders are nested `.ph > .ph`, which is what the bundle's `:has(> .ph > .ph:empty)`
selectors are written against — the outer one is the layout's, the inner one belongs to the block a
consumer dropped into it.

**`ph` is hand-authored, not platform output.** Corrected 2026-09-03 after measuring a live ODC app:
the platform emits the placeholder div and its `id`, but *no class at all*. Every class on the
element above — `ds-layout-header-breadcrumbs`, `page-header-breadcrumbs` and `ph` alike — is typed
into the Placeholder widget's Style Class property by the portal's developers. `ph` is simply a
convention they apply to every placeholder so the auto-hide selectors have something to bind to.

Two consequences:

* The `.ph` rules are not dead code in an OutSystems app — but they only work if you follow the
  convention. This corrects the earlier claim in `compat/neo-o11-compat.css` in one direction and
  the "platform behaviour" reading in the other.
* Reproducing Neo means setting Style Class `ph` on every Placeholder you author. Omitting it breaks
  auto-hide *silently*, and for `:not(:has(… .ph:not(:empty)))` rules it hides filled content. That
  cost the `Section` block its header and footer until revision 14 — see
  [`docs/odc-library.md`](../docs/odc-library.md).

## What this changes for our approach

1. **The chain is right.** `OutSystemsUI → NeoTheme → YourAppTheme` is what they do, minus the two
   legacy links. Keep the consuming app's theme thin — theirs is 69 rules.
2. **Don't fork OutSystems UI.** They had to; you don't, because your 2.28.0 has the per-channel
   variable layer their copy lacks. The bridge is ~200 mappings against ~3,600 hand overrides.
3. **A UI module is the correct container.** Themes, Blocks, Scripts and Images coexist in one
   module — the assembly guide's structure matches.
4. **Vendor scripts as separate Script elements** if you ever need Floating UI or DOMPurify; that is
   the platform-idiomatic way and it is what they did.
5. **Don't chase the Stencil bundle.** Reusing it means shipping a lazy-loading runtime, a hydration
   contract and 38 components' worth of chunks, for behaviour you can get from OutSystems UI widgets
   plus Neo's classes. The tokens are the durable part; that has not changed.

## Not verified

* The **Base Theme** properties are inferred from load order, not read from Service Studio. The order
  is strong evidence but check the property itself if you depend on it.
* Which elements are Public, and the module's layer in the architecture canvas, are not observable
  from the runtime.
* `Illustration` is inferred to be a Block from the three-segment CSS name; it could be a Screen.
* `OutSystemsNDS` was not decompiled — the 385 KB is characterised by its top-level function names
  only.

## Reproducing this

The portal is an authenticated page, but every asset above is a plain GET. In the browser console:

```javascript
[...document.querySelectorAll('link[rel=stylesheet]')].map((l, i) =>
  `${i} ${l.sheet ? l.sheet.cssRules.length : '?'} ${new URL(l.href).pathname.split('/').pop()}`).join('\n')
```

```javascript
document.querySelector('style[data-styles]').textContent    // the Stencil component registry
performance.getEntriesByType('resource').map(r => new URL(r.name).pathname)   // every asset
```
