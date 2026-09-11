# What an ODC portal page is actually made of

Captured 2026-09-03, 1440x900, light theme, logged in. Two pages, counted by rendered element.

| Layer | `/usersaccess/` | `/logic/` | distinct classes | status |
| --- | ---: | ---: | ---: | --- |
| OutSystems UI widgets | **320** | 26 | 49 | restyled by `1-osui-reskin.css` — unverified |
| Platform wrappers (`OSBlockWidget`, `OSInline`, `ph`) | 288 | 107 | 6 | runtime, nothing to build |
| Host shell (`unified-*`) | 279 | 279 | 61 | **built and verified** |
| Utilities (`display-flex`, `align-*`, `margin-*`, `line-clamp`, …) | 257 | ~700 | 24–40 | partial subset shipped |
| Fusion components (`fusion-*`) | **252** | 8 | 32 | **not built** |
| Icons (`pds-icon`, `svg-code`, `icon-base/-small`) | 138 | ~110 | 4 | **not built at all** |
| App-specific (`app-representation-*`, `user-*`) | 136 | ~110 | 30 | portal's own app, not design system |
| Page frame (`nds-layout`, `page-header-*`, `theme-grid-container`) | 26 | 23 | 23 | **built** (rev 22–24) |
| `ds-*` legacy components | 11 | 11 | 2 | effectively dead — see below |
| **Total elements** | **1941** | **1503** | 231 / 206 | |

## Four findings that change the plan

**1. The `ds-*` legacy component library is dead.** `old-neo-design-system.css` carries 1114 `ds-*`
selectors. Exactly **two** render on either page: `ds-avatar` and `ds-page-title-left-element-wrapper`.
We do not need to port it. Only its *layout* half (`page-header-*`, `nds-layout`, `main-content-*`)
is live, and that is already done.

**2. Fusion components ARE used — it is only Fusion *layout* that is not.** `/usersaccess/` renders
252 elements across 32 `fusion-*` classes: `fusion-badge`, `fusion-dropdown-item`,
`fusion-pagination`, `fusion-icon`, `fusion-empty-state`. So the component extraction work stands;
the `fusion-layout*` family was the dead part. Usage is page-dependent (`/logic/` renders only
`fusion-empty-state`).

**3. Icons are the largest completely unbuilt layer.** `pds-icon` alone appears 51–100+ times per
page — more than any other single visual component — and we have not touched it.

**4. OutSystems UI widgets are the single biggest layer.** 320 elements on `/usersaccess/`: `avatar`,
`btn`, `table*`, `form-control`, `input-*`, `pagination*`, `osui-tooltip*`, `list*`. The portal does
not reimplement these — it restyles OSUI, which is exactly what `1-osui-reskin.css` does. That file
has never been checked against the portal's rendered result.

## Coverage

Built and verified: shell + page frame + tokens ~= **305 of 1941 elements (16%)**.
The remaining 84% is OSUI widgets, utilities, icons and Fusion components.

That is the honest answer to "why are there still gaps": the two layers built so far are the
structurally hardest but numerically smallest. The three layers that make up most of what a person
actually sees on the page have not been done.

## Files

* `logic.classes.txt` — full class census for `/logic/`, `<class>:<count>`.
