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

## The 2026 restyle, and the host that did not change

The trigger was "their login page changed slightly". It had not. `id.outsystems.dev/login`
— the page every rule in `tools/extract_login.py` was extracted from — was
re-measured at 1440 dark and still renders **every single value this repo
encodes**: 4px label gaps on a 21px text grid, `0 8px` input padding, a
`#4A4E57` border, 12px links, `margin-bottom: 16px` between field groups,
`margin-top: 12px` on the button. Nothing upstream moved.

What changed is **which login OutSystems puts in front of you**.
`id.outsystems.com/community/login` is a **different application** on a newer
design system. Both are called "Log in to your OutSystems account", both are a
432px left-aligned column, and they are close enough that the difference reads
as a tweak rather than a different page. The parity target is now the
`.com/community` one.

### What actually differs

The two are the same layout at a different **rhythm**. The old page is a 21px
text grid on 14px type (`body { line-height: 1.5 }`); the new one is a flat
**24px** grid, which happens to be ODC's own default line-height. Nothing moves
horizontally — the column is 432px in both.

| | old host (`.dev`) | new host (`.com/community`) |
|---|---|---|
| text grid | 21px (`line-height: 1.5`) | 24px |
| label → input | 4px | **8px** |
| input padding | `0 8px` | **`0 12px`** |
| input border | `#4A4E57` | **`#464B56`** |
| links | 12px/16px | **14px/24px** |
| sign-up line | 12px/18px | **14px/24px** |
| heading | 600, no tracking | **500, `-0.2px`** |
| logo → heading | 80px (32 margin + 48 padding) | **32px, margin alone** |
| wordmark | 130×25 | **168×32.5 in a 39px box** |
| field group → group | 16px | **24px** |
| forgot row → button | 36px | **24px** |
| reveal icon | `right: 8px`, white @ 50% | **`right: 12px`, flat `#B3BAC4`** |
| corner artwork | four SVGs | **none at all** |

### Three of these reverse an earlier decision, and that is the point

**The input border is no longer a login token.** `#464B56` is *exactly* our own
`--input-border-default` in dark. The old host's `#4A4E57` was the reason
`--login-input-border` existed at all; the new host agrees with the design
system, so the token is gone and `TOKEN_MAP` points straight at
`--input-border-default`. One fewer bespoke value.

**The button now needs nothing.** There was a rule here forcing the label to
400 weight, no tracking and a 14px line-height, on the finding that the old
host *declared* `font-weight: 500` but *rendered* 400 — it loaded only the 400
and 600 noto-sans faces, and CSS font matching for a missing 500 falls to the
next lighter face. That rule declared what the host rendered rather than what
it declared, which was right at the time.

The new host **loads a genuine Noto Sans 500** (`document.fonts` reports the
400, 500 and 600 faces all `loaded`) and renders "Log in" at **41.52px**.
Probed in the host's own font at its own 0.1px tracking: 400 → 40.92,
500 → **41.52**, 600 → 42.19. It is really drawing 500.

Our base `.btn` already resolves to exactly that — `--actions-base` is
`500 14px/24px`, `--letter-spacing-3` is `0.1px`, `--component-size-base` is
40px, padding is `0 var(--space-4)`. Every one is the new host's measured
value, so **the correct adaptation is none**, and the rule was deleted. Note
that `getComputedStyle` would never have caught this: it reports the *computed*
weight, so both hosts say `500`. Only the rendered glyph advance distinguishes
them.

**`.pds-login { line-height: 1.5 }` is gone.** It existed to reproduce the old
host's 21px grid against ODC's inherited 24px. The new host's grid *is* 24px,
so matching it means getting out of the way rather than overriding — and the
explicit `17.5px` and `21px` line-heights on the input and label went with it.

### How it is applied

A `RESTYLE` table in the extractor rewrites declarations **at emission**, so
the generated file keeps one value per property. The alternative — a second
layer of `!important` in `ODC_ADAPT` — would have left every changed property
stated twice, with the dead value still reading as the intended one.

Two traps in that table, both of which bit:

- **Every selector in a rule has to match, not just one.** The button's
  `margin-top` reset was also landing on
  `.pds-login-right-button, ... > div, ... > div > div { width: 100% }`,
  zeroing a margin on two inner divs that never had one.
- **`lift_generic()` does not go through `keep_rule()`.** Both `.link-small`
  rules arrive by that path, so the first attempt left the links at 12/16
  while everything around them moved to the 24px grid. It now restyles too.

The 24px group gap needed one hand-written rule: `RESTYLE` puts 24px under
*every* `.pds-login-right-inputs`, but the gap below the **password** group is
16px, and both groups carry the same class. The password column is already
marked `.pds-login-password-field` for the reveal icon, so that class
distinguishes them — no `:nth-child`, which would silently pick the wrong group
if a consumer adds a field.

### The empty slot that cost 24px

The first pass shipped with the button **24px low**, and the harness had
reported zero delta. Both had the same cause: the harness DOM was missing a
container that does nothing.

`.pds-login-right-forgot-signedin` is
`display: flex; flex-direction: column-reverse; gap: 8px` and holds **two**
children — the forgot link and `.pds-login-right-signedin`, the slot a consumer
drops a "keep me signed in" checkbox into. Left empty that slot measures
**h0** — and a zero-height flex item is still a flex item, so the row pays the
8px gap for it, and mtsi adds `margin-top: 16px` on top. 8 + 16 = the 24px.
Measured live: row h48 against the host's h24, everything below it 24px low.

**The old host had the identical dead space** — its row measured h40 and ours
matched exactly — which is why this never surfaced before. The new host has no
signed-in control at all, so its row is just the link.

The fix is `display: none !important` on `:empty`, not a margin reset: an
element with `display: none` is not a flex item, so it generates no gap either,
where zeroing the margin alone would leave the 8px. The `!important` is not
optional — mtsi declares `display: flex !important` on the class, so the first
attempt at (0,1,1) lost outright and was *visually indistinguishable from
having written no rule*.

It also turns the slot into a real optional placeholder: empty and the row is
one line like the new host, filled and the old two-line layout returns with its
spacing intact.

### Deleting a declaration is not the same as setting it

The reveal icon shipped at **half strength in both themes**, and the reason is
worth recording because it looks like a no-op change.

The old rule inked the icon `var(--login-text-primary)` with `opacity: 0.5`.
Matching the new host meant a flat `#B3BAC4` — `--icon-primary`, which is
`--neutral-8` in dark — so the colour was repointed and the opacity line was
**removed**. But mtsi declares `opacity: 0.5` on the bare
`.pds-login-password-eye` class underneath, so deleting the line only uncovered
it: `#B3BAC4` at 50% over `#181A1F` is about `#666A72`, visibly dimmer than the
reference, and light was equally dim.

Verified against the host before fixing: its icon is `rgb(179,186,196)` at an
effective opacity of **1**, every ancestor in the chain included. The rule now
states `opacity: 1` explicitly.

**Deleting a declaration only uncovers whatever the cascade already had.** When
the goal is a specific value rather than "no opinion", the value has to be
stated. Three other deletions in this pass were safe — `line-height: 1.5` on
`.pds-login`, the button's weight/tracking/line-height rule, and the heading's
`padding-top` — but that was luck about what sat underneath, not a property of
deleting, and each was confirmed by live measurement rather than assumed.

### Light theme

Geometry is theme-agnostic, so light matches the host's nine rows exactly too,
and the column centres identically. The colours resolve through the design
system rather than the host, which ships no light login at all:

| | dark (host's own) | light (ours) |
|---|---|---|
| heading | `#F9FAFB` | `#181A1F` |
| label | `#F9FAFB` | `#626568` (`--color-neutral-7`) |
| input | `#181A1F` on `#464B56` | `#FFFFFF` on `#BBC2CC` |
| link | `#B2B4FF` | `#5757F5` |
| button | `#5252F2` | `#514DEC` |
| reveal icon | `#B3BAC4` | `#4C525D` |
| input hover | `#777f8d` | `#868e9c` |
| input focus | `#b2b4ff` | `#392f9c` |
| corner art | four dark SVGs | the same four, `invert(1) hue-rotate(180deg)` |

The hover and focus inks move in opposite directions by theme, which is right:
dark lightens the border away from `#464B56`, light darkens it away from
`#BBC2CC`. The dark pair is the host's own; **the light pair is ours**, from
`--border-hover` / `--border-focus`, because the host ships no light login to
compare against. Both screens resolve identically — the rule is scoped to
`.pds-login-right-inputs`, so the password column gets it too.

The corner artwork is the one light-only mechanism and it holds up at the new
metrics — the filter is independent of the restyle, which only touched
typography and rhythm.

### Verified without a publish

`tools/login-harness.html` mirrors the DOM ODC renders for the block and links
`dist/neobase.css`, so the rules can be measured locally. Against the new host
at 1440 dark, all nine rows — logo, heading, both labels, both inputs, forgot
row, button, sign-up — are now **byte-identical**, not merely close.

**The harness is only worth as much as its DOM.** It originally omitted the
empty signed-in slot and so reported a clean zero on a layout that was 24px
out. A harness that drops "dead" containers does not simplify the test, it
deletes the bug. It now carries the slot, the `<span>` inside the link and
ButtonLoading's real two-wrapper structure — and it reproduced the 24px error
on the first run.

It needs two stubs, and both are worth knowing about:

- **`box-sizing: border-box`.** ODC's platform reset provides it; `neobase.css`
  does not. Without it every 40px control measures 42, and that 2px accumulates
  down the column into a 3px error at the button — which looks exactly like a
  margin bug and is not one.
- **the 24px body line-height**, which is ODC's default, not ours.

Corner artwork stays blank in the harness: its background urls are ODC
authoring paths that only resolve after a publish rewrites them.

### Deliberately not matched

**The corner artwork stays.** The new host ships none at all. Keeping ours was
the explicit instruction, and it is the one place this block is now richer than
the page it copies.

~~`padding-top: 95px` stays.~~ **Reversed.** This was argued as 1px of a
different page's chrome and therefore noise. Once the 24px error above was
fixed, that 1px was the *only* remaining divergence in the whole column, and
leaving it meant the column sat uniformly 1px high for no reason. It is now
96px, and every row matches exactly.

Doing it safely needed one change to the machinery: **`RESTYLE` is a
desktop-layer table**, skipped inside `@media`. `.pds-login-right` carries a
`padding-top` in four media queries (600, 600–768, 768+, 991.98), and rewriting
it inside them would have flattened every responsive value to the desktop one.
No entry targets a media rule today; the guard only guarantees it stays that
way.

**`x504` vs the host's `x500`.** The new host's page is genuinely taller than
the viewport, so it has a real scrollbar and centres its 432px column in
1432px. Ours does not scroll, so it centres in 1440. The
`:has(.pds-login) { overflow-y: auto }` rule is doing precisely what it
documents — when our login *does* overflow, the scrollbar appears and insets
the column the same way.

## Reset password: the same block, fewer rows

`id.outsystems.com/community/resetpassword` is not a second design. It is the
login column with the password group and the forgot row taken out, and **every
computed value is identical** — 168×32.5 wordmark, 24/32/500/`-0.2px` heading,
14/24 label with an 8px gap, 40px input at `0 12px` on `#464B56`, the same
primary button, the same 14/24 footer line.

So it needs **no new CSS at all**. The block's existing rhythm already lands it:

| row | host | produced by |
|---|---|---|
| logo | 96→135 | `.pds-login-right-logo` (empty → wordmark), `min-height: 39px` + 32px margin |
| heading | 167→199 | `.pds-login-right-account` |
| label | 223→247 | 8px `margin-bottom` |
| input | 255→295 | 40px control |
| **button** | **319→359** | `.pds-login-right-inputs { margin-bottom: 24px }` + `.pds-login-right-button { margin-top: 0 }` |
| back link | 375→399 | `.pds-login-right-button { margin-bottom: 16px }` |

The button row is the one worth noticing. On the login screen the 24px under
`.pds-login-right-inputs` is the gap between the *email and password groups*;
here, with no password group, the same 24px becomes the gap from the email
group to the button — which is exactly what the host does. The
`.pds-login-password-field` override that narrows it to 16px is scoped to the
password column, so it simply does not apply. **The restyle happened to make
this screen free**; under the old 16px rhythm the button would have landed at
311 instead of 319.

Verified in `tools/resetpassword-harness.html`: all six rows identical to the
host, column centred 504/504.

### Widget structure

Same `Layout_Login` block. `b1-` ids are block-owned, unprefixed ids are
screen-owned content in the **Content** placeholder:

```
Layout_Login
  Logo placeholder    -> leave EMPTY (the theme paints the wordmark)
  Title placeholder   -> "Forgot your password?"
  Content placeholder
      Container .pds-login-right-inputs            #EmailContainer
          Label  .OSFillParent                     "Email"
          Input  .form-control .input-large .OSFillParent
      Container .pds-login-right-button            #ButtonContainer
          ButtonLoading  -> Button .btn .btn-primary .btn-large  "Reset password"
  Footer placeholder  -> "Back to " + Link "Log in" (.link-small) -> Login screen
```

Do **not** add `.pds-login-password-field` to the email container: that class
exists to position the reveal icon and to narrow the bottom margin to 16px, and
on this screen it would pull the button 8px up.

Keep the screen inert, like `Login` — no reset action, no client logic. The
"Log in" link navigates to the `Login` screen, which is the one live behaviour
the host's own footer has.

## Building ResetPassword: three things the model does that the DOM doesn't say

The screen is `Layout_Login` with `Logo` empty, a Text in `Title`, two
containers in `Content` and a Text + Link in `Footer`. Three defects came out
of the first build, and all three are worth recording.

**1. `form-control` is a Style Class, not a platform default.** The spec I gave
Mentor said the email Input's Style Classes were `OSFillParent`, copied from
part of what the Login screen renders. The full set is
`form-control input-large OSFillParent`. Without `form-control` the input does
not match

    .pds-login-right-inputs .form-control[data-input] { height: 40px; ... }

so it rendered at the platform default — **32px tall, square corners, a grey
`#AAAAAA` border** — and the 8px deficit pushed the button and the footer down
by exactly 8px. An input that looks unstyled is the tell; the vertical error it
causes looks like a margin bug and is not one.

**2. `ThemeGrid_MarginGutter` comes from `Margin Left = Adaptive`.** The footer
link rendered as `class="ThemeGrid_MarginGutter link-small"` with
`margin-left: 1.96078%` (~8px), opening a gap between "Back to " and "Log in"
that the reference does not have. Its Style Classes really were just
`link-small` — the extra class is **compiled from the widget's Margin Left
property**, which Mentor had set to `Adaptive`. Login's own footer link has it
empty. Fixed on the widget, not with CSS: the class is generated, so a CSS
override would have been fighting the compiler forever.

**3. Mentor adds a `NoOp` screen action for an inert button.** Asked for no
screen actions, it created `NoOp` (Start → End) and wired the button's OnClick
to it. That is the right call — an ODC Button needs a destination — and the
result is genuinely inert, but it is a deviation from the literal instruction.

## The hover and focus states the login layer was eating

Reported as "inputs are missing its hover status", and it was real in **both**
themes and on **both** screens.

mtsi declares

    .pds-login .form-control { border: 1px solid <colour> !important; ... }

and an `!important` **shorthand** carries that importance into every longhand it
expands to — `border-color` included. The design system's own state rules,

    .form-control[data-input]:hover { border-color: var(--input-border-hover) }
    .form-control[data-input]:focus { border-color: var(--input-border-focus) }

are `(0,2,0)` and not important, so inside the login column they lost outright.
The border sat at its resting colour under the cursor and while focused.

**A dead hover state has no geometry**, which is why it survived every pass of
this work: everything measured was position and size, and those were perfect.

The fix restores only `border-color`, at `(0,4,0)` and important. The focus ring
was never broken — mtsi sets no `box-shadow`, so it never competed for it. And
there are **no new values**: our `--input-border-hover` (`#777f8d`) and
`--input-border-focus` (`#b2b4ff`) are already byte-identical to the host's own
tokens, read off `id.outsystems.com`.

### Verifying a state the pane cannot show

`:hover` cannot be produced here at all — a synthetic pointer leaves
`document.querySelectorAll(':hover')` **empty** — and `:focus` never matches
because `document.hasFocus()` is false even with the tab fronted. So the state
was tested by substitution: replace `:hover` with a class, which carries
**identical specificity weight**, and read the result.

That test lied twice before it worked, and the reason is worth knowing:
**`.form-control` declares `transition: all`, and transitions do not advance in
this pane** — a fronted tab included, which is broader than the background-tab
rule I had written down. Every border change was animating from the old value
and freezing there, so `#e { border: 1px solid red !important }` measured as
*unchanged*. That reads exactly like a cascade failure and is not one. With
`transition: none !important` forced first, the substitution test gives:

| case | result |
|---|---|
| literal `!important` sanity check | applies |
| hover-equivalent | `#777f8d` |
| focus-equivalent | `#b2b4ff` |
| same rule **without** `!important` | loses to mtsi |

That last row is the one that proves the diagnosis rather than just the fix.

## The two screens are wired together

`Login`'s `ForgotLink` now navigates to `ResetPassword`, and `ResetPassword`'s
`LoginLink` navigates back. Both are plain screen destinations on the Link
widget — no screen action, no client logic — which keeps both screens as inert
as they have always been. Navigation is the only live behaviour either one has,
and the reference pages do exactly the same.

Verified as a round trip: `Login` → `ResetPassword` → `Login`, with all nine of
`Login`'s rows still identical to the host afterwards.

**Synthetic pointer events do not reach the page in this pane.** A `computer`
click reported the right page coordinates, landed inside the link's box with
nothing covering it and `pointer-events: auto` throughout — and did not
navigate. It is the same limitation that makes `:hover` unobservable here:
`document.querySelectorAll(':hover')` comes back empty no matter where the
pointer is put. Calling `element.click()` exercises the app's own handler and
does navigate, which is the useful test; a dead synthetic click is not evidence
of a broken link.

## Sign up: the third screen off the same block

`id.outsystems.com/community/signup` is the reset-password layout again, row for
row — the **same six positions**, the same computed values, three different
strings:

| | ResetPassword | SignUp |
|---|---|---|
| heading | Forgot your password? | Create your free account |
| button | Reset password | Continue |
| footer | Back to **Log in** | Already have an account? **Log in** |

So it needed **no new CSS** either. Three screens now come off `Layout_Login`
with the login CSS untouched, which is the strongest evidence so far that the
restyle landed on the right primitives rather than on one page's measurements.

The host does have one extra element: a hidden `#Recaptcha` div between the
input and the button, `margin-top: 24px` and **h0**. Its margin collapses
through with the button group's own 24px rather than summing, so the effective
gap is the same 24px our block already produces. A zero-height block between
two margins is easy to read as +24px and is not.

### `Adaptive` is the DEFAULT for a new Link widget

The `ThemeGrid_MarginGutter` gap came back on `SignUp`'s footer link even though
the build instructions said explicitly to leave every margin empty — and Mentor
again reported, correctly, that it had set no margin.

Both things are true because **`Margin Left = Adaptive` is the platform default
for a newly created Link widget.** "Leave it empty" is not an instruction the
platform can honour; the property has to be *actively cleared* on every new
Link. The earlier note here read this as Mentor having chosen `Adaptive`, which
was wrong — it chose nothing, and that is the problem.

Consequence for anything built on this block: after creating a Link, check the
rendered class list, not the model's Style Classes. The model is clean in both
the broken and the fixed state.

### Navigation

All three screens are wired as plain Link destinations — no screen actions, no
client logic:

    Login  --Forgot password?-->  ResetPassword  --Log in-->  Login
    Login  --Sign up here----->   SignUp         --Log in-->  Login

Verified as five consecutive hops in one session, with `Login`'s nine rows still
identical to the host at the end.

### Standing validation warnings (2, neither from this work)

1. **Unused `NoOp` screen action on `Login`.** Nothing calls it. Mentor reports
   it as pre-dating today; the warning count did go from 1 to 2 between the
   `ForgotLink` change and the `SignUp` build, so wiring `ForgotLink` to a real
   destination plausibly orphaned it. Harmless dead code either way, left in
   place rather than deleted unasked.
2. **`Home` / `GetUsersData` exposed without authentication** — the known
   pre-existing notice, untouched.

## The placeholder that text dumps cannot see

Sign up's email field carries `placeholder="Enter your work email"`. It was
missed because every text sweep of the host used `innerText` / text nodes, and
**a placeholder is an attribute, not text** — it appears in no text walk of the
DOM, and a screenshot of an empty field is the only visual trace.

Checked across all three reference pages, and it is sign up only:

| page | email placeholder |
|---|---|
| login | none |
| resetpassword | none |
| signup | **Enter your work email** |

So the fix is one widget property on one screen, not a pattern-wide rule.

Its rendered style needed no CSS at all: the host draws it `rgb(148,156,168)`
14px/400, and our `::placeholder` → `--input-text-placeholder` → `--text-secondary`
already resolves to exactly that ink in dark. In light ours is `rgb(104,111,125)`,
which has no reference to match — the host ships no light sign up.

**When sweeping a reference page for content, walk attributes too** —
`placeholder`, `aria-label`, `title`, `alt`. `innerText` is not the page.

## Light theme, all three screens

| | Login | ResetPassword | SignUp |
|---|---|---|---|
| rows vs host | 9/9 | 6/6 | 6/6 |
| centred | 504/504 | 504/504 | 504/504 |
| corner art | filter applied | filter applied | filter applied |
| placeholder | none | none | `rgb(104,111,125)` |

Geometry is identical in both themes on all three, which is the point of the
single unscoped layout layer — light is a palette swap, never a second layout.

## Step 2 of sign up: "Verify your email"

Reached by submitting an email on `/community/signup`; it lands on
`/community/signupactivation?email=<base64 of the address>&redirect_uri=`. That
URL is directly addressable, so the page can be revisited for measurement
without going through the form again.

**This one is not the same column with new strings.** It is a real form, and the
first of these screens that needs components the block does not have.

Measured at 1440 dark, column `500->932` (432 wide) as always:

| row | y | h | gap above |
|---|---|---|---|
| logo | 96→135 | 39 | — |
| title "Verify your email" | 167→199 | 32 | 32 |
| email card | 223→303 | 80 | 24 |
| First name / Last name | 327→399 | 72 | 24 |
| Country | 423→495 | 72 | 24 |
| Verification code | 519→591 | 72 | 24 |
| Password **+ requirements** | 615→819 | **204** | 24 |
| Terms checkbox | 843→891 | 48 | 24 |
| Subscribe checkbox | 915→947 | 32 | 24 |
| button "Agree and start free" | 971→1011 | 40 | 24 |
| footer "Already have an account? Log in" | 1027→1051 | 24 | 16 |

A flat 24px rhythm all the way down, 16px before the footer.

**Two traps in reading this page.** The password row is `h72` when the
requirements are collapsed and `h204` when they are shown, and everything below
it moves by 132px — the first measurement taken was the collapsed one, and the
rows under it were wrong. And a later pass came back 16px short on every row
because the page had been scrolled: `getBoundingClientRect()` is
viewport-relative, so on a page taller than the viewport the scroll offset has
to be added back before comparing against anything.

The logo and title land on **exactly the same y as every other screen** (96→135,
167→199), and the footer is the same 14/24 line. So the block's top and bottom
still fit; it is the middle that is new.

### The email card

`.card.email-card.margin-bottom-6`, `h80`: background `#24262C`, radius 8px,
padding `0 24px`, `display:flex`. A 48×48 icon, then `.flex1.margin-left-3`
(24px) holding two lines:

- `.body-semi-bold-l` — 16px/24 weight 600, `#F9FAFB` — "We've sent you a verification code"
- `.body-regular-base.text-neutral-7.line-clamp` — 14px/24 weight 400, `#949CA8` — the address

### The two-column name row

`.columns.columns2.gutter-base`: the container is **448 wide against a 432
column** — `margin: 0 -8px` — and each `.columns-item` is 224 wide with
`padding: 0 8px`, so the two fields are 208 wide and 16px apart.

**This grid already works in the consumer** — it comes from OutSystems UI, not
from our bundle (`grep` finds it in none of `dist/*.css`, but a runtime probe on
the live app returns `display:flex`, `margin: 0px -8px`, child `padding: 0 8px`).
Worth knowing before writing CSS for it: it would have been a duplicate.

### Content for the rest

**Password** — an `InputWithIcons` (the same reveal control as login) wrapped in
`.password-analysis`, collapsed to h40 until engaged, listing:

> Your password must contain: · At least 12 characters · 1 number ·
> 1 lower letter · 1 uppercase letter · No spaces at the beginning or end

**Terms checkbox** — "I agree to use OutSystems per the EULA or Trial
Agreement,, as applicable, and consent to the Privacy Statement, including
personal data collection." Three links: EULA, Trial Agreement, Privacy
Statement. (The doubled comma after "Trial Agreement," is the host's own copy,
not a transcription slip — the link text ends in a comma and another follows.)

**Subscribe checkbox** — "I'd like to receive the latest news and insights about
AI development, and OutSystems products and services."

**Country** — a custom block, `DropdownSearchCustomCommunity.DropdownEmptyCustomCommunity`,
rendered as `.ds-dropdown-empty-search.signup-country-dropdown-navigation`.
Trigger reads "Select your country"; open, it has a Search field and the full
ISO country list.

### What we have and what we do not

| piece | status |
|---|---|
| `.card` | in the bundle (17 rules) |
| `.columns/.columns2/.gutter-base` | from OutSystems UI at runtime |
| `.checkbox` | in the bundle (32 rules) |
| `body-semi-bold-l`, `body-regular-base`, `text-neutral-7`, `line-clamp` | in the bundle |
| `.password-analysis` | **absent everywhere** |
| searchable country dropdown | **absent** — the host's is a bespoke block |

So most of it is assembly. The two genuinely new pieces are the password
requirements display and the country dropdown.

### Where the requirements list has to live

First build put `PasswordRequirements` as a SIBLING of the password field's
container. The host nests it INSIDE that container, and the difference is not
cosmetic: as a sibling it becomes another row in the 24px rhythm, where the
reference has it 8px under the input.

Mentor cannot move a widget from one container to another, so the fix is delete
and recreate in the right parent — the same constraint that applies to a block's
Content placeholder, and it applies between two ordinary containers too.

Verified after the fix: `PasswordContainer` holds `PasswordLabel`,
`PasswordInput`, `PasswordRequirements` in that order, and the Content
placeholder's direct children are exactly

    EmailCard, NameRow, CountryContainer, VerificationCodeContainer,
    PasswordContainer, TermsContainer, SubscribeContainer, ButtonContainer

**Build the nesting right the first time.** The instruction "these N containers
in this order" reads as a flat list and will be built as one; anything that
belongs inside another widget has to say so explicitly.

### Four rounds on one screen, and what each one was

`VerifyEmail` took four corrective passes. None of them were the model builder's
fault; all four were errors in what it was told or in the CSS written for it.
They are worth listing because three are the same two mistakes repeating.

| # | symptom | cause |
|---|---|---|
| 1 | requirements list a sibling of the password field | the build spec read as a flat list of containers; nesting has to be stated |
| 2 | card lines ran together as "verification code**name@**example.com" | ODC renders a Text widget as an inline `<span>` |
| 3 | password block 8px short, list flush to the input | **same as 2** — `.password-analysis-title` is an inline span, and an inline box discards vertical margins, so `margin: 8px 0` was dropped |
| 4 | consent rows unstyled, no gap between them | the stylesheet defined `.verify-consent-row`; the build applied `display-flex align-items-center`. **The class that was styled was never on the page** |
| 5 | name row 24px too tall | `.pds-login-right-inputs` carries `margin-bottom: 24px` **!important** from RESTYLE, so a (0,3,0) override without `!important` lost to a bare (0,1,0) |

**Two rules come out of this.**

*Anything from a Text widget that needs its own line or a vertical margin needs
`display: block` stated.* It bit twice on one screen, fifteen rules apart.

*Everything RESTYLE touches is `!important`, so everything overriding it must be
too.* This is the third time — the input hover states, the empty signed-in slot,
and now the name row. Specificity does not substitute: `(0,3,0)` loses to a bare
`(0,1,0)` when only the latter is important.

Number 4 deserves its own note because it fails with no signal anywhere: the CSS
is valid, the rule ships in the bundle, and `querySelector` for the class simply
returns nothing. Writing one class name in the stylesheet and a different one in
the build instructions produces no error at either end.

### Skinning OutSystems UI's DropdownSearch

The country field is OutSystems UI's `DropdownSearch`, which wraps the `vscomp`
virtual-select and brings its **own light skin**: measured on our dark column it
rendered a white background, a `#CED4DA` border, a 4px radius and 12px value
text, beside inputs that are `#181A1F` on `#464B56` at 8px and 14px. It looked
like a control from a different product.

compat section 22 records a decision **not** to ship the bundle's `vscomp`
rules, on the grounds that the family rendered zero times on any portal page
measured. That was true and still is of the portal — the component is here
because *we* chose `DropdownSearch` for this field, so its skin has to come from
this file rather than from the extraction.

`!important` on the value colour **only**. Tested rule by rule on the live
screen: background, border, radius, height and font-size all apply at `(0,2,0)`
and only the value's colour loses. Blanket `!important` would have worked and
hidden which one of the five actually needed it.

### A wrong token that only light could show

`.email-card-title` was written as `--login-text-secondary`. In **dark** that
token and `--login-text-primary` are both `#F9FAFB`, so the mistake was
invisible — the card looked right. In **light** `--login-text-secondary`
resolves to the same muted grey as the address line beneath it, and the card's
two lines came out identical, the title losing the emphasis the whole component
is built on.

It is `--login-text-primary`: `#F9FAFB` in dark (the host's own value) and the
dark ink in light.

**Two tokens that coincide in one theme will not be told apart by testing that
theme.** Dark was measured against the host on every pass and never caught it.

## What "identical to the host" did not cover

The screen was reported as matching the host on the strength of eleven row
positions and a handful of computed properties. It was not. Four components
were wrong, and none of them were things row geometry could ever have caught:

| reported defect | what it actually was |
|---|---|
| email icon wrong colour | the icon slot was given a size and never a colour, so it inherited `#F9FAFB` white against the host's `#949CA8` |
| dropdown incomplete, closed and expanded | only the closed trigger was skinned; the panel was OutSystems UI's stock light dropdown |
| no eye toggle; requirements always visible | the reveal control was never built, and the list was permanently shown where the host collapses it |
| checkboxes incomplete | the box matched exactly — the 8px gap to the label and the label ink did not |

**Row coordinates are not a rendering.** Every pass measured positions and
declared parity; a 0.8-scale screenshot of a 1440 viewport is a ~640px image in
which a white dropdown on a dark page is a few grey pixels. Component-level
checks — ink, borders, radii, states — have to be their own pass.

### The portalled panel

`.pds-login .vscomp-dropbox` could never match. vscomp **portals** the dropbox
to the end of `<body>`:

    body > .vscomp-dropbox-wrapper > .vscomp-dropbox-container > .vscomp-dropbox

so the open panel has no `.pds-login` ancestor at all — `closest('.pds-login')`
on it returns null. The rules were valid, shipped, and dead.

They are scoped to `.vscomp-dropbox-wrapper` now, which necessarily reaches
every vscomp panel in a consuming app: a portaled element cannot be scoped by
DOM position, and there is no ancestor tying it back to the pattern.

**A portaled component breaks ancestor scoping silently.** Check where a
library actually mounts its overlay before scoping rules to a container.

It breaks **token scoping** too, and that failure is even quieter. After the
selectors were fixed the panel took its backgrounds and inks but its corners
stayed square, with the rule sitting in the bundle, matching the element,
carrying `!important`, and doing nothing. The cause:

    --border-radius: 8px   is declared on `.pds-login, .full-screen-background`

— one of the PDS tokens this file deliberately scopes to the login roots rather
than declaring globally. Outside those roots `var(--border-radius)` resolves to
nothing, the declaration is invalid at computed-value time, and it is discarded
whole. Confirmed by reading the custom property off the open panel: `8px`
inside `.pds-login`, **undefined** on the portaled dropbox.

Every other token in those rules is global, which is why only the radius failed
— the failure pointed straight at the single scoped token. `--border-radius-2`
is the design system's own root-level 8px step (the one `.btn` uses).

**When a rule targets something outside the pattern, its tokens have to come
from outside the pattern too.** A scoped `var()` in an unscoped rule fails
silently and takes the whole declaration with it.

### The password field

Two things the first build missed: no reveal control at all, and the
requirements list permanently visible where the host keeps it at
`height: 0; overflow: hidden` until the field is engaged. `:focus-within` gives
the reveal with **no client logic**, so the screen stays as inert as the other
three.

The eye is positioned from the **top** (44px = the label's 24px + its 8px gap +
(40 − 16) / 2), not from the bottom as on the login screen. There the input is
the last thing in its column so `bottom: 12px` centres it; here the
requirements list follows the input, and a bottom offset would put the eye
under the list. Measured after the fix: eye centre and input centre both at
y667, inset 12px from the input's right edge.

### One deviation worth naming

The consent label is `#C6C9CE` on the host, which is **not on our neutral
ramp** — it sits between `--neutral-8` (`#B3BAC4`) and `--neutral-9`
(`#D5DADF`). Ours uses `--neutral-8` rather than hardcoding an off-ramp value,
so light gets a coherent counterpart instead of a value that only means
something in dark.

## Reading the host's CSS instead of measuring it

The dropdown skin and the password requirements were both hand-written from
computed values. They should not have been: **the host's stylesheets are
same-origin and fetchable**, and `fetch()` on them from the page returns the
real rules. Three things came out of reading the source that measuring had
missed or got wrong.

**1. The country field is not a DropdownSearch.** The host's control is the
`.dropdown-empty` component — the portal's own dropdown. The `vscomp` CSS in
the host's bundle is the raw vendor default (`#fff`, `#ddd`, `#333`): the host
ships it and never uses it. Our bundle already carries 30 `.dropdown-empty*`
rules, but the extraction dropped the **base** `.dropdown-empty-trigger.input`
rule while keeping its `:hover` and `.not-valid` variants — a component whose
error states ship without its base state looks covered to a grep and renders
unskinned.

**2. The requirements list animates.** The real rule is

    .password-analysis-requirements { max-height: 0; overflow: hidden;
                                      transition: max-height .4s ease-out }
    .password-analysis--show-requirements .password-analysis-requirements { max-height: 140px }

A `display` toggle — what was written from measurements — cannot animate at
all. Ours uses `:focus-within` in place of the host's JS-applied class, so the
screen still needs no client logic.

**3. The default marker is a bullet, not a tick.** The host draws `•` via
`::before` and only swaps in a green tick on `.rule-pass`, which real
validation adds. Ours rendered `ph ph-check` on every row — the page was
showing all five password rules as **already satisfied**. Computed styles look
entirely plausible either way; only the source says which state you are in.

### Two self-inflicted bugs while fixing it

**The bullet shipped as a literal "2".** `ODC_ADAPT` is a plain (non-raw)
Python string, so a CSS escape written into it is parsed by **Python first** —
and a hex escape for the bullet starts with a digit run that Python reads as an
**octal** escape. It emitted U+0082 followed by `2`; the bytes were `302 202 2`.
Write the character itself: it survives however many string layers it passes
through.

**The rule it replaced was never deleted.** The new `max-height` block went in
at line 1051 and the old `display: none` pair stayed at line 1283 — same
specificity, 230 lines later, so it won on source order and the list never
rendered whatever `max-height` said. Measured after removing it: collapsed 0,
expanded 132px, five 16px rows, 8px marker gap.

**Replacing a rule means deleting the old one, not only writing the new one.**
And a `display` rule beats any amount of correct `max-height` while it survives.

## Taking the dropdown component properly

The hand-written vscomp skin was the wrong solution to the wrong problem, and
comparing the two DOMs showed why: **we were never rendering the host's
component.** The host's country field is

    .dropdown-empty
      .dropdown-empty-trigger.input        the visible closed control
        .dropdown-empty-button-label         the prompt text
        svg.dropdown-empty-trigger-chevron   a real <svg>, not a CSS border
      .dropdown-empty-popover              in place, NOT portaled
        .dropdown-empty-popover-content
          the virtual-select               with its own toggle hidden
        .dropdown-empty-popover-footer     helper + action row

and ours was OutSystems UI's `DropdownSearch`: a `.vscomp-toggle-button` and a
dropbox portaled to `<body>`. Our bundle already shipped CSS for the host's
structure and our page rendered **zero** elements it targeted.

**The host uses vscomp too — nested inside its own popover**, which dissolves
the choice between the two. This rule is the whole architecture:

    .dropdown-empty-popover-content .vscomp-toggle-button { display: none }

The virtual-select supplies the searchable list; the visible control is the
design system's own. Nothing needs portal scoping, because the popover opens in
place.

### Why the CSS was only two-thirds there

The component lives **only** in `old-neo-design-system.css`, which three
extractors mine by whitelist — and none of them claimed it. What we shipped were
the fragments whose selectors happen to name an OutSystems UI class, picked up
incidentally by `osui_reskin.py` because `not-valid`, `btn` and `filter` are in
its CORE set:

| rule | shipped? | why |
|---|---|---|
| `.dropdown-empty-trigger.input.not-valid` | yes | selector contains `not-valid` |
| `.dropdown-empty-trigger.input.not-valid:hover` | yes | same |
| `.dropdown-empty-trigger.input` | **no** | no CORE token in the selector |

The trigger's error and hover states shipped without the trigger. **Exactly the
shape of the skeleton bug** recorded in `extract_legacy_widgets.py` — a
component present only as adjustments to itself — so the fix went in beside it
as a fourth family rather than into the re-skin layer, which is for OutSystems
UI widgets and not for the portal's own components.

Two exclusions (`.ds-combo-picker`, `.ds-date-picker`) drop rules that are dead
without families we do not ship. One deliberate inclusion admits the
`.dropdown-empty-popover-content .vscomp-*` rules even though their subject is
vendor, because scoped under that ancestor they are not vendor defaults — they
are what turns vscomp into the portal's list.

Result: 30 rules → the full component, and `dist/neobase.css` 2443 → 2692.

### The build guard earned its keep

The first passing extraction **aborted the build**:

    relative asset url() would not resolve in ODC:
      ['../img/NeoDesignSystem.icsearch__<hash>.svg?<hash>']

The popover's search field draws its magnifier from a portal image by a path
relative to the stylesheet, and ODC rewrites its own asset paths at publish but
leaves pasted theme CSS verbatim — that url would have 404'd in silence.
Rewritten to the authoring form using the same `ICONS` convention
`osui_reskin.py` already had, with the asset fetched into
`reference/raw/assets/` and copied to `dist/assets/`. **Import it as a library
Image named `icsearch`.**

### The JavaScript is ours, because the portal's is not source

The behaviour cannot be copied. The 2MB `FusionDesignSystem` bundle contains a
`fusion-dropdown-empty` **Stencil web component** — BEM class names, Floating
UI, its own shadow lifecycle — which is the portal's *next* generation and not
what this page renders. The page's own script turned out to be Tab-navigation
glue that *reads* `is--open` and never sets it. The real open/close logic is
compiled ODC client actions.

What is recoverable is the **contract**, and the CSS states it exactly: put
`is--open` on the wrapper and the popover, take it off, and position the
popover — which is `position: fixed`, so script has to place it. Every visual,
including both transitions and the chevron rotation, is already in the CSS.

`behaviour/dropdown-empty.js` (139 lines) implements that, and is a
hand-maintained sibling of the generated bundle in the same way `compat/` is.
Two decisions in it are deliberate:

- **It keeps no state.** State is read back from the class every time, because
  ODC re-renders markup freely and rewrites variable-bound attributes — a JS
  flag would go stale behind a re-render while the class stayed true.
- **It binds nothing per element.** One delegated listener set on `document`,
  installed once behind a guard, so a dropdown ODC renders later (inside an If,
  a List, a popover) works with no re-initialisation and no MutationObserver.

### Reading the served theme, and the 47KB that is not missing

Checking whether a paste reached the consumer means fetching the served
stylesheet, and the served bytes do **not** match `dist/neobase.css`: 353,991
against 401,199, and 716 `dropdown-empty` occurrences against 743. Neither gap
is a gap. ODC minifies pasted theme CSS at publish — it strips the space after
every selector comma and the quotes inside attribute selectors, so
`input[type="checkbox"]` is served as `input[type=checkbox]`. A naive
string-compare of preludes reports every multi-selector rule as absent.

Normalise commas and combinators before comparing, and confirm the handful of
remaining differences by grepping for the class itself rather than the rule
text. What actually proves delivery is a small set of flags, not a byte count:

| check | what it proves |
|---|---|
| `.dropdown-empty-trigger.input {` | the base trigger arrived |
| `.dropdown-empty-popover {` | the popover arrived |
| `dropdown-empty-popover-content .vscomp-toggle-button` | the vscomp hosting rules arrived |
| `icsearch` | the image reference survived the paste |

### `dropdown-empty-trigger` is not the class that gets the focus ring

The trigger carries two class names in the portal's markup, and they are not
interchangeable:

```css
.dropdown-empty-trigger.input        { /* the box: border, height, padding */ }
.dropdown-empty.is--open .dropdown-empty-button.input
                                     { border-color: var(--input-border-focus);
                                       box-shadow: var(--component-shadow-focus) }
```

The open-state ring is keyed to **`dropdown-empty-button`**, which has no base
rules of its own and so looks redundant when you read the markup. The first
version of this field on `VerifyEmail` had only `dropdown-empty-trigger input`;
it measured correctly closed and would have opened with no focus ring at all.
The trigger needs `dropdown-empty-button dropdown-empty-trigger input`.

The `.dropdown-empty-backdrop` element in the portal's markup is deliberately
**not** replicated. It is a `position: fixed`, `100vw × 100vh`, `z-index: -1`
element raised to `101` while open — the portal's own outside-click catcher.
Our behaviour resolves outside clicks by delegation on `document`, which is
strictly better: the backdrop would sit over the whole viewport while open and
swallow a click meant for a second dropdown's trigger.

### Making vscomp render its list inside the popover

`Interaction.DropdownSearch` initialises virtual-select with
`show-dropbox-as-popup`, which portals the list to `<body>` — outside the
popover, and out of reach of anything scoped to it. The portal runs the same
widget the other way, and its CSS says so outright:

```css
.dropdown-empty-popover-content .vscomp-wrapper.keep-always-open .vscomp-dropbox
  { border: none }
.dropdown-empty-popover-content .vscomp-toggle-button { display: none }
```

`keepAlwaysOpen` is read **once, at init**; assigning the field on the live
instance does nothing, because the dropbox has already been portaled. The route
that works is a deliberate re-initialisation, and it is safe for one specific
reason:

```js
vs.destroy();                      // empties the div, does NOT remove it
window.VirtualSelect.init({ ele: sameDiv, …, keepAlwaysOpen: true });
```

`destroy()` unmounts the `body > .vscomp-dropbox-wrapper` and empties the div
while leaving the div itself in place. The platform's change handler is bound to
**that div**, not to anything vscomp built, so it survives the swap and the new
instance dispatches to it exactly as before. Verified live: after the re-init a
`setValue('PT')` still fired precisely one `change` event, the dropbox measured
432×279 *inside* `.dropdown-empty-popover-content`, and `body >
.vscomp-dropbox-wrapper` count went to zero.

Options are recoverable from the old instance (`vs.options`, minus group titles
and `isNew` entries), as are `placeholder`, `hasSearch`,
`searchPlaceholderText`, `noSearchResultsText`, `hideClearButton`, `multiple`,
`zIndex` and the current `getValue()`. The re-init runs at most once per
element, and its guard is the flag it sets: `if (vs.keepAlwaysOpen) return`.

### The component is a library block, not screen markup

**The block is called `DropdownField`, not `DropdownEmpty`.** That name was
already taken, by a real public component: the row-actions kebab menu the
Users page uses, built on the `fusion-dropdown-empty__*` class family with its
own `Trigger`/`Content` placeholders and keyboard handling. The two are
siblings, not versions of each other — `DropdownEmpty` is the icon-button menu,
`DropdownField` is the input-shaped select.

They share CSS hooks, which needs care: the menu's trigger carries
`dropdown-empty-trigger` even though its root is `fusion-dropdown-empty`. The
behaviour script therefore matches that trigger, finds no `.dropdown-empty`
ancestor and **returns before `preventDefault`**, leaving the menu to drive
itself. Keep that order if you touch the click handler.

`DropdownField` lives in NeoDesignSystem: the wrapper, trigger, chevron and
popover with a `Content` placeholder for the list, a single `Label` parameter,
and the behaviour installed from the block's own **On Ready** JavaScript node.
That placement is what makes the script's self-guard load-bearing rather than
merely tidy — every instance runs it, and only the first one installs anything.

The canonical copy of the script stays at `behaviour/dropdown-empty.js`; the
node in the block carries a header pointing at it, because there is no way to
reference a repo file from inside ODC.

### The `Label` parameter has to be bound, not set

`DropdownField` renders its closed trigger from a `Label` parameter, and a
literal there is a trap: the field then never shows what the user picked. The
hand-built version had the same bug — a static `CountryPromptText` Text widget —
so it was invisible until the block made the parameter explicit.

The fix belongs in the consumer, not the block, because only the consumer knows
where the value lives. On `VerifyEmail`: a screen variable
`CountrySelectedLabel` (default `"Select your country"`), assigned in the
`DropdownSearch`'s existing `OnChanged` handler from the option it already
receives, and bound to `Label`:

```
If(SelectedOptionList.Length = 0, "Select your country",
   SelectedOptionList.Current.Label)
```

`Label` is the display text on OutSystemsUI's `DropdownOption` structure;
`Value` is the key. The empty-list branch matters: clearing the selection has to
restore the prompt rather than blank the trigger.

There is a useful signal in the validation counts here. The two "unused input
parameter" warnings on `OnCountryChanged` were the tell that the screen was
receiving the selection and discarding it — exactly the gap that left the label
static. Wiring it took the app from 3 warnings to 2, one of which is the
intentional public-access notice on `Home`.

### `DropdownField` mirrors `DropdownSearch`, and owns its list

The first version of the block took a single `Label` parameter and exposed a
`Content` placeholder for the consumer to drop `Interaction.DropdownSearch`
into. That works, but it pushes the whole API onto every consumer: each one has
to place the inner widget, pass its options, and wire the trigger text by hand.
The second version has the same surface as `DropdownSearch` and owns the list:

| Parameter | Type | Mandatory |
|---|---|---|
| `OptionsList` | `OutSystemsUI.DropdownOption` List | yes |
| `StartingSelection` | `OutSystemsUI.DropdownOption` List | no |
| `Prompt` | Text (default `"Select..."`) | no |
| `OptionalConfigs` | `OutSystemsUI.DropdownOptionalConfigs` | no |
| `ExtendedClass` | Text | no |

plus the two events it raises: `Initialized(DropdownFieldId)` and
`OnChanged(DropdownFieldId, SelectedOptionList)`. A consumer now uses it exactly
as it would use `DropdownSearch`, and gets the portal skin for free.

Three things this needs that are not obvious:

- **The structures are OutSystemsUI's**, `DropdownOption` and
  `DropdownOptionalConfigs`, so the library takes a reference to OutSystemsUI's
  `DropdownSearch` block. Reading that block's parameter *signature* is itself
  what adds the reference — the live definition is only returned once it is
  referenced, so a purely read-only inspection of it is not possible.
- **`ExtendedClass` needs a Style *expression*, not a Style Classes string.**
  The pattern is already in the library, on `DropdownEmpty`'s root:
  `"dropdown-empty" + If(ExtendedClass <> "", " " + ExtendedClass, "")`.
- **The trigger text is block state, not a parameter.** A local `TriggerText`,
  seeded in `OnReady` from `StartingSelection` and reassigned by the block's own
  handler on the inner widget's `OnChanged`, with the Expression falling back to
  `Prompt` when it is empty:

  ```
  If(SelectedOptionList.Length = 0, "",
     If(SelectedOptionList.Length = 1, SelectedOptionList.Current.Label,
        IntegerToText(SelectedOptionList.Length) + " selected"))
  ```

  `IntegerToText` is required — `+` will not concatenate an Integer onto Text.
  The multi-selection branch matches the portal, which shows a count rather
  than a list of labels once more than one option is picked.

This is a **breaking change** for consumers: `Label` and the `Content`
placeholder are gone. A consumer pinned to the previous version keeps working;
one that bumps the pin has to drop the inner `DropdownSearch` instance and pass
`OptionsList` instead. Bump the pin *before* republishing the consumer, so the
screen can be reworked against the new signature and the old revision keeps
serving until that publish lands.

### Verifying keyboard behaviour: synthetic events need a legacy `keyCode`

The dropdown's keyboard path is verified end to end, but the first attempt
reported a failure that was not real, and the reason is worth keeping.

`new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true })` leaves
`keyCode` and `which` at **0**. Our own handler reads `e.key`, so opening on
Enter, Space and ArrowDown tested fine. virtual-select branches on the legacy
`keyCode`, so arrowing *through* the list did nothing and the run looked like a
broken hand-off. Real keystrokes always carry `keyCode`; the gap was the test.

Populate it explicitly — the property is read-only, so define it:

```js
const e = new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true, cancelable: true });
Object.defineProperty(e, 'keyCode', { get: () => 40 });
Object.defineProperty(e, 'which',   { get: () => 40 });
el.dispatchEvent(e);
```

With that, the whole path is observable in the browser pane:
Enter opens and moves focus to `.vscomp-search-input`; ArrowDown/ArrowUp move
`.vscomp-option.focused` (measured: down×3 → Germany, up×1 → United Kingdom);
Enter sets the value to `GB`, closes the popover, flips `aria-expanded` to false
and leaves the trigger reading "United Kingdom"; typing `ger` filters the list to
Germany alone; Escape closes and returns focus to the trigger.

`document.activeElement` is reliable here even though real focus rings are not —
see the note on states that cannot be produced in the pane.

### Tab order: what the portal does, and why we do it differently

Tab could not get past the country trigger. The CSS was not the cause — our
`.dropdown-empty-popover` rule is byte-identical to the portal's, `opacity: 0`
and `pointer-events: none` with `visibility: visible`, and neither side removes
the popover from the tab order in CSS.

Enumerating the actual tab sequence on both pages found the difference.
virtual-select leaks focusable elements: its wrapper and **every option** carry
`tabindex="0"`, and until it is switched to keep-always-open it also parks a
dropbox on `<body>`. Inside a closed popover those are invisible tab stops.

**The portal's answer is an explicit positive tabindex on every field:**

| Field | Portal | Ours (before) |
|---|---|---|
| First name | `tabindex="1"` | natural |
| Last name | `tabindex="2"` | natural |
| Country trigger | `tabindex="3"` | `tabindex="0"` |
| Verification code | `tabindex="5"` | natural |
| Password | `tabindex="6"` | natural |
| Terms / Subscribe | `7` / `8` | natural |
| Submit | `tabindex="9"` | natural |

Positive values are traversed first in numeric order, so every `tabindex="0"`
element — all of virtual-select's internals — is pushed to the end of the page.
That is what makes the portal's Tab order feel correct. Note the portal's
trigger carries **no** `role`, `aria-expanded` or `aria-haspopup`; `tabindex` is
the whole of it. Note also `tabindex="4"` is absent from the sequence.

Measured on our side at rest, before the fix: `FirstName → LastName → trigger →
.vscomp-ele-wrapper (0px tall, tabindex 0, inside the closed popover) →
VerificationCode → … → LoginLink → .vscomp-search-input (0×0, portaled to
<body>)`. Two phantom stops, one of them immediately after the trigger.

**We fix it at source instead**, so a consumer needs no tabindex at all:

- the closed popover gets `inert`, which removes its whole subtree from the tab
  order and from hit-testing in one attribute, set in `close()` and cleared in
  `open()` before focus moves;
- `inlineList()` now also runs at install, retried while the platform's
  `DropdownSearch` finishes its own OnReady, so there is never a `<body>`
  dropbox — the portal has `keepAlwaysOpen: true` and zero portals at rest, and
  now so do we.

Positive tabindex was the alternative and it would have matched the portal
exactly, but it pushes these fields ahead of everything else on the page and has
to be repeated, in order, by every consuming screen. Removing the leak gives the
same observable behaviour from the component itself.

### The stop was there all along — it just rendered nothing

The report was "set focus on the first name input, then tab tab tab, you'll see
you can't navigate to the dropdown". With real Tab keypresses (the `computer`
tool's `key` action, not a `querySelectorAll` enumeration, which is what made an
earlier check of this claim weaker than the claim) the order was already right:

    FirstNameInput → LastNameInput → b2-Trigger → VerificationCodeInput

The trigger WAS receiving focus. Measured on it at that moment:

| | value |
|---|---|
| `matches(':focus')` | `true` |
| `matches(':focus-visible')` | `true` |
| `outline-style` / `outline-width` | `none` / `0px` |
| `box-shadow` | `none` |
| `border-color` | `rgb(70,75,86)` — its resting colour |

So focus landed and drew nothing, which is indistinguishable from a skipped
stop. A scan of every rule in every loaded sheet for a selector matching
`dropdown-empty-(trigger|button)` **and** `focus` returned zero.

**Where the portal's rule lives.** Not in the design system. The 566KB
`NeoDesignSystem.Old_NeoDesignSystem__*.css` styles only the OPEN state
(`.dropdown-empty.is--open .dropdown-empty-button.input`), and has no focus rule
for the closed trigger under this naming anywhere — so the extractor had nothing
to find and was right not to emit one. The identity host's signup app patches it
in its OWN 5KB theme, `community.community__*.css`:

    .dropdown-empty-trigger.input:focus {
      border-color: var(--input-border-focus);
      box-shadow: var(--component-shadow-focus);
    }

Copied verbatim into `ODC_ADAPT`, `:focus` and not `:focus-visible`, because
that is what the host has. Reading that sheet needs `fetch(href)` from inside
the page: it is cross-origin to script, so iterating `cssRules` throws
`SecurityError`, and a scan that swallows the throw reports zero rules — which
looks exactly like "the portal doesn't have this either".

Two near-misses made this look handled. The bundle already carries
`.fusion-dropdown-empty__trigger:focus-visible` — the same rule in the other
sheet's naming, which our markup can never match. And the open-state rule keys
on `dropdown-empty-button`, one of the three classes our trigger carries, so
grepping for a focus ring on the component finds something plausible.

Verified after: focused `LastNameInput` and focused `b2-Trigger` now report the
same `border-color` and `box-shadow`, which is the relationship the host has
(`#b2b4ff` + `--component-shadow-focus` on both, in its dark theme).

### The password eye: two screens, one script, one id

Reported as the eye on VerifyEmail not behaving like Login's. It is not CSS —
the geometry already matches the host on both screens (16px glyph, `right: 12px`,
0px off the input's vertical centre; the host puts its own icons wrap at
`position: absolute; right: 12px; top: 0; height: 40px` and centres a 16px
`#ic-view` in it, on Login and VerifyEmail alike). The eye simply was never
wired:

| | Login | VerifyEmail |
|---|---|---|
| markup | container `PasswordEyeIcon` + child `PasswordEyeGlyph.ph.ph-eye` | one container `PasswordEye`, classes merged |
| `data-neo-reveal-wired` | `1` | absent |
| `role` / `tabindex` / `aria-label` | `button` / `0` / Show password | none |

`WirePasswordReveal`, the JavaScript node on Login's OnReady, opens with
`document.getElementById('PasswordEyeIcon')` and then does
`eye.querySelector('.ph')`. On VerifyEmail the first lookup returns null, and
even given the right element the second would too, because the glyph classes are
on the container itself. Both screens now run one tolerant version —
`getElementById('PasswordEye') || getElementById('PasswordEyeIcon')` and
`eye.querySelector('.ph') || eye` — rather than the markup being changed to suit
the script, so a third screen can adopt either shape.

Also in that same host app sheet, and deliberately NOT copied:

    .toggle-password .input-with-icon .input-with-icon-content-icon { top: 8px; transform: translateY(0) }

Nothing on the host's current Login or VerifyEmail has a `.toggle-password`
ancestor — it is dead legacy. App-level rules are worth reading and worth
checking against the live DOM before adopting.

### Reaching the dropdown by keyboard: the host opens it on focus

Fixing the focus ring made the stop visible but not equivalent. Tabbing through
the host's own VerifyEmail, recording `document.activeElement` and the wrapper's
`is--open` at every stop:

| step | focus | host dropdown | ours, before |
|---|---|---|---|
| Tab from Last name | trigger | **open**, popover 333px | closed |
| a moment later | `vscomp-search-input` | open | — |
| Tab | `Input_VerificationCode` | **closed** | — |

So the host is reached by **Tab alone** — no Enter, no ArrowDown — and typing
filters immediately because focus has already moved into the search box. Ours
opened only on a key, which is what "keyboard navigation to the dropdown is not
the same" meant: the stop was reachable, and after the focus-ring fix it even
looked focused, but it stayed shut.

It hangs on the focus event, not on a key: `document.getElementById(trigger).focus()`
from the console opens it, with no key involved.

**The constraint on implementing that** is the host's mouse behaviour, which is
an ordinary toggle — click opens, click again closes, click again opens, with
focus on the trigger throughout. A click on an unfocused trigger fires `focus`
*before* `click`, so opening on that focus and then toggling on the click lands
closed: the first click of every session would look dead. The focus path is
therefore keyboard-only, guarded by a flag armed on `pointerdown`/`mousedown`/
`touchstart` and cleared on the next task — the focus a press causes is
dispatched as that press's default action, so it always arrives while the flag
is still set.

Escape needed the same guard from the other side. It closes and returns focus to
the trigger, and a bare `trigger.focus()` now re-opens what it just closed;
`focusTrigger()` sets a `silentFocus` flag around the call.

**Tab out** is the third rule: from the search box, and equally from an option,
the host closes the popover and moves to the next form field — never to the next
option. Our popover is inline inside the wrapper (`keepAlwaysOpen`), so its
search box and every rendered option are tabbable while it is open; `Tab` is
intercepted and `focusBeyond()` walks the tabbables that are NOT inside any
`.dropdown-empty` to find the field after the trigger, both directions.

One deliberate deviation: tabbing off the host's trigger in the moment before
focus has moved into its search box leaves the popover hanging open with focus
two fields away. That is a race, not a designed behaviour, and is not copied —
ours closes on the way out either way.

Worth recording about the host's own markup, since it contradicts what our
component does: its trigger carries no `role` and no `aria-expanded` (we set
`aria-expanded`), and its popover is portaled to a `<body>`-level div while the
vscomp list inside it runs `keep-always-open`, the same list mode as ours. A
stale `is--open` stays on that portaled popover after closing, so the popover's
own classes are not a reliable read of the open state — the wrapper's are.

**After a selection, focus has nowhere to go.** Picking a value closes the
popover, and `close()` sets `inert` on it — which a browser will not let hold
focus, so focus drops to `<body>` and the next Tab restarts at the TOP OF THE
DOCUMENT. Measured on the host: after picking a country by keyboard its focus
stays on its own search input, inside the closed popover, and the next Tab still
moves forward through the form (to `Input_Password` — it skips
`Input_VerificationCode`, which is its own oddity).

That one cannot be copied: `inert` is exactly what keeps the closed popover's
search box and options out of the tab order, which is the leak that put two
phantom stops in our sequence in the first place. So focus goes back to the
trigger instead — one stop earlier than the host, travelling the same direction,
and the next Tab lands on the verification code. Through `focusTrigger()`, or
the `focusin` handler re-opens what the selection just closed.

## The OutSystemsUI/Dropdowns client actions

The component is not a lookalike of `DropdownSearch` — it **contains** one. The
platform registers that inner widget with `OutSystems.OSUI.Patterns.DropdownAPI`,
and every one of the thirteen `OutSystemsUI/Dropdowns` client actions is a thin
wrapper that resolves the instance by widget id and calls one method on it:

    Open → open()          SetValues → setValue()      Clear → clear()
    Close → close()        SetValidation → validation() Disable → disable()
    TogglePopup → togglePopup()   SetProviderConfigs → setProviderConfigs()   …

So the actions already reach us. The question was only what they do on arrival,
and each was driven against a live `DropdownField` and the result measured:

| client action | before | why |
|---|---|---|
| DropdownGetSelectedValues | works | returns the full DropdownOption structure |
| DropdownSetValue | works | value **and** our trigger label follow |
| DropdownClear | works | value and label return to the placeholder |
| SetVirtualSelectEvent | works | callback fired on change |
| UnsetVirtualSelectEvent | works | callback stopped |
| DropdownOpen / DropdownClose | **no-op** | they move the vscomp's own dropbox; ours is `keepAlwaysOpen` inside our popover, so there is none |
| DropdownNotValid | **invisible** | class and message land on the inner element, which lives *inside* the popover |
| DropdownClearValidation | partial | clears OSUI's, not ours |
| DropdownDisable / DropdownEnable | **invisible** | vscomp gets `disabled`; our trigger keeps enabled styling and stays interactive |
| DropdownTogglePopup | **breaks it** | flips `ShowDropboxAsPopup` and redraws |
| SetVirtualSelectConfigs | **breaks it** | redraw rebuilds the provider from the block's configs, which do not carry our arrangement |

That last row is the one that matters most. After a single
`SetVirtualSelectConfigs` call: `keepAlwaysOpen` false, `showDropboxAsPopup`
true, the list gone from our popover. The component silently reverts to ODC's
portal-to-`<body>` popup — every login-scoped rule stops matching, because a
portaled overlay escapes the scope.

The five that work are untouched. The rest are bridged by wrapping the
**instance's own methods**, so a consumer calls the stock client actions with no
special casing:

- `open`/`close` drive our popover; the originals are not called at all.
- `validation()` still runs, then is mirrored: `not-valid` onto the trigger,
  where `.dropdown-empty-trigger.input.not-valid` was already waiting, and a
  sibling `<span class="validation-message">`.
- `disable`/`enable` add the class to the wrapper *and* the trigger — the CSS
  keys on the trigger, this script's guards read the wrapper — and move
  `tabindex`, or a disabled field stays a tab stop that opens on focus.
- `redraw()` is the single funnel every rebuilding path goes through
  (`setProviderConfigs`, `togglePopup`, `changeProperty`), so it is wrapped to
  re-inline afterwards. It defers through `AsyncInvocation`, so the repair polls
  for the rebuild rather than racing it.
- `togglePopup` is deliberately inert. It is a display-MODE switch, not
  open/close; this component always renders its list inline, so there is nothing
  for the setting to select between and the redraw only does damage.

### Two traps when testing this

`SetValues` takes a JSON array of **objects**, not of values: the method does
`optionsToSelect[0].value`, so `'["PT"]'` sets `undefined` and reports success.
`'[{"value":"PT"}]'` works. And `setValue`/`open` defer through
`AsyncInvocation`, so a synchronous read straight afterwards shows the old state
and looks like a no-op. Both cost a wrong diagnosis before being caught.

### The re-inline was throwing the consumer's configs away

Bridging `redraw()` stopped `SetVirtualSelectConfigs` from breaking the
component, but it did not make the action *work*: measured right after it
reported success, `noOptionsText` was back at its default. Our `inlineList()`
rebuilt the widget from a hand-copied list of about a dozen props — options,
placeholder, search text, multiple, zIndex — so the config the consumer had just
set survived the platform's redraw and was then discarded by our own re-init.

The fix is to stop hand-copying. `inst.configs.getProviderConfig()` is the
object the block itself hands VirtualSelect, and it already contains everything:
the full option records with their groups, descriptions and icons, every prompt,
the disabled flag, and any extensibility config merged in. Three properties are
overridden on top, and they are the three the component owns — `keepAlwaysOpen:
true`, `showDropboxAsPopup: false`, and `ele` as the element rather than the
`'#id'` selector the config carries. `dropboxWrapper` is deleted: the block's
config asks for the dropbox to be wrapped on `<body>`, which is precisely the
portal-escape this component exists to avoid.

Verified on the live widget: consumer config `"Nothing here"` survived,
`keepAlwaysOpen` true, list inside our popover, nothing on `<body>`, and the
selected value, prompt and search box all preserved across the rebuild.

Worth noting what this bought beyond the bug: the re-init is now faithful to the
block's real configuration. Option descriptions, icons and group names used to
be dropped on every inline pass, because the hand-written map kept only `label`
and `value`.

### Three things the open dropdown got wrong

Reported from screenshots: the gap under the trigger differs from the host, and
a search with no match shows no message. Measured with the popover open and
opening downward on both hosts — the second reading is the one nobody reported:

| open state | ODC Portal | ours (before) |
|---|---|---|
| gap below trigger | 8px | 4px |
| trigger border | `rgb(70,75,86)` — resting | `rgb(178,180,255)` |
| trigger shadow | `none` | `rgba(77,74,230,.6) 0 0 0 3px` |

**The gap** is 8, not 4. The CSS's own closed-state offset is `top: 44px` against
a 40px trigger, which reads as 4 and is where our constant came from — but the
host's script positions the OPEN popover itself, and puts it at 8.

**The focus ring on an open trigger is ours alone.** The rule exists in the
host's sheet:

    .dropdown-empty.is--open .dropdown-empty-button.input {
      border-color: var(--input-border-focus); box-shadow: var(--component-shadow-focus) }

and on the host nothing matches it, because its trigger carries
`dropdown-empty-trigger input medium secondary` and no `dropdown-empty-button`
class at all. We put that class on our trigger, so the rule fires and paints a
ring the host never shows. Removed from the trigger. Focus is in the search box
by then anyway, and that box draws its own ring on both.

**The empty state was a content bug, not a styling one.** The bundle already
carries all three rules for it, correctly scoped. They key on an inner `div`:

    .dropdown-empty-popover-content .vscomp-dropbox .vscomp-no-search-results div
      { font: var(--body-semi-bold-base); color: var(--text-primary) }

Our `noSearchResultsText` was the plain string "There are no options to show.",
so there was no inner div, nothing matched, and the text fell back to
virtual-select's own `color: rgb(51,51,51)` — dark grey on a dark panel, which is
why it read as missing rather than wrong. The host's value is markup:

    <div>No results found<div class='vscomp-no-search-results-helper-text'>Try searching with other keywords</div></div>

and `noOptionsText` is `<div>No options to show</div>`. Set both to the host's
strings; no CSS change was needed. Worth remembering as a shape: a rule whose
subject is a child element silently does nothing when the text arrives without
that child, and the failure looks like a missing style.

## Validation on submit

The host's copy, lifted from its own compiled bundles rather than written fresh:

| screen | field | message |
|---|---|---|
| Login | Input_Email | Please enter a valid email. |
| Login | Input_Password | This field is required. |
| SignUp | Input_Email | Please enter a valid email. |
| VerifyEmail | Input_FirstName | Please provide a valid first name. |
| VerifyEmail | Input_LastName | Please provide a valid last name. |
| VerifyEmail | country | Please provide a valid country. |
| VerifyEmail | Input_VerificationCode | Please enter a valid verification code. |
| VerifyEmail | Input_Password | Please enter a valid password. |
| VerifyEmail | Checkbox_Terms | You must agree with the terms and conditions to proceed. |

(The bundle also carries "Please provide a valid state." for a state dropdown we
do not have, and a variant of the terms line without "the".)

**How the host does it.** Decompiled from its signupactivation chunk, the shape
is one guard per field, after trimming every value:

    userSignupForm.firstName === "" && (
      widgets.get("Input_FirstName").validAttr = false,
      widgets.get("Input_FirstName").validationMessageAttr = "Please provide a valid first name.")

So plain `Valid` / `ValidationMessage` on the Input widget — the platform's own
properties. Two of its fields are not done that way:

- **The country dropdown** does not use a widget's valid attr at all. The host
  keeps a `countryDropdown_ValidationVar` record with `validAttr` and
  `validMessageAttr` and passes it into its own dropdown block. We deliberately
  do NOT copy that: `DropdownNotValid` is the platform's way in, it is now
  bridged, and adding parallel Valid/ValidationMessage parameters to
  DropdownField would be a second, private way of saying the same thing.
- **The terms checkbox** message is a Text widget styled
  `validation-message margin-bottom-6 text-align-left`, with
  `visible: !Checkbox_Terms.validAttr` — not a platform-rendered message. Its
  app sheet then hides the platform's own span inside a checkbox row and indents
  the Text one to clear the box:

      .checkbox-container span.validation-message { display: none }
      .checkbox-container .validation-message { margin-left: 29px; margin-top: 0 }

**What the host does NOT do**, which is worth knowing before copying it: on an
empty form it never reaches any of this. Its inputs carry `required`, its button
is `type="submit"` inside a real form, so the browser's native validation fires
first and shows "Please fill out this field." in its own bubble. Submitting the
host's form with every field empty produces zero `.validation-message` elements
and zero `not-valid` classes — measured. The copy above is reached only once the
native pass is satisfied.

Ours has no native `required`, so the guards run on the first click, which is
what was asked for.

**Expressions, not If nodes.** Each field is one pair of assignments whose
condition is inline, so every submit both sets and clears:

    EmailInput.Valid = Trim(EmailVar) <> ""
    EmailInput.ValidationMessage = If(Trim(EmailVar) = "", "Please enter a valid email.", "")

That avoids adding If nodes to the flow, and means a second submit after the
field is filled clears the message without any extra path. Passwords are
deliberately not trimmed — spaces are legitimate password characters.

### The error border the login layer was eating

Reported as "not the same" from two screenshots of the same submitted-empty
form. Measured on both, every field invalid:

| | ODC Portal | ours |
|---|---|---|
| input border | `rgb(239,78,56)` | `rgb(70,75,86)` — resting |
| terms checkbox | red box | black, no `not-valid` |
| terms message | tight under the consent text | 24px below the row, 0px above the next |

The input one is the same bug that already ate hover and focus, found a third
time. `mtsi` declares

    .pds-login .form-control { border: 1px solid <colour> !important; … }

and an `!important` SHORTHAND carries that importance into every longhand it
expands to. The design system's `.form-control[data-input].not-valid` is
(0,3,0) and not important, so inside the login column it loses outright. Eight
rules set a border on that input; that one wins.

It hid behind its own message: the copy appears under the field, so the field
reads as validated, and only side by side with the host does the missing border
show. Restored the same way as hover and focus — same scope, same tokens,
border-color only, since the error focus ring is a box-shadow and mtsi never
sets one.

Worth generalising: this layer smothers **every** state the design system
expresses through `border-color`. Hover, focus and now error have each been
found separately, by eye, long after shipping. Any future state on
`.form-control` inside `.pds-login` needs the same treatment, and none of them
fail loudly.

The checkbox is the portal's own mechanism — it sets `Checkbox_Terms.validAttr`
false, and `.checkbox.not-valid:before` (already in the bundle) paints the box.
Ours only flipped a variable for the message's visibility, so the box stayed
black.

The message placement is structural: `TermsContainer` carries
`margin-bottom: 24px`, so a message placed after it lands nearer the NEXT
checkbox than its own. The portal keeps it inside the consent block, which puts
the row's bottom margin after the message instead of before it.

### The password eye was anchored to the wrong edge

Reported as "the eye icon is out of place" once a validation message appeared
under the password field. The rule read:

    .pds-login-password-field .pds-login-password-eye { top: auto; bottom: 12px }

which centres the icon only while the field is exactly label + input:
24 + 8 + 40 = 72, and 72 - 12 - 16 = 44. The icon was never positioned against
the input at all — it was positioned against the bottom of the column, and the
two happened to coincide.

A message broke the coincidence. Measured on Login, before and after submit:

| | field height | computed `top` | icon vs input centre |
|---|---|---|---|
| before | 72px | 44px | 0 |
| after | 92px | 64px | +20px |

The field grew by exactly the message's 20px and the icon rode the bottom edge
down onto the border. Now `top: 44px; bottom: auto` — the same resting position
stated from the top, so anything appended below the input leaves it alone.

It still assumes the standard 24px label and 8px gap; a label wrapping to two
lines would move the input and not the icon. The durable fix is a relative
wrapper around the input ALONE with the icon inside it, which is what the host
does — its `.ds-input-with-icons-icons` is `position: absolute; top: 0;
height: 40px` inside a box that wraps only the input, so nothing below can
reach it. That is harness markup rather than CSS, which is why it was not done
here.

Same family as the border bug above: a value that is correct by coincidence in
one layout, in a stylesheet that has no way to say "align with that element".

### The country trigger: matching the screen over the stylesheet

`DropdownNotValid` was putting `not-valid` on our trigger, so it turned red
while the host's country box stayed at its resting border. Both submitted empty:
host `rgb(70,75,86)`, ours `rgb(239,78,56)`.

Neither is a bug exactly. The rule `.dropdown-empty-trigger.input.not-valid`
comes from the host's OWN sheet, so its design system does say an invalid
dropdown is red — its signup screen simply never sets the class, because it
validates that field through a private record passed into its block instead of
through `DropdownNotValid`.

Removed first, to match the screen. Then put back, by request: the red stays.
So this is a deliberate deviation from the host's *screen* that follows the
host's *stylesheet*, and it also keeps the dropdown consistent with every Input
on the same form, which all turn red. `applyValidation` carries the reasoning
above the line so the next person does not read it as an oversight and quietly
"fix" it in either direction.

Worth naming the general shape, since it cost two round trips: when a host's
screen and its design system disagree, "replicate the portal exactly" has two
readings and no amount of measuring settles it. That is a question worth asking
rather than a judgement worth making — but only once, with the evidence for both
sides laid out, which is what the measurements above were for.

## The dropdown lab screen

A screen in NeoLayoutCheck putting `DropdownField` next to a stock OutSystems UI
`DropdownSearch`, with a button per client action firing at both.

It was suggested early and deliberately not built first. Driving the thirteen
actions straight at the live component through `DropdownAPI` found every defect
faster than clicking buttons would have, and needed no authoring at all. What
that testing could NOT reach is the layer the lab exists for:

- **The client actions' own wrappers.** Calling `DropdownAPI.SetValues(id, json)`
  skips whatever the `DropdownSetValue` action does to its arguments — and that
  layer matters: the method reads `optionsToSelect[0].value`, so a JSON array of
  plain strings sets `undefined` and still reports success. Only the action knows
  the shape it is meant to send.
- **A place to poke afterwards.** Every finding above was measured once, by
  script, and is only as durable as the next change. A screen survives.

Stage one is the two widgets and their ids; the buttons follow. Both dropdowns
carry identical options, so a difference on screen is a difference in behaviour
rather than in data.

Worth recording about the ids, since it is the one non-obvious part: a stock
`DropdownSearch` exposes its own `.Id` directly, but ours is a block wrapping the
real widget, and the inner widget's id (`b2-InnerDropdown`) is generated — nothing
outside can predict or reach it. The block raises it on an initialized event, and
the consumer holds it in a variable. That is the whole reason `DropdownField` can
be driven by the platform's actions at all.

### What the lab found: a silent set leaves the trigger lying

The first thing the finished lab caught, and the reason it was worth building.
Both `DropdownSetValue` and `DropdownClear` default `silentOnChangedEvent` to
TRUE. Measured through the real client actions:

| after the action | ours | stock |
|---|---|---|
| Set value (Spain) — value | `ES` | `ES` |
| Set value (Spain) — on screen | "Select your country" | "Spain" |
| Clear — value | `""` | placeholder |
| Clear — on screen | "Portugal" | placeholder |

A stock `DropdownSearch` renders its selection inside virtual-select, so setting
the value repaints it. Ours renders the label in its own trigger, from a
variable the block fills in its OnChanged handler — so a silent set moves the
value and never tells the trigger.

**This is exactly what driving `DropdownAPI` directly could not find.** The
earlier script-level test passed `silentOnChangedEvent = false` explicitly,
because it was hand-written; the client action passes its own default. The bug
lives in the gap between the two, which is the layer the lab exists to cover.

Fixed by forcing the event on in the bridge — `setValue` and `clear` call their
originals with `false`. Repainting the trigger from the bridge was the
alternative and is worse: the label is framework-rendered, so a DOM write is
reverted on the next re-render ([[framework-rendered-attributes-are-not-js-state]]
is the same trap). Going through the event keeps variable and markup in step.

The cost, stated in the code: a consumer asking for a silent set does not get
one. For this component silence was never really on offer — it would just mean a
stale trigger.

### `SetVirtualSelectConfigs`: not our bug

Worth recording because it looked like one. After the action ran, ours still
showed its default `noOptionsText`. The lab settled it in one read: BOTH
instances received `{"noOptionsSelectedText":"Nothing here"}`, and neither
applied it — the stock one still read "There are no options to show.". The
config arrives; `noOptionsSelectedText` simply is not the key that drives that
text. Ours kept `keepAlwaysOpen: true`, its list inline and its value intact, so
the re-inline repair is holding.

Having the stock widget beside ours is what made that a ten-second answer
instead of an investigation.

### The three console errors, closed

`TypeError: k is not a function`, three of them, from anonymous scripts with
document-level listeners, on every screen including ones with no dropdown. They
are gone — Login, VerifyEmail and DropdownLab all clean. The console reader was
verified working at the same time (a probe log and error both came back), so
this is not a measurement artifact.

No attribution. Something between harness 254 and 268 stopped them, and guessing
which change would be inventing a cause. Recorded here so that if they return
there is a starting point rather than a rediscovery.

### The search magnifier: centred, but the wrong colour

Reported as the icon not looking centred in the expanded dropdown. It is
centred, and the first measurement said otherwise because it was read wrong:
the computed `top` is 19px and the `transform: translateY(-50%)` on the very
next line was ignored. With the transform counted, ours and the host agree
exactly — 40px container, top 19px, height 16px, left 12px, translate -8px,
icon centre and container centre on the same pixel, same SVG content hash.

    ours   container centre 268   icon centre 268   offset 0
    host   container centre  68   icon centre  68   offset 0

What IS wrong is the colour, and it only shows in a theme the host does not
have. The icon is drawn as a `content` url, and an image arriving that way is
opaque to CSS: the `color: var(--icon-primary)` in the same rule has nothing to
tint, so the asset's own `fill="#B3BAC4"` renders. That is the dark theme's icon
grey, baked into the file. The host's identity pages are dark only, so it is
always right there. Our light theme puts a pale grey on a white search box,
about 2:1 against the background where `--icon-primary` (#4c525d) gives about
7.5:1 — visibly washed out next to the stock DropdownSearch on the lab screen.

Fixed in `compat/neo-odc-compat.css` by painting the box with the token and
masking the glyph out of it. Three declarations; width, height, left, top and
the transform still come from the extracted rule, which is where the geometry
belongs. No second asset, the same reasoning as the corner artwork.

Two things worth keeping:

- **`neobase.py` greps the WHOLE file for asset urls, comments included.** The
  first build of this change failed with `relative asset url() would not resolve
  in ODC: ['...']` because the comment contained a literal url-paren example.
  The guard was right to be blunt; the prose was wrong. Write about urls without
  writing one.
- A `content` url cannot be recoloured. Any icon that has to follow a token must
  be a mask, or an inline SVG using `currentColor`. Worth checking wherever the
  bundle draws an icon through `content`, since each one is a light-theme bug
  waiting for a screen that uses it.

## DropdownField's OptionalConfigs: four fields pass through, two did not

`DropdownOptionalConfigs` has six fields, confirmed against the OutSystemsUI
structure rather than guessed:

| field | type |
|---|---|
| `AllowMultipleSelection` | Boolean |
| `IsDisabled` | Boolean |
| `NoResultsText` | Text |
| `SearchPrompt` | Text |
| `NoOptionsText` | Text |
| `SanitizeDropdownValues` | Boolean |

When the two empty-state texts were added, the inner DropdownSearch widget's
`OptionalConfigs` was rewritten as a whole record literal. Four fields were
wired to the block's own parameter and two were written as string constants:

    NoResultsText:  "<div>No results found<div class='vscomp-no-search-results-helper-text'>Try searching with other keywords</div></div>"
    NoOptionsText:  "<div>No options to show</div>"

A consumer setting either of those got no error and no effect. The block's
parameter accepted the value and the expression threw it away.

Proving the other four still arrive needed a runtime read, because the
compile-time expression only tells you what was *written* — and two of the six
sit at their type defaults (`False`), so a field that was never wired and a
field that was wired but left alone are indistinguishable in the DOM.

`DropdownLab` was given `{ SearchPrompt: "LAB-SearchPrompt",
SanitizeDropdownValues: False }` on both dropdowns — a Text and a Boolean, the
Boolean chosen because its platform default is `True`, so `False` arriving is
only explicable as a pass-through. Read back off the OSUI instances:

    ours   SearchPrompt "LAB-SearchPrompt"   SanitizeDropdownValues false
    stock  SearchPrompt "LAB-SearchPrompt"   SanitizeDropdownValues false

Ours is the instance carrying `__neoBridged`; the search input's `placeholder`
in the DOM agrees on both. So the record literal does reach the widget intact,
and a Boolean survives it without being coerced.

That leaves the two constants, which the expression settles on its own:
`AllowMultipleSelection` and `IsDisabled` are both `OptionalConfigs.<field>`.
Four of six were fine; the two empty-state texts were the whole defect.

The attempted fix was to make them overridable with the portal text as the
fallback. It does not work, and the attempt is worth recording because both
halves of it failed for different reasons.

**The sentinel was wrong.** `If(OptionalConfigs.NoResultsText = "", "<portal
text>", OptionalConfigs.NoResultsText)` never takes the default branch. The
`DropdownOptionalConfigs` attributes are not empty by default:

| attribute | default |
|---|---|
| `NoResultsText` | `"There are no options to show."` |
| `NoOptionsText` | `"There are no options to show."` |
| `SearchPrompt` | `"Search..."` |
| `AllowMultipleSelection`, `IsDisabled`, `SanitizeDropdownValues` | `False` |

A consumer who sets nothing still sends the OSUI text, so the condition is
always false and the else-branch forwards it. Published as 195, the block lost
the portal empty state entirely and rendered the OSUI one-liner. The only
warning of that was the runtime read; the expression looked correct, validated
clean, and its true-branch was byte-identical to what had worked before.

**The corrected sentinel cannot be written through Mentor.** Comparing against
`"There are no options to show."` instead needs either two conditions joined by
`or` (to keep covering `""`) or, at minimum, a single `If` whose true-branch is
the HTML string. Mentor's argument API rejects both: it parses a record-literal
field value itself, and it cannot handle an `If` whose branches are anything
beyond a bare literal or identifier, nor an HTML string containing
`class='...'`, reporting "Missing colon separator in record field". It refused
even to restore the plain constants it had written minutes earlier.

That last point is the trap. The API's ability to write a given expression is
not stable across calls — the `= ""` version went in fine, and afterwards
nothing of the same shape would go in, including a revert. Do not assume you can
undo through the route you came in by.

Rolled back by loading revision 194 and republishing it as 196. Nothing but this
expression changed between the two, and no element identity moved, so the
consumer's reference survives — unlike the block-rename case further up, where
an earlier revision cost the consumer both the reference and the widget.

**Decided against pursuing it.** Making these two fields overridable would need
Service Studio's expression editor, and the feature was never asked for — it came
out of the audit and cost a broken release on the way. The block exists to
reproduce the portal, and the portal has exactly one empty state. `NoResultsText`
and `NoOptionsText` stay constants; `DropdownField`'s `OptionalConfigs` parameter
carries four meaningful fields, not six. Anyone reading this later: that is the
intended design, not an oversight to fix.

One correction to the pass-through evidence above: `SanitizeDropdownValues`
defaults to `False`, not `True`, so setting it to `False` proved nothing. The
pass-through conclusion stands on `SearchPrompt` — default `"Search..."`,
observed `"LAB-SearchPrompt"` — and on the expression text itself, which wires
`AllowMultipleSelection` and `IsDisabled` to the parameter. Pick a sentinel by
reading the declared default, not by assuming it.

## Console sweep

Login, SignUp, VerifyEmail, ResetPassword, Home and DropdownLab, each loaded in
a fresh tab and then exercised — empty-form submit on all four auth screens, the
password reveal, the country dropdown, and all fourteen client-action buttons on
the lab. Zero console errors on every screen.

Network was checked separately, because a 404 on an asset never reaches the
console. All 60 requests of a DropdownLab load return 200, including the two
library assets worth watching (`NeoDesignSystem.NeoBase` CSS and
`NeoDesignSystem.icsearch.svg`).

Two false positives, both mine, worth naming so they are not rediscovered:

- **`/NeoLayoutCheck/v2/logs` 404.** The platform's client telemetry endpoint is
  POST-only and answers 200; the 404 came from a sweep that re-fetched every
  resource with GET. Probe with the method the page actually used.
- **A 404 in the console after a clean load.** The pane's console buffer is per
  tab, not per navigation, so an error from an earlier page on the same tab is
  still listed. Cross-check against the network log for the current load before
  believing it.
