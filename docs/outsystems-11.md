# Building this in OutSystems 11

Target: a **Reactive Web App** in O11, with OutSystems UI as the base theme (which you already
have). End state: screens that look like the ODC portal — chrome, page header, sections — built
from Blocks you own.

Three facts make this much easier than it looks:

1. **OutSystems UI can be re-skinned entirely through variables.** Every colour, size and shadow
   in it is read through a CSS variable, so [`compat/neo-osui-bridge.css`](../compat/neo-osui-bridge.css)
   maps Neo's tokens onto them and OutSystems UI widgets adopt the Neo look — **including dark
   mode** — with no widget CSS touched. Verified: see [the bridge section](#the-bridge-the-important-part).
2. **Almost no variable conflict.** Of 671 Neo variables and 221 OutSystems UI variables, exactly
   one name is shared (`--border-radius-circle`) and both set it to `100%`. The *class* names are
   a different story — 140 collide — see [collisions](#class-name-collisions).
3. **The responsive behaviour is free.** The platform puts `desktop` / `tablet` / `phone` on
   `<body>`, and both bundles already target those classes — OutSystems UI has 219 `.tablet` and
   249 `.phone` rules of its own. No JavaScript needed for breakpoints.

Because you have OutSystems UI, only **three** variables need shimming instead of seven —
OutSystems UI and the legacy Neo theme already define `--space-s: 8px`, `--space-base: 16px`,
`--space-m: 24px` and `--border-size-s: 1px`, at exactly the values this repo had inferred.

---

## Step 1 — Theme and stylesheets

Create a Theme (Interface tab → right-click Themes → **Add Theme**), name it `NeoTheme`, and set
its **Base Theme** to `OutSystemsUI`. Set it as the module's theme, then open its Style Sheet
editor and paste, in this order:

| Order | Paste | Always? |
| --- | --- | --- |
| 1 | `dist/neo-tokens.css` | Yes |
| 2 | `compat/neo-o11-compat.css` | Yes |
| 3 | `compat/neo-osui-bridge.css` | Yes — this is what re-skins OutSystems UI |
| 4 | `src/02-components/*.css` (only the Fusion components you use) | Optional |
| 5 | `src/03-utilities/*.css` **minus** `colors.css` and `typography.css` | Optional — see collisions |
| 6 | `dist/neo-shell.css` + `compat/neo-shell-compat.css` | Only to clone the portal chrome |

**Do not paste** `src/01-base/reset.css` (it sets `html { overflow-y: hidden }` and
`body { height: 100vh }` — it will fight OutSystems UI's layout) or `legacy-interop.css`. Copy
just one line from the reset by hand, since it holds the real font stack:

```css
html:root { --font-family: "Noto Sans", sans-serif; }
```

### Fonts

The bundle's two `@font-face` sources are Google Fonts `@import` lines. CSS requires `@import`
before any rule, so they only work at the **very top** of the theme stylesheet — paste them below
anything else and the font silently falls back. Two better options:

- **Self-host (recommended).** Add the Noto Sans and Source Code Pro `.woff2` files to the module
  (Data tab → Resources → Import, Deploy Action = *Deploy to Target Directory*) and write your own
  `@font-face` rules pointing at `/<ModuleName>/<FileName>.woff2`. No external request, works in
  locked-down environments.
- **`<link>` in the layout.** Put an Expression with **Escape Content = No** in your layout Block
  emitting the `<link rel="stylesheet">` tag.

---

## The bridge — the important part

`compat/neo-osui-bridge.css` is the highest-value file in this repo for an O11 app. It maps Neo
tokens onto OutSystems UI's variables, so **the widgets you already use adopt the Neo design
language without a single change to their markup or CSS** — buttons, cards, tables, inputs,
alerts, badges, tags, avatars, lists, tabs, accordion.

OutSystems UI reads every colour through two layers:

```css
var(--background-color-primary, var(--color-primary))
 └── per-channel override ───┘        └── base value ──┘
```

The bridge writes to both. The base layer (`--color-*`, `--shadow-*`, `--font-size-*`) works on any
OutSystems UI version. The per-channel layer needs **2.28.0 or newer** — and it matters, because
only there can a surface and the text on it come from different Neo tokens. Neo's `neutral-0` is
the *page* colour while its card surface is white; without the split, cards would be the same
colour as the page and visually disappear.

**Dark mode comes free.** Every value in the bridge is a Neo token, Neo tokens flip under
`[data-theme="dark"]`, and both neutral scales run light→dark with Neo inverting its own in dark
mode — so OutSystems UI inverts with it.

Verified by rendering `templates/osui-neo-skin.html` and reading computed styles:

| | Light | Dark |
| --- | --- | --- |
| Page background | `#f9fafb` Neo `--page-background` | `#181a1f` |
| Card surface | `#ffffff` Neo `--surface-1-default` | `#24262c` |
| Input surface | `#ffffff` | `#181a1f` Neo `--input-background-default` |
| `.btn-primary` | `#514dec` Neo `--indigo-7` | `#5252f2` Neo dark `--indigo-6` |
| Link / `.btn` text | `#5757f5` Neo `--link-text-default` | `#b2b4ff` |
| Card border | `#bbc2cc` Neo `--border-default` | `#464b56` |
| `.heading1` | 30px Neo `heading-1` (was 32px) | 30px |
| Card radius | 8px Neo `--border-radius-2` (was 4px) | 8px |

Three separate depths in dark mode — page, card, input — which is what makes it read as a designed
dark theme rather than an inverted light one.

Two values cannot flip and are handled explicitly in the bridge: text on the yellow warning fill
(OutSystems UI uses `neutral-10` there, assuming it is always darkest) and the white veil
OutSystems UI paints over selected rows.

---

## Step 2 — Block structure

Build four Blocks. The nesting matters more than the naming.

```
Layout_Neo                                   ← screens use this
└── Container  [class: neo-shell]
    ├── Shell_Header                         ← Block, the top bar
    ├── Shell_Aside                          ← Block, the nav rail
    └── Container  [class: neo-host]         ← the offset target
        └── Container  [class: fusion-layout fusion-layout--scroll-type--page]
            └── Container  [class: fusion-layout__main]
                └── Container  [class: fusion-layout__content]
                    ├── Container [class: fusion-layout__header]
                    │   └── PageHeader_Neo   ← Block, the page header
                    ├── Container [class: fusion-layout__top-info]
                    │   └── Placeholder  TopInfo
                    └── Container [class: fusion-layout__main-content]
                        └── Placeholder  Content
```

`neo-host` is the offset target. Note a correction to an earlier version of this guide:
`#reactContainer` **does** exist in O11 — OutSystems UI styles it directly
(`html, body, #reactContainer, #transitionContainer, .screen-container { height: 100% }`), so
Neo's own `body:has(fusion-layout) #reactContainer` rule fires here too. Using your own
`neo-host` container is still the better choice, because `#reactContainer` is an undocumented
platform detail — but it is a preference, not a necessity.

`PageHeader_Neo` holds placeholders for `Breadcrumbs`, `Title`, `Actions`, `Description` and
`Details`, following the structure in [`layout.md`](layout.md#structure). Give it Input Parameters
for the optional bits and wrap each region in an **If** widget — do not rely on the CSS auto-hide,
which keys off an ODC placeholder wrapper O11 does not emit (details in the compat file, §2).

`Section_Neo` wraps `fusion-layout-section-structure` with `Title`, `Subtitle`, `Actions`,
`Content` and `Footer` placeholders. **Watch out:** the upstream CSS hides the section header and
footer unless they contain `div[slot] .ph:not(:empty)`. `neo-o11-compat.css` neutralises those two
rules; without it your section titles vanish with no error.

---

## Step 3 — The nav rail

Two O11 mechanics carry this.

**`data-children="true"` is mandatory on group headers.** It is what makes the group labels
uppercase (`[data-children=true] { text-transform: uppercase }`). The DOM text is "Admin"; the
portal shows "ADMIN". Set it on the group Container via **Extended Properties**:

| Property | Value |
| --- | --- |
| `data-children` | `"true"` |

**Active state via a Style Classes expression.** Pass the current menu key into `Layout_Neo` as an
Input Parameter, then on each item Container:

```
"unified-aside-item unified-aside-item--level1" + If(MenuItem = Entities.MenuItem.Organization, " is-active", "")
```

Drive the items from a Static Entity (one record per menu entry, with a group and an order) and a
List widget, so adding a screen to the menu is a data change rather than a markup change. Markup
per item, from the live portal:

```html
<div class="unified-aside-item unified-aside-item--level1 is-active">
  <a href="…">
    <div class="unified-aside-item-border"></div>
    <div class="unified-aside-item-label"><span>Organization</span></div>
  </a>
</div>
```

The rail is a **drill-down** menu: `.unified-aside-primary` is the root level and
`.unified-aside-secondary.is-open` is the level you navigated into — that is why the portal header
reads "‹ Management". If you only need one level, render the secondary container and leave the
primary empty, as `templates/portal-shell.html` does.

---

## Step 4 — The one thing that needs JavaScript

`body.is-aside-expanded` controls the rail width — 45 rules key off it, including
`body.is-aside-expanded .unified-aside { width: 256px }`. `<body>` is not a widget, so it needs a
JavaScript node. In the layout Block's **OnReady**:

```javascript
document.body.classList.add('is-aside-expanded');
```

And in a client action wired to the rail's collapse button:

```javascript
document.body.classList.toggle('is-aside-expanded');
```

That is the only JS the layout requires. Breakpoints, as noted, come free from the platform's
device classes. If you want to persist the choice, store it in Local Storage or a Client Variable
and re-apply it in OnReady.

---

## Step 5 — The logo

`.unified-header-logo` is an empty element with the SVG as a `background-image`, and the bundle
swaps light/dark variants by theme. The CSS points at `url(assets/…)` relative to the stylesheet,
which will not resolve in O11. Two options:

- **Override the rule.** Add the two SVGs from `reference/raw/assets/` to the module as Images,
  then override with your own URLs. Confirm the exact runtime URL by dropping the image into an
  Image widget and inspecting the rendered `src` — the format has changed across O11 versions, so
  read it rather than assuming.
- **Inline them as data URIs** in the theme CSS. Ugly but immune to URL changes, and they are only
  ~6 KB each.

Or skip the CSS entirely and put a normal Image widget inside the header with
`class="unified-header-logo"` removed — you lose the automatic theme swap and would use an If on
a theme variable instead.

---

## Step 6 — Where the real payoff is

For low-code work the utility classes matter more than the components. They go straight into a
widget's **Style Classes** property with no custom CSS at all:

`heading-1` `heading-2` `heading-3` `body-regular-base` `body-regular-s` `body-semi-bold-l`
`actions-base` · `text-primary` `text-secondary` `text-error` `text-success` ·
`margin-bottom-4` `padding-x-6` `margin-top-2` · `shadow-0` … `shadow-4` ·
`border-radius-2` `background-neutral-1` `border-neutral-3` ·
`line-clamp line-clamp-2` `absolute-center` `cursor-pointer`

Full list: `src/03-utilities/`. This is the cheapest way to make an O11 app look like the portal —
no Blocks, no JS, no markup discipline required.

---

## Dark mode

The bundle themes off `data-theme="dark"` on the root element, and there is no
`prefers-color-scheme` support anywhere — the switch is entirely manual, which also means you can
bind it to a user setting.

```javascript
document.documentElement.dataset.theme = 'dark';   // or 'light'
```

Call it from OnReady, reading a Client Variable or Local Storage.

**Correction to an earlier version of this guide:** I previously wrote that OutSystems UI would not
follow `data-theme` and that you would have to restyle its widgets one by one or stay in light
mode. That was wrong. OutSystems UI has no dark theme of its own — it contains zero
`data-theme`, `prefers-color-scheme` or `.dark-mode` rules, which is what I had checked — but every
colour it paints comes from a variable, so `compat/neo-osui-bridge.css` makes the whole widget
library theme-aware in one file. Verified by measurement; see [the bridge](#the-bridge--the-important-part).

---

## Class-name collisions

Neo's utility layer and OutSystems UI share **140 class names**. Run
`python3 tools/collisions.py` (point it at your own OutSystems UI file for an exact answer) —
full table in [`reference/osui-collisions.md`](../reference/osui-collisions.md).

* **100 are value-identical** and harmless: almost entirely the t-shirt spacing scale, where both
  systems resolve `xs/s/base/m/l/xl/xxl` to 4/8/16/24/32/40/48px.
* **40 genuinely differ.** Two of them invert meaning:

| Class | Neo means | OutSystems UI means |
| --- | --- | --- |
| `.text-primary` | body text `#181a1f` | brand blue `#1068eb` |
| `.text-secondary` | muted text `#686f7d` | brand navy `#303d60` |

Whichever stylesheet loads **last** wins. If existing screens use `.text-primary` for brand-blue
text, pasting Neo's utilities after OutSystems UI turns that text near-black. Also differing:
`.font-bold` (600 vs 700), `.font-semi-bold` (500 vs 600), `.text-neutral-0…10`,
`.background-neutral-0…10`, `.text-error/-warning/-success/-info`, and `.heading1…6`.

**The fix is to not need them.** The bridge already gives you the Neo look on OutSystems UI
widgets. If you want Neo's utilities anyway, take `src/03-utilities/` minus `colors.css` and
`typography.css` — the spacing, elevation, radius and layout helpers are all safe.

---

## A simpler path for the layout

Everything in Steps 2–5 builds the portal chrome from scratch. Before you do that, consider that
**OutSystems UI already ships the same layout** — and two numbers line up exactly:

* `--header-size: 56px` — identical to the portal's top bar, no change needed.
* `--side-menu-size: 300px` — the portal rail is 256px; the bridge already sets this.

So `LayoutSideMenu` + the bridge gives you a portal-shaped app with the menu toggle, the overlay,
the responsive collapse, the RTL support and the accessibility work already done —
`.layout-side .main { margin-left: var(--side-menu-size) }`, `.aside-overlay`, `.menu-visible`,
`.app-menu-links a.active` and so on. You give up pixel-identical chrome (the portal's active nav
item is a filled row; OutSystems UI uses a 2px left border, which is a two-line override).

Build the custom `unified-*` chrome only if you need the portal look exactly. Skin OutSystems UI's
own layout if you mainly need an app that feels like the portal — that is far less code to own.

---

## What you will still be missing

The Neo bundle contains no buttons, badges, tables, inputs or cards — it *restyles* them when they
appear inside Fusion containers, but the base rules are OutSystems UI's. That is good news for
you: use OutSystems UI widgets and they will pick up Neo's tweaks in the right places. Where the
portal look depends on a component the bundle does not define, build it from tokens —
`templates/portal-shell.html` does exactly that for its buttons, badge, avatar and table, and
those are worth copying as a starting point.

Reality check on parity: the ODC portal renders its pages with the **previous-generation
`ds-layout`**, not `fusion-layout` ([mapping table](layout.md#ds-layout--fusion-layout)). Building
on Fusion means you match where the portal is heading, not pixel-for-pixel where it is today.

---

## Traditional Web

All of the above works, with two changes: there is no OnReady, so use the screen's
`OnRender`/preparation plus a `RunJavaScript` action for the body class; and placeholders render
differently, so the If-widget advice matters even more. If you have the choice, use Reactive.
