# The login layout (`Layout_Login`)

Replicates the **platform identity host's login screen** — the page every ODC
tenant's sign-in round-trips through (`id.outsystems.dev`; platform-global, no
tenant in its URLs).

## Source and extraction

The page loads five stylesheets; two carry the pattern:

| Sheet | Owns |
| --- | --- |
| `login.css` (8.4 KB) | the PDS `Patterns.LoginScreen` base — its own header comment names `ProductDesignSystem.Patterns.LoginScreen.css` upstream |
| `mtsi-dark-theme.css` (21 KB) | the dark restyle: 432px form column, spacing, and the corner rectangles |

`tools/fetch.sh` has no role here — the raw sheets live in `reference/raw/login/`
(fetched directly; absolute host, not tenant-relative). `tools/extract_login.py`
emits `src/07-login/login.css` (27 base + 31 dark rules) and it enters
`dist/neobase.css` as **section 9, LOGIN LAYOUT**. `verify.py` excludes
`07-login` from the portal-fidelity check — different source of truth — and the
extractor carries its own integrity check: every `var()` it emits must be
defined in-file.

Measured structure (1280x720, dark):

    div.full-screen-background          hidden in light; shown by the dark theme
      span.rectangles.rectangle-*       4 corners, fixed sizes (163x132 / 262x270
                                        / 293x505 / 468x163), hidden < 992px
    div.pds-login > div.pds-login-right
      div.pds-login-right-form          max-width 432px, centered, top 95px
        .pds-login-right-logo           logo img 130x25
        .pds-login-right-account        24px heading, line-height 32px
        (inputs / forgot / button / signup)

## Two deliberate deviations

1. **PDS tokens are scoped, not global.** The pattern uses PDS-scheme names
   (`--color-neutral-N`, `--space-*`, `--spacing-*`, `--dark-*`). They are
   defined on `.pds-login` / `.full-screen-background` only: `dist/neobase.css`
   carries 11 dangling PDS-scheme references in portal rules whose declarations
   currently drop, and defining the names at `:root` would switch those on and
   change existing pages.

2. **Corner art is CSS background, not `<img>`.** The host ships the rectangles
   as `<img>` children; our block ships empty containers and the theme paints
   them: `url(/NeoDesignSystem/img/NeoDesignSystem.rectangletopleftdark.svg)` —
   the one URL form ODC rewrites inside theme CSS (absolute module path, no
   hash; 404s if fetched directly, and that is still correct). The four SVGs in
   `dist/assets/login/` carry separator-free filenames so importing them yields
   exactly the image names the CSS expects.

## The block

`Layout_Login` (public): `FullScreenBackground` + the `pds-login` column, with
placeholders `Logo`, `Title`, `Content`, `Footer`. The consumer builds the form
itself in `Content` — inputs, forgot-password link, submit button — using the
`pds-login-right-inputs` / `pds-login-right-forgot-signedin` /
`pds-login-right-button` classes if portal-identical spacing is wanted.

## Consumer checklist (Studio, after the block publishes)

1. Import the four SVGs from `dist/assets/login/` into the library's Images —
   do not rename them.
2. Paste the rebuilt `dist/neobase.css` over the NeoBase theme stylesheet
   (select-all, paste — it is the whole sheet, section 9 is new).
3. Publish, release, bump the consumer's pin.

Dropped from the extraction, deliberately: OS runtime utilities (ODC serves
them from `_Basic`), the `.hybrid-theme` skin, per-tool `background-img-*`
backgrounds, `.portal`-scoped community variants, and mtsi's global
text/background-neutral flips (ours is the token layer).

## Second pass: closing the gap with the host, measured

The first pass matched the controls. A rule-level diff against the live host
found nine remaining differences, all of them real. Method was the same as the
page-header work: enumerate every rule in `login.css`, `mtsi-dark-theme.css` and
`product.css` that **matches some element in the `.pds-login` subtree** (53 of
them), then diff against what this extract emits.

### What the KEEP regex was silently dropping

`KEEP` only matches selectors that *name* the pattern — `.pds-login*`,
`.rectangles`, `.full-screen-background`. The host's login is a whole page, so
it also leans on plain generic classes, and every one of those rules was being
dropped:

| rule | effect of it missing |
|---|---|
| `label { margin-bottom: var(--space-xs) }` | every input sat 4px high, and the whole column with it |
| `.mtsi-dark-theme .link-small` | links rendered ODC light-theme blue at 14px/24px instead of `#B2B4FF` at 12px/16px |
| `.mtsi-dark-theme .form-control` | input border `#464B56` instead of `#4A4E57` |
| `.text-neutral-7`, `.font-size-s`, `.font-semi-bold`, `a` | inherited by luck, not by rule |

These are now lifted by an explicit allowlist (`GENERIC` in
`tools/extract_login.py`) and emitted **scoped to `.pds-login`**. The host can
afford `label { ... }` unscoped because its login is the only thing on the
page; a library block must not restyle every label, link and input in a
consuming app. Scoping is the only edit — declarations are verbatim.

Deliberately **not** lifted: `product.css`'s `.btn`, `.btn-primary`,
`.btn-large` and `.form-control[data-input]` base rules. Our design system
already supplies that control and it measures identical to the host
(432x40, `#5252F2`, radius 8). Taking PDS's gradient `.btn` would replace a
matching control with a wrong one.

### `noto-sans` was resolving to nothing

The host loads its face as `noto-sans` (hyphenated) and declares
`font-family: noto-sans, sans-serif`. Nothing in this tree defines a face by
that name — our `@font-face` calls it `"Noto Sans"` — so all four of those
declarations were falling through to the generic `sans-serif`, quietly changing
the typeface on the account heading and both links. This predates the second
pass; it shipped with the first.

The extractor now inserts our name after the host's
(`"noto-sans", "Noto Sans", sans-serif`) rather than replacing it, so the
declaration still reads as the host's and would work if `noto-sans` were ever
defined. **Copying a declaration verbatim is right up until the name it depends
on does not exist on this side.**

### `display: contents` was the wrong call

The first pass gave the Content placeholder `display: contents`, with a note
claiming the host renders `form > div` with no wrapper. That was wrong — the
host wraps the whole form in a real `<form>`, a block box 432 wide. With
`display: contents` the placeholder's children became flex items of
`.pds-login-right-form`, whose `align-items: flex-start` made each one shrink to
its own content: `.pds-login-right-forgot-signedin` measured **117px instead of
432**. It is now `display: block; width: 100%`, which is the `<form>` exactly.

### Margin collapsing, from a class ODC does not emit

With everything above fixed, the submit button still sat 12px above the host's.

The host is an O11 app, so every Container it renders carries `.OSInline`
(`display: inline-block`) from `_Basic`. ODC does not emit that class, so the
same containers render as plain blocks — **and blocks collapse adjacent
margins**. `.pds-login-right-forgot-signedin`'s `margin-bottom: 24px` and
`.pds-login-right-button`'s `margin-top: 12px` collapsed to 24px instead of
summing to 36px. Inline-block boxes do not collapse margins, which is how the
host gets 36px without asking for it. Three containers are inline-block on the
host and are now inline-block here.

### Two elements the block did not have

- **`.pds-login-right-signedin`** — the "stay signed in" slot. Empty on this
  tenant (`stay_logged_in_feature=disabled`), but it carries
  `margin-top: 16px` inside a `column-reverse` flex with `gap: 8px`, which is
  what makes the host's forgot-password row 40px tall instead of 16px.
- **`.pds-login-password-eye`** — the reveal icon. See `ODC_ADAPT`: the host
  positions it against an inline `span.pds-login-input` fragment, which ODC's
  Input widget markup cannot reproduce, so it hangs off the password column's
  bottom edge instead. It is a Container, not a Button, because the control is
  inert here and an ODC Button would drag our `.btn` skin into a 16px slot.

### Not a difference

`.pds-login` measures 1432 wide against the host's 1040. The host's
`.mtsi-dark-theme #root` has `padding: 0 200px`; ours has none. It is invisible:
`.pds-login` is transparent in dark mode and everything inside is centred, so
both put the form on the same axis. The remaining 4px of X offset is ODC's
`.screen-container` reserving a scrollbar gutter it never uses — not a CSS
difference, and not chased.

## Third pass: three differences visible side by side

All three were spotted by eye in a screenshot comparison, and all three were
real. Worth recording because two of them are cases where a measurement I had
already taken looked fine and the conclusion drawn from it was wrong.

### The corner art sat 7px low

Every one of the four SVGs is **7px shorter than the CSS box mtsi gives it**:

| span | mtsi box | SVG artwork |
|---|---|---|
| top-left | 163x132 | 163x125 |
| top-right | 262x270 | 262x263 |
| bottom-left | 293x505 | 293x498 |
| bottom-right | 468x163 | 468x156 |

On the host those are `<img>` children at natural size, so each one starts at
its span's **top** edge and the 7px gap falls at the bottom — measured there,
`bottom-left` span `y395->900` with the img at `y395->893`.

The first pass wrote `background-position: left bottom` for the two bottom
corners, which is the obvious-looking choice for art pinned to the bottom of
the screen, and it pushed the whole lower-left cluster 7px below the host's.
All four now anchor `top`.

**This is why "the span boxes match" was not enough.** Both passes measured the
spans, and the spans were always identical; what differed was where the
artwork sat inside them. The `<img>` geometry had to be measured separately.

### The submit button was genuinely heavier than the host's

The host declares `.btn { font-weight: 500 }` — and renders **400**. The only
noto-sans faces it loads are 400 and 600, and with no 500 available CSS font
matching for a desired 500 drops to the next lighter face. Our bundle pulls a
real Noto Sans 500 from Google Fonts, so the identical declaration produced a
heavier label.

Width of "Log in" at 14px:

| | width |
|---|---|
| host | 40.0 |
| ours, 500 + 0.1px tracking | 41.5 |
| ours, 500, no tracking | 40.9 |
| ours, 400, no tracking | **40.3** |

So `.pds-login-right-button .btn` now declares `font-weight: 400` — what the
host *renders* rather than what it *declares*. That is the only way to match it
while our font set is the more complete one, and it is the sort of thing to
revisit if the host ever ships a 500 face. `letter-spacing: normal` is also
needed: our own `.btn` adds 0.1px of tracking that the host does not have.

### The form was 4px left of centre

ODC's shell gives `.screen-container` `overflow-y: scroll`, which reserves an
8px scrollbar gutter whether or not the page scrolls. The login column was
therefore 1432px wide in a 1440px viewport, putting the form at `500->932`
against the host's `504->936`.

I had measured this in the second pass, attributed it to the gutter correctly,
and then **dismissed it as invisible** — reasoning that both sides centre the
form so the offset cancels out. It does not cancel: the host reserves nothing,
so its centre is 720 and ours was 716. Four pixels is small and it is still a
visible misalignment when the two are put side by side, which is exactly how it
was caught.

Fixed with `.active-screen.screen-container:has(.pds-login) { overflow-y: auto }`
— scoped so no other screen's scrolling changes. When the login genuinely is
taller than the viewport a scrollbar appears and insets the column, which is
what the host does too.

## The password reveal control, made to work

The icon shipped inert. The host's toggle, read by driving it there, changes
four things at once:

| | masked | revealed |
|---|---|---|
| `type` | `password` | `text` |
| `-webkit-text-security` | `disc` | `none` |
| `aria-label` | "Show password" | "Hide password" |
| icon | eye (2-path SVG) | eye-slash (3-path SVG) |

All four are replicated. The icon swap uses Phosphor's `ph-eye` / `ph-eye-slash`
— both confirmed present in the Phosphor library the harness references
(`.ph.ph-eye-slash::before` resolves in the loaded sheet), which is a separate
library from NeoBase, so grepping `dist/neobase.css` for them finds nothing.

**It is a DOM listener in the screen's On Ready, not a Container OnClick.** An
ODC Container's OnClick does not fire for clicks that land on its child
widgets, and this icon has a child glyph filling it — so an OnClick handler
would have been dead for every click that actually hits the icon. Verified the
listener by clicking the child glyph specifically, not just the container.

The `neoRevealWired` data-attribute guard stops a second On Ready from binding
the handler twice.

The reveal is a field affordance only. The Login screen still has no
authentication, validation or server logic of any kind.

## The Logo placeholder was dead weight

The block painted the wordmark unconditionally on `.pds-login-right-logo`,
which made its own `Logo` placeholder pointless — and worse than pointless:

- it rendered as a bare `<div>` with **no class attribute at all**, so it could
  not participate in the `neo-ph:empty` convention the rest of the bundle uses;
- a consumer who dropped their own mark into it got **both** — their logo drawn
  on top of our background image.

Now the wordmark is gated on the placeholder being empty:

```css
.pds-login-right-logo:has(> .neo-ph:empty) { background: url(...wordmark...) }
```

Leave the placeholder empty and you get the OutSystems mark, correct in both
themes, for free. Fill it and ours switches off. The placeholder went from
inert to being the block's branding override, which is what a design-system
block should offer in that slot.

This is **the bundle's own idiom, not a new mechanism** — the portal's empty
state does the same thing seven times over
(`.fusion-empty-state__logo:has(> .neo-ph:empty) { display: none }`). It does
require the placeholder to actually carry `neo-ph`, which is the second half of
the fix and was done in the library model.

## Light mode, and why the dark sheet could not be rescoped wholesale

The light login was broken, and the cause was a wrong assumption baked into
this extractor from the first pass: that `mtsi-dark-theme.css` is a *colour*
sheet, so rescoping all of it under `[data-theme="dark"]` would leave a working
light variant underneath.

It is not a colour sheet. **It is where the login's actual layout lives** — the
432px column, the left alignment, the 95px top padding, the 24px heading, every
margin between the fields. The `login.css` base underneath it is the older PDS
design: a 400px *centred* column with a 14px heading. So light was rendering
that older design, measured:

| | light (broken) | dark |
|---|---|---|
| form | 400px, `align-items: center` | 432px, `flex-start` |
| heading | 14px/21px, centred | 24px/32px, left |
| logo | `display: block`, margin-bottom 72px | flex, left, 32px |
| forgot row | h18 | h40 |
| sign-up | centred | left |
| `.pds-login` background | `#fff`, 606px tall over a `#F9FAFB` body | transparent |

That last one is what produced the hard grey band across the lower screen.

### One layer, two themes, driven by tokens

mtsi is now emitted **unscoped** and its hardcoded dark palette is re-pointed at
tokens that carry a value per theme. Only the two **asset swaps** stay
theme-scoped, because those are different *files* rather than different values:
the corner artwork (dark ink only) and the wordmark.

Four of the host's roles turned out to be **exactly** our design system's tokens
in dark, so they need no new token and light comes free:

| host's login value | design-system token | light | dark |
|---|---|---|---|
| `--dark-bg-primary` `#181A1F` | `--input-background-default` | `#ffffff` | `#181a1f` |
| `#F9FAFB` input text | `--input-text-default` | `#181a1f` | `#f9fafb` |
| `#B2B4FF` link | `--link-text-default` | `#5757f5` | `#b2b4ff` |
| `--dark-accent` `#5252F2` | `--button-primary-background-default` | `#514dec` | `#5252f2` |
| `#f56451` error icon | `--text-error` | `#ce230c` | `#f56451` |

That is not a coincidence — our token layer is extracted from the same portal.

The remainder are login-specific values the portal's own tokens do not carry:
the host's input border is `#4A4E57` where ours is `#464B56`, and its body text
is pure `#FFFFFF` where ours is `#F9FAFB`. Those get a `--login-*` token with a
value per theme, **the dark value being the host's own**, so dark renders
exactly as before:

```css
.pds-login { --login-input-border: var(--input-border-default); … }   /* light */
[data-theme="dark"] .pds-login { --login-input-border: #4A4E57; … }   /* dark  */
```

Verified after the refactor: dark is unchanged against the host on every
geometry value *and* every colour — label `#FFFFFF`, input `#181A1F` on
`#4A4E57`, text `#F9FAFB`, link `#B2B4FF`, button `#5252F2`. Light renders the
same layout with light-theme colours and no panel.

The integrity check now also **proves** the borrowed tokens exist: it reads
`src/00-tokens/**` and fails on a reference that no token file defines, rather
than allowlisting names and hoping.

## Light corner artwork, from the one asset

Light mode had no corner artwork in any corner: the host ships **four dark
corner SVGs and only one light one** (`rectangle-top-left.svg`), so both the
rules that paint them and the rules that size them were dark-scoped.

### It needs no second set of files

The artwork is nothing but strokes on transparency, so one asset serves both
themes:

```css
.rectangles { filter: invert(1) hue-rotate(180deg); }   /* light */
[data-theme="dark"] .rectangles { filter: none; }       /* dark: as authored */
```

`invert(1) hue-rotate(180deg)` inverts lightness while holding hue, which is
exactly the relationship the corner art has between themes. No light Images to
import into the library, and no colour map in the extractor to keep in step
with a re-export of the artwork.

### What was tried first, and why this won

**The host's own light inks are invisible here.** Its single light/dark pair
proves the recolour is a pure stroke substitution — applying two swaps to the
dark file reproduces the light file *byte for byte* (`#474A8E -> #C8C9F9`,
`#2B2D4B -> #F1F2FB`). Wired up, those rendered four blank corners. Against our
light ground `#F9FAFB`, `#F1F2FB` is contrast **1.07** — nothing at all — and
the main stroke `#C8C9F9` is **1.52**, where the same stroke carries **2.19** in
dark. The host's light artwork is genuinely far fainter than its dark
counterpart; plausibly fine on pure white, but on our page it reads as missing.

**Generating a light set was tried next**, mapping each dark ink to the light
ink with equal contrast against its own ground — which landed every value on a
step of our indigo ramp. Then the filter turned out to land within 0.15 of those
values on three of the four strokes:

| dark ink | role | filter | CR | hand-picked | CR |
|---|---|---|---|---|---|
| `#474A8E` | main | `#a9acf0` | 2.04 | `#a2a5fe` | 2.15 |
| `#353762` | mid | `#c1c3ee` | 1.63 | `#c6c8ff` | 1.53 |
| `#2B2D4B` | faintest | `#cdcfed` | 1.46 | `#d8daff` | 1.31 |
| `#777AFD` | accent | `#7073f6` | 3.67 | `#5757f5` | 4.92 |

Four extra assets, an import step and a colour map to maintain, for ~0.15 of
contrast. The filter wins on every axis except the accent square, which is
weaker but still clearly legible.

**Matching dark's contrast at all is the deliberate deviation** from the host's
one light file. The filter is just how it is delivered.

Note also that the rules which **position and size** the four spans had to come
out of the dark scope too. Painting light artwork onto a `0x0` box would have
looked exactly like the original bug.
