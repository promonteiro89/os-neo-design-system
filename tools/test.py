#!/usr/bin/env python3
"""Regression tests for the tree and the shipped bundle.

    python3 tools/test.py          run everything
    python3 tools/test.py -v       also print what each check looked at

Standard-library Python 3 only, same as the rest of tools/. Exits non-zero on
the first category that fails, so it is safe to put in front of a commit.

WHAT THIS CAN AND CANNOT COVER. Everything here runs against the repository:
the source tree, the generated bundle, and the behaviour scripts. It proves the
artifact you are about to paste is internally consistent and that the build that
produced it is reproducible. It cannot see the ODC side — the library's blocks,
a block's argument expressions, or whether a consumer's pin was bumped. Those
have no local representation, so a change made through Mentor or Service Studio
is outside every check below and still has to be verified on the harness.

Each check exists because the thing it tests actually broke at least once.
"""

import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERBOSE = '-v' in sys.argv or '--verbose' in sys.argv

BUNDLE = os.path.join(ROOT, 'dist', 'neobase.css')

# Custom properties the bundle references but never defines. Every one is
# deliberate, and they fall into three groups:
#
#   set at runtime      a JS or inline style supplies the value per instance
#                       (--progress-rate, --time-to-live, --hidden-label)
#   owned elsewhere     OutSystems UI or the legacy theme defines it, and we
#                       only read it (--color-neutral-2, --surface-1, --linear)
#   component-scoped    the portal declares it on the component's own element,
#                       which is markup we do not ship (--fusion-* locals)
#
# The list is a baseline, not an approval: a NEW undefined reference is a
# genuine regression — a token renamed in one layer and not the other, which
# resolves to nothing and silently drops the declaration.
KNOWN_UNDEFINED = {
    '--border-size-none',
    '--color-neutral-2',
    '--font-size-xxs',
    '--footer-size',
    '--fusion-dropdown-empty-trigger-background',
    '--fusion-layout-sticky-top-offset',
    '--fusion-range-slider-track-height',
    '--fusion-range-slider-track-max-width',
    '--fusion-range-slider-track-min-width',
    '--fusion-slider-track-height',
    '--fusion-slider-track-max-width',
    '--fusion-slider-track-min-width',
    '--hidden-label',
    '--linear',
    '--progress-rate',
    '--surface-1',
    '--time-m',
    '--time-to-live',
}

# url() hosts the bundle is allowed to reach out to. Google Fonts is the one
# external dependency and ODC reports it as an offline-behaviour warning.
ALLOWED_REMOTE = ('https://fonts.googleapis.com/',)


# --------------------------------------------------------------------------
# harness
# --------------------------------------------------------------------------

class Results:
    def __init__(self):
        self.failures = []
        self.passed = 0

    def ok(self, name, detail=''):
        self.passed += 1
        print('  OK   %-44s %s' % (name, detail))

    def fail(self, name, detail):
        self.failures.append((name, detail))
        print('  FAIL %-44s %s' % (name, detail))


def read(path):
    with open(path, encoding='utf-8-sig') as fh:
        return fh.read()


def strip_comments(css):
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)


def run(cmd):
    """Run a command from the repo root; return (exit code, combined output)."""
    p = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


def snapshot_generated():
    """sha256 of every file the build can write, keyed by repo-relative path."""
    seen = {}
    for sub in ('dist', 'src'):
        for dirpath, _, filenames in os.walk(os.path.join(ROOT, sub)):
            if '.git' in dirpath.split(os.sep):
                continue
            for fn in filenames:
                p = os.path.join(dirpath, fn)
                with open(p, 'rb') as fh:
                    seen[os.path.relpath(p, ROOT)] = hashlib.sha256(
                        fh.read()).hexdigest()
    return seen


INITIAL = {}          # filled in main(), before any check runs


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def check_no_duplicate_files(r):
    """Finder/iCloud copies ("foo 2.css") must not exist.

    This repository lives under ~/Documents, so iCloud recreates these on its
    own — they are not a one-off mistake to clean up once. They matter because
    tools/verify.py walks src/00-tokens/components/*.css: a "_tab 2.css" beside
    "_tab.css" gets read as a second definition of every token in it, and
    verify.py fails with tokens it calls "extra". It does not affect the built
    bundle, which assembles the token layer from an explicit file list.
    """
    dupes = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if '.git' in dirpath.split(os.sep):
            continue
        for fn in filenames:
            if re.search(r' \d\.[^.]+$', fn):
                dupes.append(os.path.relpath(os.path.join(dirpath, fn), ROOT))
    if dupes:
        r.fail('no duplicate files',
               '%d found, e.g. %s' % (len(dupes), dupes[0]))
        if VERBOSE:
            for d in sorted(dupes):
                print('         %s' % d)
    else:
        r.ok('no duplicate files')


def check_build_is_reproducible(r):
    """Rebuilding must not change any tracked file.

    If this fails, the committed dist/ is not what the current src/ and tools/
    produce — so the bundle in the repo is not the bundle you would paste, and
    reviewing the diff tells you nothing about what ships.
    """
    # Compare against the snapshot taken before ANY check ran. Some checks
    # regenerate the bundle as a side effect (the guards live inside neobase.py
    # and only run while it writes), so snapshotting here would compare the
    # build against itself and pass no matter what was committed.
    before = INITIAL
    code, out = run(['sh', 'tools/build_all.sh'])
    if code != 0:
        r.fail('build reproducible', 'build_all.sh exited %d' % code)
        if VERBOSE:
            print(out)
        return
    after = snapshot_generated()

    changed = sorted(p for p in set(before) & set(after)
                     if before[p] != after[p])
    added = sorted(set(after) - set(before))
    if changed or added:
        r.fail('build reproducible',
               '%d file(s) rewritten by a rebuild' % (len(changed) + len(added)))
        for f in (changed + added)[:10]:
            print('         %s' % f)
    else:
        r.ok('build reproducible', '%d generated files byte-identical'
             % len(after))


def check_verify_py(r):
    """tools/verify.py: the split back into src/ and dist/ is lossless."""
    code, out = run(['python3', 'tools/verify.py'])
    if code != 0:
        bad = [l.strip() for l in out.splitlines() if 'FAIL' in l]
        r.fail('verify.py (lossless split)',
               bad[0] if bad else 'exit %d' % code)
        if VERBOSE:
            print(out)
    else:
        r.ok('verify.py (lossless split)')


def check_bundle_guards(r):
    """tools/neobase.py's own guards must all report CLEAN."""
    code, out = run(['python3', 'tools/neobase.py'])
    if code != 0:
        r.fail('bundle guards', 'neobase.py exited %d' % code)
        return
    guards = re.findall(r'^\s{2}(\S.*?)\s{2,}(CLEAN|.+)$', out, re.M)
    dirty = [(n, v) for n, v in guards if v.strip() != 'CLEAN']
    if not guards:
        r.fail('bundle guards', 'no guard output found')
    elif dirty:
        r.fail('bundle guards', '%s: %s' % dirty[0])
    else:
        r.ok('bundle guards', '%d clean' % len(guards))


def check_no_undefined_tokens(r):
    """Every var(--x) in the bundle resolves, apart from a known baseline."""
    css = strip_comments(read(BUNDLE))
    defined = set(re.findall(r'(--[A-Za-z0-9_-]+)\s*:', css))
    used = set(re.findall(r'var\(\s*(--[A-Za-z0-9_-]+)', css))
    undefined = used - defined
    new = sorted(undefined - KNOWN_UNDEFINED)
    gone = sorted(KNOWN_UNDEFINED - undefined)
    if new:
        r.fail('no new undefined tokens',
               '%d new: %s' % (len(new), ', '.join(new[:4])))
        if VERBOSE:
            for n in new:
                print('         %s' % n)
    elif gone:
        # Not a failure: something got defined. Say so, so the baseline can shrink.
        r.ok('no new undefined tokens',
             '%d baseline entr%s now defined — prune KNOWN_UNDEFINED'
             % (len(gone), 'y is' if len(gone) == 1 else 'ies are'))
    else:
        r.ok('no new undefined tokens',
             '%d defined, %d used' % (len(defined), len(used)))


def check_asset_references(r):
    """Every url() is either an ODC authoring path with a file behind it, or
    an allowed remote.

    An ODC authoring path (/NeoDesignSystem/img/Module.Image.svg) 404s if you
    fetch it and is still correct — ODC rewrites it to a hashed path when the
    library publishes. What must hold is that the SVG exists in this repo, so
    there is something to upload as the library Image. A missing file means the
    icon resolves to nothing at runtime, with no console error.

    A relative url() is a separate failure: it would not resolve in ODC at all.
    Inlined data: URIs are banned because they bloat the paste and cannot be
    swapped per theme.
    """
    css = read(BUNDLE)
    urls = {u.strip('\'" ') for u in re.findall(r'url\(\s*([^)]+?)\s*\)', css)}

    svgs = set()
    for sub in ('dist', 'src'):
        for dirpath, _, filenames in os.walk(os.path.join(ROOT, sub)):
            for fn in filenames:
                if fn.lower().endswith('.svg'):
                    svgs.add(fn.lower())

    missing, relative, inlined = [], [], []
    authoring = 0
    for u in sorted(urls):
        if u.startswith('data:'):
            inlined.append(u[:40])
        elif u.startswith('/NeoDesignSystem/'):
            authoring += 1
            stem = u.rsplit('/', 1)[-1]                  # Module.Image.svg
            name = stem.split('.')[-2].lower()           # Image
            if not any(name in s for s in svgs):
                missing.append(u)
        elif u.startswith(ALLOWED_REMOTE):
            pass
        elif u.startswith(('http://', 'https://')):
            relative.append('unexpected remote: ' + u)
        else:
            relative.append(u)

    if inlined:
        r.fail('asset references', '%d inlined data: URI(s)' % len(inlined))
    elif relative:
        r.fail('asset references',
               '%d url(s) would not resolve in ODC: %s' % (len(relative), relative[0]))
    elif missing:
        r.fail('asset references',
               '%d authoring path(s) with no SVG in the repo: %s'
               % (len(missing), missing[0]))
    else:
        r.ok('asset references', '%d authoring paths, all backed' % authoring)


def check_behaviour_scripts_parse(r):
    """behaviour/*.js must parse.

    These are pasted into a block's OnReady as a JavaScript node, where a syntax
    error surfaces as the whole component silently doing nothing.
    """
    d = os.path.join(ROOT, 'behaviour')
    if not os.path.isdir(d):
        r.fail('behaviour scripts parse', 'behaviour/ is missing')
        return
    scripts = sorted(f for f in os.listdir(d) if f.endswith('.js'))
    if not scripts:
        r.fail('behaviour scripts parse', 'no scripts found')
        return
    code, out = run(['node', '--version'])
    if code != 0:
        r.ok('behaviour scripts parse', 'skipped: node not installed')
        return
    bad = []
    for s in scripts:
        code, out = run(['node', '--check', os.path.join('behaviour', s)])
        if code != 0:
            bad.append((s, out.strip().splitlines()[-1] if out.strip() else ''))
    if bad:
        r.fail('behaviour scripts parse', '%s: %s' % bad[0])
    else:
        r.ok('behaviour scripts parse', '%d script(s)' % len(scripts))


def check_behaviour_scripts_are_self_installing(r):
    """Each behaviour script must be safe to run more than once.

    ODC re-runs a block's OnReady on every render of that block. A script that
    binds on each run stacks duplicate handlers, and the symptom is a toggle
    that fires twice and appears not to work at all. Both scripts guard against
    this — one with a dataset flag, one with an install-once module flag — so
    the test is that some re-entry guard is present, not which one.
    """
    d = os.path.join(ROOT, 'behaviour')
    if not os.path.isdir(d):
        r.fail('behaviour re-entry guards', 'behaviour/ is missing')
        return
    unguarded = []
    for s in sorted(f for f in os.listdir(d) if f.endswith('.js')):
        src = read(os.path.join(d, s))
        if not re.search(r'dataset\.\w+|__neo\w+|data-neo', src):
            unguarded.append(s)
    if unguarded:
        r.fail('behaviour re-entry guards', ', '.join(unguarded))
    else:
        r.ok('behaviour re-entry guards')


def check_docs_reference_real_paths(r):
    """Paths named in the README's layout tree must exist.

    The tree drifted badly once: it listed a dist/ file that had been removed
    and omitted three src/ layers and the whole behaviour/ directory.
    """
    readme = read(os.path.join(ROOT, 'README.md'))
    m = re.search(r'^## Layout\n\n```\n(.*?)^```', readme, re.S | re.M)
    if not m:
        r.fail('README paths exist', 'could not find the layout tree')
        return

    # The tree is two columns: a name, then its description from column 27.
    # A line whose text starts at or past that column is a wrapped description,
    # not an entry. Indentation nests an entry under the last shallower one.
    DESC_COL = 27
    missing = []
    stack = []                                   # [(indent, path), ...]
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent >= DESC_COL:
            continue
        name = line.split()[0]
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1] if stack else ''
        path = os.path.join(parent, name.rstrip('/'))
        if name.endswith('/'):
            stack.append((indent, path))
        if '*' in name:                          # a glob standing for a family
            continue
        if not os.path.exists(os.path.join(ROOT, path)):
            missing.append(path)
    if missing:
        r.fail('README paths exist', '%d missing: %s' % (len(missing), missing[0]))
        if VERBOSE:
            for p in missing:
                print('         %s' % p)
    else:
        r.ok('README paths exist')


CHECKS = [
    ('tree', [check_no_duplicate_files]),
    ('bundle', [check_no_undefined_tokens,
                check_asset_references,
                check_bundle_guards]),
    ('behaviour', [check_behaviour_scripts_parse,
                   check_behaviour_scripts_are_self_installing]),
    ('docs', [check_docs_reference_real_paths]),
    ('build', [check_verify_py, check_build_is_reproducible]),
]


def main():
    global INITIAL
    INITIAL = snapshot_generated()
    r = Results()
    for group, checks in CHECKS:
        print('\n%s' % group)
        for c in checks:
            try:
                c(r)
            except Exception as exc:                      # noqa: BLE001
                r.fail(c.__name__, 'raised %s: %s' % (type(exc).__name__, exc))

    print()
    if r.failures:
        print('FAILED: %d of %d checks' % (len(r.failures), r.passed + len(r.failures)))
        for name, detail in r.failures:
            print('  %-44s %s' % (name, detail))
        return 1
    print('All %d checks passed.' % r.passed)
    print('Note: this covers the repository only. Changes made in ODC — block '
          'expressions,\nlibrary releases, consumer pins — have no local '
          'representation and are not tested here.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
