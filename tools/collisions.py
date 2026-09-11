#!/usr/bin/env python3
"""Report class-name collisions between Neo's utility layer and OutSystems UI.

A collision matters only if the two stylesheets give the same class a different
value — Neo and OutSystems UI share a whole t-shirt spacing scale that resolves
identically, and those are noise. This splits the two cases by resolving each
declaration against its own :root.

Output: reference/osui-collisions.md

Usage:  python3 tools/collisions.py [path-to-outsystems-ui.css]

Defaults to reference/raw/outsystems-ui-theme.css (the build the ODC portal
bundles). Point it at your own O11 OutSystems UI file for an exact answer —
the utility layer is stable across versions, but values can move.
"""

import glob
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import (ROOT, split_top_level, split_decls, parse_decl,  # noqa: E402
                   strip_comments, write)

NEO_UTILS = os.path.join(ROOT, 'src', '03-utilities', '*.css')
DEFAULT_OSUI = os.path.join(ROOT, 'reference', 'raw', 'outsystems-ui-theme.css')
OUT = os.path.join(ROOT, 'reference', 'osui-collisions.md')


def read(path):
    with open(path, encoding='utf-8-sig') as fh:
        return strip_comments(fh.read())


def single_class_rules(paths):
    """{class: {prop: value}} for rules whose selector is exactly one class."""
    out = {}
    for p in paths:
        for kind, prelude, body in split_top_level(read(p)):
            if kind != 'rule' or prelude.startswith('@'):
                continue
            for sel in prelude.split(','):
                sel = sel.strip()
                if not re.fullmatch(r'\.[A-Za-z_][\w-]*', sel):
                    continue
                d = {}
                for decl in split_decls(body):
                    prop, val = parse_decl(decl)
                    # Service Studio-only properties never reach the browser.
                    if val and not prop.startswith('-servicestudio'):
                        d[prop] = ' '.join(val.split())
                out.setdefault(sel[1:], {}).update(d)
    return out


def root_vars(paths):
    table = {}
    for p in paths:
        for kind, prelude, body in split_top_level(read(p)):
            if kind == 'rule' and prelude.strip() == ':root':
                for decl in split_decls(body):
                    prop, val = parse_decl(decl)
                    if val:
                        table[prop] = ' '.join(val.split())
    return table


def resolve(value, table, depth=8):
    """Follow a plain `var(--x)` / `var(--x, fallback)` chain to a literal."""
    for _ in range(depth):
        m = re.fullmatch(r'var\((--[\w-]+)(?:\s*,.*)?\)', value.strip())
        if not m or m.group(1) not in table:
            break
        value = table[m.group(1)]
    return value


def main():
    osui_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OSUI
    neo_files = sorted(glob.glob(NEO_UTILS))
    neo = single_class_rules(neo_files)
    osui = single_class_rules([osui_path])
    neo_root = root_vars(sorted(glob.glob(
        os.path.join(ROOT, 'src', '00-tokens', '**', '*.css'), recursive=True)))
    osui_root = root_vars([osui_path])

    version = 'unknown'
    with open(osui_path, encoding='utf-8-sig') as fh:
        head = fh.read(400)
    m = re.search(r'OutSystems UI ([\d.]+)', head)
    if m:
        version = m.group(1)

    identical, differing = [], []
    for cls in sorted(set(neo) & set(osui)):
        a = {k: resolve(v, neo_root) for k, v in neo[cls].items()}
        b = {k: resolve(v, osui_root) for k, v in osui[cls].items()}
        shared = sorted(set(a) & set(b))
        if not shared:
            differing.append((cls, '(different properties)',
                              '; '.join(f'{k}: {v}' for k, v in list(a.items())[:2]),
                              '; '.join(f'{k}: {v}' for k, v in list(b.items())[:2])))
        elif all(a[k] == b[k] for k in shared):
            identical.append(cls)
        else:
            for k in shared:
                if a[k] != b[k]:
                    differing.append((cls, k, a[k], b[k]))
                    break

    md = [
        '# Neo utilities vs OutSystems UI — class-name collisions', '',
        f'Generated on {date.today().isoformat()} by `tools/collisions.py`.', '',
        f'* Neo utility classes: **{len(neo)}** (from `src/03-utilities/`)',
        f'* OutSystems UI classes: **{len(osui)}** (version **{version}**, `{os.path.basename(osui_path)}`)',
        f'* Shared names: **{len(identical) + len(differing)}**',
        f'* Of those, value-identical: **{len(identical)}** — harmless',
        f'* Value-different: **{len(differing)}** — real behaviour change', '',
        'Whichever stylesheet loads **last** wins. Both files are flat utility',
        'layers with no specificity tricks, so ordering is the only factor.', '',
        '## Real behaviour changes', '',
        'Watch `.text-primary` and `.text-secondary` especially: the two systems',
        'mean *opposite* things by them. In Neo they are body and muted text; in',
        'OutSystems UI they are the brand colours. Loading Neo\'s utilities after',
        'OutSystems UI turns brand-blue text near-black on existing screens.', '',
        '| Class | Property | Neo | OutSystems UI |', '| --- | --- | --- | --- |',
    ]
    for cls, prop, a, b in differing:
        md.append('| `.{}` | `{}` | `{}` | `{}` |'.format(
            cls, prop, a.replace('|', '\\|')[:44], b.replace('|', '\\|')[:44]))

    md += [
        '', '## Value-identical (safe to ignore)', '',
        'Almost entirely the t-shirt spacing scale — both systems resolve',
        '`xs/s/base/m/l/xl/xxl` to 4/8/16/24/32/40/48px.', '',
        ', '.join(f'`.{c}`' for c in identical), '',
        '## Avoiding the problem', '',
        'Use `compat/neo-osui-bridge.css` instead of Neo\'s colour and typography',
        'utilities. The bridge re-skins OutSystems UI widgets through its own',
        'variables, so you get the Neo look without introducing any class that',
        'OutSystems UI already owns. If you do want Neo\'s utilities, the safe',
        'subset is `src/03-utilities/` minus `colors.css` and `typography.css`.',
    ]
    write(OUT, '\n'.join(md))
    print('OutSystems UI {}: {} shared names -> {} identical, {} differing'.format(
        version, len(identical) + len(differing), len(identical), len(differing)))
    print('wrote', os.path.relpath(OUT, ROOT))


if __name__ == '__main__':
    main()
