"""Assemble THE NeoBase stylesheet — one file, correct cascade order, no duplicates.

Replaced the old dist/paste/0..6 pile, which had three problems:
  * 1-osui-reskin.css and 3-utilities.css duplicated content already inside
    0-neobase-complete.css, so pasting all of them shipped rules twice;
  * 0-neobase-complete.css still carried the `fusion-layout*` family, which the
    ODC portal does not render (0 elements across two live pages) and which no
    block emits any more — ~90 rules of dead weight;
  * a dozen measured corrections had been appended to the theme one at a time,
    so they sat at the end in arrival order rather than in the layer they belong
    to.

LAYER ORDER. Each layer must be able to override everything above it.

  0  @import        font faces (CSS requires @import to lead the file)
  1  tokens         primitives -> semantic -> component -> dark overrides
  2  base           animations + the body surface (background, colour, font)
  3  osui reskin    the widget layer: .btn .form-control .table .avatar ...
  4  legacy widgets ds-avatar whitelist (2 of 1114 ds-* classes are rendered)
  5  page frame     nds-layout / page-header-* / main-content / theme-grid
  6  host shell     unified-header / unified-aside + the --unified-* dimensions
  7  components     Fusion components the portal actually uses
  8  icons          pds-icon sizing contract + icon colour utilities
  9  utilities      spacing, display, motion, radius, transform ...
 10  corrections    ODC-specific fixes, LAST so they win

Run via tools/build_all.sh, which sequences the extractors correctly.
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import ROOT, TOKEN_FILE_ORDER

SRC = os.path.join(ROOT, 'src')
DIST = os.path.join(ROOT, 'dist')
OUT = os.path.join(DIST, 'neobase.css')

FONT_IMPORTS = (
    '@import url("https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;500;600&display=swap");\n'
    '@import url("https://fonts.googleapis.com/css2?family=Source+Code+Pro:wght@400;500;600&display=swap");\n')

# --- exclusions, each with a reason -----------------------------------------
DROP_COMPONENTS = {
    # The Fusion layout family. Verified 2026-09-03 and RE-VERIFIED 2026-09-07
    # across 28 portal pages: zero fusion-layout* elements on any of them. Our
    # blocks emit the legacy frame instead.
    #
    # layout.css also mentions ds-tabs, app-representation-*, avatar,
    # metadata-container-* and skeleton-box, several of which DO render on the
    # portal (ds-tabs on 9 of the 28 pages, app-representation on 11) — which
    # looks alarming until you read the selectors. All 91 rules are either
    # `.fusion-layout*` themselves or scoped under a `.fusion-layout` /
    # `.fusion-wizard` ancestor; checked 2026-09-07, there is not one unscoped
    # rule for those classes. They are layout-context overrides, dead without
    # the ancestor, so dropping the file cannot leave a rendered element
    # unstyled. Their base styling lives in their own component files.
    'layout.css',
    # Only TWO of the original six "OutSystems UI already ships these" drops
    # survive. RE-VERIFIED 2026-09-07 by sweeping 28 portal pages (every entry
    # in the aside, plus an app detail page) and counting rendered elements by
    # class prefix. Four of the six DID render and were restored:
    #
    #   fusion-carousel     /solutions/ — 1 carousel + 16 splide__ elements
    #   fusion-progress-bar /subscription/ — 42 elements
    #   fusion-tag          /usersaccess/identityproviders 24,
    #                       /usersaccess/organizationroles 6
    #   fusion-counter      /maintenance/ — 10 elements
    #
    # The earlier note said "evidence of absence on two pages, not proof —
    # re-check if a page turns up that uses one". Four did. The two pages
    # originally sampled (/usersaccess/ and /apps/) happened to be the ones
    # that use none of them.
    #
    # These two remain dropped. Re-checked 2026-09-07 on 31 pages, this time
    # including the log, trace and app DETAIL views that list pages never reach:
    #
    #   fusion-accordion   0 instances. The portal HAS accordions — the "Stack"
    #                      section on a Logs detail page is one — but they are
    #                      OutSystems UI's `osui-accordion` wrapped in the
    #                      legacy `ds-accordion-item`, not the Fusion component:
    #                        <div class="ds-accordion-item is--right">
    #                          <div class="osui-accordion-item ...">
    #                      So the drop is right, and chasing it found a REAL gap
    #                      elsewhere: the 12 ds-accordion rules were in no
    #                      extractor whitelist and had never been in the bundle.
    #                      Fixed in tools/extract_legacy_widgets.py.
    #
    #   fusion-side-panel  0 instances, and no side-panel/drawer/sidebar class
    #                      of ANY family. The trace detail's right-hand region
    #                      that looks like a panel is plain containers.
    #
    # Still absence rather than proof for side-panel — a modal or drawer flow we
    # did not trigger could use it. For accordion the evidence is now positive:
    # we know what the portal uses instead.
    'accordion.css', 'side-panel.css',
    # pagination.css and dropdown.css are NOT dropped. The same "OutSystems UI
    # already ships these" reasoning was wrong for both, measured 2026-09-07:
    #
    #   fusion-pagination      18 elements on /usersaccess/, 16 on /apps/.
    #                          The portal's element carries BOTH classes
    #                          ("fusion-pagination pagination") and the bundle
    #                          had ZERO pagination classes of either family, so
    #                          a paginated list rendered completely unstyled.
    #
    #   fusion-dropdown-item  430 elements on /apps/, 145 on /usersaccess/.
    #                          The portal's filter dropdowns are the regular
    #                          OutSystems UI dropdown with custom option
    #                          content, and that option content is
    #                          fusion-dropdown-item*. The reskin covers the
    #                          .dropdown control (27 classes) but not the
    #                          option rows inside it.
    #
    # dropdown.css also carries three rules that mention .btn, .pds-icon and
    # .ds-tooltip, but all three are scoped under a fusion-dropdown-* ancestor,
    # so they cannot collide with the reskin.
    #
    # This is the same defect class as avatar.css above: the file was written,
    # extracted and then never emitted.
    # avatar.css is NOT dropped. It used to be, on the same "OutSystems UI
    # already ships it" reasoning — which measurement contradicts. The portal's
    # Users page (/usersaccess/, the newer generation) renders
    #   <div class="fusion-avatar fusion-avatar--size-xs fusion-avatar--color-red
    #               fusion-avatar--format-circle"><span class="fusion-avatar__initials">
    # not OutSystems UI's .avatar and not the legacy .ds-avatar. Measured
    # 2026-09-07. Dropping this file left the whole --size/--color/--format
    # modifier set out of the bundle, so that markup rendered unstyled and we
    # had to emit ds-avatar instead.
    #
    # Both families are legitimately needed and do not collide: the shell chrome
    # uses legacy .avatar (the header login avatar is <span class="avatar
    # avatar-amber">), page content uses fusion-avatar.
}
DROP_UTILITIES = {
    # 40 class names collide with OutSystems UI at different values, and
    # .text-primary / .text-secondary mean opposite things in each.
    'colors.css', 'typography.css',
}
DROP_BASE = {
    'reset.css',           # takes over scrolling; hostile inside an existing app
    'legacy-interop.css',  # O11 interop, meaningless on ODC
    'fonts.css',           # empty; the @import block above covers it
}


def body_of(path):
    """File contents minus the generated banner comment."""
    with open(path, encoding='utf-8') as fh:
        text = fh.read()
    return re.sub(r'/\* =+\n(?:.*\n)*?   =+ \*/\n', '', text).strip()


PH = re.compile(r'\.ph(?![a-zA-Z0-9_-])')


def rename_ph(text):
    """`ph` is Phosphor's reserved base class in ODC — see corrections layer."""
    out, i = [], 0
    while True:
        j = text.find('/*', i)
        if j < 0:
            out.append(PH.sub('.neo-ph', text[i:]))
            break
        out.append(PH.sub('.neo-ph', text[i:j]))
        k = text.find('*/', j)
        if k < 0:
            out.append(text[j:]); break
        out.append(text[j:k + 2])
        i = k + 2
    return ''.join(out)


def banner(n, title, note=''):
    line = '=' * 76
    s = '\n\n/* %s\n   LAYER %s — %s\n' % (line, n, title)
    if note:
        s += '   ' + '-' * 74 + '\n'
        for ln in note.strip().split('\n'):
            s += '   %s\n' % ln
    return s + '   %s */\n\n' % line


def collect(paths, transform=rename_ph):
    out = []
    for p in paths:
        if os.path.isfile(p):
            b = body_of(p)
            if b.strip():
                out.append(transform(b) if transform else b)
    return '\n\n'.join(out)



def assert_comments_well_formed(css):
    """A `*/` inside a comment closes it early and the prose after becomes CSS.

    This shipped once: a section banner quoted `.ph { font-family: Phosphor }
    /* ... */` and the inner close terminated the block, leaving several lines of
    English to be parsed as a selector. Browsers recover, but recovery can swallow
    the rule that follows. Fail the build instead.
    """
    i = 0
    while True:
        a = css.find('/*', i)
        if a < 0:
            return
        b = css.find('*/', a + 2)
        if b < 0:
            raise SystemExit('unclosed comment at line %d' % (css[:a].count('\n') + 1))
        if '/*' in css[a + 2:b]:
            raise SystemExit('comment opened at line %d contains a nested /* or */ — '
                             'it will terminate early and leak prose into the cascade'
                             % (css[:a].count('\n') + 1))
        i = b + 2



def assert_corrections_win(css):
    """A correction that lands BEFORE the rule it corrects is silently reverted.

    This happened once: `.unified-header { position: sticky }` was folded into the
    shell layer ahead of header.css, which re-declares `fixed` — so the header
    went back to being out of flow and page content slid under it. Static-check
    the ones we know about rather than rediscovering them in a browser.
    """
    checks = [
        (r'\.unified-header\s*\{[^}]*position:\s*fixed',
         r'\.unified-header\s*\{[^}]*position:\s*sticky',
         'unified-header sticky correction'),
    ]
    for target_re, fix_re, label in checks:
        t = [m.start() for m in re.finditer(target_re, css)]
        f = [m.start() for m in re.finditer(fix_re, css)]
        if not f:
            raise SystemExit('%s: correction missing entirely' % label)
        if t and max(t) > max(f):
            raise SystemExit('%s: last overriding rule at char %d comes AFTER the '
                             'correction at char %d — the correction is dead'
                             % (label, max(t), max(f)))



# ---------------------------------------------------------------------------
# Brand assets
# ---------------------------------------------------------------------------
# The shell paints the header logo with a CSS background-image, theme-switched
# on [data-theme]. In the raw shell CSS those point into the capture's own asset
# folder (`url(assets/outsystems-logo--light.svg)`), which does not exist once
# the stylesheet is pasted into an ODC theme. They are rewritten to the module
# asset path, the same form osui_reskin.py uses for its two icons:
#     /NeoDesignSystem/img/<Module>.<Image>.svg
#
# That path is the AUTHORING form, not a URL the browser ever requests. ODC
# recognises it as a reference to the library Image and rewrites it at publish
# time to the content-hashed runtime path. Verified in the deployed theme:
#
#     source:   /NeoDesignSystem/img/NeoDesignSystem.icchevrondownxl.svg
#     deployed: ../img/NeoDesignSystem.icchevrondownxl__xjvXUO6Wfmb6QC4zsLNEQQ.svg
#
# Do not "fix" this to a relative path because the absolute one 404s when you
# fetch it directly — of course it does, nothing is served under the library's
# own module name. The rewrite is what makes it resolve, and it only fires for
# the absolute form.
#
# The two rules are also HOISTED to the top of the stylesheet, because they are
# the one thing a consuming team is expected to change. Safe to hoist: nothing
# else in the sheet sets background-image on .unified-header-logo, so no later
# rule overrides them.
LOGOS = {
    'outsystems-logo--light': 'outsystemslogolight',
    'outsystems-logo--dark': 'outsystemslogodark',
}
LOGO_RULE = re.compile(
    r'\[data-theme=(?:"|\')?(light|dark)(?:"|\')?\]\s*\.unified-header-logo\s*\{[^}]*\}')


# The sortable-header caret. The legacy table CSS references it with a relative,
# content-hashed path (`url(../img/NeoDesignSystem.icsortablexl__<hash>.svg)`)
# straight out of the portal capture, where the hash is the PORTAL's and will
# not match ours. It is rewritten to the same authoring form as the logos and
# the chevron, and ODC re-hashes it at publish:
#     /NeoDesignSystem/img/NeoDesignSystem.icsortablexl.svg
#
# Do NOT inline this as a data: URI. That was tried and shipped broken twice
# over: the raw `#` in `fill='#181A1F'` starts a fragment identifier, so the
# browser truncated the SVG and it painted nothing while still computing as a
# set background-image; and an inlined asset cannot be swapped by a consumer.
# The build gate below refuses any SVG data: URI outright.
def rewrite_asset_urls(css):
    """Point relative shell asset paths at their runtime library Image paths."""
    for stem, name in LOGOS.items():
        css = re.sub(r'url\(\s*[\'"]?assets/' + re.escape(stem) + r'[^)\'"]*[\'"]?\s*\)',
                     'url(/NeoDesignSystem/img/NeoDesignSystem.%s.svg)' % name, css)
    css = re.sub(r'url\(\s*[\'"]?\.\./img/NeoDesignSystem\.icsortablexl[^)\'"]*[\'"]?\s*\)',
                 'url(/NeoDesignSystem/img/NeoDesignSystem.icsortablexl.svg)', css)
    return css


def extract_brand(css):
    """Pull the logo rules out so they can be emitted first. Returns (rules, rest)."""
    found = LOGO_RULE.findall(css)
    rules = [m.group(0) for m in LOGO_RULE.finditer(css)]
    rest = LOGO_RULE.sub('', css)
    return rules, rest



def strip_comments(css):
    """Drop /* ... */ blocks and the blank runs they leave behind.

    Runs on the assembled output only. Source files keep their comments.
    """
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    css = re.sub(r'\n[ \t]*\n[ \t]*(\n[ \t]*)+', '\n\n', css)
    return css.strip() + '\n'


def assert_no_relative_assets(css):
    """A relative url() silently resolves to nothing inside an ODC theme.

    Local assets must be referenced by the authoring path
    `/NeoDesignSystem/img/<Module>.<Image>.svg`. ODC recognises that as a
    reference to the library Image and rewrites it at publish time to the
    content-hashed runtime path (`../img/<Module>.<Image>__<hash>.svg`), which
    is what the browser actually requests.

    Fetching the authoring path directly returns 404 — nothing is served under
    the library's own module name. That is expected and is NOT evidence the
    path is wrong; the rewrite is what makes it resolve, and it only fires for
    the absolute form. Verified in the deployed theme, all four images:

        source:   /NeoDesignSystem/img/NeoDesignSystem.icchevrondownxl.svg
        deployed: ../img/NeoDesignSystem.icchevrondownxl__xjvXUO6Wfmb6QC4zsLNEQQ.svg

    Absolute http(s) URLs are allowed through for the Google Fonts imports.
    Parse the url() contents and strip quotes BEFORE testing the scheme — an
    earlier version put the lookahead after an optional quote it had not
    consumed, so every quoted absolute URL tripped it.
    """
    bad = []
    for raw in re.findall(r'url\(([^)]*)\)', css):
        v = raw.strip().strip('\'"').strip()
        if v and not re.match(r'(https?:|//|/|data:)', v):
            bad.append(v[:70])
    if bad:
        raise SystemExit('relative asset url() would not resolve in ODC: %s' % bad[:3])


def main():
    parts = [FONT_IMPORTS.rstrip()]
    brand_slot = len(parts)          # filled in once the shell layer is built
    parts.append(None)

    # 1 — tokens
    tok = [os.path.join(SRC, '00-tokens', g + '.css') for g in TOKEN_FILE_ORDER]
    tok.append(os.path.join(SRC, '00-tokens', '_dark-theme.css'))
    # Four properties the upstream bundle references but never defines. Folded
    # in here so the single artifact resolves every var() it contains — without
    # them the browser drops the whole declaration. Kept in compat/ rather than
    # src/00-tokens/ so the generated token layer stays a faithful extract and
    # tools/verify.py's token-count check still compares like with like.
    tok.append(os.path.join(ROOT, 'compat', 'neo-missing-tokens.css'))
    parts.append(banner(1, 'TOKENS',
        'primitives -> semantic -> component -> dark, then the four properties\n'
        'the upstream bundle references but never defines.\n'
        'The dark block keys on [data-theme="dark"], which TrueShade sets on <html>.')
        + collect(tok))

    # 2 — base
    base = [os.path.join(SRC, '01-base', f) for f in sorted(os.listdir(os.path.join(SRC, '01-base')))
            if f.endswith('.css') and f not in DROP_BASE]
    parts.append(banner(2, 'BASE',
        'The reset is deliberately excluded — it takes over scrolling and is\n'
        'hostile inside an existing app. The body surface lives in layer 10.')
        + collect(base))

    # 3 — osui reskin
    parts.append(banner(3, 'OUTSYSTEMS UI RESKIN',
        'The widget layer. OutSystems UI ships .btn / .form-control / .table /\n'
        '.avatar and the portal restyles them rather than reimplementing.\n'
        'Verified against the portal: buttons match on all 12 probed properties.')
        + collect([os.path.join(DIST, 'osui-reskin.css')]))

    # 4 — legacy widgets
    parts.append(banner(4, 'LEGACY WIDGETS',
        'A whitelist, not the whole legacy library. Covers what the portal actually\n'
        'renders on its list pages: the ds-avatar family, and the table family that\n'
        'gives a data table its card, header row, sortable headers and row hover.')
        + collect([os.path.join(SRC, '06-legacy-widgets', 'widgets.css')]))

    # 5 — page frame
    parts.append(banner(5, 'PAGE FRAME',
        'What the portal actually renders for a page: OutSystems UI\'s stock Layout\n'
        '(.layout/.main/.content) with page-header-* and main-content-wrapper on top.\n'
        '.theme-grid-container is the width constraint: max-width 1344px, padding 0 32px.')
        + collect([os.path.join(SRC, '05-legacy-layout', 'page-layout.css')]))

    # 6 — components
    comp_dir = os.path.join(SRC, '02-components')
    comps = sorted(f for f in os.listdir(comp_dir)
                   if f.endswith('.css') and f not in DROP_COMPONENTS and f != 'icon.css')
    # vendor/ is a SUB-DIRECTORY, so os.listdir never yielded it and
    # vendor/splide.css (21 rules) was silently absent from every build. The
    # carousel needs it: /solutions/ renders 16 splide__ elements. Found
    # 2026-09-07 while restoring carousel.css.
    vendor_dir = os.path.join(comp_dir, 'vendor')
    vendor = ([os.path.join(vendor_dir, f) for f in sorted(os.listdir(vendor_dir))
               if f.endswith('.css')] if os.path.isdir(vendor_dir) else [])
    parts.append(banner(6, 'COMPONENTS',
        'Fusion components. The portal renders badge, dropdown-item, pagination,\n'
        'icon and empty-state; the rest are kept because usage is page-dependent.\n'
        'fusion-layout* is EXCLUDED — 0 rendered on any portal page measured.')
        + collect([os.path.join(comp_dir, f) for f in comps] + vendor))

    # 7 — icons
    parts.append(banner(7, 'ICONS',
        'Sizing contract for the SVG sprite system:\n'
        '  <svg viewBox="0 0 32 32" fill="currentColor" class="pds-icon icon-small">\n'
        '    <use href="#ic-name"></use></svg>\n'
        'The artwork is a separate sprite of <symbol> elements — supply your own.')
        + collect([os.path.join(comp_dir, 'icon.css'),
                   os.path.join(SRC, '03-utilities', 'icons.css')])
        # Sizes Phosphor font glyphs, which ignore the width/height that the
        # .pds-icon / .icon-* classes set for <svg>. Last in the layer so it
        # wins over them. transform=None is REQUIRED: this file's `.ph` is
        # Phosphor's own class, not the OutSystems placeholder, so it must NOT
        # go through rename_ph. Without it the rules silently become
        # `.neo-ph.pds-icon` and target our placeholder div instead — inert,
        # and invisible unless you diff the built file. Caught 2026-09-07.
        + collect([os.path.join(ROOT, 'compat', 'neo-phosphor-bridge.css')],
                  transform=None))

    # 8 — utilities
    util_dir = os.path.join(SRC, '03-utilities')
    utils = sorted(f for f in os.listdir(util_dir)
                   if f.endswith('.css') and f not in DROP_UTILITIES and f != 'icons.css')
    parts.append(banner(8, 'UTILITIES',
        'colors.css and typography.css are excluded: 40 class names collide with\n'
        'OutSystems UI at different values, and .text-primary / .text-secondary mean\n'
        'the opposite thing in each.')
        + collect([os.path.join(util_dir, f) for f in utils]))

    # 9 — host shell
    shell_order = ['host-integration', 'header', 'aside', 'banner', 'tooltip',
                   'toast', 'misc', 'animations']
    # neo-shell-compat.css must come AFTER the extracted shell: it CORRECTS
    # header.css (position: fixed -> sticky, measured on the portal). Custom
    # properties resolve at use time, so its --unified-* dimensions still apply
    # to rules above it. Ordering it first silently reverts the correction.
    #
    # This layer is LAST before the corrections layer because that is the
    # portal's own cascade: the host injects prod.unified.css AFTER the Neo
    # bundle. Ordering it earlier lets equal-specificity utilities win over it.
    # Measured 2026-09-07: with the shell first, `.icon-small { width: 16px }`
    # beat `.unified-aside-menu-header-icon { width: 0 }`, so the hidden section
    # icon still occupied 16px and pushed the menu title to 72px where the
    # portal has 56px.
    shell = [os.path.join(SRC, '04-shell', f + '.css') for f in shell_order]
    shell += [os.path.join(ROOT, 'compat', 'neo-shell-compat.css')]
    # 9 — login layout
    parts.append(banner(9, 'LOGIN LAYOUT',
        'The identity host\'s login screen (PDS Patterns.LoginScreen + the dark\n'
        'restyle): centered 432px form column, corner-rectangle background (dark\n'
        'only). PDS-scheme tokens are scoped to .pds-login/.full-screen-background\n'
        'on purpose — defining them at :root would activate the 11 dangling\n'
        'PDS-scheme references elsewhere in the portal CSS.')
        + collect([os.path.join(SRC, '07-login', 'login.css')]))

    parts.append(banner(10, 'HOST SHELL',
        'In the portal this markup is injected by the platform host, outside\n'
        '#reactContainer. Both roots are position:fixed/sticky, so emitting the same\n'
        'markup from a Block lands in the same place. Driven by body classes set from\n'
        'JavaScript (InitShell), not media queries — 45 rules key on .is-aside-expanded.\n'
        'Emitted after components/icons/utilities to match the portal cascade.')
        + collect(shell))

    # 10 — corrections
    parts.append(banner(11, 'ODC CORRECTIONS',
        'Everything measured against the live portal that the extracted CSS gets\n'
        'wrong on ODC. LAST in the file so these win. Each carries its evidence.')
        + collect([os.path.join(ROOT, 'compat', 'neo-odc-compat.css')], transform=None))


    body = '\n\n'.join(p for p in parts[brand_slot + 1:] if p)
    body = rewrite_asset_urls(body)
    brand_rules, body = extract_brand(body)
    parts[brand_slot] = (banner(0, 'BRAND — swap these for your own',
        'The header logo, painted by the shell as a themed background-image.\n'
        'Replace the two Images in the library (same names) or repoint these two\n'
        'rules. Hoisted here because it is the one thing you are meant to change;\n'
        'nothing later in this file sets background-image on .unified-header-logo.')
        + '\n\n'.join(brand_rules)) if brand_rules else ''
    # @import MUST lead the file or browsers drop it — fonts silently vanish.
    css = parts[0] + '\n\n' + ((parts[brand_slot] + '\n\n' + body) if brand_rules else body)
    assert_comments_well_formed(css)
    assert_corrections_win(css)
    assert_no_relative_assets(css)
    if not css.lstrip().startswith('@import'):
        raise SystemExit('@import no longer leads the file — fonts would be dropped')

    # Ship lean. Every decision behind these rules is recorded in the repo —
    # compat/*.css, src/, docs/odc-library.md — which is where a maintainer
    # looks. None of it belongs in the stylesheet ODC serves to every user on
    # every page load. The portal's own CSS carries no such prose either.
    css = strip_comments(css)

    os.makedirs(DIST, exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write(css)

    rules = css.count('{') - css.count('@import')
    print('neobase.css : %d rules, %d KB -> %s'
          % (rules, os.path.getsize(OUT) // 1024, os.path.relpath(OUT, ROOT)))
    # `(?<!-)` keeps this off custom properties: `--fusion-layout-sticky-top-offset`
    # is a variable the live `.fusion-sticky-container` rule reads, not the dead
    # layout family. Matching the bare string flagged it and cost a false alarm.
    failed = []
    # A stray `*/` (or an unterminated `/*`) is invalid CSS. Browsers skip it via
    # error recovery, so nothing looks broken — but it shipped in every paste from
    # section 26 onward before anyone noticed, and a stray terminator will swallow
    # the next rule if one is ever appended after it. Both gates test the text
    # AFTER well-formed comments are stripped, so anything left over is unbalanced.
    for bad, why in ((r'(?<!-)fusion-layout', 'dead layout family'),
                     (r'\.ph(?!\.pds-icon)[^a-zA-Z0-9_-]',
                      'unrenamed Phosphor collision'),
                     (r'\*/', 'stray comment terminator'),
                     (r'/\*', 'unterminated comment')):
        n = len(re.findall(bad, re.sub(r'/\*.*?\*/', '', css, flags=re.S)))
        print('  %-34s %s' % (why, 'CLEAN' if n == 0 else 'STILL PRESENT x%d' % n))
        if n:
            failed.append('%s x%d' % (why, n))
    # ---- PRESENCE: is everything we expect actually here? --------------
    # The two gates above only ask "is anything BAD in the file". Nothing asked
    # "is everything GOOD still in the file", and that blind spot shipped twice:
    #
    #   2026-09-07  running tools/build.py alone (it clears dist/ and the
    #               src/05-*, src/06-* trees) silently dropped the OSUI reskin
    #               layer and both legacy extracts. 770 selectors — .btn,
    #               .avatar, .badge, .alert, .breadcrumbs — vanished and the
    #               bundle fell from 2,126 rules to 1,329. Both gates said
    #               CLEAN, because a smaller file contains less that is bad.
    #
    #   2026-09-07  vendor/splide.css had NEVER been in any build: the
    #               component collector used os.listdir, which does not descend
    #               into vendor/. 21 rules, absent since the file was written.
    #
    # Each entry is a family that has to survive assembly, with a floor well
    # under its real count so ordinary churn does not trip it. Raise a floor
    # only when you have a reason; the point is catching a layer going to ZERO,
    # not pinning exact numbers.
    expect = (
        (r'\.btn(?![a-zA-Z0-9_-])', 'osui reskin: .btn', 20),
        (r'\.form-control(?![a-zA-Z0-9_-])', 'osui reskin: .form-control', 10),
        (r'\.badge(?![a-zA-Z0-9_-])', 'osui reskin: .badge', 3),
        (r'\.alert(?![a-zA-Z0-9_-])', 'osui reskin: .alert', 3),
        (r'splide__', 'carousel vendor (splide)', 10),
        (r'fusion-carousel', 'fusion-carousel', 5),
        (r'fusion-progress-bar', 'fusion-progress-bar', 5),
        (r'fusion-tag(?![a-zA-Z0-9_-])', 'fusion-tag', 5),
        (r'fusion-counter', 'fusion-counter', 2),
        (r'fusion-pagination', 'fusion-pagination', 10),
        (r'ds-accordion', 'legacy ds-accordion', 5),
        (r'ds-avatar', 'legacy ds-avatar', 5),
        (r'unified-header', 'shell: header', 20),
        (r'unified-aside', 'shell: aside', 20),
        (r'^\s*--[a-z0-9-]+\s*:', 'token layer (custom props)', 500),
        (r'\.ph\.pds-icon', 'phosphor bridge', 3),
        (r'display:\s*contents', 'placeholder unwrapping', 4),
        (r'min-width:\s*104px', 'dropdown sizing', 1),
        (r'screen-container::-webkit-scrollbar', 'visible scrollbar', 1),
        (r'ThemeGrid_MarginGutter', 'ThemeGrid gutter reset', 1),
    )
    bare = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    missing = []
    for pat, label, floor in expect:
        n = len(re.findall(pat, bare, re.M))
        if n < floor:
            missing.append('%s (%d < %d)' % (label, n, floor))
    print('  %-34s %s' % ('expected families present',
                          'CLEAN' if not missing else
                          'MISSING %d of %d' % (len(missing), len(expect))))
    for m in missing:
        print('      missing: %s' % m)
    failed.extend(missing)

    # ---- NO INLINED SVG: assets belong in the library Images -----------
    # Images ship as library Images and are referenced at their runtime path,
    # `../img/<Module>.<Image>.svg` — the form the logos, the
    # chevron and the sortable caret all use. Inlining is banned outright, for
    # two reasons learned the hard way:
    #
    #   * A raw `#` in `fill='#181A1F'` inside a data: URI starts a fragment
    #     identifier. The browser truncates the SVG, it never parses, and it
    #     paints nothing — while background-image still computes as set and the
    #     box still measures its full size, so every DOM probe says it is fine.
    #     The sortable caret shipped that way and was only caught by eye.
    #   * A consumer cannot restyle or swap an inlined asset.
    inlined = re.findall(r'data:image/svg\+xml[^)]*', css)
    print('  %-34s %s' % ('no inlined SVG data URIs',
                          'CLEAN' if not inlined else
                          'INLINED x%d' % len(inlined)))
    if inlined:
        failed.append('inlined SVG data URI x%d' % len(inlined))


    # Fail loudly. A gate that only prints is a gate you scroll past.
    if failed:
        raise SystemExit('neobase gate failed: ' + '; '.join(failed))


if __name__ == '__main__':
    main()
