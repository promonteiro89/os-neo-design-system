"""Recover the few LEGACY widget families the ODC portal actually renders.

`old-neo-design-system.css` carries 1114 `ds-*` selectors, so this extracts a
whitelist, not the library.

The whitelist is only ever as good as the pages you looked at. It began as a
census of TWO portal pages, which found `ds-avatar` and
`ds-page-title-left-element-wrapper`. On 2026-09-07 a sweep of 31 pages —
including log, trace and app DETAIL pages, which the original census never
opened — found `ds-accordion` rendering too, and it had been missing from the
bundle entirely. Widen this list from evidence, and prefer detail//interaction
views: list pages do not exercise most widgets.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import split_top_level, ROOT

RAW = os.path.join(ROOT, 'reference', 'raw', 'old-neo-design-system.css')
OUT = os.path.join(ROOT, 'src', '06-legacy-widgets', 'widgets.css')

# Whitelist: verified rendered on the portal.
#
# ds-accordion added 2026-09-07. The portal's accordion is NOT fusion-accordion
# (0 instances anywhere on 31 pages) — it is OutSystems UI's `osui-accordion`
# wrapped in the legacy `ds-accordion-item`, e.g. on a Logs detail page:
#   <div class="ds-accordion-item is--right">
#     <div class="osui-accordion-item osui-accordion-item--is-closed">
# We already carried the osui half (38 rules, via osui_reskin.py) but none of
# the 12 ds-accordion rules, so the wrapper was unstyled.
KEEP = re.compile(r'\.(ds-avatar|avatar-format-|avatar-color-|avatar-size-|table|sortable|input-clear-search|clear-search|input-search|svg-code)(?![a-z])')

# ds-accordion is matched separately, NOT by adding it to KEEP, because it needs
# an exclusion that the rest of the whitelist must not get.
ACCORDION = re.compile(r'\.ds-accordion(?![a-z])')

# Two `:where(...)` rules name `.ds-accordion-item` in a long ancestor list but
# actually style `.ds-ncard`, a card family with no other presence in the
# bundle. They are the only reason this exclusion exists.
#
# It is applied ONLY to the accordion branch, deliberately. Applying it to every
# rule cost 11 real table rules on the first attempt: selectors like
#   :where(.section-expandable,.osui-accordion-item,.card,...,.ds-ncard) .table
# name `.ds-ncard` as one ancestor ALTERNATIVE while styling `.table`, which we
# do ship. A whole-selector substring test cannot tell an ancestor alternative
# from the rule's subject, so scope the test as narrowly as the problem.
DROP_CARD = re.compile(r'\.ds-ncard')

# The skeleton (loading placeholder) family, added 2026-09-08. The portal renders
# it on every list page while data loads — the Users page shows a header row plus
# ten shimmering row placeholders — and the bundle carried 53 skeleton MENTIONS
# but not one rule of the component itself: only context overrides recovered
# incidentally by other extractors, e.g.
#   .table-small .skeleton-table-header-item { height: var(--size-9) }
# So we were shipping the adjustments to a component we never shipped.
#
# Two reasons it was missed. It lives only in this legacy stylesheet (the Fusion
# bundle has no skeleton component at all), and KEEP above cannot see it: the
# `.table` alternative matches `.table`, while these selectors read
# `.skeleton-table`, where the substring is `-table`.
#
# SKELETON keeps only rules whose SUBJECT is a skeleton class, which is what makes
# the component self-contained. The raw file also holds ~23 skeleton rules scoped
# under families we deliberately do not ship (ds-card, ds-tabs, ds-code-snippet,
# ds-tree-view, app-representation, page-wizard); those are dead without their
# ancestor, exactly like the fusion-layout family neobase.py drops, so IS_SUBJECT
# rejects them. It admits bare `div` because the table skeleton's wrappers are
# plain divs (`.skeleton-table-header>div`), and `:where(...)`/`[data-theme=dark]`
# because a zero-specificity ancestor list and the dark shimmer override are part
# of the component.
#
# Document order is what makes this safe: the base `.skeleton-box` sits at byte
# 80441 and the `:where(...)` background override at 477048, so walking the file
# in order emits the base BEFORE the override. That matters because `:where()`
# contributes no specificity — the override wins on order alone.
SKELETON = re.compile(r'\.skeleton(?![a-z])')
SUBJECT_NOISE = (
    re.compile(r':where\([^)]*\)'),      # zero-specificity ancestor alternatives
    re.compile(r':not\([^)]*\)'),
    re.compile(r'\[data-theme=dark\]'),
    re.compile(r'\.skeleton[\w-]*'),
    re.compile(r'::?[a-z-]+'),           # :first-child, :after ...
    re.compile(r'\bdiv\b'),
    re.compile(r'[>+~,]'),
)


def is_skeleton_subject(prelude):
    """True when every part of the selector is styling a skeleton element."""
    s = prelude
    for rx in SUBJECT_NOISE:
        s = rx.sub(' ', s)
    return not s.strip()


ANIMATION = re.compile(r'animation:\s*([\w-]+)')


def collect(css, out):
    for kind, prelude, body in split_top_level(css):
        if kind != 'rule':
            continue
        p = prelude.strip()
        if p.startswith('@'):
            if p.startswith(('@media', '@supports')):
                collect(body, out)
            continue
        if (KEEP.search(p)
                or (ACCORDION.search(p) and not DROP_CARD.search(p))
                or (SKELETON.search(p) and is_skeleton_subject(p))):
            out.append((p, body))


def keyframes_for(css, kept):
    """The @keyframes blocks the kept rules name, in the order first referenced.

    Pulled by reference rather than by a hardcoded list so a future skeleton or
    widget rule that animates something new cannot ship without its animation —
    which is the shape of the bug this whole file exists to fix.
    """
    wanted = []
    for _, body in kept:
        for name in ANIMATION.findall(body):
            if name not in wanted:
                wanted.append(name)
    found = []
    for name in wanted:
        m = re.search(r'@keyframes\s+' + re.escape(name) + r'\s*\{', css)
        if not m:
            continue
        depth, i = 0, m.end() - 1
        while i < len(css):
            if css[i] == '{':
                depth += 1
            elif css[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        found.append(css[m.start():i + 1])
    return found


def main():
    with open(RAW, encoding='utf-8', errors='replace') as fh:
        css = fh.read()
    kept = []
    collect(css, kept)

    # Skip any animation the base layer already defines, so the two layers can
    # never ship the same @keyframes twice.
    base_path = os.path.join(ROOT, 'src', '01-base', 'animations.css')
    base = ''
    if os.path.isfile(base_path):
        with open(base_path, encoding='utf-8') as fh:
            base = fh.read()
    frames = [k for k in keyframes_for(css, kept)
              if re.match(r'@keyframes\s+([\w-]+)', k)
              and '@keyframes ' + re.match(r'@keyframes\s+([\w-]+)', k).group(1) not in base]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    banner = ('/* ' + '=' * 74 + '\n'
              '   ds-avatar + ds-accordion + skeleton — recovered from\n'
              '   reference/raw/old-neo-design-system.css\n'
              '   ' + '-' * 72 + '\n'
              '   A whitelisted subset of the 1114-selector ds-* library; the rest is dead\n'
              '   on every portal page measured and deliberately not extracted.\n'
              '   ds-avatar renders 10 elements on /usersaccess/. ds-accordion wraps the\n'
              '   OutSystems UI accordion on detail pages such as a Logs entry, where the\n'
              '   portal emits `<div class="ds-accordion-item is--right">` around\n'
              '   `<div class="osui-accordion-item">`.\n'
              '   The skeleton family is the portal\'s loading placeholder, shown on every\n'
              '   list page while data loads. It is here rather than in a component file\n'
              '   because it exists only in this legacy stylesheet.\n'
              '   Generated by tools/extract_legacy_widgets.py.\n'
              '   ' + '=' * 72 + ' */\n\n')
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write(banner
                 + ''.join(k + '\n\n' for k in frames)
                 + '\n\n'.join('%s {%s}' % (p, b) for p, b in kept) + '\n')
    print('legacy widgets: %d rules + %d keyframes -> %s (%dKB)'
          % (len(kept), len(frames), os.path.relpath(OUT, ROOT), os.path.getsize(OUT) // 1024))


if __name__ == '__main__':
    main()
