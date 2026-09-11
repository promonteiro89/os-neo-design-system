# Audit

Generated on 2026-09-11.

Every `var()` reference in the bundle checked against every custom property definition in it.

## 1. Broken references — 3 found

Referenced with no fallback, and defined **nowhere** — not in this bundle, not in any other stylesheet the portal loads. Genuine bugs in the upstream bundle: the browser drops the whole declaration. `compat/neo-compat.css` defines them; see that file for the reasoning behind each value.

| Token | Referenced by |
| --- | --- |
| `--border-focus-default` | `.fusion-accordion-item__header:focus-visible` |
| `--box-shadow-0` | `.fusion-carousel .splide__arrow` |
| `--icon-default` | `.fusion-icon--color-icon-default` |

## 1b. Owned by another portal stylesheet — 5 found

Not bugs. These belong to OutSystems UI or the legacy Neo theme, so they resolve for free in any app that loads those — which every OutSystems app does, since OutSystems UI is the base theme. `compat/neo-compat.css` still defines them so the bundle works standalone; the values agree with the owners.

| Token | Owner | Value there |
| --- | --- | --- |
| `--border-size-none` | `outsystems-ui-theme.css` | `0` |
| `--border-size-s` | `outsystems-ui-theme.css` | `1px` |
| `--space-base` | `legacy-neo-theme.css` | `16px` |
| `--space-m` | `legacy-neo-theme.css` | `24px` |
| `--space-s` | `legacy-neo-theme.css` | `8px` |

## 2. Provided by the ODC portal shell — 3 found

Set by the portal chrome (unified header / side nav / banner), not by this stylesheet. A standalone app has no such chrome, so `compat/neo-compat.css` defaults them to `0px`.

| Token | Referenced by |
| --- | --- |
| `--unified-aside-width-expanded` | `body:has(fusion-layout) #reactContainer` |
| `--unified-banner-height` | `body:has(fusion-layout) #reactContainer` |
| `--unified-header-height` | `.screen-container.fade-leave`<br>`body:has(fusion-layout) #reactContainer` |

## 3. Component-scoped locals — 32 found

Defined on the component element itself rather than on `:root`, which is correct and intentional — they are per-instance knobs (panel widths, layout max-width, carousel progress set from JS). Nothing to fix; listed so you do not mistake them for missing.

| Token | Referenced by |
| --- | --- |
| `--fusion-dropdown-empty-trigger-background-default` | `.fusion-dropdown-empty--open .fusion-dropdown-empty__trigger--type-button,.fusio`<br>`.fusion-dropdown-empty--open .fusion-dropdown-empty__trigger--type-button.fusion`<br>`.fusion-dropdown-empty__trigger--type-accent.fusion-dropdown-empty__trigger--acc`<br>`.fusion-dropdown-empty__trigger--type-accent.fusion-dropdown-empty__trigger--dis` |
| `--fusion-layout-sticky-top-offset` | `.fusion-layout__content` |
| `--illustration-blue-1` | `.fusion-illustration--empty-new-app`<br>`:root[data-theme=dark] .fusion-illustration--empty-new-app` |
| `--illustration-green-1` | `.fusion-illustration--impact-analysis`<br>`:root[data-theme=dark] .fusion-illustration--impact-analysis` |
| `--illustration-green-2` | `.fusion-illustration--impact-analysis`<br>`:root[data-theme=dark] .fusion-illustration--impact-analysis` |
| `--illustration-green-3` | `.fusion-illustration--impact-analysis`<br>`:root[data-theme=dark] .fusion-illustration--impact-analysis` |
| `--illustration-green-4` | `.fusion-illustration--impact-analysis`<br>`:root[data-theme=dark] .fusion-illustration--impact-analysis` |
| `--illustration-green-5` | `.fusion-illustration--impact-analysis`<br>`:root[data-theme=dark] .fusion-illustration--impact-analysis` |
| `--illustration-indigo-1` | `.fusion-illustration--broken-link`<br>`.fusion-illustration--connect-external-systems`<br>`.fusion-illustration--create-process`<br>`.fusion-illustration--empty-new-app` |
| `--illustration-indigo-10` | `.fusion-illustration--connect-external-systems`<br>`.fusion-illustration--empty-new-app`<br>`.fusion-illustration--generic-empty-state`<br>`.fusion-illustration--impact-analysis` |
| `--illustration-indigo-11` | `.fusion-illustration--connect-external-systems`<br>`.fusion-illustration--empty-new-app`<br>`.fusion-illustration--generic-empty-state`<br>`.fusion-illustration--impact-analysis` |
| `--illustration-indigo-12` | `.fusion-illustration--connect-external-systems`<br>`.fusion-illustration--empty-new-app`<br>`.fusion-illustration--generic-empty-state`<br>`.fusion-illustration--impact-analysis` |
| `--illustration-indigo-13` | `.fusion-illustration--connect-external-systems`<br>`.fusion-illustration--generic-empty-state`<br>`.fusion-illustration--impact-analysis`<br>`.fusion-illustration--mobile-experience` |
| `--illustration-indigo-14` | `.fusion-illustration--generic-empty-state`<br>`.fusion-illustration--impact-analysis`<br>`.fusion-illustration--mobile-experience`<br>`:root[data-theme=dark] .fusion-illustration--generic-empty-state` |
| `--illustration-indigo-15` | `.fusion-illustration--generic-empty-state`<br>`:root[data-theme=dark] .fusion-illustration--generic-empty-state` |
| `--illustration-indigo-16` | `.fusion-illustration--generic-empty-state`<br>`:root[data-theme=dark] .fusion-illustration--generic-empty-state` |
| `--illustration-indigo-17` | `.fusion-illustration--generic-empty-state`<br>`:root[data-theme=dark] .fusion-illustration--generic-empty-state` |
| `--illustration-indigo-18` | `.fusion-illustration--generic-empty-state`<br>`:root[data-theme=dark] .fusion-illustration--generic-empty-state` |
| `--illustration-indigo-19` | `.fusion-illustration--generic-empty-state`<br>`:root[data-theme=dark] .fusion-illustration--generic-empty-state` |
| `--illustration-indigo-2` | `.fusion-illustration--broken-link`<br>`.fusion-illustration--connect-external-systems`<br>`.fusion-illustration--create-process`<br>`.fusion-illustration--empty-new-app` |
| `--illustration-indigo-3` | `.fusion-illustration--broken-link`<br>`.fusion-illustration--connect-external-systems`<br>`.fusion-illustration--create-process`<br>`.fusion-illustration--empty-new-app` |
| `--illustration-indigo-4` | `.fusion-illustration--broken-link`<br>`.fusion-illustration--connect-external-systems`<br>`.fusion-illustration--empty-new-app`<br>`.fusion-illustration--error-404` |
| `--illustration-indigo-5` | `.fusion-illustration--broken-link`<br>`.fusion-illustration--connect-external-systems`<br>`.fusion-illustration--empty-new-app`<br>`.fusion-illustration--generic-empty-state` |
| `--illustration-indigo-6` | `.fusion-illustration--connect-external-systems`<br>`.fusion-illustration--empty-new-app`<br>`.fusion-illustration--generic-empty-state`<br>`.fusion-illustration--impact-analysis` |
| `--illustration-indigo-7` | `.fusion-illustration--connect-external-systems`<br>`.fusion-illustration--empty-new-app`<br>`.fusion-illustration--generic-empty-state`<br>`.fusion-illustration--impact-analysis` |
| `--illustration-indigo-8` | `.fusion-illustration--connect-external-systems`<br>`.fusion-illustration--empty-new-app`<br>`.fusion-illustration--generic-empty-state`<br>`.fusion-illustration--impact-analysis` |
| `--illustration-indigo-9` | `.fusion-illustration--connect-external-systems`<br>`.fusion-illustration--empty-new-app`<br>`.fusion-illustration--generic-empty-state`<br>`.fusion-illustration--impact-analysis` |
| `--layout-content-max-width` | `.fusion-layout`<br>`.fusion-layout--type--widescreen` |
| `--side-panel-collapsed-width` | `.fusion-side-panel`<br>`.fusion-side-panel--type-floating` |
| `--side-panel-expanded-width` | `.fusion-side-panel`<br>`.fusion-side-panel--size-small` |
| `--side-panel-toggle-right` | `.fusion-side-panel`<br>`.fusion-side-panel--open`<br>`.fusion-side-panel--type-floating` |
| `--side-panel-viewport-offset` | `.fusion-layout--reserve-side-panel-space .fusion-side-panel:not(.fusion-side-pan`<br>`.fusion-side-panel` |

## 4. External classes this bundle expects — 36 found

Class names the bundle styles *through* (as ancestors, siblings or descendants) but never defines itself. They come from the other stylesheets loaded alongside it in the portal — OutSystems UI and the older Neo/DS component CSS. If a Fusion component looks wrong in your app, check whether it is leaning on one of these.

`.app-representation-icon-type`, `.app-representation-type`, `.avatar`, `.btn`, `.desktop`, `.ds-card-style-default`, `.ds-card-style-ghost`, `.ds-card-type-checkbox`, `.ds-card-type-link`, `.ds-card-type-radio`, `.ds-card-type-selectable`, `.ds-tabs`, `.ds-tabs-content`, `.ds-tabs-content-tab`, `.ds-tooltip`, `.ghost`, `.is-overflow`, `.is-soft-responsive`, `.is-unified`, `.is-unified-tablet`, `.list`, `.metadata-container`, `.metadata-container-content`, `.metadata-container-label`, `.metadata-container-title`, `.noUi-rtl`, `.noUi-state-drag`, `.noUi-state-tap`, `.noUi-txt-dir-rtl`, `.ph`, `.phone`, `.skeleton-avatar-xxs`, `.skeleton-box`, `.svg-code`, `.tabs-content-wrapper`, `.vertical-align`

## 5. Defined but never used inside the bundle — 204 found

Not a bug. These are the public token API, meant to be consumed by *your* CSS. Listed so you know what is safe to drop if you trim the token set.

`--alert-error-background`, `--alert-error-border`, `--alert-error-icon`, `--alert-info-background`, `--alert-info-border`, `--alert-info-icon`, `--alert-success-background`, `--alert-success-border`, `--alert-success-icon`, `--alert-warning-background`, `--alert-warning-border`, `--alert-warning-icon`, `--avatar-amber`, `--avatar-blue`, `--avatar-image-background`, `--avatar-image-border`, `--avatar-lime`, `--avatar-orange`, `--avatar-red`, `--avatar-sky`, `--avatar-teal`, `--avatar-yellow`, `--badge-icon-negative`, `--badge-icon-success`, `--badge-icon-transitional`, `--badge-icon-warning`, `--border-info-default`, `--border-success-default`, `--border-warning-default`, `--breadcrumb-icon-separator`, `--breadcrumb-text-hover`, `--breadcrumb-text-pressed`, `--button-destructive-border-default`, `--button-destructive-border-disabled`, `--button-destructive-border-hover`, `--button-destructive-border-pressed`, `--button-destructive-icon-default`, `--button-destructive-icon-disabled`, `--button-destructive-text-disabled`, `--button-ghost-border-hover`, `--button-ghost-border-pressed`, `--button-group-border-default`, `--button-group-border-disabled`, `--button-group-border-hover`, `--button-group-border-pressed`, `--button-group-selected-border-default`, `--button-primary-icon-disabled`, `--button-social-background-default`, `--button-social-background-disabled`, `--button-social-background-hover`, `--button-social-background-pressed`, `--button-social-border-default`, `--button-social-border-disabled`, `--button-social-border-hover`, `--button-social-border-pressed`, `--button-social-icon-default`, `--button-social-icon-disabled`, `--card-disabled`, `--chart-cyan-hover`, `--chart-error-hover`, `--chart-info-hover`, `--chart-orange-hover`, `--chart-pink-hover`, `--chart-purple-hover`, `--chart-success-hover`, `--chart-warning-hover`, `--confirmation-message-overlay`, `--control-border-default`, `--control-border-disabled`, `--control-border-hover`, `--data-visualization-cyan-0`, `--data-visualization-cyan-1`, `--data-visualization-cyan-2`, `--data-visualization-cyan-4`, `--data-visualization-cyan-5`, `--data-visualization-orange-0`, `--data-visualization-orange-1`, `--data-visualization-orange-2`, `--data-visualization-orange-3`, `--data-visualization-orange-6`, `--data-visualization-pink-0`, `--data-visualization-pink-1`, `--data-visualization-pink-2`, `--data-visualization-pink-3`, `--data-visualization-pink-4`, `--data-visualization-pink-5`, `--data-visualization-pink-9`, `--data-visualization-purple-0`, `--data-visualization-purple-1`, `--data-visualization-purple-2`, `--data-visualization-purple-3`, `--data-visualization-purple-4`, `--data-visualization-purple-6`, `--data-visualization-purple-9`, `--data-visualization-semantic-blue-0`, `--data-visualization-semantic-blue-1`, `--data-visualization-semantic-blue-2`, `--data-visualization-semantic-blue-3`, `--data-visualization-semantic-blue-4`, `--data-visualization-semantic-blue-6`, `--data-visualization-semantic-blue-8`, `--data-visualization-semantic-blue-9`, `--data-visualization-semantic-green-0`, `--data-visualization-semantic-green-1`, `--data-visualization-semantic-green-2`, `--data-visualization-semantic-green-3`, `--data-visualization-semantic-green-4`, `--data-visualization-semantic-green-6`, `--data-visualization-semantic-green-9`, `--data-visualization-semantic-red-0`, `--data-visualization-semantic-red-1`, `--data-visualization-semantic-red-2`, `--data-visualization-semantic-red-3`, `--data-visualization-semantic-red-4`, `--data-visualization-semantic-red-6`, `--data-visualization-semantic-red-9`, `--data-visualization-semantic-yellow-0`, `--data-visualization-semantic-yellow-1`, `--data-visualization-semantic-yellow-2`, `--data-visualization-semantic-yellow-3`, `--data-visualization-semantic-yellow-4`, `--data-visualization-semantic-yellow-5`, `--data-visualization-semantic-yellow-6`, `--data-visualization-semantic-yellow-9`, `--divider-background-2`, `--helper-text-error`, `--helper-text-success`, `--helper-text-warning`, `--icon-ide-blue`, `--icon-ide-gray`, `--icon-ide-green`, `--icon-ide-inverse`, `--icon-ide-orange`, `--icon-ide-red`, `--icon-ide-yellow`, `--icon-selected`, `--icon-severity-critical`, `--icon-severity-low`, `--icon-severity-medium`, `--input-ghost-border-default`, `--input-ghost-border-disabled`, `--input-ghost-border-hover`, `--input-ghost-border-pressed`, `--input-text-placeholder`, `--label-text-default`, `--link-subtle-default`, `--link-subtle-disabled`, `--link-text-hover`, `--link-text-pressed`, `--opacity-0`, `--opacity-10`, `--opacity-100`, `--opacity-20`, `--opacity-30`, `--opacity-40`, `--opacity-50`, `--opacity-70`, `--opacity-80`, `--opacity-90`, `--orange-0`, `--orange-1`, `--orange-2`, `--orange-4`, `--orange-8`, `--orange-9`, `--orange-rgba-0`, `--page-layout`, `--popover-width-base`, `--popover-width-l`, `--popover-width-s`, `--popover-width-xs`, `--popup-overlay`, `--scrollbar-track`, `--size-1`, `--size-15`, `--size-18`, `--size-2`, `--size-20`, `--skeleton-background-1`, `--skeleton-line-height-0`, `--skeleton-line-height-1`, `--skeleton-line-height-2`, `--skeleton-line-height-3`, `--skeleton-line-height-4`, `--surface-1-hover`, `--surface-interactive-default`, `--surface-nav-hover`, `--surface-nav-pressed`, `--surface-nav-selected`, `--surface-neutral-disabled`, `--tab-border-selected`, `--tab-text-default`, `--tab-text-disabled`, `--tab-text-hover`, `--table-header-background`, `--table-header-background-2`, `--tag-error-border-default`, `--tag-error-border-focus`, `--tag-error-border-hover`, `--tag-icon-focus`, `--tag-icon-hover`, `--tag-icon-pressed`, `--tag-selected-background-focus`, `--tooltip-border`
