# Forge listing copy — Neo design system

Paste-ready metadata for submitting the `NeoDesignSystem` ODC library
(asset key `9243697a-362a-45fa-928e-1a3db861b488`, currently 0.1.7) to the Forge.
Companion to [forge-listing-phosphor-icons.md](forge-listing-phosphor-icons.md).

Facts this copy is built on: 907 custom properties (612 light + 295 dark),
1,298 rules, 24 Fusion components across 32 component stylesheets, 10 utility
families, portal chrome as `AppShell` / `ShellAside` / `ShellHeader` blocks,
light-and-dark via `TrueShade`, theme `NeoBase` based on `OutSystemsUI`, plus an
O11 paste-in variant (`dist/o11-theme.css`, 63 KB).

---

## 0. Read this before you submit

**The Phosphor pack was clean to publish. This is not, and the difference is
worth being precise about.** Phosphor is MIT licensed by a third party and the
pack repackages it with its licence intact. This library's CSS is a
restructuring of the ODC Portal's own stylesheet — `README.md` states it
directly: *"it is OutSystems' proprietary product CSS, not a published design
system with a license, so keep it to internal apps rather than anything you ship
or open-source"* — and `tools/verify.py` exists specifically to prove the split
is **lossless**, i.e. that the output is the same declarations as the source.
The Forge is public redistribution.

Three ways forward, in descending order of exposure:

1. **Publish the whole thing as-is.** Highest risk. OutSystems could pull the
   listing, and the asset advertises its own provenance to the one party that
   would object.
2. **Publish the components and shell only, minus the extracted token values.**
   Ship the *structure* — the blocks, the layout, the pagination window, the
   skeleton loader, the dropdown control — against a token contract the consumer
   fills in. That is genuinely your own work: the blocks, the `display: contents`
   fixes, the pagination window, `TrueShade`, the O11 bridge. The 907 extracted
   custom-property *values* are the part that isn't.
3. **Ask OutSystems first.** You are a customer with an account team. A yes
   costs one email and settles it permanently; the Forge review may raise it
   anyway.

The copy below is written for **option 2**, and works unchanged for option 1. It
deliberately does **not** say "the same CSS as the ODC Portal" or name the
portal as the source — that framing is the asset's main legal exposure and, as
marketing, it sells a lookalike instead of a tool. Everything below is claims
you can stand behind on your own work.

## 1. Asset name

**Primary:**

    Neo UI Kit

**Alternatives:**

    Neo Design Tokens
    Neo Theme and Components

**Do not publish it as `NeoDesignSystem`.** That is the name of the UI module in
the portal's own theme inheritance chain
(`OutSystemsUITheme → Legacy_NeoTheme → Old_NeoDesignSystem → NeoDesignSystem`),
so the name is simultaneously an SEO dead-end — you would be competing with
OutSystems' own product for a term nobody searches — and the single clearest
signal of provenance you could put on a public listing. Rename the Forge asset;
the ODC library keeps its internal name.

Forge search is essentially a name-and-tag match, so if you want the traffic
rather than the brand, `Neo Design Tokens` is the stronger of the three: it puts
a searched term in the name itself.

## 2. Summary / short description

The field that becomes the search-results card and the search-engine snippet.
142 characters:

    A complete design system for ODC: 900+ design tokens, light and dark mode,
    24 components and a full app shell. Reactive Web and OutSystems 11.

Shorter, 88 characters:

    900+ design tokens, light and dark mode, 24 components and an app shell for
    ODC and O11.

Token-only variant, if you go with option 2 above and drop the components, 114
characters:

    900+ design tokens with automatic light and dark mode for ODC and
    OutSystems 11. One theme paste, no dependencies.

## 3. Tags / keywords

Ordered by value — **use the first five if you can only have five.**

    design-system, design-tokens, theme, dark-mode, components

Then:

    ui-kit, css-variables, layout, app-shell, admin, accessibility,
    light-dark, tokens

Notes:

- `dark-mode` is the strongest single tag here. It is a feature people search
  for specifically and by name, and most Forge themes do not have it.
- `design-tokens` and `tokens` both earn a slot — Forge search does not stem,
  and `design tokens` is the term the design-tooling world uses while `tokens`
  is what a developer types.
- `css-variables` catches the developer who knows the mechanism but not the
  vocabulary.
- Skip `outsystems`, `odc`, `forge`, `reactive`. Every asset is all of those, so
  they carry no discriminating power and dilute a capped tag list.

## 4. Category

    UI / Front-end — Themes

Not "Library": it is a theme plus UI blocks, and the audience is browsing for a
look, not for server logic.

## 5. Long description (markdown, paste as-is)

> ### A design system for OutSystems, tokens first
>
> **900+ design tokens.** Colour, type, spacing, radius, elevation and motion,
> all as CSS custom properties — 612 light values with 295 dark overrides. Style
> your app in `var(--text-primary)` and `var(--space-4)` instead of hex codes and
> pixel values, and every screen stays consistent because there is one place a
> value can come from.
>
> **Light and dark, done properly.** Dark mode is not a second stylesheet; it is
> the same 612 tokens with 295 of them overridden. Components inherit it for
> free, and the included `TrueShade` block follows the OS setting, remembers an
> explicit choice, and reports theme changes so your own logic can react to them.
>
> **24 components.** Badge, tag, avatar, breadcrumb, pagination, dropdown,
> accordion, wizard, side panel, empty state, filter row, progress bar, range
> slider, carousel, code snippet, loading spinner, skeleton loader and more —
> each one a handful of CSS rules over the tokens, so restyling is changing a
> variable rather than fighting a specificity war.
>
> **A full app shell.** A collapsible navigation rail and a top bar, as
> `AppShell`, `ShellAside` and `ShellHeader` blocks, with the page scaffold to go
> under them. This is the part that is tedious to build and easy to get subtly
> wrong — sticky headers, collapse states, focus order, the layout not shifting
> when the rail animates.
>
> **10 utility families** for the last-mile adjustments, so you are not writing a
> one-off class for a margin.
>
> ### Install
>
> Reference the library and set your app's theme to inherit `NeoBase`. The
> tokens arrive with the theme — there is nothing to paste by hand, and no
> dependencies beyond OutSystems UI.
>
> Building on **OutSystems 11** instead? A single-file variant of the tokens and
> the OutSystems UI bridge is included for O11 themes.
>
> ### Why tokens rather than a fixed theme
>
> A theme locks you into someone else's taste. A token layer gives you the
> structure — the scales, the semantic naming, the dark-mode pairing — and lets
> you change the values. Override a dozen custom properties and the whole system
> follows, components included.
>
> ### Compatibility
>
> OutSystems Developer Cloud (Reactive Web) and OutSystems 11. Built on
> OutSystems UI, so it composes with the widgets you already use rather than
> replacing them.

## 6. Before you submit

- **Screenshots outrank every word above.** For a design system that means
  three: the token palette in light and dark side by side, the component
  gallery, and the app shell with a real page in it. `demo/index.html` renders
  the first two from plain HTML with no OutSystems runtime, and
  `templates/portal-shell.html` gives you the third.
- **The demo app is your best asset.** `NeoLayoutCheck` is already a working
  screen exercising the table, filters, dropdowns, pagination, skeletons and
  the shell. A published demo URL on the listing converts far better than a
  feature list.
- **Version.** The library is at 0.1.7. A `0.x` version number tells a
  prospective consumer the API may move under them; tag a `1.0.0` before
  submitting if the block signatures are settled.
- **State what it does not do.** No form components beyond the input helpers, no
  charts, no data grid. Saying so up front costs one line and prevents the
  one-star review that says "no data grid".
