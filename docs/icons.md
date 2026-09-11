# Icons

Icons in the ODC portal are an **SVG sprite**, not a font and not individual files.

```html
<!-- one hidden sprite per page, holding the definitions -->
<div class="unified-icons neo-icon-sprite">
  <svg><symbol id="ic-user" viewBox="0 0 32 32"><path …/></symbol>…</svg>
</div>

<!-- every icon on the page is a reference to one -->
<svg viewBox="0 0 32 32" fill="currentColor" class="pds-icon icon-small">
  <use xlink:href="#ic-user"></use>
</svg>
```

`fill="currentColor"` is the whole colour model — an icon takes the text colour of whatever
contains it. The 26 `.icon-*` colour utilities in the theme set that colour.

## Why we ship the mechanism and not the artwork

On the portal the sprite is a body-level `div.unified-icons` injected by the platform host,
outside `#reactContainer` — the same arrangement as the top bar and nav rail. A standalone app
gets no such host.

The 148 symbols the portal ships (`ic-apps`, `ic-chevron-down`, `ic-user`, …, 105 KB) are
**OutSystems' icon artwork**. Redistributing them inside your own design system is your
organisation's decision, so the library provides the plumbing and you supply the glyphs.

## Blocks

| Block | Purpose |
| --- | --- |
| `IconSprite` | The hidden host. Place **once** per layout — inside `AppShell`'s Header placeholder is fine. Pass your sprite markup as the `SpriteMarkup` input (Text, mandatory). |
| `Icon` | One icon. `Name` (mandatory), `Size` (`""` \| `"small"` \| `"large"`), `IdPrefix` (default `"ic-"`). |

`Icon` renders `<svg class="pds-icon[ icon-<Size>]"><use href="#<IdPrefix><Name>"
xlink:href="#<IdPrefix><Name>"></use></svg>`. Both attributes are emitted deliberately — modern
browsers read `href`, older ones still need the `xlink:` form.

## Why the markup is injected, not expressed

No OutSystems widget emits `<svg>` or `<use>`, so the obvious route is an unescaped Expression.
**That route does not exist in ODC.** The Expression widget always escapes its value:

- ODC Studio's Expression properties panel has no Escape Content row — only Name, Value, Example,
  Style Classes, Attributes, Events.
- `IExpression` in the model exposes `Value`, `Example`, `Width`, `MarginTop`, `MarginLeft`,
  `Style`, `ExtendedProperties`, `Events` — nothing named `EscapeContent`.
- An `EscapeContent` metadata entry (`IBooleanMetadata`, `ManagedBy: NRWidgets`, `Value: False`)
  can be written and stored, but is inert at runtime whether its `Hidden` flag is True or False.
  Measured on the deployed app: output stayed `&lt;svg …`.

All three were measured, not assumed. Do not spend another round hunting for that toggle.

So both blocks render an **empty Container** and write into it from a client action wired to
`OnReady` (and to `OnParametersChanged`, so changed inputs re-render):

```js
var el = document.getElementById($parameters.ElemId);
if (el && el.innerHTML !== $parameters.Markup) { el.innerHTML = $parameters.Markup; }
```

`Icon`'s container carries `neo-icon-host`, which the theme gives `display: contents` so the
wrapper contributes nothing to layout — on the portal an icon is a bare `<svg>` inline in flow.

`SpriteMarkup` is an input parameter rather than a placeholder because the injection then lives
entirely inside the library: consumers pass a Text value and inherit the mechanism, with no
per-app widget and no manual step anywhere.

`IdPrefix` exists so a sprite that does not use the `ic-` convention still works — set it to `""`
and pass whole ids in `Name`.

## Sizes

| `Size` | class | resolves to |
| --- | --- | --- |
| `""` | `pds-icon` | `--icon-size-base` (24px) |
| `"small"` | `pds-icon icon-small` | `--icon-size-s` (16px) |
| `"large"` | `pds-icon icon-large` | `--icon-size-l` (32px) |

## Supplying your own sprite

Any SVG sprite works. Symbols must use `viewBox="0 0 32 32"` to match the icon element's viewBox,
and should draw with `fill="currentColor"` (or no fill) so the colour model works.

```html
<svg xmlns="http://www.w3.org/2000/svg">
  <symbol id="ic-user" viewBox="0 0 32 32"><path d="…"/></symbol>
  <symbol id="ic-search" viewBox="0 0 32 32"><path d="…"/></symbol>
</svg>
```

Three routes, in order of preference:

1. **Your own set** — export as a sprite with `ic-` ids. Nothing else changes.
2. **An open set** (Phosphor, Lucide, Material Symbols) — most publish a sprite build. Note the app
   already loads Phosphor's font; see `compat/neo-odc-compat.css` section 7 for why `ph` is a
   reserved class here.
3. **The portal's own** — parity, but it is OutSystems' artwork.

## The host must not take space

`.unified-icons, .neo-icon-sprite { position: absolute; width: 0; height: 0; overflow: hidden }`
ships in the theme. `display: none` is deliberately avoided: in several browsers a `<use>` cannot
reference a symbol inside a `display:none` subtree. Both class names are matched so a page behaves
the same whether the sprite comes from our block or from the platform host.

## Portal sprite → Phosphor name

Captured 2026-09-07 by reading every `<svg><use xlink:href>` on the portal's Users page and pairing
it, by container class and label, with the `ph-*` class our harness renders in the same slot. The
portal's artwork is OutSystems' own; these are the closest Phosphor 2.0 equivalents.

| Portal symbol | Phosphor | Where |
| --- | --- | --- |
| `#ic-chevron-down` | `ph-caret-down` | `.unified-aside-item-arrow` |
| `#ic-chevron-left` | `ph-caret-left` | `.unified-aside-menu-header-icon-left` |
| `#ic-chevron-right` | `ph-caret-right` | `.unified-aside-menu-header-icon-right` |
| `#ic-configurations` | `ph-sliders-horizontal` | `.unified-aside-menu-header-icon` |
| `#ic-solutions` | `ph-cube` | aside — Solutions |
| `#ic-apps` | `ph-squares-four` | aside — Apps |
| `#ic-agents` | `ph-robot` | aside — Agents |
| `#ic-business-process` | `ph-flow-arrow` | aside — Workflows |
| `#ic-overview` | `ph-gauge` | aside — Overview |
| `#ic-deployment` | `ph-rocket-launch` | aside — Deployments |
| `#ic-charts` | `ph-chart-bar` | aside — Analytics |
| `#ic-logs` | `ph-list-bullets` | aside — Logs |
| `#ic-trace` | `ph-path` | aside — Traces |
| `#ic-code-quality` | `ph-seal-check` | aside — Code quality |
| `#ic-agent-evaluations` | `ph-clipboard-text` | aside — Agent evaluations |
| `#ic-library` | `ph-books` | aside — External logic |
| `#ic-external-data` | `ph-database` | aside — Connections |
| `#ic-ai-models` | `ph-brain` | aside — AI models |
| `#ic-forge` | `ph-package` | `.unified-header-button-icon` |
| `#ic-support` | `ph-question` | `.unified-header-additional-blocks-support-body` |
| `#ic-launch` | `ph-arrow-square-out` | help overlay — See documentation |
| `#ic-sun` | `ph-sun` | account overlay — dark-theme row |
| `#ic-search` | `ph-magnifying-glass` | search input |
| `#ic-close` | `ph-x` | search clear |
| `#ic-more` | `ph-dots-three` | table row actions |

Two of these were wrong until 2026-09-07 and were found by diffing the two pages rather than by
looking at the harness:

- **`#ic-support` was `ph-lifebuoy`.** The portal's support glyph is a question mark in a circle;
  a lifebuoy reads as a gear at 16px. The circled Phosphor question mark is `ph-question`
  (U+e3e8) — **not** `ph-question-mark` (U+e3e9), which is the bare `?` with no ring.
- **`#ic-sun` was missing entirely.** The account overlay's dark-theme row had a label and no icon.

**Verifying a Phosphor name exists.** A wrong `ph-*` class is silent — the element still lays out at
the right size, it just draws nothing, so a width check will not catch it. Read the `::before`
content and count ink:

```js
const i = document.createElement('i');
i.className = 'ph ph-question';
i.style.cssText = 'position:fixed;left:-9999px;font-size:32px';
document.body.appendChild(i);
getComputedStyle(i, '::before').content;   // "" (empty) => the class does not exist
```

Always include a control (`ph-zzz-not-a-real-icon`) in the same run — it must come back `none`,
which is what proves the test can detect absence at all.
