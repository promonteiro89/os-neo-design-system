# Assembling the theme as a shared O11 module

Goal: one module that carries the Neo design language, published once and consumed by every app —
the same way `OutSystemsUI` itself is distributed.

Everything you paste is already generated:

| File | Size | Paste into | Needed? |
| --- | --- | --- | --- |
| [`dist/o11-theme.css`](../dist/o11-theme.css) | 60 KB | the Theme's **Style Sheet** | **Yes** — this is the theme |
| [`dist/o11-theme-utilities.css`](../dist/o11-theme-utilities.css) | 19 KB | same Style Sheet, after the above | Optional |
| [`dist/o11-theme-components.css`](../dist/o11-theme-components.css) | 98 KB | same Style Sheet, after the above | Only if you hand-build Fusion markup |

`o11-theme.css` is Neo's 612 tokens + the O11 adaptation layer + the OutSystems UI bridge,
concatenated in cascade order. It deliberately contains **no** reset, **no** legacy interop and
**none** of the 40 utility classes that collide with OutSystems UI — `tools/verify.py` asserts all
of that on every build, so a bad edit cannot slip through.

Verified: loading only `dist/o11-theme.css` over OutSystems UI reproduces every value in
[the bridge table](outsystems-11.md#the-bridge--the-important-part), in both themes.
See `templates/o11-theme-check.html`.

---

## 1. Where the theme lives

**Use a Reactive Web module, not a Library.** In **O11** a Library module holds non-UI elements
only — it cannot contain a Theme, a Block or a Screen. (This is an O11 rule, not an OutSystems-wide
one: an **ODC** library holds themes perfectly well — a brand UI library in this tenant (anonymised here as `BrandUI`) has 14 of them. See
[`odc-library.md`](odc-library.md).) Themes ship inside Reactive Web modules; that is what
`OutSystemsUI` is, and it is also how OutSystems ships the portal's own design system: the
`NeoDesignSystem` module holds 4 Themes, Blocks, 7 Scripts and Images side by side. Measurements in
[`reference/portal-module.md`](../reference/portal-module.md).

```
App:    "Neo Design System"      ← Foundation layer of the architecture canvas
└── Module: NeoTheme             ← kind: Reactive Web App
    ├── Theme:   NeoTheme        ← Base Theme = OutSystemsUI      (public)
    ├── Blocks:  Layout_Neo, LayoutHeader, Section …             (public)  ← the skeleton
    ├── Client Actions: SetTheme, ToggleTheme                     (public)
    ├── Resources: fonts (.woff2), the two logo SVGs
    └── Screens: NONE
```

**No Screens.** The module ships a Theme, Blocks and Resources — nothing that a user navigates to.
Service Studio scaffolds a `Home` screen and a `Common` flow when you create a Reactive Web App
module from the template; delete them. A screenless module publishes and is consumed normally, it
just has no entry point of its own, which is correct for a design system. (If your Service Studio
warns about the empty module, it is a warning, not an error.)

Foundation layer means it consumes nothing from your apps and everything consumes it. Keep it that
way — a theme module that depends on an app module will bite you at deploy time.

---

## 2. Create the Theme

Interface tab → right-click **Themes** → **Add Theme**, name it `NeoTheme`, then in its properties
set **Base Theme = OutSystemsUI**. That inheritance is what gives you OutSystems UI's widgets;
the bridge then re-skins them.

Open the Theme's **Style Sheet** and paste `dist/o11-theme.css` — the whole file, as-is.

The chain ends up as:

```
OutSystemsUI  →  NeoTheme  →  (optional) YourAppTheme
   widgets        tokens + bridge      app-specific overrides
```

Encourage consuming apps to create their own Theme with **Base Theme = NeoTheme** rather than
editing this one. They get a place for app-specific CSS without forking the library.

This is the portal's own structure, two links shorter. It runs
`OutSystemsUITheme → Legacy_NeoTheme → Old_NeoDesignSystem → NeoDesignSystem → Configuration_Th`,
keeping two design-system generations alive at once; the app theme at the end of that chain is
**69 rules**. That last number is the one to copy — if a consuming app's theme starts growing, the
tokens aren't covering something and the fix belongs here, not there.

---

## 3. The Blocks — the layout skeleton

The Theme carries the look; the Blocks carry the structure. Neo's layout is a specific nesting of
divs with specific classes, and no consumer should have to remember it — that is what the Blocks are
for. Build them as Containers with **Style Classes**, and Placeholders where content goes.

### How a Placeholder actually renders

Measured on the live portal, because it decides how you nest things: a Placeholder renders as a real
`div` carrying the `ph` class, always, whether or not it has content, and any Style Classes you set
merge onto that same element:

```html
<div class="ds-layout-header-breadcrumbs page-header-breadcrumbs ph" id="b1-b1-Breadcrumbs">
```

Two consequences:

* The bundle's 13 `:has(> .ph:empty) { display: none }` rules **work in O11**. Put the Placeholder
  *inside* the region Container and optional regions collapse on their own — no If widget, no code.
* Two rules are the inverse and will eat your content. The section header and footer are hidden
  unless they contain `div[slot] .ph:not(:empty)`, so those need a Container with the **Extended
  Property** `slot` = `"header"` wrapping the Placeholder. The portal does the same thing — 26 of its
  58 placeholders sit inside a `[slot]` container. `compat/neo-o11-compat.css` neutralises the pair
  by default because the failure is silent; delete those two rules once you have built the wrapper.

### Every Placeholder needs Style Class `ph`

Before the Block designs, the rule that makes all of them work. Neo hides empty regions with
selectors that key on a `ph` class — `:has(> .ph:empty)`, `:not(:has(div[slot] .ph:not(:empty)))`
and a dozen more. **That class is not emitted by the runtime.** An OutSystems Placeholder renders as
a bare `<div id="<block>-<Name>">`; the portal's developers set `ph` by hand in the Placeholder's
Style Class property, which is exactly what you see on the ODC portal:

```html
<div class="ds-input-with-icons-icons ph" data-test-id="ds-input-with-icons-icons" id="b4-Icons">
```

So: **set Style Class `ph` on every Placeholder in every Block below.** Skip it and the failure is
silent and asymmetric — regions using `:has(> .ph:empty)` simply never collapse, while regions using
`:not(:has(… .ph:not(:empty)))` hide *even when filled*, so a Section's header disappears with no
error anywhere. See [`docs/odc-library.md`](odc-library.md) for the measured evidence.

### Block `Layout_Neo`

```
Container  class = <expression below>              ← the fusion-layout root
├── Container  class "fusion-layout__main"
│   └── Container  class "fusion-layout__content"
│       ├── Container  class "fusion-layout__header"        → Placeholder  Header    (class ph)
│       ├── Container  class "fusion-layout__top-info"      → Placeholder  TopInfo   (class ph)
│       └── Container  class "fusion-layout__main-content"  → Placeholder  Content   (class ph)
└── Container  class "fusion-layout__side-panel"            → Placeholder  SidePanel (class ph)
```

Input parameters, so the 12 modifiers stay off the consumer's hands:

| Parameter | Type | Default |
| --- | --- | --- |
| `ScrollType` | Text | `"page"` — or `"section"`, `"section-column"` |
| `LayoutType` | Text | `""` — or `"narrow"`, `"widescreen"` |
| `ReserveSidePanelSpace` | Boolean | `False` |

Style Classes expression on the root Container:

```
"fusion-layout"
+ If(ScrollType <> "", " fusion-layout--scroll-type--" + ScrollType, "")
+ If(LayoutType <> "", " fusion-layout--type--" + LayoutType, "")
+ If(ReserveSidePanelSpace, " fusion-layout--reserve-side-panel-space", "")
```

Skip the `<fusion-layout>` custom element — it is only `{ display: contents }`, and without the
Stencil runtime it does nothing. The classes are the whole API.

### Block `LayoutHeader`

Goes into `Layout_Neo`'s `Header` placeholder. Mirror the portal's own placeholder names, which are
readable straight off its DOM — `Breadcrumbs`, `SupportTextLeft`, `SupportTextRight`, `Actions`,
`Description`, `Metadata`:

```
Container  class = "fusion-layout-header" + If(Collapsed, " fusion-layout-header--collapsed", "")
└── Container  class "fusion-layout-header__inner"
    ├── Container  class "fusion-layout-header__breadcrumbs"   → Placeholder  Breadcrumbs
    ├── Container  class "fusion-layout-header__content"
    │   ├── Container  class "fusion-layout-header__left-content"
    │   │   ├── Container class "fusion-layout-header__title"         → Expression Title
    │   │   └── Container class "fusion-layout-header__support-text"  → Placeholder SupportTextLeft
    │   └── Container  class "fusion-layout-header__right-content"
    │       └── Container class "fusion-layout-header__actions"       → Placeholder Actions
    ├── Container  class "fusion-layout-header__description"   → Placeholder  Description
    └── Container  class "fusion-layout-header__details"       → Placeholder  Metadata
```

`Collapsed` (Boolean) gives the sticky condensed bar: it drops breadcrumbs, description and details
and shrinks the title to `heading-3`, all in CSS.

Note the breadcrumbs, description and details regions auto-hide on `:has(> .ph > .ph:empty)` — two
nested placeholders, which is what you get when a consumer drops another Block into the placeholder.
Empty ones disappear for free.

### Block `Section`

The card-like section, and the one with the trap:

```
Container  class "fusion-layout-section-structure"
├── Container  class "fusion-layout-section-structure__header"
│   └── Container  Extended Property  slot = "header"        ← REQUIRED or the header vanishes
│       ├── Container class "…__header-content"
│       │   ├── Container class "…__title"     → Placeholder Title    (class ph)
│       │   └── Container class "…__subtitle"  → Placeholder Subtitle (class ph)
│       └── Container class "fusion-layout-header__actions" → Placeholder Actions (class ph)
├── Container  class "fusion-layout-section-structure__content"  → Placeholder Content (class ph)
└── Container  class "fusion-layout-section-structure__footer"
    └── Container  Extended Property  slot = "footer"        ← same
        └── Placeholder  Footer                              (class ph)
```

Extended Properties live in the Container's property sheet: Name `slot`, Value `"header"` (a text
expression, so the quotes are part of it).

The `slot` wrappers and the `ph` classes are a matched pair. The rule is
`…__header:not(:has(div[slot] .ph:not(:empty)))` — it needs *both* a `div[slot]` ancestor and a
non-empty `.ph` inside it. Drop either one and the header is hidden even when it has content.

One more thing this Block needs, which is not in the portal's CSS because the portal does not have
Placeholders: `.fusion-layout__main-content` is a flex container with `gap: var(--space-6)`, and the
Content placeholder becomes its only child, so consecutive Sections sit flush. The compat layer
restores the rhythm with `.fusion-layout__main-content > .ph { display: contents }`.

### Which Blocks are worth building

Start with these three — they cover the page shape and are the part nobody wants to re-derive. Skip
blocks for anything OutSystems UI already gives you: the bridge has already restyled `.btn`, `.card`,
inputs, alerts, badges and tags, so a "Neo Button" block would be a wrapper around a widget that is
already correct. Add a Block only where Neo has structure OutSystems UI has no equivalent for —
`fusion-wizard`, `fusion-score`, `fusion-empty-state`, `fusion-page-title` are the realistic
candidates, and each is plain markup plus state classes.

---

## 4. Fonts

`o11-theme.css` starts with two Google Fonts `@import` lines so it works immediately. For
production, self-host — it removes an external request and survives locked-down environments.

1. Data tab → **Resources** → Import the four `.woff2` files (Noto Sans 400/500/600, Source Code
   Pro 400). Set each one's **Deploy Action = Deploy to Target Directory**.
2. Delete the two `@import` lines at the top of the Theme stylesheet and put this in their place:

```css
@font-face {
  font-family: "Noto Sans";
  font-weight: 400;
  font-display: swap;
  src: url("/NeoTheme/NotoSans-Regular.woff2") format("woff2");
}
@font-face {
  font-family: "Noto Sans";
  font-weight: 500;
  font-display: swap;
  src: url("/NeoTheme/NotoSans-Medium.woff2") format("woff2");
}
@font-face {
  font-family: "Noto Sans";
  font-weight: 600;
  font-display: swap;
  src: url("/NeoTheme/NotoSans-SemiBold.woff2") format("woff2");
}
@font-face {
  font-family: "Source Code Pro";
  font-weight: 400;
  font-display: swap;
  src: url("/NeoTheme/SourceCodePro-Regular.woff2") format("woff2");
}
```

The path is `/<ModuleName>/<ResourceName>`. Confirm it once in DevTools after publishing — the
resource URL format has moved across O11 versions, so read it rather than trusting the pattern.

Neo needs weights **400, 500 and 600** only. It never uses 700, so don't ship a Bold file.

---

## 5. Dark mode

Neo themes off `data-theme` on `<html>`, and the bridge carries OutSystems UI with it. Expose that
as a public Client Action so consuming apps never touch the DOM themselves.

**Client Variable** `Theme` (Text, default `"light"`) — survives page navigation and reload.

**Public Client Action `SetTheme`** — Input `Theme` (Text). One Assign, one JavaScript node:

```javascript
// Inputs: Theme (Text)
document.documentElement.dataset.theme = $parameters.Theme === "dark" ? "dark" : "light";
```

Assign `Client.Theme = Theme` before the JavaScript node so the choice persists.

**Public Client Action `ToggleTheme`** — calls `SetTheme` with
`If(Client.Theme = "dark", "light", "dark")`.

**Applying it on load.** The `data-theme` attribute has to be re-applied after every full page
load. Put a `SetTheme(Client.Theme)` call in the **OnReady** of your layout Block, so every screen
using the layout gets it for free. If you would rather not depend on the layout, use the
`OnApplicationReady` of each consuming app.

There is no `prefers-color-scheme` support anywhere in the Neo CSS — the switch is entirely yours,
which also means you can bind it to a user preference rather than the OS.

---

## 6. What to make public

Element visibility is per-element in O11 and defaults to private. Set **Public = Yes** on:

* the **Theme** `NeoTheme` — otherwise consumers cannot select it
* every **Block** you intend to share
* `SetTheme` and `ToggleTheme`
* any **Static Entity** driving a shared menu

Leave everything else private. A private helper you can rename later is worth more than a public
one you cannot.

---

## 7. Publish, then consume

In the theme module: **1-Click Publish**.

In each consuming app's module:

1. **Manage Dependencies** (Ctrl+Q) → select `NeoTheme` → tick the Theme, the Blocks and the
   Client Actions you need → Apply.
2. Module properties → **Theme** → pick `NeoTheme` (or your own theme that inherits from it).
3. Publish.

When the theme changes, consumers pick it up on **Refresh Dependencies** + republish. Nothing
propagates silently, which is what you want for a design system.

---

## 8. Keeping it current

The portal CSS is an undocumented internal API with a content-hashed URL, so treat updates as a
deliberate act:

```bash
./tools/fetch.sh          # re-download; reports which of the 12 files changed
python3 tools/build.py    # regenerate src/, dist/, reference/
python3 tools/verify.py   # prove the split is still lossless
python3 tools/collisions.py path/to/your/outsystems-ui.css
git diff --stat dist/     # review before pasting anything into Service Studio
```

Then paste the new `dist/o11-theme.css` over the Theme stylesheet and republish. Because the
tokens carry stable names, a portal restyle usually lands as changed *values* and nothing in your
Blocks needs touching — which is the whole reason to depend on the token layer rather than on
component CSS.

---

## Gotchas specific to this assembly

**Theme CSS is global.** It is not scoped to the module that declares it. Once an app consumes
`NeoTheme`, every screen in that app gets all 612 tokens and the bridge. That is the intent — just
don't be surprised when an unrelated screen changes colour.

**`@import` must be first.** If you paste anything above the font imports, the fonts silently stop
loading. Self-hosting (step 4) removes the hazard.

**Do not paste `src/01-base/reset.css`.** It sets `html { overflow-y: hidden }` and
`body { height: 100vh }` and will fight OutSystems UI's layout. It is excluded from
`o11-theme.css` and `verify.py` fails the build if it ever reappears.

**Skip the colliding utilities.** `dist/o11-theme-utilities.css` already excludes `colors.css` and
`typography.css`. If you add them back, `.text-primary` and `.text-secondary` flip meaning against
OutSystems UI — see [`reference/osui-collisions.md`](../reference/osui-collisions.md).

**Service Studio preview lies a little.** OutSystems UI ships hundreds of `-servicestudio-*`
declarations that only apply inside the editor canvas. A Block can look wrong in the editor and
correct at runtime. Judge in the browser.

**Licensing.** This is OutSystems' proprietary product CSS with no published licence. A shared
internal theme module is a reasonable use; publishing the module to Forge or to customers is not.
