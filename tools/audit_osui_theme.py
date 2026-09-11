"""Audit reference/raw/outsystems-ui-theme.css against what NeoBase ships.

That file is `NeoDesignSystem.OutSystemsUITheme` — one of the four design-system
stylesheets the portal loads, and the one nothing in our build currently reads.
`.ph:empty { display: none }` was found only there, so it demonstrably carries
rules we lose. This scores what else is missing, weighted by whether the portal
actually renders the classes involved.
"""
import os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import split_top_level, ROOT

THEME = os.path.join(ROOT, 'reference', 'raw', 'outsystems-ui-theme.css')
OURS = os.path.join(ROOT, 'dist', 'neobase.css')
CENSUS = os.path.join(ROOT, 'reference', 'portal-dom', 'logic.classes.txt')


def rules_of(path):
    """(normalised selector, declaration text) for every style rule, at any depth."""
    out = []

    def walk(css):
        for kind, prelude, body in split_top_level(css):
            if kind != 'rule':
                continue
            p = prelude.strip()
            if p.startswith('@'):
                if p.startswith(('@media', '@supports')):
                    walk(body)
                continue
            out.append((re.sub(r'\s+', ' ', p), re.sub(r'\s+', ' ', body).strip()))
    with open(path, encoding='utf-8', errors='replace') as fh:
        css = fh.read()
    # Strip comments FIRST. split_top_level counts braces and does not skip
    # comments — its usual inputs are minified vendor CSS with none. neobase.css
    # is full of prose containing braces (`.ph:empty { display: none }`), which
    # desynchronises the brace counter and silently loses ~70% of the rules.
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    walk(css)
    return out


def portal_classes():
    txt = open(CENSUS, encoding='utf-8').read()
    return {c.split(':')[0] for c in re.findall(r'([A-Za-z][\w-]*):\d+', txt)}


def main():
    theme = rules_of(THEME)
    ours = rules_of(OURS)
    have = {s for s, _ in ours}
    rendered = portal_classes()

    missing = [(s, b) for s, b in theme if s not in have]
    # does the selector reference a class the portal actually renders?
    def relevant(sel):
        return any(c in rendered for c in re.findall(r'\.([A-Za-z][\w-]*)', sel))

    hot = [(s, b) for s, b in missing if relevant(s)]

    def family(sel):
        m = re.search(r'\.([a-z][\w-]*)', sel)
        if not m:
            return '(element/other)'
        n = m.group(1)
        for pref in ('unified-', 'fusion-', 'ds-', 'page-header', 'main-content',
                     'table', 'btn', 'form-', 'input', 'avatar', 'badge', 'card',
                     'list', 'dropdown', 'tooltip', 'pagination', 'icon', 'ph'):
            if n.startswith(pref):
                return pref.rstrip('-')
        return n.split('-')[0]

    print('outsystems-ui-theme.css : %d rules' % len(theme))
    print('dist/neobase.css        : %d rules' % len(ours))
    print('missing from ours       : %d' % len(missing))
    print('  ...of which reference a class the portal renders: %d' % len(hot))
    print()
    by = collections.Counter(family(s) for s, _ in hot)
    print('%-22s %s' % ('family', 'missing rules that matter'))
    for fam, n in by.most_common(18):
        print('  %-20s %d' % (fam, n))
    print()
    print('sample (selector -> first declaration):')
    for s, b in hot[:22]:
        print('  %-56s %s' % (s[:56], b[:56]))


if __name__ == '__main__':
    main()
