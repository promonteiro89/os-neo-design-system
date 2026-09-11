# Neo utilities vs OutSystems UI — class-name collisions

Generated on 2026-08-01 by `tools/collisions.py`.

* Neo utility classes: **581** (from `src/03-utilities/`)
* OutSystems UI classes: **955** (version **2.16.0**, `outsystems-ui-theme.css`)
* Shared names: **140**
* Of those, value-identical: **100** — harmless
* Value-different: **40** — real behaviour change

Whichever stylesheet loads **last** wins. Both files are flat utility
layers with no specificity tricks, so ordering is the only factor.

## Real behaviour changes

Watch `.text-primary` and `.text-secondary` especially: the two systems
mean *opposite* things by them. In Neo they are body and muted text; in
OutSystems UI they are the brand colours. Loading Neo's utilities after
OutSystems UI turns brand-blue text near-black on existing screens.

| Class | Property | Neo | OutSystems UI |
| --- | --- | --- | --- |
| `.background-neutral-0` | `background-color` | `#f9fafb` | `#ffffff` |
| `.background-neutral-1` | `background-color` | `#eef1f3` | `#f8f9fa` |
| `.background-neutral-10` | `background-color` | `#181a1f` | `#101213` |
| `.background-neutral-2` | `background-color` | `#e3e7eb` | `#f1f3f5` |
| `.background-neutral-3` | `background-color` | `#ced4db` | `#e9ecef` |
| `.background-neutral-4` | `background-color` | `#bbc2cc` | `#dee2e6` |
| `.background-neutral-5` | `background-color` | `#a8b0bc` | `#ced4da` |
| `.background-neutral-6` | `background-color` | `#868e9c` | `#adb5bd` |
| `.background-neutral-7` | `background-color` | `#686f7d` | `#6a7178` |
| `.background-neutral-8` | `background-color` | `#4c525d` | `#4f575e` |
| `.background-neutral-9` | `background-color` | `#32363e` | `#272b30` |
| `.font-bold` | `font-weight` | `600` | `700` |
| `.font-semi-bold` | `font-weight` | `500` | `600` |
| `.font-size-base` | `(different properties)` | `font: var(--font-weight-0) var(--font-size-3` | `font-size: 16px` |
| `.font-size-display` | `(different properties)` | `font: var(--font-weight-2) var(--font-size-8` | `font-weight: 600; line-height: 1.25` |
| `.font-size-s` | `(different properties)` | `font: var(--font-weight-0) var(--font-size-2` | `font-size: 14px` |
| `.font-size-xs` | `(different properties)` | `font: var(--font-weight-0) var(--font-size-1` | `font-size: 12px` |
| `.heading1` | `(different properties)` | `font: var(--font-weight-2) var(--font-size-7` | `font-weight: 600; line-height: 1.25` |
| `.heading2` | `(different properties)` | `font: var(--font-weight-2) var(--font-size-6` | `font-weight: 600; line-height: 1.25` |
| `.heading3` | `(different properties)` | `font: var(--font-weight-2) var(--font-size-5` | `font-weight: 600; line-height: 1.25` |
| `.heading4` | `(different properties)` | `font: var(--font-weight-2) var(--font-size-4` | `font-weight: 600; line-height: 1.25` |
| `.heading5` | `(different properties)` | `font: var(--font-weight-2) var(--font-size-4` | `font-weight: 600; line-height: 1.25` |
| `.heading6` | `(different properties)` | `font: var(--font-weight-2) var(--font-size-4` | `font-weight: 600; line-height: 1.25` |
| `.text-error` | `color` | `#ce230c` | `#dc2020` |
| `.text-info` | `color` | `#0c6ace` | `#017aad` |
| `.text-neutral-0` | `color` | `#f9fafb` | `#ffffff` |
| `.text-neutral-1` | `color` | `#eef1f3` | `#f8f9fa` |
| `.text-neutral-10` | `color` | `#181a1f` | `#101213` |
| `.text-neutral-2` | `color` | `#e3e7eb` | `#f1f3f5` |
| `.text-neutral-3` | `color` | `#ced4db` | `#e9ecef` |
| `.text-neutral-4` | `color` | `#bbc2cc` | `#dee2e6` |
| `.text-neutral-5` | `color` | `#a8b0bc` | `#ced4da` |
| `.text-neutral-6` | `color` | `#868e9c` | `#adb5bd` |
| `.text-neutral-7` | `color` | `#686f7d` | `#6a7178` |
| `.text-neutral-8` | `color` | `#4c525d` | `#4f575e` |
| `.text-neutral-9` | `color` | `#32363e` | `#272b30` |
| `.text-primary` | `color` | `#181a1f` | `#1068eb` |
| `.text-secondary` | `color` | `#686f7d` | `#303d60` |
| `.text-success` | `color` | `#015b35` | `#29823b` |
| `.text-warning` | `color` | `#895b01` | `#e9a100` |

## Value-identical (safe to ignore)

Almost entirely the t-shirt spacing scale — both systems resolve
`xs/s/base/m/l/xl/xxl` to 4/8/16/24/32/40/48px.

`.absolute-center`, `.font-regular`, `.margin-base`, `.margin-bottom-base`, `.margin-bottom-l`, `.margin-bottom-m`, `.margin-bottom-s`, `.margin-bottom-xl`, `.margin-bottom-xs`, `.margin-bottom-xxl`, `.margin-l`, `.margin-left-base`, `.margin-left-l`, `.margin-left-m`, `.margin-left-s`, `.margin-left-xl`, `.margin-left-xs`, `.margin-left-xxl`, `.margin-m`, `.margin-right-base`, `.margin-right-l`, `.margin-right-m`, `.margin-right-s`, `.margin-right-xl`, `.margin-right-xs`, `.margin-right-xxl`, `.margin-s`, `.margin-top-base`, `.margin-top-l`, `.margin-top-m`, `.margin-top-s`, `.margin-top-xl`, `.margin-top-xs`, `.margin-top-xxl`, `.margin-x-base`, `.margin-x-l`, `.margin-x-m`, `.margin-x-s`, `.margin-x-xl`, `.margin-x-xs`, `.margin-x-xxl`, `.margin-xl`, `.margin-xs`, `.margin-xxl`, `.margin-y-base`, `.margin-y-l`, `.margin-y-m`, `.margin-y-s`, `.margin-y-xl`, `.margin-y-xs`, `.margin-y-xxl`, `.padding-base`, `.padding-bottom-base`, `.padding-bottom-l`, `.padding-bottom-m`, `.padding-bottom-s`, `.padding-bottom-xl`, `.padding-bottom-xs`, `.padding-bottom-xxl`, `.padding-l`, `.padding-left-base`, `.padding-left-l`, `.padding-left-m`, `.padding-left-s`, `.padding-left-xl`, `.padding-left-xs`, `.padding-left-xxl`, `.padding-m`, `.padding-right-base`, `.padding-right-l`, `.padding-right-m`, `.padding-right-s`, `.padding-right-xl`, `.padding-right-xs`, `.padding-right-xxl`, `.padding-s`, `.padding-top-base`, `.padding-top-l`, `.padding-top-m`, `.padding-top-s`, `.padding-top-xl`, `.padding-top-xs`, `.padding-top-xxl`, `.padding-x-base`, `.padding-x-l`, `.padding-x-m`, `.padding-x-s`, `.padding-x-xl`, `.padding-x-xs`, `.padding-x-xxl`, `.padding-xl`, `.padding-xs`, `.padding-xxl`, `.padding-y-base`, `.padding-y-l`, `.padding-y-m`, `.padding-y-s`, `.padding-y-xl`, `.padding-y-xs`, `.padding-y-xxl`

## Avoiding the problem

Use `compat/neo-osui-bridge.css` instead of Neo's colour and typography
utilities. The bridge re-skins OutSystems UI widgets through its own
variables, so you get the Neo look without introducing any class that
OutSystems UI already owns. If you do want Neo's utilities, the safe
subset is `src/03-utilities/` minus `colors.css` and `typography.css`.
