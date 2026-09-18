#!/usr/bin/env python3
"""Runtime tests against the deployed ODC app.

    python3 tools/test_runtime.py          run everything
    python3 tools/test_runtime.py -v       also list what each check looked at

Standard-library Python 3 only, same as the rest of tools/. Needs network and a
published app; exits non-zero on failure.

WHY THIS EXISTS, AND WHAT tools/test.py CANNOT DO. test.py proves the repository
is internally consistent: the bundle is what src/ builds, every token resolves,
the scripts parse. It says nothing about whether any of that reached ODC. The
expensive failures on this project have all lived in that gap:

  - a library published but never RELEASED, so no consumer sees it
  - a library released but the consumer's pin never bumped
  - a consumer publish from a stale session silently reverting a pin bump
  - a theme paste rolled back by a later publish
  - a library Image missing, so an icon resolves to nothing at runtime

Every one of those leaves the repository green and the running app wrong. The
checks below all ask the deployed app what it is actually serving.

CONFIGURATION. The app's base URL is configuration, not source, the same way
the tenant host is: put it in a gitignored `odc-app` file at the repo root
(copy odc-app.example), or set $ODC_APP. For example:

    https://your-env.outsystems.app/YourApp
"""

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERBOSE = '-v' in sys.argv or '--verbose' in sys.argv
TIMEOUT = 30

# The harness's screens. Not discoverable: ODC's module manifest lists versioned
# assets, not screens, so this is a deliberate inventory — adding a screen means
# adding it here, which is the point.
SCREENS = ['Home', 'Login', 'SignUp', 'VerifyEmail', 'ResetPassword']

# A screen that must NOT exist. Without it, "every screen returns 200" would
# also pass against a server that answers 200 for everything, which is exactly
# what a misconfigured route or a catch-all error page looks like.
ABSENT_SCREEN = 'ScreenThatMustNotExist'

# The library stylesheet the consumer should be serving, by filename stem.
LIBRARY_CSS = 'NeoDesignSystem.NeoBase'
LOCAL_BUNDLE = os.path.join(ROOT, 'dist', 'neobase.css')


# --------------------------------------------------------------------------
# harness
# --------------------------------------------------------------------------

class Results:
    def __init__(self):
        self.failures = []
        self.passed = 0

    def ok(self, name, detail=''):
        self.passed += 1
        print('  OK   %-40s %s' % (name, detail))

    def fail(self, name, detail):
        self.failures.append((name, detail))
        print('  FAIL %-40s %s' % (name, detail))


def base_url():
    env = os.environ.get('ODC_APP')
    if env:
        return env.rstrip('/')
    path = os.path.join(ROOT, 'odc-app')
    if os.path.isfile(path):
        with open(path, encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith('#'):
                    return line.rstrip('/')
    return None


def fetch(url, want_bytes=False):
    """GET url. Returns (status, body) — status 0 with the reason on failure."""
    req = urllib.request.Request(url, headers={'User-Agent': 'neo-runtime-tests'})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read()
            return r.status, body if want_bytes else body.decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception as e:                                    # noqa: BLE001
        return 0, '%s: %s' % (type(e).__name__, e)


# --------------------------------------------------------------------------
# comparing served CSS with the repo's bundle
# --------------------------------------------------------------------------

_KEYFRAME = re.compile(r'^(from|to|[\d.]+%)$')


def selector_atoms(css):
    """The set of individual selectors in a stylesheet, normalised.

    ODC minifies a pasted theme on publish, so the served bytes never match the
    file you pasted and a byte or rule-count comparison is useless. Three of its
    transformations have to be undone before the two sides can be compared:

        combinator spacing   "a > b"            -> "a>b"
        attribute quoting    "[type='checkbox']"-> "[type=checkbox]"
        rule merging         two rules with identical declarations become one
                             comma-separated selector list

    Splitting every selector list into its individual selectors makes the last
    one a non-issue: a merged rule decomposes to exactly the same atoms. Double
    colons are folded to single so ::before and :before compare equal, and
    keyframe stops are dropped — they are positions, not selectors.

    On a correctly deployed app the two sides come out exactly equal.
    """
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    out = set()
    for m in re.finditer(r'([^{}]+)\{', css):
        sel = m.group(1)
        if '@' in sel or ';' in sel:
            continue
        for one in sel.split(','):
            one = re.sub(r'\s+', ' ', one).strip()
            one = re.sub(r'\s*([>+~])\s*', r'\1', one)
            one = one.replace('::', ':')
            one = re.sub(
                r'\[([^\]]*)\]',
                lambda mm: '[' + mm.group(1).replace('"', '').replace("'", '')
                                            .replace(' ', '') + ']',
                one)
            if one and not _KEYFRAME.match(one):
                out.add(one)
    return out


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def check_pages(r, base):
    """Every screen answers 200, and a screen that does not exist answers 404."""
    broken = []
    for s in SCREENS:
        status, _ = fetch('%s/%s' % (base, s))
        if status != 200:
            broken.append('%s -> %s' % (s, status or 'unreachable'))
        elif VERBOSE:
            print('         %-18s 200' % s)

    status, _ = fetch('%s/%s' % (base, ABSENT_SCREEN))
    if broken:
        r.fail('pages reachable', '; '.join(broken))
    elif status != 404:
        r.fail('pages reachable',
               'a missing screen returned %s, not 404 — "200" proves nothing here'
               % status)
    else:
        r.ok('pages reachable', '%d screens, 404 control passed' % len(SCREENS))


def check_manifest(r, base, state):
    """The module manifest is readable and lists the library stylesheet.

    The manifest is how the running app resolves a versioned asset URL. It is
    also the only way to discover the library CSS's hashed filename without
    executing the page's JavaScript, which is why it is fetched before anything
    that needs that URL.
    """
    status, body = fetch('%s/moduleservices/moduleinfo' % base)
    if status != 200:
        r.fail('module manifest', 'moduleinfo -> %s' % (status or body))
        return
    try:
        urls = json.loads(body)['manifest']['urlVersions']
    except Exception as e:                                    # noqa: BLE001
        r.fail('module manifest', 'unparseable: %s' % e)
        return

    hit = [u for u in urls if LIBRARY_CSS in u and u.endswith('.css')]
    if not hit:
        r.fail('module manifest',
               '%s is not served — library not referenced, or the consumer was '
               'never republished' % LIBRARY_CSS)
        return
    state['css_url'] = urllib.parse.urljoin(base + '/', hit[0] + urls[hit[0]])
    r.ok('module manifest', '%d versioned assets, library CSS present' % len(urls))


def check_library_css_matches_repo(r, base, state):
    """The CSS the app serves carries every selector the repo's bundle has.

    This is the check that catches the whole family of "it is green here and
    wrong there" failures: a library published but not released, a pin never
    bumped, a pin bump reverted by a later consumer publish, a theme paste
    rolled back. All of them show up the same way — selectors that exist in
    dist/neobase.css and are missing from what the app serves.
    """
    url = state.get('css_url')
    if not url:
        r.fail('library CSS matches repo', 'skipped: no CSS URL from the manifest')
        return
    status, served = fetch(url)
    if status != 200:
        r.fail('library CSS matches repo', 'CSS -> %s' % (status or served))
        return
    state['served_css'] = served

    with open(LOCAL_BUNDLE, encoding='utf-8-sig') as fh:
        local = selector_atoms(fh.read())
    remote = selector_atoms(served)

    missing = sorted(local - remote)
    if missing:
        r.fail('library CSS matches repo',
               '%d selector(s) in dist/neobase.css are not being served, '
               'e.g. %s' % (len(missing), missing[0][:60]))
        for s in missing[:10] if VERBOSE else missing[:3]:
            print('         - %s' % s[:100])
        print('         the app is serving an older library: release it, bump '
              'the consumer pin, republish')
    else:
        extra = len(remote - local)
        r.ok('library CSS matches repo',
             '%d selectors, all present%s'
             % (len(local), ' (+%d ahead of the repo)' % extra if extra else ''))


def check_css_assets_resolve(r, state):
    """Every image the served CSS references actually resolves.

    A library Image is authored as /NeoDesignSystem/img/Module.Image.svg, which
    404s if you fetch it and is still correct — ODC rewrites it to a hashed path
    when the library publishes. What it rewrites to has to exist: if the Image
    was never added to the library, the icon resolves to nothing at runtime with
    no console error and no failed request to notice.
    """
    served = state.get('served_css')
    url = state.get('css_url')
    if not served or not url:
        r.fail('CSS assets resolve', 'skipped: the library CSS was not fetched')
        return

    css_dir = url.rsplit('/', 1)[0] + '/'
    refs = {u.strip('\'" ') for u in re.findall(r'url\(\s*([^)]+?)\s*\)', served)}
    broken, checked, unrewritten = [], 0, []
    for ref in sorted(refs):
        if ref.startswith('data:'):
            continue
        if ref.startswith('/NeoDesignSystem/'):
            # An authoring path that survived publish: it will 404 in the browser.
            unrewritten.append(ref)
            continue
        if ref.startswith(('http://', 'https://')):
            continue                      # external (fonts); not ours to police
        # urljoin, not string concatenation: a served ref is "../img/x.svg",
        # and a literal ".." left in the path is rejected with a 403 rather
        # than resolved.
        target = urllib.parse.urljoin(css_dir, ref)
        status, _ = fetch(target)
        checked += 1
        if status != 200:
            broken.append('%s -> %s' % (ref.split('/')[-1][:50], status))
        elif VERBOSE:
            print('         %-60s 200' % ref.split('/')[-1][:60])

    if unrewritten:
        r.fail('CSS assets resolve',
               '%d authoring path(s) were not rewritten at publish: %s'
               % (len(unrewritten), unrewritten[0]))
    elif broken:
        r.fail('CSS assets resolve', '; '.join(broken[:3]))
    else:
        r.ok('CSS assets resolve', '%d asset(s), all 200' % checked)


CHECKS = [
    ('pages', [check_pages]),
    ('library', [check_manifest, check_library_css_matches_repo,
                 check_css_assets_resolve]),
]


def main():
    base = base_url()
    if not base:
        print('No app configured.\n'
              '  copy odc-app.example to odc-app and put your app URL in it,\n'
              '  or set ODC_APP=https://your-env.outsystems.app/YourApp')
        return 2

    print('app: %s' % base)
    r = Results()
    state = {}
    for group, checks in CHECKS:
        print('\n%s' % group)
        for c in checks:
            try:
                if c is check_css_assets_resolve:
                    c(r, state)
                elif c is check_pages:
                    c(r, base)
                else:
                    c(r, base, state)
            except Exception as exc:                          # noqa: BLE001
                r.fail(c.__name__, 'raised %s: %s' % (type(exc).__name__, exc))

    print()
    if r.failures:
        print('FAILED: %d of %d checks'
              % (len(r.failures), r.passed + len(r.failures)))
        for name, detail in r.failures:
            print('  %-40s %s' % (name, detail))
        return 1
    print('All %d checks passed.' % r.passed)
    print('Note: this proves what the app SERVES. It does not render the pages, '
          'so a\ncomponent that loads and then misbehaves is still only caught '
          'by using it.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
