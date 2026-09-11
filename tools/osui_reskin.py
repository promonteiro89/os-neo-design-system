#!/usr/bin/env python3
"""Extract the ODC portal's OutSystems UI re-skin layer.

The portal does NOT re-tint OutSystems UI through variables. It ships direct
class overrides in its `Old_NeoDesignSystem` theme, pointing OutSystems UI's
widgets at Neo's own tokens. This pulls that layer out of
reference/raw/old-neo-design-system.css so we can replicate it verbatim.

Emits dist/osui-reskin.css.  Usage: python3 tools/osui_reskin.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import ROOT, DIST, split_top_level, render, header, write  # noqa: E402

OLD = os.path.join(ROOT, 'reference', 'raw', 'old-neo-design-system.css')

# Third-party widget internals bundled into the portal's theme. Not OutSystems
# UI, not ours to replicate — 186 flatpickr rules and 112 vscomp rules alone.
VENDOR = ('flatpickr', 'vscomp', 'splide', 'dayContainer', 'numInput',
          'cur-', 'shepherd', 'tippy', 'ql-', 'ace_')

# Selectors that only ever match inside the ODC portal itself — its own layout
# shells, onboarding screens and app cards. 41 of 411 rules, dead weight in a
# customer app, so they are dropped rather than shipped as never-matching CSS.
PORTAL_ONLY = ('pds-', 'layout-neo', 'hybrid-global', 'neo-layout',
               'app-representation', 'is-unified', 'unified-', 'onboarding',
               'welcome', 'stage-')

# The re-skin points at two portal image assets by hashed filename. Import the
# copies in dist/assets/ as Images in the library under exactly these
# names and the references resolve. The hard-coded #181A1F fill is upstream's —
# the CSS recolours it with filter: invert(), which is why it must stay.
ICONS = {
    'NeoDesignSystem.icchevrondownxl': 'icchevrondownxl',
    'NeoDesignSystem.icsortablexl': 'icsortablexl',
}

# OutSystems UI's own widget classes, i.e. what a consuming app actually renders.
CORE = {
    'btn', 'btn-primary', 'btn-secondary', 'btn-tertiary', 'btn-group',
    'button-group', 'button-group-item', 'form-control', 'dropdown',
    'dropdown-container', 'dropdown-display', 'card', 'card-header',
    'card-footer', 'alert', 'alert-error', 'alert-warning', 'alert-success',
    'alert-info', 'badge', 'tag', 'table', 'table-header', 'list', 'list-item',
    'tabs', 'tabs-header', 'tabs-content', 'checkbox', 'radio-button', 'switch',
    'toggle', 'input-with-icon', 'label', 'link', 'avatar', 'pagination',
    'progress', 'spinner', 'tooltip', 'popover', 'accordion', 'sidebar',
    'wizard', 'counter', 'feedback-message', 'notification', 'not-valid',
    'placeholder', 'heading1', 'heading2', 'heading3', 'heading4', 'title',
    'section', 'section-index', 'datepicker', 'search',
}

# Referenced by the re-skin but defined nowhere in the portal's own 12
# stylesheets either — genuine upstream gaps. Values for --color-brand-blue are
# the portal's (legacy-neo-theme.css); the other two are inferred from Neo's
# nearest equivalents and marked as such.
SHIM = '''/* --------------------------------------------------------------------------
   Variables the re-skin needs that nothing defines
   --------------------------------------------------------------------------
   --color-brand-blue    the portal's own values, from legacy-neo-theme.css,
                         which is a chain link we do not ship.
   --input-border-error  referenced once, defined NOWHERE in any of the 12
   --input-height        portal stylesheets — broken upstream too. Mapped to
                         Neo's nearest equivalents; these two are inferences,
                         not recovered values.

   Four other undefined-looking variables need no shim: --color-neutral-0/2/9
   and --space-s are provided by OutSystems UI itself (measured in a live ODC
   app: #ffffff, #f1f3f5, #272b30, 8px).
   -------------------------------------------------------------------------- */
:root {
  --color-brand-blue: #0077b3;
  --input-border-error: var(--border-error-default);   /* inferred */
  --input-height: var(--component-size-base);          /* inferred */
}

[data-theme="dark"]:root {
  --color-brand-blue: #38bdff;
}
'''


def _image_url(text):
    """Point the two icon references at Images in the library.

    Import dist/assets/*.svg as Images named `icchevrondownxl` and
    `icsortablexl`, and these resolve.

    The path form is the one ODC actually uses, confirmed in ODC Studio after
    publishing: an absolute module path, `/NeoDesignSystem/img/<Module>.<Image>.svg`
    — not the `../img/...` relative form the portal's own published CSS shows.
    """
    swapped = 0
    for stem, name in ICONS.items():
        text, n = re.subn(r'url\(\.\./img/' + re.escape(stem) + r'[^)]*\)',
                          'url(/NeoDesignSystem/img/NeoDesignSystem.%s.svg)' % name, text)
        swapped += n
    print('  pointed %d image reference(s) at library Images' % swapped)
    return text


def main():
    with open(OLD, encoding='utf-8-sig') as fh:
        old = fh.read()

    keep = []
    for kind, prelude, body in split_top_level(old):
        if kind != 'rule' or not prelude:
            continue
        if any(v in prelude for v in VENDOR):
            continue
        cls = set(re.findall(r'\.(-?[A-Za-z_][\w-]*)', prelude))
        if any(c.startswith(('ds-', 'fusion-')) for c in cls):
            continue          # the portal's own components, not an OSUI re-skin
        if not (cls & CORE):
            continue
        if any(p in prelude for p in PORTAL_ONLY):
            continue
        keep.append((kind, prelude, body))

    parts = [header('OutSystems UI re-skin — as the ODC portal does it',
                    'Direct class overrides lifted from the portal\'s Old_NeoDesignSystem\n'
                    '   theme, pointing OutSystems UI widgets at Neo tokens. The portal does\n'
                    '   NOT re-tint OutSystems UI through variables — verified in a live ODC\n'
                    '   app, where overriding --color-primary and --background-color-primary\n'
                    '   left .btn-primary unchanged at #1068eb.\n\n'
                    '   {} rules. Vendor internals (flatpickr, vscomp, splide) and the\n'
                    '   portal\'s own .ds-* / .fusion-* components are excluded.'.format(len(keep))),
             SHIM]
    parts += [render(c) for c in keep]
    out = _image_url('\n'.join(parts) + '\n')
    write(os.path.join(DIST, 'osui-reskin.css'), out)
    print('osui-reskin: %d rules -> dist/osui-reskin.css (%dKB)' % (len(keep), len(out) // 1024))


if __name__ == '__main__':
    main()
