# Reskin verification — OutSystems UI widgets

Portal `/usersaccess/` vs our harness, both 1440x900 light, specimens built from the portal's own
markup. Run with `tools/probe/widget-probe.js`.

## Result

| Widget | Verdict |
| --- | --- |
| `.btn` / `.btn-primary` | **identical on all 12 probed properties** |
| `.form-control[data-input]` | identical (bg, border, radius, height, colour, font) |
| `.table` | identical (radius, border, shadow, colour, font) |
| `.table-header th` padding | **portal `0 24px` / ours `0 20px`** |
| `.table-row td` padding | **portal `4px 24px` / ours `8px 24px`** |
| `.avatar` | identical (32px, inline-flex, amber, uppercase) |
| `.avatar-format-circle` (`ds-avatar`) | **absent from our CSS entirely** |

Buttons — the most-used widget on the page — match on background, border, radius, shadow, colour,
display, font, gap, height, padding and rendered size. The reskin is broadly right.

## Two "defects" that were my measurement errors

Both were caught only by asking *which stylesheet supplied the value*, and both would have sent me
chasing a fix for something that was already correct.

**`.avatar` is not 24px.** The portal's header avatar renders 24x24 with `border-radius: 50%` — from
`.unified-header-login-avatar span` in `prod.unified.css`. That is the **shell**, not the avatar
widget. The widget itself is `32px; inline-flex` from `NeoDesignSystem.OutSystemsUITheme`, which is
exactly what we render.

**`.table` is not transparent.** That value comes from `usersaccess.Users_Th` — the Users *screen's*
own stylesheet. The design system's rule is `background-color: var(--surface-1-default)` (white),
which is what we ship. A portal page loads `<app>.<Screen>_Th` files that are not design system at
all; reading rendered values without checking their origin invents defects.

## Two real gaps

1. **`ds-avatar` family missing.** `avatar-format-circle`, `avatar-color-*`, `avatar-size-*`,
   `ds-avatar` — **0 rules** in anything we ship, present in `old-neo-design-system.css`. It is one of
   only two `ds-*` classes the portal actually renders (10 elements on `/usersaccess/`), so it is
   worth extracting despite the rest of the `ds-*` library being dead.

2. **Table cell padding.** Measured on both, real difference. The portal renders the
   `--space-none/--space-m` values (`0 24px`, `4px 24px`); we render `--space-5`-based values
   (`0 20px`, `8px 24px`). Token scales are byte-identical between portal and our app, so this is a
   *rule* difference, not a token one.

## Open question — do not act on this yet

The portal layers at least four design-system stylesheets:

```
NeoDesignSystem.OutSystemsUITheme     NeoDesignSystem.Legacy_NeoTheme
NeoDesignSystem.Old_NeoDesignSystem   NeoDesignSystem.NeoDesignSystem
```

`tools/osui_reskin.py` builds our reskin from `old-neo-design-system.css` only. We also hold
`reference/raw/outsystems-ui-theme.css` (434 KB, 3242 rules) which is currently **unused**, and which
carries the `--space-none/--space-m` values the portal renders for table cells.

That suggests the reskin may be built from the layer the portal overrides — but an attempt to
attribute each computed property to its winning stylesheet was **inconclusive**: the resolver could
not expand nested `var()` or normalise shorthands, and returned no winner for several properties.

Do not rebuild the reskin on that hypothesis until attribution is done properly. Buttons already
match perfectly, which argues the current source is at least largely correct; a wholesale swap could
regress more than it fixes.

---

## Audit of `outsystems-ui-theme.css` — RESOLVED, hypothesis disproven

The open question above was whether `tools/osui_reskin.py` builds from the wrong
source: it reads `old-neo-design-system.css`, while `reference/raw/outsystems-ui-theme.css`
(434 KB) sits unused, and `.ph:empty { display: none }` was found only in the latter.

**Answer: the source file is correct. Do not swap it.**

`outsystems-ui-theme.css` is **OutSystems UI's own stock theme**, not Neo's reskin. Two
things give it away, and the second is conclusive:

1. Its rules use OSUI's token vocabulary — `--color-neutral-0`, `--border-size-s`,
   `--font-size-xs`, `--space-m` — whereas Neo's reskin uses Neo's — `--surface-1-default`,
   `--text-primary`, `--space-5`.

2. Every rule it appears to be "missing" is **already served to our app by the platform**.
   Probed live in the running harness:

   | selector | served by |
   | --- | --- |
   | `.form-control[data-input]:hover` / `:focus` | `OutSystemsUI.OutSystemsUI` + our NeoBase |
   | `.form-control.input-small[data-input]` | `OutSystemsUI.OutSystemsUI` |
   | `.pagination-button`, `.pagination-button.is--active` | `OutSystemsUI.OutSystemsUI` |
   | `.table-row:hover td`, `.table-row-small td` | `OutSystemsUI.OutSystemsUI` |
   | `.table-header th.sorted` | `OutSystemsUI.OutSystemsUI` + our NeoBase |

So of 2979 rules the audit flagged as absent from NeoBase, essentially all are either
OSUI base layout (device/RTL/native variants — platform-served) or OSUI stock theme
(also platform-served). Shipping them would duplicate what ODC already sends.

**Exactly one rule was genuinely missing: `.ph:empty { display: none }`** — already
recovered as `.neo-ph:empty` in compat section 9, which is what closed the 105px vs 73px
page-header gap.

### Why the table padding still differed

The portal's `NeoDesignSystem.OutSystemsUITheme` is a *customised* OSUI theme whose
`.table-header th` uses `var(--space-m)` (24px). Our app receives **stock** OSUI, then our
Neo reskin applies `var(--space-5)` (20px). Pinning the portal's measured values in compat
section 8 is the correct fix; importing 434 KB of stock theme would not have been.

### Audit tooling note

`tools/audit_osui_theme.py` initially reported our file as 493 rules against an actual
1535. `split_top_level` counts braces and does not skip comments — its usual inputs are
minified vendor CSS with none, but `neobase.css` is full of prose containing braces
(`.ph:empty { display: none }` inside an explanation), which desynchronises the counter.
The audit now strips comments before parsing. Any tool pointed at our own generated CSS
needs to do the same.
