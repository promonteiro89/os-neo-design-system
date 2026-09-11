# The portal layout

Two layers, two templates:

| | Template | Covers |
| --- | --- | --- |
| **Page scaffold** | [`templates/fusion-layout.html`](../templates/fusion-layout.html) | Header, breadcrumbs, title, actions, content, side panel |
| **Full layout** | [`templates/portal-shell.html`](../templates/portal-shell.html) | The above **plus** the top bar and nav rail |

Open either in a browser; the switcher in the corner toggles every modifier. Start with
[the shell section](#the-portal-shell) if you want the complete portal look, or stay in this
first half if you only need the page scaffold inside your own chrome.

## How this was established

Two independent sources, which is why the awkward details below are trustworthy:

1. **Read out of the CSS.** Child combinators and `:has()` rules pin the nesting down exactly —
   `.fusion-layout__header:has(.fusion-layout-header)` only matches one arrangement.
2. **Cross-checked against the live portal** at `/configurations/organization`. That page still
   runs the *previous* generation, `ds-layout` — see [the mapping](#ds-layout--fusion-layout) —
   but the region-for-region correspondence confirms the intent of each Fusion class.

Every modifier below was then verified in the browser by reading computed styles, not assumed
from the class name.

## Structure

```
fusion-layout                                 custom element, {display:contents}
└── .fusion-layout                            flex row, height 100%
    ├── .fusion-layout__main                  flex: 1
    │   └── .fusion-layout__content           flex column
    │       ├── .fusion-layout__header        → .fusion-layout-header
    │       ├── .fusion-layout__top-info      full-bleed alert slot
    │       └── .fusion-layout__main-content  max-width 1384px, centred, gap space-7
    └── .fusion-layout__side-panel            sticky, sibling of __main
        └── .fusion-side-panel
```

Header internals:

```
.fusion-layout-header
└── .fusion-layout-header__inner              max-width + padding-inline space-7
    ├── __breadcrumbs                         margin-bottom space-3
    ├── __content                             flex, space-between
    │   ├── __left-content
    │   │   ├── __title  → .fusion-page-title (__avatar __title __icon __badge)
    │   │   └── __support-text                truncates at max-width 100px
    │   └── __right-content
    │       └── __actions                     gap space-3
    ├── __description                         margin-top space-2, 2-line clamp
    └── __details                             margin-top space-4, wraps, gap space-6/space-4
        └── .metadata-container ×n            (-label, -content, -title)
```

## Modifiers

| Class | Applied to | Effect |
| --- | --- | --- |
| `--type--narrow` | `.fusion-layout` | Content locked to 636px (min *and* max), centred |
| `--type--widescreen` | `.fusion-layout` | `--layout-content-max-width` 1384px → 2352px |
| `--scroll-type--page` | `.fusion-layout` | The whole content column scrolls — the common case |
| `--scroll-type--section` | `.fusion-layout` | Only the section body scrolls; tabs get `height: 100%` |
| `--scroll-type--section-column` | `.fusion-layout` | As above, plus the section-structure itself scrolls |
| `--reserve-side-panel-space` | `.fusion-layout` | Panel keeps its width when closed, so content does not reflow |
| `--collapsed` | `.fusion-layout-header` | Sticky condensed bar: hides breadcrumbs, description and details; title drops to `heading-3`; adds `--overflow-shadow` |
| `--open` | `.fusion-side-panel` | 400px (320px with `--size-small`); shell fades in |
| `--size-small` | `.fusion-side-panel` | Expanded width 400px → 320px |
| `--type-floating` | `.fusion-side-panel` | Collapses to a 32px rail instead of 0, toggle always visible |
| `--style-ghost` | `.fusion-side-panel` | Transparent, no left border |
| `--sticky` | section `__header` / `__footer` | Pins to top / bottom with a `--page-background` backdrop |

Verified: with `--collapsed` the three regions compute to `display: none` and the title to
`600 20px/32px "Noto Sans"`; with `--type--narrow` main content computes to `min-width: 636px`;
closing the panel animates it to `0px` with the shell at `opacity: 0`.

## Three things that will bite you

**1. Regions auto-hide based on OutSystems placeholder wrappers.** `.ph` is the platform's
placeholder div. These hide when the placeholder chain is empty:

```css
.fusion-layout__top-info:has(> .ph:empty)                    { display: none }
.fusion-layout-header__breadcrumbs:has(> .ph > .ph:empty)    { display: none }
.fusion-layout-header__description:has(> .ph > .ph:empty)    { display: none }
.fusion-layout-header__details:has(> .ph > .ph:empty)        { display: none }
```

In hand-written markup, just omit the `.ph` div and the region always shows. Include it and you
inherit the auto-hide for free — useful when the content is bound to an optional field.

**2. The section header and footer are the inverse — hidden until proven non-empty.**

```css
.fusion-layout-section-structure__header:not(:has(div[slot] .ph:not(:empty))) { display: none }
.fusion-layout-section-structure__footer:not(:has(div[slot] .ph:not(:empty))) { display: none }
```

Your section title **will silently vanish** unless it is wrapped:

```html
<div class="fusion-layout-section-structure__header">
  <div slot="header">
    <div class="ph">…title and subtitle here…</div>
  </div>
</div>
```

This one cost me a debugging cycle; it is not guessable from the markup.

**3. `--layout-content-max-width` is scoped to `.fusion-layout`, not `:root`.** Override it on the
layout element. Note also that `--type--narrow` only narrows `__main-content` — `__top-info` and
the header keep following the max-width, so a page alert stays full width while the content is
636px. That is the upstream behaviour, not a bug in this template.

## `ds-layout` → `fusion-layout`

The portal's `/configurations/organization` DOM, mapped to its Fusion counterpart. This is a
correspondence by name and role — I read the `ds-` side from the live DOM and verified the Fusion
side renders, but did not diff the two stylesheets rule by rule, so treat the geometry as
equivalent-in-intent rather than pixel-identical.

| Portal today (`ds-layout`) | Fusion equivalent |
| --- | --- |
| `.ds-layout` | `.fusion-layout` |
| `.ds-layout-main-content` | `.fusion-layout__main` |
| `.ds-layout-wrapper` | `.fusion-layout__content` |
| `.ds-layout-header` | `.fusion-layout-header` |
| `.ds-layout-header-breadcrumbs` | `.fusion-layout-header__breadcrumbs` |
| `.ds-layout-header-wrapper` | `.fusion-layout-header__content` |
| `.ds-layout-header-left` / `-right` | `.fusion-layout-header__left-content` / `__right-content` |
| `.ds-layout-header-title` | `.fusion-layout-header__title` |
| `.ds-layout-header-support-text-left` / `-right` | `.fusion-layout-header__support-text` |
| `.ds-layout-header-actions` | `.fusion-layout-header__actions` |
| `.ds-layout-header-description` | `.fusion-layout-header__description` |
| `.ds-layout-header-page-details` | `.fusion-layout-header__details` |
| `.page-header-title` / `-title-wrapper` | `.fusion-page-title` / `__title` |
| `.metadata-container` (+ `-label`, `-content`, `-title`) | unchanged — Fusion restyles the same markup |
| `.neo-layout-shield*`, `.OSBlockWidget`, `.display-contents` | no equivalent — platform plumbing |

`.metadata-container` is the interesting row: it belongs to the legacy theme, but the Fusion
bundle restyles it inside `__details` (resets border and background, sets label and title type),
so metadata blocks render correctly with only Neo loaded. That is also why it appeared in
[`reference/audit.md`](../reference/audit.md) §4 as an external class.

## Measured: our `fusion-layout` vs the portal's rendered `ds-layout`

The mapping above was a correspondence by name and role — I flagged it as "equivalent-in-intent
rather than pixel-identical" because I had not diffed the two. This is that diff. Portal side read
from computed styles on `/configurations/organization`; our side resolved from
`src/02-components/layout.css` through the token chain.

| | Portal, rendered (`ds-layout`) | Ours (`fusion-layout`) | |
| --- | --- | --- | --- |
| content max-width | `1384px` (`.ds-layout-wrapper`) | `1384px` (`--layout-content-max-width`) | match |
| horizontal padding | `32px` | `32px` (`--space-7`) | match |
| content top padding | `16px` (`.ds-layout-content`) | `16px` (`--space-4`) | match |
| header content gap | `24px` (`.ds-layout-header-wrapper`) | `24px` (`--space-6`) | match |
| header title | `600 30px/40px "Noto Sans"` | `var(--heading-1)` → `600 30px/40px` | match |
| section header/footer gap | `24px` (`.ds-layout-section-base`) | `24px` (`--space-6`) | match |
| **stack rhythm between sections** | no flex gap — `.ds-layout-content` is `display:flex; gap:normal; flex-direction:row`, spacing comes from `.ds-layout-section-base`'s own `24px` | `24px` flex gap on `.fusion-layout__main-content` (was Fusion's `32px`) | matched, see below |

So the outer frame is pixel-identical — same 1384px measure, same 32px gutters, same 16px top
padding, same 24px header gap, same 30/40 title. The one real difference is vertical rhythm between
stacked sections: Fusion puts a `32px` gap on the content column, where `ds-layout` has no gap and
lets each section's own `24px` do the work.

That difference was **upstream's**, not ours — `fusion-layout` is OutSystems' own newer CSS, copied
verbatim, and Fusion differs from `ds-layout` by 8px of section rhythm.

**We now follow the portal here.** `.fusion-layout__main-content` uses `gap: var(--space-6)` (24px)
rather than Fusion's `var(--space-7)` (32px):

```css
.fusion-layout__main-content {
  gap: var(--space-6);  /* portal rhythm: ds-layout 24px, Fusion 32px */
  padding: var(--space-4) var(--space-7);
}
```

This is **the only place this library knowingly departs from the Fusion CSS**, and it is a deliberate
choice to match what the portal renders today. It is applied by the build pipeline via
`GAP_DEVIATION`, which fails the build if it ever stops matching exactly one rule — so a future
upstream restructure cannot silently drop it. Delete that constant to go back to stock Fusion.

`ds-layout` also carries structure Fusion reorganises rather than keeps — `.ds-layout-filter-row`
(with `-search-filter` and `-page-filters`) and
`.ds-layout-section-base-content-{main-content,footer}`. Fusion folds the equivalent into
`fusion-layout-section-structure`. The filter row's styling ships in `2-components.css`.

**Fusion adoption is creeping forward.** An earlier capture found two Fusion custom elements on this
screen (`fusion-dropdown-item`, `fusion-empty-state`); it now renders three — `fusion-badge` has
joined them. The layout itself is still `ds-layout`, with zero `fusion-layout` elements, so building
on Fusion is still a bet on where the portal is going rather than where it is.

## The portal shell

The top bar and nav rail come from a **different product**: `prod.unified.css`, served by
`UnifiedExperienceMenuServices`, not by the Neo bundle. It is split into
[`src/04-shell/`](../src/04-shell) (8 files, 322 rules) and flattened to `dist/neo-shell.css`,
and it consumes 121 Neo tokens — so Neo must load first.

```
body.is-aside-expanded.is-unified-desktop
├── .unified-header              fixed, top 0, height 56px, z-index 101
│   ├── a.unified-header-logo    empty element; SVG comes from background-image
│   ├── .unified-header-divider
│   ├── .unified-expand          rail toggle
│   ├── .unified-tenant-dropdown → .unified-header-portfolio (org name)
│   ├── .unified-header-buttons  → .unified-header-button ("Forge")
│   ├── .unified-header-additional-blocks → -support (the "?" menu)
│   └── .unified-header-login    → .unified-header-login-avatar
├── .unified-aside               fixed, top 56px, width 72px / 256px expanded
│   └── .unified-aside-inner
│       └── .unified-aside-menu
│           ├── .unified-aside-menu-header        "‹ Management"
│           ├── .unified-aside-menu-header-divider
│           └── .unified-aside-menu-content
│               ├── .unified-aside-primary       root level
│               └── .unified-aside-secondary.is-open   level you drilled into
│                   └── .unified-aside-section ×n
│                       ├── .unified-aside-item--level0[data-children=true]  group header
│                       └── .unified-aside-grid.is-displayed
│                           └── .unified-aside-wrapper
│                               └── .unified-aside-item--level1 > a          page link
└── #reactContainer              your app; offset by both
    └── fusion-layout            the page scaffold from the first half
```

### The portfolio dropdown: four variants, and why ours is inert

`.unified-header-portfolio` is not "a dropdown that happens to be dead in a single-portfolio
tenant" — that was the earlier reading here, and it was wrong. The shell chooses one of four
**variants** and writes it to `data-variant` on the root. Measured 2026-09-07 on
the ODC portal renders:

```html
<div class="unified-header-portfolio" data-test-id="portfolio-dropdown" data-variant="minimal">
```

`minimal` is why there is no arrow and no overlay — not the portfolio count. `buildOverlayItems`
and `bindTriggerEvents` run **only** when `variant === "dropdown"`, so under every other variant
the overlay div is emitted and left empty and the trigger has no click handler at all. Clicking it
does nothing, which is exactly what we measure.

| variant | title | description | arrow | overlay + click |
| --- | --- | --- | --- | --- |
| `minimal` | removed | organization label | removed | no |
| `label` | kept | active portfolio label, else removed | removed | no |
| `dropdown` | kept | active portfolio label, else removed | kept | **yes** |
| `full` (default) | kept | active portfolio label, else removed | kept | no |

Do not wire a toggle onto the trigger to "fix" the dead dropdown — under `minimal` the portal has
no handler either. Emit the empty overlay div and leave it alone, which is what `ShellHeader` does.

#### The populated markup

This is no longer inferred. It is read from the shell's own templates in
`UnifiedExperienceMenuServices/resources/0.1.122/prod.unified.js`, so it is exact — a
multi-portfolio tenant is not needed after all:

```html
<div class="unified-header-portfolio" data-test-id="portfolio-dropdown" data-variant="dropdown">
  <div class="unified-header-portfolio-body" data-test-id="portfolio-dropdown-body">
    <div class="unified-header-portfolio-trigger">
      <div class="unified-header-portfolio-trigger-content">
        <div class="unified-header-portfolio-trigger-title"
             data-test-id="portfolio-trigger-title">{organization.label}</div>
        <div class="unified-header-portfolio-trigger-description-row">
          <div class="unified-header-portfolio-trigger-description"
               data-test-id="portfolio-trigger-description">{activePortfolio.label}</div>
          <div class="unified-header-portfolio-trigger-arrow">
            <svg viewBox="0 0 32 32" fill="currentColor" class="pds-icon icon-small">
              <use xlink:href="#ic-chevron-down"></use></svg>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="unified-header-portfolio-overlay" data-test-id="portfolio-dropdown-overlay">
    <div class="unified-header-portfolio-items">
      <div class="unified-header-portfolio-item is-active"
           data-id="{key}" data-test-id="portfolio-item-{key}">
        <div class="unified-header-portfolio-item-label"
             data-test-id="portfolio-item-label-{key}">{label}</div>
      </div>
      <!-- one .unified-header-portfolio-item per entry in portfolios[] -->
    </div>
  </div>
</div>
```

Notes that matter for replicating it:

- `.unified-header-portfolio-items` is created in code, not in a template — it is a bare
  `document.createElement("div")` with the class assigned, appended to the overlay. The nesting
  above is therefore established, not read off the flex properties.
- **`is-open` goes on the ROOT**, not on the overlay: `this._elPortfolio.classList.add("is-open")`.
  Both open-state rules key off it — `.unified-header-portfolio.is-open .unified-header-portfolio-overlay`
  and `... .unified-header-portfolio-trigger-arrow { transform: rotate(-180deg) }`.
- The active item carries `.is-active` when `key === activePortfolioKey`.
- Both the title and the description also get a `title` attribute equal to their text.
- Dismissal is a one-shot capture-phase listener on `body`; it bails out if the click target's
  className contains `unified-header-portfolio`.
- Selecting an item does not navigate. It re-marks `.is-active`, rewrites the trigger description,
  closes the root, and posts `UNIFIED_PORTFOLIOCHANGE` with `{PortfolioKey}` to the host.

All 17 portfolio rules are already in `dist/neobase.css`, mined wholesale from `unified-shell.css`
— including every class above that no portal page we can reach ever renders. There is no CSS gap
here, only markup we had not read.

#### The tenant switcher is gated differently — by count, not variant

Easy to conflate with the portfolio, and the two behave differently. Read from the same bundle:

| | gate |
| --- | --- |
| portfolio overlay | `variant === "dropdown"` |
| tenant overlay | `tenants.length > 1` for the items; opening also allows a `Type == "tenant"` menu entry |

So the portfolio really is variant-driven, while the tenant switcher really is count-driven — the
"needs more than one of them" intuition is correct for the tenant and wrong for the portfolio.

The two are also mutually exclusive: `createPortfolio()` removes `.unified-header-tenant`, and the
tenant's `create()` removes `.unified-header-portfolio`. Verified on the portal 2026-09-07 —
`.unified-header-tenant` is absent and `.unified-header-portfolio` present, with
`osunified.asideInformation.tenants.length === 0`.

One wrinkle worth knowing before you chase it: `.unified-header-tenant-overlay` **is** in the
portal DOM at 200x16 with 0 children, but it is an **orphan** — its parent is `.unified-header`
directly, not a `.unified-header-tenant` root, which no longer exists. It is a leftover stub, not a
live widget. Do not read it as evidence the tenant switcher is mounted.


### Load order

```html
<link rel="stylesheet" href="dist/neobase.css">   <!-- everything, in order. That is all. -->
```

One file. `neobase.css` already contains the shell, `neo-shell-compat.css`, `neo-odc-compat.css`
and the four properties the upstream bundle references but never defines — assembled in the
portal's own cascade order by `tools/neobase.py`.

**Do not also load `compat/neo-compat.css` after it.** That file exists for the tokens-only path
(`dist/neo-tokens.css` + `neo-compat.css`, no bundle). Loading it after the bundle used to zero
`--unified-header-height` and `--unified-aside-width-expanded`, collapsing the header to 0px tall
and the rail to 0px wide — measured 2026-09-07 in `templates/portal-shell.html`. The zeros are
gone now, but the file still redefines four properties the bundle already has, so it buys you
nothing here.

### Body classes are mandatory

The shell is driven by classes the portal sets **from JavaScript, not media queries** — 45 rules
key off `.is-aside-expanded` alone. The live portal uses, verbatim:

```html
<body class="is-aside-expanded osx is-unified-desktop desktop landscape">
```

| Class | Effect |
| --- | --- |
| `.is-aside-expanded` | Rail at 256px; omit for the 72px icon rail |
| `.is-unified-desktop` | Rail sits beside the content |
| `.is-unified-tablet` | Rail overlays the content — no content offset |
| `.is-unified-phone` | Rail becomes a full-screen sheet |

There is no CSS-only fallback; `compat/neo-shell-compat.css` carries a resize handler you can copy.
The thresholds are the portal's own, read out of `prod.unified.js` — not media queries, and not
guessable from the CSS:

| `window.innerWidth` | Class |
| --- | --- |
| `<= 543` | `.is-unified-phone` |
| `<= 1199` | `.is-unified-tablet` |
| otherwise | `.is-unified-desktop` |

`.is-aside-expanded` keys off the **same 1199 boundary**: at or below it the portal removes the
class, above it adds it, persisting the choice to storage.

### State classes, all JS-driven

| Class | Meaning |
| --- | --- |
| `.unified-aside-secondary.is-open` | Drilled into a sub-menu (why the header reads "‹ Management") |
| `.unified-aside-item--level0.is-open` | Group header, expanded |
| `.unified-aside-grid.is-displayed` | Group body visible |
| `.unified-aside-item--level1.is-active` | Selected page |

### How the collapse actually animates

Not `height`, and not `display`. `.unified-aside-grid` is a CSS grid whose single row goes from
`0fr` to `1fr`, transitioned. That only clips if `.unified-aside-wrapper` — the element carrying
`overflow: hidden` — is the grid's **direct child**. Put anything between them (an OutSystems
placeholder div, for instance) and the row still animates but nothing is clipped, so the group
appears to expand instantly and never collapses.

The portal pairs header and body by id, not by nesting:

```html
<div class="unified-aside-item unified-aside-item--level0 is-open"
     data-children="true" data-parentid="create">…</div>
<div class="unified-aside-grid is-displayed" data-parentid="create">
  <div class="unified-aside-wrapper">…level-1 items…</div>
</div>
```

Opening adds `is-displayed` **and** `is-transitioning`, then removes `is-transitioning` on
`transitionend`. Closing just removes `is-displayed`.

The wrapper's overflow is `hidden` at rest, `visible` under `.is-displayed`, and `auto` under
`.is-transitioning`; the two rules carry equal specificity, so the later `is-transitioning` one
wins while both are present. Worth knowing: **in practice the `transitionend` cleanup does not
fire**, so an opened group sits with both classes and an `overflow: auto` wrapper indefinitely.
That is not a bug in this replica — the live portal's own DOM is in exactly that state (measured
2026-09-07: `unified-aside-grid is-displayed is-transitioning`, wrapper `overflow: auto`, long
after load). Reproduce the portal, not the apparent intent.

One `.unified-aside-section` holds exactly one group: the level-0 header followed by its grid. The
portal renders ten sections, not one section with forty flat items.

**Level-1 icons depend on which menu you are in, and the CSS will not tell you.** The two menus
carry different item markup even though they share every class:

| | `.unified-aside-primary` (root) | `.unified-aside-secondary` (drilled in) |
| --- | --- | --- |
| Example | Create → Solutions, Apps, Agents | Management → Admin, Govern, Configure |
| Level-1 `.unified-aside-item-icon` | present | **absent** |
| Label offset from aside edge | 56px | **32px** |

`.unified-aside-item--level0 .unified-aside-item-icon` and the level-1 icon rules exist in the
stylesheet either way, so reading the CSS suggests icons belong everywhere. They do not. Copying
the primary menu's item markup into a secondary-menu replica pushes every label 24px right — the
kind of difference that reads as "close but wrong" without being obvious. Check the menu you are
actually replicating.

The secondary menu's header also shows a back chevron: `.unified-aside-menu-header-icon-left`
holds `#ic-chevron-left`, revealed by
`.unified-aside-menu:has(.unified-aside-secondary.is-open) .unified-aside-menu-header-icon-left`.
Its sibling `.unified-aside-menu-header-icon` is the primary menu's section glyph and stays hidden
while the secondary menu is open.

**`data-children="true"` is not optional on group headers.** The uppercase group labels come from
`.unified-aside-item--level0[data-children=true] { text-transform: uppercase }`. Without the
attribute the DOM text renders as-is — you get "Admin" where the portal shows "ADMIN". The DOM
never contains the uppercase string.

### The glue you have to write yourself

Four declarations, because the shell only *resets* content offsets to `0` — the real ones live in
the host app's own theme, which this repo does not ship:

```css
html, body { height: 100%; }
body { margin: 0; }                                   /* Neo's reset does NOT do this */
#reactContainer { margin-top: var(--unified-header-height); }
body:not(.is-aside-expanded) #reactContainer { margin-left: var(--unified-aside-width, 72px); }
body.is-unified-tablet #reactContainer,
body.is-unified-phone  #reactContainer { margin-left: 0; }
```

Each one earns its place:

- **`body { margin: 0 }`** — the Neo reset styles `html` and `body` but never zeroes the margin
  (the portal gets that from `_Basic.css`). Without it the default 8px UA margin puts content at
  264/64 instead of 256/56, visibly misaligned against the fixed chrome.
- **`margin-top`** — the top bar is `position: fixed`, so content would slide underneath.
- **The `:not(.is-aside-expanded)` rule** — Neo ships
  `body:has(fusion-layout) #reactContainer { margin-left: var(--unified-aside-width-expanded) }`,
  which hardcodes the *expanded* width and never checks the class. Collapsing the rail to 72px
  would otherwise leave a 184px gap. Specificity (1,1,1) beats Neo's (1,0,2), so it wins.
- **The tablet/phone rule** — Neo's own version is `.is-unified-tablet #reactContainer`, which
  expects the class on an *ancestor* of the container. On `<body>` it never matches, so the
  overlay mode keeps a stale 256px offset.

### Assets

The logo is a `background-image` on an empty element, with light and dark variants swapped by
theme. `tools/fetch.sh` downloads both into `reference/raw/assets/`, and `build.py` copies them
next to every CSS copy (`dist/assets/`, `src/04-shell/assets/`) because the URLs are relative to
the stylesheet. They are the only two assets the shell references.

### Verified against the live portal

Measured on `/configurations/organization` and on the template, same viewport:

| Metric | Portal | Template |
| --- | --- | --- |
| Header height | 56px | 56px |
| Rail width (expanded) | 256px | 256px |
| Content left offset | 256px | 256px |
| Content top offset | 56px | 56px |
| Nav item height | 32px | 32px |
| Active item background | `rgb(47, 50, 58)` | `rgb(47, 50, 58)` |
| Group label type | `600 12px/16px "Noto Sans"` | `600 12px/16px "Noto Sans"` |

Rail states also reflow correctly: expanded 256/256, collapsed 72/72, tablet overlay 256/0.

### What the shell does *not* give you

`dist/neo-shell.css` also contains `.unified-toast-notification` (28 rules), `.unified-tooltip`
(13) and `.unified-banner*` — usable, but undocumented here. What is missing entirely, as with
the page scaffold: `.btn`, `.badge`, the legacy `.avatar` used by the header, `.form-control`,
tables. Those live in `outsystems-ui-theme.css` (already in `reference/raw/`, not split).
`templates/portal-shell.html` builds its buttons, badges, avatar and table from tokens alone so
it stays self-contained — swap in your real widgets.

## Using it in OutSystems

The scaffold is plain divs and classes, so build it as a reusable Block:

1. One Block, `PageLayout`, containing the nesting above.
2. Placeholders for `Breadcrumbs`, `Title`, `Actions`, `Description`, `Details`, `TopInfo`,
   `Content`, `SidePanel`. OutSystems emits `.ph` wrappers for these, which is exactly what the
   auto-hide rules want — so empty placeholders collapse on their own.
3. Input parameters for the modifiers (`Type`, `ScrollType`, `IsHeaderCollapsed`,
   `IsPanelOpen`) and concatenate them into the root element's Style Classes.
4. For the collapsed header, toggle `fusion-layout-header--collapsed` from a scroll handler.

Requires `dist/neo-tokens.css` plus `src/02-components/layout.css`, `page-title.css`,
`side-panel.css`, `breadcrumb.css` — or just `dist/neobase.css` for everything. Buttons are **not**
in this bundle (`.btn` lives in `outsystems-ui-theme.css`), so use your own button widget in the
actions slot; the template styles its buttons inline with tokens only to stay self-contained.

## The Placeholder gap (measured 2026-09-03)

`.fusion-layout__main-content` carries `display: flex; flex-direction: column; gap: var(--space-6)`.
In the portal the page's sections are its direct children, so the 24px lands between them. Through
an OutSystems Block it cannot: a Placeholder always renders a real `<div>`, so the flex container
ends up with exactly one child and the gap has nothing to apply between.

```
.fusion-layout__main-content     display:flex; gap:24px
└── div#b1-Content .ph                                    ← the Placeholder — the only flex item
     ├── .fusion-layout-section-structure
     └── .fusion-layout-section-structure                 ← measured gap: 0px
```

`compat/neo-odc-compat.css` restores it:

```css
.fusion-layout__main-content > .ph { display: contents; }
```

Measured in `NeoLayoutCheck` after the fix: 24px between consecutive sections, matching
the live portal. Note this depends on the Content placeholder carrying the `ph` class — see
[`docs/odc-library.md`](odc-library.md) for why that class is hand-authored, not runtime output.

## The portal does not use `fusion-layout` (measured 2026-09-03)

Two stylesheets are in play and they were conflated for most of this project:

| | `NeoDesignSystem.…css` (Fusion) | `old-neo-design-system.css` (legacy) |
| --- | --- | --- |
| `fusion-layout*` selectors | 91 | **0** |
| `page-header-*` | — | 76 |
| `main-content*` | — | 28 |
| `nds-layout` / `.layout` | — | 146 |
| `ds-*` components | — | 1114 |

On the live portal at `/usersaccess/`, **zero** `fusion-layout*` classes and zero `<fusion-layout>`
elements are rendered. What it renders is:

```
div.layout.nds-layout            #b1-Layout_Wrapper
└── div.main.display-flex         #b1-Main
    ├── header.header
    └── div.full-height.display-flex      #b1-Page_Content
        └── div.flex1
            ├── div.page-header-wrapper   256,56  1176x73   padding 16px 0
            └── div.main-content-wrapper  256,145 1176x850  padding 0 0 32px
```

Fusion *is* on the page — 194 elements, 32 distinct classes — but only as **components**:
`fusion-badge`, `fusion-pagination`, `fusion-dropdown-item`, `fusion-icon`, `fusion-empty-state`.
The portal is mid-migration: Fusion components inside a legacy page frame.

### Measured three ways, same content, 1440x900

| Property | Portal | Built on legacy | Built on Fusion (shipped) |
| --- | --- | --- | --- |
| header block height | 73px | **73px** | 108px |
| header padding | `16px 0` | **`16px 0`** | `16px 0` |
| header margin-bottom | 16px | **16px** | — |
| content max-width | none | **none** | 1384px |
| content padding | `0 0 32px` | **`0 0 32px`** | `16px 32px` |
| page title | 600 30px/40px Noto Sans | same | same |

The legacy build reproduces the portal on every property; the Fusion build differs on three of six.
Reproduce with a local page carrying `dist/neobase.css` inlined (the preview pane
snapshots local files to a `data:` URL, so linked stylesheets do not resolve).

The legacy layout CSS was always available in the raw stylesheet but had never been extracted;
`tools/extract_legacy_layout.py` now recovers it into `src/05-legacy-layout/page-layout.css`
(149 rules).

**Correction to earlier revisions of this document:** the "matches the portal" figures for page
geometry (max-width 1384px, padding `16px 32px`, 24px section gap) were read from the Fusion CSS,
not measured on a portal page. They describe a component the portal does not use for layout.
