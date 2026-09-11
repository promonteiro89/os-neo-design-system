#!/usr/bin/env python3
"""Split the ODC Neo Design System CSS bundle into a structured source tree.

Input:  reference/raw/neo-design-system.original.css  (see tools/fetch.sh)
Output: src/**  dist/**  reference/tokens.json  reference/tokens.md  reference/audit.md

The split is lossless: every top-level rule and every custom property in the
source lands in exactly one output file, in its original order. Run
`python3 tools/verify.py` after building to prove it.

Usage:  python3 tools/build.py
"""

import json
import os
import re
import shutil
from collections import defaultdict, OrderedDict
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'reference', 'raw', 'neo-design-system.original.css')
SHELL_RAW = os.path.join(ROOT, 'reference', 'raw', 'unified-shell.css')
SRC = os.path.join(ROOT, 'src')
DIST = os.path.join(ROOT, 'dist')
REFERENCE = os.path.join(ROOT, 'reference')

# The tenant host is configuration, not source. It lives in the gitignored
# `odc-tenant` file at the repo root ($ODC_TENANT overrides); tools/fetch.sh is
# the only tool that dereferences it. Provenance strings below record the
# stylesheet, never the tenant.
SOURCE_URL = ('NeoDesignSystem.NeoDesignSystem.css, served by the ODC tenant '
              '(host: ./odc-tenant; exact URLs: tools/stylesheets.txt)')


# --------------------------------------------------------------------------
# 1. Parsing
# --------------------------------------------------------------------------

def strip_comments(css):
    """Remove /* … */ comments. The Neo bundle has none; the shell bundle does."""
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)


def split_top_level(css):
    """Yield top-level chunks: ('rule', prelude, body) | ('decl', text, None)."""
    chunks, i, n, start, depth, quote, prelude_end = [], 0, len(css), 0, 0, None, None
    while i < n:
        c = css[i]
        if quote:
            if c == '\\':
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in '"\'':
            quote = c
        elif c == '{':
            if depth == 0:
                prelude_end = i
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                chunks.append(('rule', css[start:prelude_end].strip(),
                               css[prelude_end + 1:i]))
                start = i + 1
        elif c == ';' and depth == 0:
            text = css[start:i].strip()
            if text:
                chunks.append(('decl', text, None))
            start = i + 1
        i += 1
    tail = css[start:].strip()
    if tail:
        chunks.append(('decl', tail, None))
    return chunks


def split_decls(body):
    """Split a declaration block into individual declaration strings."""
    out, depth, quote, buf = [], 0, None, []
    for c in body:
        if quote:
            buf.append(c)
            if c == quote:
                quote = None
            continue
        if c in '"\'':
            quote = c
            buf.append(c)
            continue
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
        if c == ';' and depth == 0:
            d = ''.join(buf).strip()
            if d:
                out.append(d)
            buf = []
            continue
        buf.append(c)
    d = ''.join(buf).strip()
    if d:
        out.append(d)
    return out


def parse_decl(d):
    """Split one declaration on its first top-level colon -> (prop, value).

    Values legitimately contain colons (`url(https://…)`, `url(data:…)`), so a
    naive split is wrong. Returns (text, None) for anything with no colon.
    """
    depth, quote = 0, None
    for i, c in enumerate(d):
        if quote:
            if c == quote:
                quote = None
            continue
        if c in '"\'':
            quote = c
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
        elif c == ':' and depth == 0:
            return d[:i].strip(), d[i + 1:].strip()
    return d.strip(), None


def format_decl(d, sep=': '):
    prop, value = parse_decl(re.sub(r'\s+', ' ', d).strip())
    return prop if value is None else prop + sep + value


def format_selector(prelude, indent):
    """One comma-separated selector per line (at-rules stay on one line)."""
    if prelude.startswith('@'):
        return indent + re.sub(r'\s+', ' ', prelude).strip()
    parts, depth, quote, buf = [], 0, None, []
    for c in prelude:
        if quote:
            buf.append(c)
            if c == quote:
                quote = None
            continue
        if c in '"\'':
            quote = c
            buf.append(c)
            continue
        if c in '([':
            depth += 1
        elif c in ')]':
            depth -= 1
        if c == ',' and depth == 0:
            parts.append(''.join(buf).strip())
            buf = []
            continue
        buf.append(c)
    parts.append(''.join(buf).strip())
    parts = [re.sub(r'\s+', ' ', p) for p in parts if p]
    return (',\n' + indent).join(parts)


NESTING_AT = ('@media', '@supports', '@keyframes', '@-webkit-keyframes',
              '@layer', '@container', '@document')


def render(chunk, indent=''):
    kind, prelude, body = chunk
    if kind == 'decl':
        return indent + re.sub(r'^@import(?=["\'])', '@import ', prelude) + ';'
    lines = [format_selector(prelude, indent) + ' {']
    if prelude.startswith(NESTING_AT):
        for sub in split_top_level(body):
            lines.append(render(sub, indent + '  '))
    else:
        for d in split_decls(body):
            lines.append(indent + '  ' + format_decl(d) + ';')
    lines.append(indent + '}')
    return '\n'.join(lines)


def minify(chunk):
    """Re-minify a chunk (used for dist/*.min.css)."""
    kind, prelude, body = chunk
    if kind == 'decl':
        # Canonicalise `@import"…"` so pretty and minified output compare equal.
        return re.sub(r'^@import(?=["\'])', '@import ', prelude) + ';'
    pre = re.sub(r'\s*,\s*', ',', re.sub(r'\s+', ' ', prelude).strip())
    if prelude.startswith(NESTING_AT):
        inner = ''.join(minify(s) for s in split_top_level(body))
    else:
        inner = ';'.join(format_decl(d, ':') for d in split_decls(body))
    return pre + '{' + inner + '}'


# --------------------------------------------------------------------------
# 2. Classification of top-level rules into layers / files
# --------------------------------------------------------------------------

UTIL_PATTERNS = [
    ('colors', r'^\.(background|text|border)-(white|black|neutral|red|yellow|green|blue|indigo|transparent)'),
    ('colors', r'^\.text-(primary|secondary|disabled|error|warning|success|info)$'),
    ('icons', r'^\.(icon-|pds-icon|svg-code|vertical-align)'),
    ('radius', r'^\.border-radius-'),
    ('cursor', r'^\.cursor-'),
    ('elevation', r'^\.shadow-\d'),
    ('spacing', r'^\.(margin|padding)-'),
    ('typography', r'^\.(display|heading|body-semi-bold|body-regular|alert-title|link-underline|actions)'),
    ('typography', r'^\.(font-size|font-weight|letter-spacing|line-height|font-bold|font-semi-bold|font-regular)'),
    ('transform', r'^\.rotate-'),
    ('motion', r'^\.transition-'),
    ('helpers', r'^\.(absolute-center|pointer-events-none|line-clamp)'),
]

# fusion-* selector fragments that belong to a shared component file
MERGE = {
    'accordion-item': 'accordion',
    'collapsible-core': 'collapsible',
    'dropdown-item': 'dropdown',
    'dropdown-empty': 'dropdown',
    'layout-header': 'layout',
    'layout-section-structure': 'layout',
    'wizard-section': 'layout',
    'wizard-step': 'wizard',
    'breadcrumb-item': 'breadcrumb',
}

LEGACY_RE = re.compile(r'\.(ds-ncard|ds-card|ds-tabs|checkbox|screen-container)')


def component_of(prelude):
    m = re.search(r'fusion-([a-z0-9]+(?:-[a-z0-9]+)*)', prelude)
    if m:
        return MERGE.get(m.group(1), m.group(1))
    if 'splide' in prelude:
        return 'vendor/splide'
    return None


def classify(kind, prelude, body):
    """-> (layer, file) for one top-level chunk."""
    p = ' '.join(prelude.split())

    if kind == 'decl':
        return ('01-base', 'fonts') if p.startswith('@import') else ('01-base', 'reset')

    if p.startswith(('@keyframes', '@-webkit-keyframes')):
        return ('01-base', 'animations')

    # Nested at-rules: classify by what they contain, not by the at-rule itself.
    if p.startswith(NESTING_AT):
        for sub in split_top_level(body):
            layer, f = classify(sub[0], sub[1], sub[2])
            if (layer, f) != ('01-base', 'reset'):
                return (layer, f)
        return ('01-base', 'reset')

    if p == ':root':
        return ('00-tokens', '@light')
    if p == '[data-theme=dark]:root':
        return ('00-tokens', '@dark')

    for fname, pat in UTIL_PATTERNS:
        for sel in [s.strip() for s in p.split(',') if s.strip()]:
            if re.match(pat, sel):
                return ('03-utilities', fname)

    # Overrides targeting the older OutSystems Neo/DS class names.
    if LEGACY_RE.search(p) and not re.match(r'^(\.)?fusion-', p):
        return ('01-base', 'legacy-interop')

    comp = component_of(p)
    if comp:
        return ('02-components', comp)

    return ('01-base', 'reset')


# --------------------------------------------------------------------------
# 3. Custom property grouping
# --------------------------------------------------------------------------

TOKEN_GROUPS = [
    ('primitives/_size', 'Size scale', [r'^--size-\d+$']),
    ('primitives/_palette', 'Base', [r'^--(black|white)$']),
    ('primitives/_palette', 'Neutral', [r'^--neutral-']),
    ('primitives/_palette', 'Red', [r'^--red-']),
    ('primitives/_palette', 'Orange', [r'^--orange-']),
    ('primitives/_palette', 'Yellow', [r'^--yellow-']),
    ('primitives/_palette', 'Green', [r'^--green-']),
    ('primitives/_palette', 'Blue', [r'^--blue-']),
    ('primitives/_palette', 'Indigo (brand accent)', [r'^--indigo-']),
    ('primitives/_typography', 'Font family', [r'^--font-family$']),
    ('primitives/_typography', 'Font size scale', [r'^--font-size-\d+$']),
    ('primitives/_typography', 'Line height scale', [r'^--line-height-\d+$']),
    ('primitives/_typography', 'Letter spacing scale', [r'^--letter-spacing-\d+$']),
    ('primitives/_typography', 'Font weight scale', [r'^--font-weight-\d+$']),
    ('primitives/_opacity', 'Opacity scale', [r'^--opacity-']),

    ('semantic/_typography', 'Type styles — `font` shorthand: weight size/line-height family',
     [r'^--(display|heading-\d|body-semi-bold|body-regular|actions-)',
      r'^--alert-title$', r'^--link-underline-', r'^--underline$']),

    ('semantic/_color', 'Text', [r'^--text-']),
    ('semantic/_color', 'Icon', [r'^--icon-(?!size)']),
    ('semantic/_color', 'Border', [r'^--border-(?!radius)']),
    ('semantic/_color', 'Surface', [r'^--surface-']),
    ('semantic/_color', 'Page & divider', [r'^--(page-|divider-)']),
    ('semantic/_color', 'Scrollbar', [r'^--scrollbar-']),

    ('semantic/_space', 'Spacing scale', [r'^--space-']),
    ('semantic/_space', 'Border radius', [r'^--border-radius-']),
    ('semantic/_space', 'Component heights', [r'^--component-size-']),
    ('semantic/_space', 'Icon sizes', [r'^--icon-size-']),
    ('semantic/_space', 'Popover widths', [r'^--popover-width-']),

    ('semantic/_elevation', 'Shadows', [r'^--shadow-\d']),
    ('semantic/_elevation', 'Focus rings & component shadows',
     [r'^--component-(shadow|error-shadow)', r'^--link-shadow-focus$',
      r'^--overflow-shadow$', r'^--switch-shadow$']),

    ('semantic/_motion', 'Durations', [r'^--transition-time-']),
    ('semantic/_motion', 'Easing curves', [r'^--transition-curve-']),

    ('semantic/_charts', 'Data visualization ramps', [r'^--data-visualization-']),
    ('semantic/_charts', 'Chart series', [r'^--chart-']),

    ('components/_alert', 'Alert', [r'^--alert-']),
    ('components/_avatar', 'Avatar', [r'^--avatar-']),
    ('components/_badge', 'Badge', [r'^--badge-']),
    ('components/_breadcrumb', 'Breadcrumb', [r'^--breadcrumb-']),
    ('components/_button', 'Button', [r'^--button-']),
    ('components/_card', 'Card', [r'^--card-']),
    ('components/_control', 'Control (checkbox / radio / switch)', [r'^--control-']),
    ('components/_counter', 'Counter', [r'^--counter-']),
    ('components/_form', 'Label & helper text', [r'^--(label-|helper-)']),
    ('components/_form', 'Input', [r'^--input-']),
    ('components/_link', 'Link', [r'^--link-']),
    ('components/_overlay', 'Popup & confirmation overlay', [r'^--(popup-|confirmation-)']),
    ('components/_overlay', 'Tooltip', [r'^--tooltip-']),
    ('components/_progress', 'Progress bar', [r'^--progress-bar-']),
    ('components/_skeleton', 'Skeleton', [r'^--skeleton-']),
    ('components/_spinner', 'Spinner', [r'^--spinner-']),
    ('components/_table', 'Table', [r'^--table-']),
    ('components/_tab', 'Tabs', [r'^--tab-']),
    ('components/_tag', 'Tag', [r'^--tag-']),
]

TOKEN_FILE_ORDER = [
    'primitives/_size', 'primitives/_palette', 'primitives/_typography',
    'primitives/_opacity',
    'semantic/_color', 'semantic/_typography', 'semantic/_space',
    'semantic/_elevation', 'semantic/_motion', 'semantic/_charts',
    'components/_alert', 'components/_avatar', 'components/_badge',
    'components/_breadcrumb', 'components/_button', 'components/_card',
    'components/_control', 'components/_counter', 'components/_form',
    'components/_link', 'components/_overlay', 'components/_progress',
    'components/_skeleton', 'components/_spinner', 'components/_tab',
    'components/_table', 'components/_tag',
]


def token_group(name):
    for grp, section, pats in TOKEN_GROUPS:
        for pat in pats:
            if re.match(pat, name):
                return grp, section
    raise SystemExit('unclassified custom property: ' + name)


# --------------------------------------------------------------------------
# 4. Emit
# --------------------------------------------------------------------------

BANNER = """/* ==========================================================================
   {title}
   --------------------------------------------------------------------------
   OutSystems ODC — Neo Design System (Fusion components)
   Extracted from: {url}
   Generated by tools/build.py on {today} — do not edit by hand.
   {extra}
   ========================================================================== */
"""


def header(title, extra=''):
    return BANNER.format(title=title, url=SOURCE_URL, today=date.today().isoformat(),
                         extra=extra)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(text if text.endswith('\n') else text + '\n')


# --------------------------------------------------------------------------
# 4b. The unified shell (prod.unified.css) — portal chrome, separate product
# --------------------------------------------------------------------------

# Evaluated in order, first match wins.
SHELL_GROUPS = [
    ('aside', r'unified-aside'),
    ('header', r'unified-(header|expand|tenant-dropdown)'),
    ('banner', r'unified-banner'),
    ('toast', r'unified-toast'),
    ('tooltip', r'unified-tooltip'),
    ('host-integration', r'is-unified-|is-aside-expanded|nds-layout|pds-layout|'
                         r'neo-layout-shield|hybrid-global-layout|\.main\b'),
]

SHELL_FILE_ORDER = ['host-integration', 'header', 'aside', 'banner', 'tooltip',
                    'toast', 'misc']


def classify_shell(kind, prelude, body):
    p = ' '.join((prelude or '').split())
    if kind == 'decl':
        return 'misc'
    if p.startswith(('@keyframes', '@-webkit-keyframes')):
        return 'animations'
    if p.startswith(NESTING_AT):
        for sub in split_top_level(body):
            f = classify_shell(sub[0], sub[1], sub[2])
            if f != 'misc':
                return f
        return 'misc'
    for fname, pat in SHELL_GROUPS:
        if re.search(pat, p):
            return fname
    return 'misc'


def build_shell():
    """Split the portal chrome into src/04-shell/ + dist/neo-shell.css."""
    if not os.path.isfile(SHELL_RAW):
        print('shell  : skipped (reference/raw/unified-shell.css absent)')
        return
    with open(SHELL_RAW, encoding='utf-8-sig') as fh:
        css = strip_comments(fh.read())
    chunks = split_top_level(css)

    buckets = OrderedDict()
    for chunk in chunks:
        buckets.setdefault(classify_shell(*chunk), []).append(chunk)

    order = SHELL_FILE_ORDER + sorted(set(buckets) - set(SHELL_FILE_ORDER))
    written = []
    for f in order:
        items = buckets.get(f)
        if not items:
            continue
        write(os.path.join(SRC, '04-shell', f + '.css'),
              header('Portal shell — ' + f.replace('-', ' '),
                     '{} rules. Source: prod.unified.css (UnifiedExperienceMenuServices), '
                     'a separate product from the Neo bundle.'.format(len(items)))
              + '\n' + '\n\n'.join(render(c) for c in items))
        written.append('04-shell/{}.css'.format(f))

    write(os.path.join(SRC, 'neo-shell.css'),
          header('Portal shell index',
                 'Load AFTER the Neo tokens — the shell consumes 121 of them.')
          + '\n' + '\n'.join('@import url("{}");'.format(p) for p in written))

    out = [header('Portal shell — flattened',
                  'Paste-ready. Requires the Neo tokens and compat/neo-shell-compat.css.')]
    for p in written:
        with open(os.path.join(SRC, p), encoding='utf-8') as fh:
            text = fh.read()
        text = re.sub(r'/\* =+\n(?:.*\n)*?   =+ \*/\n', '', text).strip()
        out.append('/* ---- {} {} */\n\n{}'.format(p, '-' * max(4, 66 - len(p)), text))
    write(os.path.join(DIST, 'neo-shell.css'), '\n\n'.join(out))

    # The shell CSS references url(assets/outsystems-logo--{light,dark}.svg)
    # relative to itself, so the folder has to sit next to every copy.
    src_assets = os.path.join(ROOT, 'reference', 'raw', 'assets')
    copied = 0
    if os.path.isdir(src_assets):
        for dest in (os.path.join(DIST, 'assets'),
                     os.path.join(SRC, '04-shell', 'assets')):
            os.makedirs(dest, exist_ok=True)
            for asset in sorted(os.listdir(src_assets)):
                shutil.copy2(os.path.join(src_assets, asset), os.path.join(dest, asset))
                copied += 1

    print('shell  : {} rules -> {} files ({}), {} assets copied'.format(
        len(chunks), len(written), ', '.join(w.split('/')[1][:-4] for w in written), copied))


# --------------------------------------------------------------------------
# 4c. Paste-ready bundles for an OutSystems 11 theme module
# --------------------------------------------------------------------------

# Utility files that collide with OutSystems UI on 40 class names whose values
# differ (see tools/collisions.py). Excluded from the O11 utility bundle.
O11_UTILITY_EXCLUDE = {'colors.css', 'typography.css'}

FONT_IMPORTS = (
    '@import url("https://fonts.googleapis.com/css2'
    '?family=Noto+Sans:wght@400;500;600&display=swap");\n'
    '@import url("https://fonts.googleapis.com/css2'
    '?family=Source+Code+Pro:wght@400;500;600&display=swap");\n'
)


def build_o11():
    """Emit dist/o11-theme*.css — what you paste into an O11 Theme."""
    def body_of(path):
        with open(path, encoding='utf-8') as fh:
            text = fh.read()
        # Drop the generated banner; keep hand-authored comments intact.
        return re.sub(r'/\* =+\n(?:.*\n)*?   =+ \*/\n', '', text).strip()

    token_files = ['00-tokens/' + g + '.css' for g in TOKEN_FILE_ORDER
                   if os.path.isfile(os.path.join(SRC, '00-tokens', g + '.css'))]
    token_files.append('00-tokens/_dark-theme.css')

    # ---- 1. the theme itself: tokens + O11 adaptation + OutSystems UI bridge
    parts = [
        '/* Fonts first: CSS requires @import before any rule. Replace these two\n'
        '   lines with your own @font-face if you self-host (recommended). */\n'
        + FONT_IMPORTS,
        header('OutSystems 11 theme — paste this into your Theme stylesheet',
               'Neo tokens + O11 adaptation + OutSystems UI bridge, in cascade order.\n'
               '   Nothing here fights OutSystems UI: no reset, no legacy interop, and none\n'
               '   of the utility classes that collide with it.'),
    ]
    for rel in token_files:
        parts.append('/* ---- src/{} {} */\n\n{}'.format(
            rel, '-' * max(4, 56 - len(rel)), body_of(os.path.join(SRC, rel))))
    for name in ('neo-o11-compat.css', 'neo-osui-bridge.css'):
        path = os.path.join(ROOT, 'compat', name)
        if os.path.isfile(path):
            parts.append('/* ---- compat/{} {} */\n\n{}'.format(
                name, '-' * max(4, 56 - len(name)), body_of(path)))
    write(os.path.join(DIST, 'o11-theme.css'), '\n\n'.join(parts))

    # ---- 2. the safe utility subset
    utils = sorted(f for f in os.listdir(os.path.join(SRC, '03-utilities'))
                   if f.endswith('.css') and f not in O11_UTILITY_EXCLUDE)
    uparts = [header('OutSystems 11 utility classes — optional',
                     'Drop straight into a widget\'s Style Classes property.\n'
                     '   colors.css and typography.css are deliberately EXCLUDED: they collide\n'
                     '   with OutSystems UI on 40 class names, and .text-primary /\n'
                     '   .text-secondary mean the opposite thing in each. See\n'
                     '   reference/osui-collisions.md.')]
    for f in utils:
        uparts.append('/* ---- src/03-utilities/{} {} */\n\n{}'.format(
            f, '-' * max(4, 44 - len(f)), body_of(os.path.join(SRC, '03-utilities', f))))
    write(os.path.join(DIST, 'o11-theme-utilities.css'), '\n\n'.join(uparts))

    # ---- 3. the Fusion components, for apps that build Neo-native blocks
    comps = sorted(f for f in os.listdir(os.path.join(SRC, '02-components'))
                   if f.endswith('.css'))
    cparts = [header('Fusion components — optional',
                     'Only needed if you hand-build Neo component markup in Blocks.\n'
                     '   OutSystems UI widgets do NOT need this; the bridge covers them.')]
    for f in comps:
        cparts.append('/* ---- src/02-components/{} {} */\n\n{}'.format(
            f, '-' * max(4, 44 - len(f)), body_of(os.path.join(SRC, '02-components', f))))
    write(os.path.join(DIST, 'o11-theme-components.css'), '\n\n'.join(cparts))

    def kb(p):
        return os.path.getsize(os.path.join(DIST, p)) // 1024
    print('o11    : o11-theme.css {}KB, utilities {}KB, components {}KB'.format(
        kb('o11-theme.css'), kb('o11-theme-utilities.css'),
        kb('o11-theme-components.css')))


def build_odc():
    """Emit dist/odc-library.css — the bundle for an ODC library/app."""
    def body_of(path):
        with open(path, encoding='utf-8') as fh:
            text = fh.read()
        return re.sub(r'/\* =+\n(?:.*\n)*?   =+ \*/\n', '', text).strip()

    token_files = ['00-tokens/' + g + '.css' for g in TOKEN_FILE_ORDER
                   if os.path.isfile(os.path.join(SRC, '00-tokens', g + '.css'))]
    token_files.append('00-tokens/_dark-theme.css')

    parts = [
        '/* Fonts first: CSS requires @import before any rule. Replace these two\n'
        '   lines with your own @font-face if you self-host (recommended). */\n'
        + FONT_IMPORTS,
        header('ODC library stylesheet',
               'Neo tokens + the ODC adaptation layer. Deliberately NOT included:\n'
               '   the reset (takes over scrolling), the legacy interop, the component\n'
               '   rules, and the OutSystems UI bridge — see compat/neo-odc-compat.css\n'
               '   for why each one is left out.\n\n'
               '   dist/o11-theme-utilities.css and dist/o11-theme-components.css apply\n'
               '   here unchanged: the 40-class collision with OutSystems UI is the same\n'
               '   in ODC, so the same exclusions hold.'),
    ]
    for rel in token_files:
        parts.append('/* ---- src/{} {} */\n\n{}'.format(
            rel, '-' * max(4, 56 - len(rel)), body_of(os.path.join(SRC, rel))))
    path = os.path.join(ROOT, 'compat', 'neo-odc-compat.css')
    if os.path.isfile(path):
        parts.append('/* ---- compat/neo-odc-compat.css {} */\n\n{}'.format(
            '-' * 26, body_of(path)))
    # dist/odc-library.css retired — dist/neobase.css is the ODC artifact now.
    return


def main():
    with open(RAW, encoding='utf-8-sig') as fh:
        css = fh.read()
    chunks = split_top_level(css)

    # ---- bucket rules -------------------------------------------------
    buckets = OrderedDict()
    light_body = dark_body = None
    for chunk in chunks:
        layer, f = classify(*chunk)
        if f == '@light':
            light_body = chunk[2]
            continue
        if f == '@dark':
            dark_body = chunk[2]
            continue
        buckets.setdefault((layer, f), []).append(chunk)

    # Clear only what this build regenerates. dist/o11-phosphor is produced by
    # tools/phosphor_o11.py, which needs network and is NOT in build_all.sh —
    # rmtree(DIST) used to destroy it silently on every rebuild.
    if os.path.isdir(SRC):
        shutil.rmtree(SRC)
    if os.path.isdir(DIST):
        for entry in os.listdir(DIST):
            if entry == 'o11-phosphor':
                continue
            full = os.path.join(DIST, entry)
            shutil.rmtree(full) if os.path.isdir(full) else os.remove(full)

    # ---- token files --------------------------------------------------
    def group_decls(body):
        out = defaultdict(list)
        for d in split_decls(body):
            name, _, value = d.partition(':')
            name, value = name.strip(), ' '.join(value.split())
            grp, section = token_group(name)
            out[grp].append((section, name, value))
        return out

    light = group_decls(light_body)
    dark = group_decls(dark_body)

    def render_token_block(selector, items, title, extra=''):
        lines = [header(title, extra), selector + ' {']
        current = None
        for section, name, value in items:
            if section != current:
                lines.append(('\n' if current else '') + '  /* ' + section + ' */')
                current = section
            lines.append('  {}: {};'.format(name, value))
        lines.append('}')
        return '\n'.join(lines)

    token_files = []
    for grp in TOKEN_FILE_ORDER:
        items = light.get(grp)
        if not items:
            continue
        title = grp.split('/')[-1].lstrip('_').replace('-', ' ').title() + ' tokens'
        path = os.path.join(SRC, '00-tokens', grp + '.css')
        write(path, render_token_block(':root', items, title,
                                      'Light theme. Dark overrides live in 00-tokens/_dark-theme.css.'))
        token_files.append('00-tokens/' + grp + '.css')

    dark_items = []
    for grp in TOKEN_FILE_ORDER:
        for section, name, value in dark.get(grp, []):
            dark_items.append((grp.split('/')[-1].lstrip('_') + ' — ' + section, name, value))
    write(os.path.join(SRC, '00-tokens', '_dark-theme.css'),
          render_token_block('[data-theme="dark"]:root', dark_items, 'Dark theme overrides',
                             'Only the tokens that differ from light. Grouped to mirror the light files.'))
    token_files.append('00-tokens/_dark-theme.css')

    # ---- rule files ---------------------------------------------------
    LAYER_TITLES = {
        '01-base': 'Base',
        '02-components': 'Component',
        '03-utilities': 'Utility',
    }
    written = []
    for (layer, f), items in buckets.items():
        title = '{} — {}'.format(LAYER_TITLES[layer], f.split('/')[-1].replace('-', ' '))
        body = '\n\n'.join(render(c) for c in items)
        write(os.path.join(SRC, layer, f + '.css'),
              header(title, '{} top-level rules.'.format(len(items))) + '\n' + body)
        written.append((layer, f))

    # ---- index files --------------------------------------------------
    def order_key(item):
        layer, f = item
        base_order = ['fonts', 'reset', 'animations', 'legacy-interop']
        if layer == '01-base':
            return (0, base_order.index(f) if f in base_order else 99, f)
        if layer == '02-components':
            return (0, 0 if f.startswith('vendor/') else 1, f)
        return (0, 0, f)

    base = sorted([w for w in written if w[0] == '01-base'], key=order_key)
    comps = sorted([w for w in written if w[0] == '02-components'], key=order_key)
    utils = sorted([w for w in written if w[0] == '03-utilities'], key=order_key)

    def imports(paths):
        return '\n'.join('@import url("{}");'.format(p) for p in paths)

    tokens_index = (header('Token index — variables only, no component CSS',
                           'Import this alone when you only want the design language.')
                    + '\n' + imports(token_files))
    write(os.path.join(SRC, 'neo-tokens.css'), tokens_index)

    all_paths = (['01-base/fonts.css'] + token_files
                 + ['{}/{}.css'.format(l, f) for l, f in base if f != 'fonts']
                 + ['{}/{}.css'.format(l, f) for l, f in comps]
                 + ['{}/{}.css'.format(l, f) for l, f in utils])
    write(os.path.join(SRC, 'neo.css'),
          header('Full bundle index', 'Cascade order: fonts, tokens, base, components, utilities.')
          + '\n' + imports(all_paths))

    # ---- dist (flattened, paste-ready) --------------------------------
    def concat(paths, title, extra):
        out = [header(title, extra)]
        for p in paths:
            with open(os.path.join(SRC, p), encoding='utf-8') as fh:
                text = fh.read()
            text = re.sub(r'/\* =+\n(?:.*\n)*?   =+ \*/\n', '', text).strip()
            out.append('/* ---- {} {} */\n\n{}'.format(p, '-' * max(4, 66 - len(p)), text))
        return '\n\n'.join(out)

    write(os.path.join(DIST, 'neo-tokens.css'),
          concat(token_files, 'Neo tokens — flattened',
                 'Paste-ready. Variables only: no component or utility CSS.'))
    # dist/neo.css and dist/neo.min.css retired: dist/neobase.css supersedes both
    # as the ODC paste, and nothing consumed them.

    # ---- machine-readable tokens --------------------------------------
    def flat(groups):
        d = OrderedDict()
        for grp in TOKEN_FILE_ORDER:
            for section, name, value in groups.get(grp, []):
                d[name] = (grp, section, value)
        return d

    lflat, dflat = flat(light), flat(dark)

    def resolve(name, table, seen=None):
        seen = seen or set()
        if name in seen or name not in table:
            return None
        seen.add(name)
        value = table[name][2]
        m = re.fullmatch(r'var\((--[\w-]+)\)', value.strip())
        if m:
            return resolve(m.group(1), table, seen)
        return value

    tokens = OrderedDict()
    for name, (grp, section, value) in lflat.items():
        dark_value = dflat[name][2] if name in dflat else None
        tokens[name] = OrderedDict([
            ('group', grp), ('section', section),
            ('light', value), ('dark', dark_value),
            ('lightResolved', resolve(name, lflat)),
            ('darkResolved', resolve(name, {**lflat, **dflat})),
            ('alias', bool(re.fullmatch(r'var\((--[\w-]+)\)', value.strip()))),
        ])
    write(os.path.join(REFERENCE, 'tokens.json'), json.dumps(OrderedDict([
        ('source', SOURCE_URL),
        ('generated', date.today().isoformat()),
        ('themes', ['light', 'dark']),
        ('counts', {'light': len(lflat), 'dark': len(dflat)}),
        ('tokens', tokens),
    ]), indent=2))

    # ---- markdown token reference -------------------------------------
    md = ['# Neo design tokens', '',
          'Generated from `{}` on {}.'.format(os.path.basename(RAW), date.today().isoformat()),
          '', '{} tokens in light theme, {} overridden in dark.'.format(len(lflat), len(dflat)),
          '', '`->` marks an alias that points at another token.', '']
    current_grp = None
    for name, meta in tokens.items():
        if meta['group'] != current_grp:
            current_grp = meta['group']
            md += ['', '## `{}`'.format(current_grp), '',
                   '| Token | Light | Dark | Resolved (light) |',
                   '| --- | --- | --- | --- |']
        def cell(v):
            if v is None:
                return '—'
            v = v.replace('|', '\\|')
            return '`{}`'.format(v)
        light_cell = ('-> ' if meta['alias'] else '') + cell(meta['light'])
        md.append('| `{}` | {} | {} | {} |'.format(
            name, light_cell, cell(meta['dark']), cell(meta['lightResolved'])))
    write(os.path.join(REFERENCE, 'tokens.md'), '\n'.join(md))

    # ---- audit ---------------------------------------------------------
    # Every var() reference, and every place a custom property is defined —
    # including component-scoped definitions, not just the :root blocks.
    used = defaultdict(set)
    hard_used = defaultdict(set)   # referenced with no var() fallback value
    scoped = defaultdict(set)
    for kind, prelude, body in chunks:
        sel = ' '.join((prelude or '').split())
        for m in re.finditer(r'var\(\s*(--[\w-]+)\s*(,?)', (prelude or '') + (body or '')):
            used[m.group(1)].add(sel[:80])
            if not m.group(2):
                hard_used[m.group(1)].add(sel[:80])
        if kind == 'rule' and not sel.startswith(NESTING_AT):
            for d in split_decls(body):
                prop, value = parse_decl(d)
                if prop.startswith('--') and value is not None:
                    scoped[prop].add(sel[:80])

    root_defined = set(lflat) | set(dflat)
    local_only = {k: v for k, v in scoped.items() if k not in root_defined}
    # A reference with a fallback — var(--x, 0) — degrades gracefully, so it is
    # not a broken reference even when --x is never defined.
    undefined = OrderedDict((k, sorted(v)) for k, v in sorted(hard_used.items())
                            if k not in root_defined and k not in scoped)

    # Cross-reference the other stylesheets the portal loads: a name missing
    # here may simply be owned by OutSystems UI or the legacy theme, in which
    # case it resolves for free in any app that loads them.
    siblings = {}
    raw_dir = os.path.dirname(RAW)
    for fname in sorted(os.listdir(raw_dir)):
        if not fname.endswith('.css') or fname == os.path.basename(RAW):
            continue
        try:
            with open(os.path.join(raw_dir, fname), encoding='utf-8-sig') as fh:
                text = fh.read()
        except OSError:
            continue
        for name, value in re.findall(r'(--[\w-]+)\s*:\s*([^;}]+)', text):
            if name in undefined and name not in siblings:
                siblings[name] = (fname, ' '.join(value.split())[:40])

    platform = OrderedDict((k, v) for k, v in undefined.items() if k.startswith('--unified-'))
    provided = OrderedDict((k, v) for k, v in undefined.items()
                           if k in siblings and k not in platform)
    broken = OrderedDict((k, v) for k, v in undefined.items()
                         if k not in platform and k not in provided)
    unused = sorted(n for n in lflat if n not in used)

    # Classes the bundle only ever styles *through* (never as the subject of a
    # rule) must be defined by some other stylesheet.
    seen_classes, styled_classes = set(), set()

    def scan_selectors(chunk_list):
        for kind, prelude, body in chunk_list:
            if kind != 'rule':
                continue
            if prelude.startswith(NESTING_AT):
                scan_selectors(split_top_level(body))
                continue
            for sel in prelude.split(','):
                sel = sel.strip()
                # Prism syntax-highlighting classes belong to Prism, not here.
                if '.token' in sel:
                    continue
                seen_classes.update(re.findall(r'\.([A-Za-z_][\w-]*)', sel))
                bare = re.sub(r'::?[\w-]+(\([^)]*\))?', '', sel)
                compounds = [c for c in re.split(r'[\s>+~]+', bare) if c]
                # A class is "owned" by this bundle if a rule targets it with no
                # ancestor context, or if it is a modifier sitting on a Neo class.
                # `.fusion-x .btn { margin: 0 }` tweaks .btn; it does not define it.
                for compound in compounds:
                    names = re.findall(r'\.([A-Za-z_][\w-]*)', compound)
                    if len(compounds) == 1 or any(
                            n.startswith(('fusion-', 'splide')) for n in names):
                        styled_classes.update(names)

    scan_selectors(chunks)
    external = sorted(c for c in seen_classes - styled_classes
                      if not c.startswith(('fusion-', 'splide', 'token', 'il-')))

    def table(rows):
        out = ['| Token | Referenced by |', '| --- | --- |']
        for name, sels in rows.items():
            out.append('| `{}` | {} |'.format(name, '<br>'.join(
                '`{}`'.format(s.replace('|', '\\|')) for s in sels[:4])))
        return out

    audit = [
        '# Audit', '', 'Generated on {}.'.format(date.today().isoformat()), '',
        'Every `var()` reference in the bundle checked against every custom property '
        'definition in it.', '',
        '## 1. Broken references — {} found'.format(len(broken)), '',
        'Referenced with no fallback, and defined **nowhere** — not in this bundle, not in any '
        'other stylesheet the portal loads. Genuine bugs in the upstream bundle: the browser '
        'drops the whole declaration. `compat/neo-compat.css` defines them; see that file for '
        'the reasoning behind each value.', '',
    ] + table(broken) + [
        '', '## 1b. Owned by another portal stylesheet — {} found'.format(len(provided)), '',
        'Not bugs. These belong to OutSystems UI or the legacy Neo theme, so they resolve for '
        'free in any app that loads those — which every OutSystems app does, since OutSystems UI '
        'is the base theme. `compat/neo-compat.css` still defines them so the bundle works '
        'standalone; the values agree with the owners.', '',
        '| Token | Owner | Value there |', '| --- | --- | --- |',
    ] + ['| `{}` | `{}` | `{}` |'.format(k, siblings[k][0], siblings[k][1]) for k in provided] + [
        '', '## 2. Provided by the ODC portal shell — {} found'.format(len(platform)), '',
        'Set by the portal chrome (unified header / side nav / banner), not by this stylesheet. '
        'A standalone app has no such chrome, so `compat/neo-compat.css` defaults them to `0px`.',
        '',
    ] + table(platform) + [
        '', '## 3. Component-scoped locals — {} found'.format(len(local_only)), '',
        'Defined on the component element itself rather than on `:root`, which is correct and '
        'intentional — they are per-instance knobs (panel widths, layout max-width, carousel '
        'progress set from JS). Nothing to fix; listed so you do not mistake them for missing.',
        '',
    ] + table(OrderedDict((k, sorted(v)) for k, v in sorted(local_only.items()))) + [
        '', '## 4. External classes this bundle expects — {} found'.format(len(external)), '',
        'Class names the bundle styles *through* (as ancestors, siblings or descendants) but '
        'never defines itself. They come from the other stylesheets loaded alongside it in the '
        'portal — OutSystems UI and the older Neo/DS component CSS. If a Fusion component looks '
        'wrong in your app, check whether it is leaning on one of these.', '',
        ', '.join('`.{}`'.format(c) for c in external),
        '', '## 5. Defined but never used inside the bundle — {} found'.format(len(unused)), '',
        'Not a bug. These are the public token API, meant to be consumed by *your* CSS. Listed '
        'so you know what is safe to drop if you trim the token set.', '',
        ', '.join('`{}`'.format(u) for u in unused),
    ]
    write(os.path.join(REFERENCE, 'audit.md'), '\n'.join(audit))

    # ---- summary ------------------------------------------------------
    print('tokens : {} light + {} dark -> {} files'.format(len(lflat), len(dflat), len(token_files)))
    print('rules  : {} top-level -> {} files'.format(
        len(chunks) - 2, len(written)))
    for layer in ('01-base', '02-components', '03-utilities'):
        names = [f for l, f in written if l == layer]
        print('  {}: {} files ({})'.format(layer, len(names), ', '.join(sorted(names))))
    print('audit  : {} genuinely broken refs, {} owned by OutSystems UI / legacy theme, '
          '{} portal chrome, {} component-scoped locals, {} unused tokens'.format(
              len(broken), len(provided), len(platform), len(local_only), len(unused)))
    build_shell()
    build_o11()
    build_odc()


if __name__ == '__main__':
    main()
