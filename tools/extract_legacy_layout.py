"""Pull the portal's ACTUAL page-layout family out of the raw legacy stylesheet.

The Neo bundle (NeoDesignSystem.*.css) supplies `fusion-layout*`. The live ODC
portal does not use it for page layout — it renders `nds-layout` / `page-header-*`
/ `main-content-wrapper`, which live in old-neo-design-system.css and were never
extracted. This script recovers them so the two can be compared side by side.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import split_top_level, ROOT                      # reuse the tested splitter

RAW = os.path.join(ROOT, 'reference', 'raw', 'old-neo-design-system.css')
OUT = os.path.join(ROOT, 'src', '05-legacy-layout', 'page-layout.css')

# The families the portal actually renders for a page frame.
KEEP = re.compile(
    r'\.page-header'          # title / actions / support text / description / metadata
    r'|\.main-content'        # the content column
    r'|\.nds-layout'          # the layout root
    r'|\.layout-section'
    r'|\.theme-grid-container'
    r'|\.full-height'
    r'|(^|[\s,>+~])\.layout([\s,.:>+~{]|$)'   # bare .layout, not .layout-popup-*
    r'|(^|[\s,>+~])\.main([\s,.:>+~{]|$)'     # bare .main
)
# Portal-host chrome that only makes sense inside the unified shell.
DROP = re.compile(r'#reactContainer|\.is-unified|\.is-aside-expanded|\.unified-')


def walk(css, depth=0):
    """Yield (prelude, body) for style rules, descending into at-rules."""
    for kind, prelude, body in split_top_level(css):
        if kind != 'rule':
            continue
        p = prelude.strip()
        if p.startswith('@'):
            if p.startswith(('@media', '@supports')):
                for sub_p, sub_b, _ in walk(body, depth + 1):
                    yield sub_p, sub_b, p
            continue
        yield p, body, None


def main():
    with open(RAW, encoding='utf-8', errors='replace') as fh:
        css = fh.read()

    kept, by_cond = [], {}
    for prelude, body, cond in walk(css):
        if not KEEP.search(prelude) or DROP.search(prelude):
            continue
        (by_cond.setdefault(cond, []) if cond else kept).append((prelude, body))
        if cond:
            by_cond[cond].append  # noqa: B018  (kept for readability)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out = ['/* ' + '=' * 74 + '\n'
           '   Portal page layout — the LEGACY family the ODC portal actually renders\n'
           '   ' + '-' * 72 + '\n'
           '   Recovered from reference/raw/old-neo-design-system.css by\n'
           '   tools/extract_legacy_layout.py — do not edit by hand.\n\n'
           '   The live portal renders nds-layout / page-header-* / main-content-wrapper\n'
           '   for page layout. It renders ZERO fusion-layout* classes. Fusion supplies\n'
           '   components only (badge, pagination, dropdown-item, icon, empty-state).\n'
           '   ' + '=' * 72 + ' */\n']
    for prelude, body in kept:
        out.append('%s {%s}' % (prelude, body))
    for cond, rules in by_cond.items():
        inner = '\n'.join('  %s {%s}' % (p, b) for p, b in rules if isinstance(b, str))
        if inner.strip():
            out.append('%s {\n%s\n}' % (cond, inner))

    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('\n\n'.join(out) + '\n')
    print('legacy layout: %d top-level rules + %d conditional groups -> %s (%dKB)'
          % (len(kept), len(by_cond), os.path.relpath(OUT, ROOT), os.path.getsize(OUT) // 1024))


if __name__ == '__main__':
    main()
