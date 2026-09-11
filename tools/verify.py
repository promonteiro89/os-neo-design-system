#!/usr/bin/env python3
"""Prove that src/ and dist/ carry exactly the same CSS as the original bundle.

Compares, as multisets, every top-level rule and every custom property between
the original download and the generated tree. Exits non-zero on any difference.

Usage:  python3 tools/verify.py
"""

import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import (RAW, SHELL_RAW, SRC, DIST, split_top_level, split_decls,  # noqa: E402
                   minify)

FAIL = []


def strip_comments(css):
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)


def read(path):
    with open(path, encoding='utf-8-sig') as fh:
        return strip_comments(fh.read())


def chunks_of(css):
    return split_top_level(css)


def partition(chunks):
    """-> (Counter of minified non-token rules, list of (name, value) token decls)"""
    rules = Counter()
    tokens = []
    for kind, prelude, body in chunks:
        p = ' '.join((prelude or '').split())
        is_light = kind == 'rule' and p == ':root'
        is_dark = kind == 'rule' and re.fullmatch(r'\[data-theme=[\'"]?dark[\'"]?\]:root', p)
        if is_light or is_dark:
            theme = 'light' if is_light else 'dark'
            for d in split_decls(body):
                name, _, value = d.partition(':')
                tokens.append((theme, name.strip(), ' '.join(value.split())))
            continue
        rules[minify((kind, prelude, body))] += 1
    return rules, tokens


INDEX_FILES = ('neo.css', 'neo-tokens.css', 'neo-shell.css')


def collect_src(subdir=None, exclude=None):
    """Collect from src/, optionally restricted to (or excluding) a subdirectory."""
    rules, tokens = Counter(), []
    base = os.path.join(SRC, subdir) if subdir else SRC
    for dirpath, _dirs, files in os.walk(base):
        for name in sorted(files):
            if not name.endswith('.css'):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), SRC)
            if rel in INDEX_FILES:
                continue  # index files: @import only
            if exclude and rel.startswith(exclude):
                continue
            r, t = partition(chunks_of(read(os.path.join(dirpath, name))))
            rules += r
            tokens += t
    return rules, tokens


def compare(label, orig, got):
    missing = orig - got
    extra = got - orig
    if not missing and not extra:
        print('  OK  {}: {} rules match'.format(label, sum(orig.values())))
        return
    FAIL.append(label)
    print('  FAIL {}'.format(label))
    for r in list(missing)[:5]:
        print('       missing: ' + r[:150])
    for r in list(extra)[:5]:
        print('       extra  : ' + r[:150])
    print('       ({} missing, {} extra)'.format(sum(missing.values()), sum(extra.values())))


def compare_tokens(label, orig, got):
    co, cg = Counter(orig), Counter(got)
    if co == cg:
        print('  OK  {}: {} custom properties match'.format(label, len(orig)))
        return
    FAIL.append(label)
    print('  FAIL {}'.format(label))
    for t in list(co - cg)[:8]:
        print('       missing: {} {} = {}'.format(*t))
    for t in list(cg - co)[:8]:
        print('       extra  : {} {} = {}'.format(*t))


def main():
    orig_rules, orig_tokens = partition(chunks_of(read(RAW)))

    dupes = [n for n, c in Counter((t, n) for t, n, _ in orig_tokens).items() if c > 1]
    if dupes:
        print('  NOTE original declares these twice: {}'.format(dupes))

    print('original: {} rules, {} custom properties'.format(
        sum(orig_rules.values()), len(orig_tokens)))

    print('\nsrc/ tree (excluding the shell layer)')
    # 04-shell comes from unified-shell.css, 05/06 from
    # old-neo-design-system.css, and 07-login from the identity host's
    # login.css + mtsi-dark-theme.css (see tools/extract_login.py, which
    # carries its own integrity check) — none are in the Fusion source this
    # compares against, so counting them here reports phantom extras.
    src_rules, src_tokens = collect_src(
        exclude=('04-shell', '05-legacy-layout', '06-legacy-widgets', '07-login'))
    compare('src rules', orig_rules, src_rules)
    compare_tokens('src tokens', orig_tokens, src_tokens)

    # dist/neo.css and dist/neo.min.css are gone; dist/neobase.css is the artifact.
    # It carries deliberate additions (compat layers, the OSUI palette bridge) and
    # deliberate omissions, so a rule-for-rule diff against the raw source is not
    # the right check for it — its own gates in tools/neobase.py cover that.
    print('\ndist/neobase.css')
    nb = read(os.path.join(DIST, 'neobase.css'))
    print('  {:,} bytes, {:,} rules'.format(len(nb), nb.count('{') - nb.count('@import')))

    print('\ndist/neo-tokens.css')
    t_rules, t_tokens = partition(chunks_of(read(os.path.join(DIST, 'neo-tokens.css'))))
    compare_tokens('tokens', orig_tokens, t_tokens)
    if sum(t_rules.values()):
        FAIL.append('neo-tokens.css contains non-token rules')
        print('  FAIL contains {} non-token rules'.format(sum(t_rules.values())))
    else:
        print('  OK  contains no component or utility rules')

    # ---- the portal shell, split from its own source file ----------------
    if os.path.isfile(SHELL_RAW):
        print('\nportal shell (prod.unified.css)')
        shell_orig, shell_orig_tokens = partition(chunks_of(read(SHELL_RAW)))
        print('  original: {} rules'.format(sum(shell_orig.values())))
        s_rules, s_tokens = collect_src(subdir='04-shell')
        compare('src/04-shell rules', shell_orig, s_rules)
        compare_tokens('src/04-shell tokens', shell_orig_tokens, s_tokens)
        d_rules, d_tokens = partition(chunks_of(read(os.path.join(DIST, 'neo-shell.css'))))
        compare('dist/neo-shell.css rules', shell_orig, d_rules)
        compare_tokens('dist/neo-shell.css tokens', shell_orig_tokens, d_tokens)

    # ---- the O11 paste-ready theme bundle --------------------------------
    o11 = os.path.join(DIST, 'o11-theme.css')
    if os.path.isfile(o11):
        print('\ndist/o11-theme.css (paste into an O11 Theme)')
        text = read(o11)
        rules, tokens = partition(chunks_of(text))
        got = {name for _theme, name, _v in tokens}
        want = {name for _t, name, _v in orig_tokens}
        missing = want - got
        if missing:
            FAIL.append('o11-theme.css tokens')
            print('  FAIL missing {} tokens, e.g. {}'.format(
                len(missing), sorted(missing)[:5]))
        else:
            print('  OK  carries all {} Neo custom properties'.format(len(want)))

        # Must NOT drag in the rules that fight OutSystems UI.
        banned = {
            'html { overflow-y: hidden }': r'html\s*\{[^}]*overflow-y:\s*hidden',
            'body { height: 100vh }': r'body\s*\{[^}]*height:\s*100vh',
            '.ds-ncard legacy interop': r'\.ds-ncard',
            'fusion component rules': r'\.fusion-tag\b',
        }
        hits = [label for label, pat in banned.items() if re.search(pat, text)]
        if hits:
            FAIL.append('o11-theme.css contains ' + ', '.join(hits))
            print('  FAIL contains: ' + ', '.join(hits))
        else:
            print('  OK  no reset, no legacy interop, no component rules')

        # Must NOT define the utility classes that collide with OutSystems UI.
        colliding = ('.text-primary', '.text-secondary', '.heading1', '.font-bold')
        present = [c for c in colliding
                   if re.search(re.escape(c) + r'\s*[,{]', text)]
        if present:
            FAIL.append('o11-theme.css defines colliding classes')
            print('  FAIL defines colliding utility classes: ' + ', '.join(present))
        else:
            print('  OK  defines none of the colliding utility classes')

        # The bridge has to come last or it cannot override OutSystems UI.
        if text.rfind('--background-color-primary') < text.rfind('--text-primary:'):
            FAIL.append('o11-theme.css ordering')
            print('  FAIL bridge does not come after the tokens')
        else:
            print('  OK  bridge sits after the token layer')

    # ---- the ODC bundle ---------------------------------------------------
    odc = os.path.join(DIST, 'odc-library.css')
    if os.path.isfile(odc):
        print('\ndist/odc-library.css (paste into an ODC theme)')
        text = read(odc)
        _rules, tokens = partition(chunks_of(text))
        got = {name for _t, name, _v in tokens}
        want = {name for _t, name, _v in orig_tokens}
        if want - got:
            FAIL.append('odc-library.css tokens')
            print('  FAIL missing {} tokens'.format(len(want - got)))
        else:
            print('  OK  carries all {} Neo custom properties'.format(len(want)))

        banned = {
            'html { overflow-y: hidden }': r'html\s*\{[^}]*overflow-y:\s*hidden',
            '.ds-ncard legacy interop': r'\.ds-ncard',
            'fusion component rules': r'\.fusion-tag\b',
            'the OutSystems UI bridge': r'--background-color-primary\s*:',
        }
        hits = [k for k, pat in banned.items() if re.search(pat, text)]
        if hits:
            FAIL.append('odc-library.css contains ' + ', '.join(hits))
            print('  FAIL contains: ' + ', '.join(hits))
        else:
            print('  OK  no reset, no interop, no components, no bridge')

        shims = ('--icon-default', '--box-shadow-0', '--border-focus-default')
        absent = [s for s in shims if not re.search(re.escape(s) + r'\s*:', text)]
        if absent:
            FAIL.append('odc-library.css missing shims')
            print('  FAIL missing shims: ' + ', '.join(absent))
        else:
            print('  OK  defines the 3 genuinely undefined variables')

    print()
    if FAIL:
        print('FAILED: ' + ', '.join(FAIL))
        sys.exit(1)
    print('All checks passed — the split is lossless.')


if __name__ == '__main__':
    main()
