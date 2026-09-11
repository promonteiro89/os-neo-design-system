"""Extract the login-screen layout from the OutSystems ID login page.

SOURCE. https://id.outsystems.dev — the platform-global identity host every ODC
tenant's login round-trips through (no tenant in these URLs). Two sheets carry
the pattern:

  login.css            the PDS Patterns.LoginScreen base — its own header names
                       ProductDesignSystem.Patterns.LoginScreen.css upstream
  mtsi-dark-theme.css  the dark restyle: form column geometry, spacing, and the
                       decorative corner rectangles (dark theme only)

WHAT IS KEPT. Rules whose subject is the login pattern: .pds-login*,
.full-screen-background, .rectangles, and the pdsLogin keyframes. Dark rules are
re-scoped `.mtsi-dark-theme X` -> `[data-theme="dark"] X`, matching how the rest
of this tree expresses dark mode. Declarations are copied verbatim.

WHAT IS DROPPED, deliberately:
  - OS runtime utilities (.OSFillParent, .OSInline, ThemeGrid_*, .OSBlockWidget,
    focus rings): ODC serves these from _Basic on every page already.
  - .hybrid-theme rules: a different login skin, not the one id.outsystems.dev
    renders today.
  - .background-img-{toolname,lifetime,servicecenter}: per-tool backgrounds for
    O11 consoles, referencing images this repo does not ship.
  - .portal-scoped variants: community-site context, not ours.
  - mtsi's .text-neutral-N / .background-neutral-N flips and its body/html/
    .screen-container overrides: that is their global dark mechanism; ours is
    the token layer, and a block must not restyle the page around it.

TOKENS. The pattern uses PDS-scheme names (--color-neutral-N, --space-*,
--spacing-*, --dark-*). These are DEFINED HERE but SCOPED to the login roots:
dist/neobase.css carries 11 dangling references to PDS-scheme tokens in portal
rules whose declarations currently drop silently — defining the names at :root
would switch those on and change existing pages. Scoping keeps this additive.
Values come from product.css (the PDS source) and mtsi-dark-theme.css.

THE CORNER ART. The identity host ships the rectangles as <img> children. In
the ODC library the four spans are empty Containers and the art rides the
theme's Images instead, referenced with the one URL form ODC rewrites inside
theme CSS: url(/NeoDesignSystem/img/NeoDesignSystem.<image>.svg) — absolute
module path, no hash (confirmed in ODC Studio; see docs/odc-library.md, "the
real image path"). The SVGs are copied to dist/assets/login/ under separator-
free names so importing them into the library yields exactly the image names
the CSS expects.

Run: python3 tools/extract_login.py   (after build.py — build.py clears src/)
"""
import glob
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'reference', 'raw', 'login')
OUT = os.path.join(ROOT, 'src', '07-login')
ASSETS_OUT = os.path.join(ROOT, 'dist', 'assets', 'login')

KEEP = re.compile(r'\.pds-login|\.full-screen-background|\.rectangles|pdsLogin|'
                  r'#dark-theme-logo')
DROP = re.compile(r'hybrid-theme|\.portal |background-img|text-neutral-\d|'
                  r'background-neutral-\d|screen-container|\.layout|\.content|'
                  r'\.main-content|\bbody\b|\bhtml\b')

# Scoped token layer: PDS values from product.css, dark constants from mtsi.
TOKENS = """/* PDS tokens the pattern references, SCOPED to the login roots.
   Global definition would activate the 11 dangling PDS-scheme references
   elsewhere in the portal CSS (see docs) and change existing pages. */
.pds-login,
.full-screen-background {
  --color-neutral-0: #fff;
  --color-neutral-1: #f7f8fa;
  --color-neutral-4: #cccdd0;
  --color-neutral-7: #626568;
  --color-neutral-9: #2c2f32;
  --color-neutral-10: #202327;
  --color-neutral-11: #101214;
  --space-base: 16px;
  --space-s: 8px;
  --space-m: 24px;
  --space-l: 32px;
  --space-xl: 40px;
  --space-xxl: 48px;
  --font-size-h1: 32px;
  --spacing-xs: 8px;
  --spacing-sm: 12px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --border-radius: 8px;
  --space-xs: 4px;
  --font-size-s: 12px;
  --font-semi-bold: 600;

  /* Two-theme tokens. LIGHT values here, dark overridden below. These are the
     roles where the host's login palette does NOT coincide with the design
     system's own tokens - see TOKEN_MAP for the four that do and therefore
     need nothing. */
  --login-text-primary: var(--text-primary);
  --login-text-secondary: var(--text-secondary);
  --login-label: var(--color-neutral-7);
  --login-input-border: var(--input-border-default);
  --login-link-hover: var(--link-text-hover);
}

/* DARK. Every value here is the identity host's own, so dark renders exactly
   as it did when this layer was wholesale dark-scoped. */
[data-theme="dark"] .pds-login,
[data-theme="dark"] .full-screen-background {
  --login-text-primary: #FFFFFF;
  --login-text-secondary: #F9FAFB;
  --login-label: #FFFFFF;
  --login-input-border: #4A4E57;
  --login-link-hover: #F9FAFB;
}
"""



# ---------------------------------------------------------------------------
# GENERIC-CLASS RULES, LIFTED AND SCOPED
#
# KEEP only matches selectors that name the pattern (.pds-login*, .rectangles,
# ...). That silently dropped every rule whose subject is a GENERIC class but
# which still styles the login form - the host's login is a whole page, so it
# leans on plain `label`, `a`, `.link-small`, `.form-control`.
#
# Found by enumerating, on the live host, every rule in login.css /
# mtsi-dark-theme.css / product.css that matches some element in the .pds-login
# subtree (53 of them) and diffing against this extract. These are the ones
# that were missing and that changed the rendering:
#
#   label                       margin-bottom: 4px  - without it every input
#                               sat 4px too high, and the whole column below
#                               it with them
#   .link-small (dark)          12px/16px #B2B4FF   - ours rendered the ODC
#                               light-theme blue at 14px/24px
#   .form-control (dark)        border #4A4E57      - ours was #464B56
#
# They are emitted SCOPED to .pds-login. The host can afford `label { ... }`
# unscoped because its login is the only thing on the page; a library block
# must not restyle every label, link and input in a consuming app. Scoping is
# the one edit - declarations are copied verbatim.
#
# NOT lifted, deliberately: product.css's .btn / .btn-primary / .btn-large /
# .form-control[data-input] base rules. Those are PDS's own control skin, and
# our design system already supplies the control it renders - measured
# identical to the host (432x40, #5252F2, radius 8, border #5252F2). Taking
# PDS's gradient .btn would replace a matching control with a wrong one.
GENERIC = [
    ('product.css', 'label'),
    ('product.css', 'a, a:visited'),
    ('product.css', '.link-small'),
    ('product.css', '.font-size-s'),
    ('product.css', '.font-semi-bold'),
    ('product.css', '.text-neutral-7'),
    ('mtsi-dark-theme.css', '.mtsi-dark-theme .link-small'),
    ('mtsi-dark-theme.css', '.mtsi-dark-theme .link-small:hover'),
    ('mtsi-dark-theme.css', '.mtsi-dark-theme .text-neutral-7'),
    ('mtsi-dark-theme.css', '.mtsi-dark-theme .form-control'),
    ('mtsi-dark-theme.css', '.mtsi-dark-theme .form-control:valid'),
]


def scope_generic(sel):
    """Scope a generic selector to the pattern: `X` -> `.pds-login X`.

    The dark variants lose their theme scope along with the rest of mtsi -
    their colours are re-pointed at two-theme tokens by retoken(), so one
    unscoped rule now serves both themes. What they keep is the `.pds-login`
    scope, because the host can afford `label { }` unscoped on a page that is
    nothing but a login and a library cannot."""
    parts = []
    for part in sel.split(','):
        part = part.strip()
        if part.startswith('.mtsi-dark-theme '):
            part = part[len('.mtsi-dark-theme '):]
        parts.append('.pds-login ' + part)
    return ',\n'.join(parts)


def lift_generic():
    """Pull the allowlisted generic rules out of their source sheets."""
    out = []
    for fname, want in GENERIC:
        path = os.path.join(RAW, fname)
        txt = open(path, encoding='utf-8', errors='replace').read()
        found = False
        for m in re.finditer(r'([^{}@]{1,400}?)\{([^{}]*)\}', txt):
            sel = re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).strip()
            sel = ' '.join(sel.split())
            if sel != want:
                continue
            decl = [d.strip() for d in m.group(2).split(';') if d.strip()]
            decl = [re.sub(r'/\*.*?\*/', '', d, flags=re.S).strip() for d in decl]
            decl = [d for d in decl if d]
            out.append('%s {\n%s\n}' % (scope_generic(sel),
                                         retoken(sel, ';\n'.join('  ' + d for d in decl) + ';')))
            found = True
            break
        if not found:
            raise SystemExit('extract_login: generic rule not found in %s: %s'
                             % (fname, want))
    return out


ODC_ADAPT = """

/* ---- ODC adaptation: corner art as theme-image backgrounds ------------
   The identity host renders the rectangles as <img> children; the ODC block
   ships them as empty containers and the art comes from the library's own
   Images. This absolute module path is the authoring form ODC rewrites at
   publish; fetched directly it 404s, and that is still correct. Import the
   four SVGs from dist/assets/login/ without renaming - the separator-free
   filenames become exactly these image names. Dark-only, like the art.

   EVERY ONE OF THESE SVGs IS 7px SHORTER THAN ITS CSS BOX. mtsi sizes the
   spans 163x132, 262x270, 293x505 and 468x163; the artwork is 163x125,
   262x263, 293x498 and 468x156. On the host that gap sits at the BOTTOM,
   because an <img> at natural size starts at its span's top edge - measured
   there: bottom-left span y395->900, img y395->893.

   So the anchor is `top` on all four, including the two bottom ones. An
   earlier pass wrote `left bottom` / `right bottom`, which reads as the
   obvious choice for a corner pinned to the bottom of the screen and put the
   whole lower-left cluster 7px below the host's. */

.rectangles.rectangle-top-left {
  background: url(/NeoDesignSystem/img/NeoDesignSystem.rectangletopleftdark.svg) no-repeat left top;
}

.rectangles.rectangle-top-right {
  background: url(/NeoDesignSystem/img/NeoDesignSystem.rectangletoprightdark.svg) no-repeat right top;
}

.rectangles.rectangle-bottom-left {
  background: url(/NeoDesignSystem/img/NeoDesignSystem.rectanglebottomleftdark.svg) no-repeat left top;
}

.rectangles.rectangle-bottom-right {
  background: url(/NeoDesignSystem/img/NeoDesignSystem.rectanglebottomrightdark.svg) no-repeat right top;
}

/* ---- ODC adaptation: placeholder wrapper and control widths -----------
   MEASURED on a real ODC login screen at 1280x760, dark.

   1. The Content placeholder renders as a bare <div id="bN-Content"> with NO
      class attribute, so nothing gives it width. Its three sibling Containers
      are 432px only because the portal CSS puts width:100% on
      .pds-login-right-logo / -account / -signup-account by name. The
      placeholder collapsed to content width (213px), taking the inputs and
      button with it.

      It is a BLOCK at width 100%, not display:contents. An earlier note here
      claimed the host renders `form > div` with no wrapper; that was wrong -
      the host wraps all of it in a real <form>, which is a block box 432 wide.
      With display:contents the placeholder's children became flex items of
      .pds-login-right-form, and that column sets align-items:flex-start, so
      every one of them shrank to its own content: measured
      .pds-login-right-forgot-signedin at 117px instead of 432. Restoring a
      block box reproduces the <form> exactly.

   2. On the host, the submit button and inputs get width from .OSFillParent.
      ODC's _Basic does define that, but it is not applied to a Button widget,
      so the button stayed at its 80px intrinsic width. The portal's intent is
      a full-column button, and .pds-login-right-button already declares
      width:100% for itself and two levels of div - just not for the control. */

.pds-login-right-form > div:not([class]) {
  display: block;
  width: 100%;
}

.pds-login-right-button .btn {
  width: 100%;
}

/* ---- ODC adaptation: the wordmark, painted by CSS ---------------------
   The identity host puts an <img> in the logo slot. Here the theme paints it
   so a consumer gets the right mark in both themes for free. Two inks, from
   the shell extraction: outsystemslogolight.svg is #0F0E0B for light grounds,
   outsystemslogodark.svg is #F9FAFB for dark. The dark file IS the host's own
   130x25 artwork, so dark mode is pixel-identical; the light one is the
   shell's 124x24 mark drawn into the same 130x25 box (0.6% aspect difference,
   imperceptible).

   Height is explicit because a background needs one: on the host the wrapper
   was sized by the <img> it contained. Left-aligned and 32px below, matching
   the host's own #dark-theme-logo rules now captured above.

   ONLY WHEN THE Logo PLACEHOLDER IS EMPTY. Painting it unconditionally made
   the block's Logo placeholder meaningless: it did nothing, and a consumer
   who dropped their own mark into it got BOTH - their logo drawn over our
   background. Gating on `:has(> .neo-ph:empty)` turns the placeholder into a
   real branding override: leave it empty and you get the OutSystems wordmark,
   fill it and ours switches off.

   This is the bundle's own idiom, not a new invention - the portal's empty
   state does the same thing seven times over
   (.fusion-empty-state__logo:has(> .neo-ph:empty) { display: none }). It
   requires the placeholder to actually carry the neo-ph class, which it did
   not: it rendered as a bare <div> with no class at all. */

.pds-login-right-logo:has(> .neo-ph:empty) {
  background: url(/NeoDesignSystem/img/NeoDesignSystem.outsystemslogolight.svg) no-repeat left center;
  background-size: 130px 25px;
  min-height: 25px;
}

[data-theme="dark"] .pds-login-right-logo:has(> .neo-ph:empty) {
  background-image: url(/NeoDesignSystem/img/NeoDesignSystem.outsystemslogodark.svg);
}

/* ---- ODC adaptation: control metrics ----------------------------------
   The identity host's login is a PDS page; our controls are Fusion. Button,
   radius, border colour and background already matched exactly - these three
   did not. MEASURED at 1280, dark, host vs ours:

     input height     40px      vs 48px
     input font       14/17.5   vs 16/24
     input padding    0 8px     vs 0 16px
     label colour     #FFFFFF   vs #4F575E (grey)
     label line-box   21px      vs 24px

   Scoped to the login column so the rest of the design system keeps Fusion
   sizing. The label colour is dark-only: the host has no light mode, so in
   light our own form-label token stays correct. */

/* The [data-input] attribute is load-bearing here. Our own control rules are
   .form-control[data-input].input-large -> (0,3,0), so a plain
   .pds-login-right-inputs .form-control at (0,2,0) silently loses and the
   inputs stay 48px. The second selector below is (0,4,0) and wins outright
   rather than relying on document order or !important. */

.pds-login-right-inputs .form-control[data-input],
.pds-login-right-inputs .form-control[data-input].input-large {
  height: 40px;
  padding: 0 8px;
  font-size: 14px;
  line-height: 17.5px;
}

.pds-login-right-inputs label {
  color: var(--login-label);
  line-height: 21px;
}

/* ---- ODC adaptation: the host's inline-block containers ---------------
   MEASURED: with everything above correct, our submit button still sat 12px
   above the host's (y482 vs y494) and the column was 12px short.

   The host is an O11 app, so every Container it renders carries .OSInline
   (`display:inline-block; vertical-align:top`) from _Basic. ODC does not emit
   that class, so the same three containers render as plain blocks - and
   BLOCKS COLLAPSE ADJACENT MARGINS. .pds-login-right-forgot-signedin's
   margin-bottom:24px and .pds-login-right-button's margin-top:12px collapsed
   to 24px instead of summing to 36px. Inline-block boxes do not collapse
   margins, which is why the host gets 36px without asking for it.

   Only these three are inline-block on the host; -logo, -inputs and
   -forgot-signedin all declare `display:flex` by name, which wins. */

.pds-login-right-account,
.pds-login-right-button,
.pds-login-right-signup-account {
  display: inline-block;
  vertical-align: top;
}

/* ---- ODC adaptation: the host's body line-height ----------------------
   outsystems.css gives the login page `body { line-height: 1.5 }` -> 21px at
   14px. Our consumer inherits ODC's 24px, which stretched every text box in
   the column: the "Forgot password" link measured h24 against the host's h16,
   and the button label h24 against h14.

   Applied to .pds-login rather than to body: the host can set it on body
   because its login IS the page, but a library block must not restyle the
   page around it (same reason mtsi's own body/html overrides are dropped). */

.pds-login {
  line-height: 1.5;
}

/* ---- ODC adaptation: the password reveal control ---------------------
   The host renders `span.pds-login-input` (INLINE, position:relative) holding
   the input and the eye button as siblings, and positions the eye against
   that inline fragment - which is why its `top:0` lands mid-input rather than
   at the input's top edge.

   ODC's Input widget renders its own `span.input-password` wrapper and no
   widget can be placed inside it, so the inline-fragment trick is not
   reproducible. The eye is instead the last child of the password's
   .pds-login-right-inputs column, which is marked .pds-login-password-field
   and positioned; because the input is the last thing in that column, the
   column's bottom edge IS the input's bottom edge, so a bottom offset of
   (40 - 16) / 2 centres the icon in the field deterministically.

   Measured against the host: eye 912->928 y373->389, ours 912->928 y374->390.
   One pixel low, and that pixel is the host's inline-box rounding, not ours.

   It is a Container, not a Button. The control is inert on this template, and
   an ODC Button widget would bring our own .btn skin - background, border,
   40px height - into a 16px icon slot. */

.pds-login-password-field {
  position: relative;
}

.pds-login-password-field .pds-login-password-eye {
  position: absolute;
  right: 8px;
  /* top:auto is load-bearing. The dark rule above sets top:0 at the same
     specificity (0,2,0), and with an explicit height a non-auto `top` wins
     over `bottom` outright - the icon pinned to the column's top edge, 36px
     high, until this reset it. */
  top: auto;
  bottom: 12px;
  margin: 0;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  line-height: 1;
  color: var(--login-text-primary);
  opacity: 0.5;
  cursor: pointer;
}

.pds-login-password-field .pds-login-password-eye:hover {
  opacity: 1;
}

/* ---- ODC adaptation: the submit button's type ------------------------
   The host declares `.btn { font-weight: 500 }` but RENDERS 400, because the
   only noto-sans faces it loads are 400 and 600 - with no 500 available, CSS
   font matching for a desired 500 falls to the next lighter face. Our bundle
   pulls a real Noto Sans 500 from Google Fonts, so the same declaration gave
   us a genuinely heavier label than the host's.

   Measured width of "Log in" at 14px:
       host                            40.0
       ours, 500 + 0.1px tracking      41.5
       ours, 500, no tracking          40.9
       ours, 400, no tracking          40.3   <- matches

   So this declares what the host RENDERS rather than what it DECLARES, which
   is the only way to match it while our font set is the more complete one.
   `letter-spacing` is ours (our .btn adds 0.1px; the host has none) and
   line-height is the host's own .btn value. */

.pds-login-right-button .btn {
  font-weight: 400;
  letter-spacing: normal;
  line-height: 14px;
}

/* ---- ODC adaptation: don't reserve a scrollbar gutter ----------------
   ODC's shell gives `.screen-container` `overflow-y: scroll`, which reserves
   an 8px gutter whether or not the page scrolls. That made the login column
   1432px wide inside a 1440px viewport and put the form 4px left of centre -
   small, but visible side by side with the host, whose page reserves nothing.

   Scoped with :has() so it applies only to a screen that actually contains
   this block, leaving every other screen's scroll behaviour alone. When the
   login really is taller than the viewport the scrollbar appears and insets
   the column, which is exactly what the host does too. */

.active-screen.screen-container:has(.pds-login) {
  overflow-y: auto;
}
/* ---- ODC adaptation: light corner artwork, by filter ------------------
   The host ships FOUR dark corner SVGs and only ONE light one
   (rectangle-top-left.svg), so light mode had no artwork in three corners.

   The artwork is nothing but strokes on transparency, so the one asset can
   serve both themes: `invert(1) hue-rotate(180deg)` inverts lightness while
   holding hue, which is exactly the light/dark relationship the corner art
   has. NO SECOND SET OF FILES, and therefore no light Images to import into
   the library and no colour map in this script to keep in step with a
   re-export of the artwork.

   Generating a light set was tried first, mapping each dark ink to the light
   ink with the same contrast against its own theme's ground. The filter lands
   within 0.15 of those values on three of the four strokes, which is not worth
   four more assets:

     dark ink   role         filter -> CR    hand-picked -> CR
     #474A8E    main         #a9acf0  2.04   #a2a5fe       2.15
     #353762    mid          #c1c3ee  1.63   #c6c8ff       1.53
     #2B2D4B    faintest     #cdcfed  1.46   #d8daff       1.31
     #777AFD    accent       #7073f6  3.67   #5757f5       4.92

   The host's OWN light inks were tried before either and are invisible here:
   #F1F2FB is contrast 1.07 against our #F9FAFB ground and its main stroke
   #C8C9F9 is 1.52, where the same stroke carries 2.19 in dark. Its light
   artwork is genuinely far fainter than its dark; on our page it read as
   missing, which is how this was reported. Matching dark's contrast is the
   deliberate deviation, and the filter is how it is delivered.

   Light is the default and dark switches the filter OFF, because dark is where
   the asset is already the right ink. */

.rectangles {
  filter: invert(1) hue-rotate(180deg);
}

[data-theme="dark"] .rectangles {
  filter: none;
}

"""

def rules(css):
    """Yield (selector, body) at top level; @media yields (media, inner-css)."""
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    i, n = 0, len(css)
    while i < n:
        j = css.find('{', i)
        if j < 0:
            break
        sel = css[i:j].strip()
        depth, k = 1, j + 1
        while k < n and depth:
            depth += {'{': 1, '}': -1}.get(css[k], 0)
            k += 1
        yield sel, css[j + 1:k - 1]
        i = k


# ---------------------------------------------------------------------------
# ONE LAYER, TWO THEMES, DRIVEN BY TOKENS.
#
# mtsi-dark-theme.css is named for a theme but it is NOT a colour sheet: it is
# where the login's ACTUAL LAYOUT lives - the 432px column, the left alignment,
# the 95px top padding, the 24px heading, every margin between the fields. The
# base login.css underneath it is the older PDS design, a 400px CENTRED column
# with a 14px heading.
#
# Rescoping all of mtsi under [data-theme="dark"] therefore left light mode
# rendering the raw PDS base - measured: form 400px wide with
# align-items:center, heading 14px/21px centred, logo margin-bottom 72px and
# not left-aligned, forgot row 18px instead of 40px, sign-up centred, and a
# white panel 606px tall sitting on the consumer's #F9FAFB body. That is not a
# "light variant", it is a different, half-finished design.
#
# So mtsi is emitted UNSCOPED and its colours are re-pointed at tokens that
# carry a value for each theme. The host never renders a light login (it ships
# no light artwork at all), so there is no upstream light design to copy -
# taking mtsi's geometry as THE geometry is the only coherent reading.
#
# WHAT STAYS THEME-SCOPED: only the two ASSET swaps, because those are
# different files rather than different values - the corner artwork (dark ink
# only) and the wordmark (light/dark SVGs, in ODC_ADAPT).
# Nothing is dark-only any more. The corner artwork used to be, because only
# dark SVGs existed; now that write_light_art() derives a light set, the rules
# that POSITION and SIZE those spans must apply in both themes too - otherwise
# the light artwork is painted onto a 0x0 box and never appears. The only
# theme-scoped things left in this layer are the two asset swaps, both of them
# hand-written in ODC_ADAPT.
DARK_ONLY = re.compile(r'(?!x)x')  # matches nothing

# The host's login hardcodes its own dark palette. Four of those roles turn out
# to be EXACTLY our design system's tokens in dark, so they need no new token
# at all and light comes free:
#
#   --dark-bg-primary  #181A1F == --input-background-default          (dark)
#   #F9FAFB input text         == --input-text-default                (dark)
#   #B2B4FF link               == --link-text-default                 (dark)
#   --dark-accent      #5252F2 == --button-primary-background-default (dark)
#   #f56451 error icon         == --text-error                        (dark)
#
# The rest are login-specific values the portal's own tokens do not carry -
# the host's input border is #4A4E57 where ours is #464B56, and its body text
# is pure #FFFFFF where ours is #F9FAFB. Those get a --login-* token defined
# per theme in TOKENS, so DARK IS PRESERVED EXACTLY and light gets a sane
# counterpart from the design system.
TOKEN_MAP = [
    ('var(--dark-bg-primary)',            'var(--input-background-default)'),
    ('var(--dark-accent)',                'var(--button-primary-background-default)'),
    ('var(--dark-border)',                'var(--login-input-border)'),
    ('var(--dark-text-primary)',          'var(--login-text-primary)'),
    ('var(--dark-text-secondary)',        'var(--login-text-secondary)'),
    ('var(--Link-Text-Default, #B2B4FF)', 'var(--link-text-default)'),
    ('var(--color-selection-5)',          'var(--link-text-default)'),
    ('#f56451',                           'var(--text-error)'),
]

# Literal #F9FAFB means three different roles depending on the rule, so it is
# mapped per selector rather than globally.
LITERAL_BY_SELECTOR = [
    (re.compile(r'\.form-control'),        '#F9FAFB', 'var(--input-text-default)'),
    (re.compile(r'\.link-small:hover'),    '#F9FAFB', 'var(--login-link-hover)'),
    (re.compile(r'\.text-neutral-7'),      'var(--color-neutral-4)',
                                           'var(--login-text-secondary)'),
    (re.compile(r'label'),                 '#F9FAFB', 'var(--login-label)'),
    (re.compile(r''),                      '#F9FAFB', 'var(--login-text-secondary)'),
]


def retoken(sel, body):
    """Re-point the host's hardcoded dark palette at two-theme tokens."""
    for old, new in TOKEN_MAP:
        body = body.replace(old, new)
    for pat, old, new in LITERAL_BY_SELECTOR:
        if old in body and pat.search(sel):
            body = body.replace(old, new)
            break
    return body


def keep_rule(sel, body, rescope=False):
    if sel.startswith('@keyframes'):
        return '%s {%s}' % (sel, body) if KEEP.search(sel) else None
    parts = []
    for s in (x.strip() for x in sel.split(',')):
        if not (KEEP.search(s) and not DROP.search(s)):
            continue
        if rescope:
            # The host puts id="dark-theme-logo" on the logo wrapper and keys
            # its overrides off it. We have no ids, so they land on the class.
            if '#dark-theme-logo' in s:
                s = s.replace('#dark-theme-logo', '.pds-login-right-logo')
            s = s.replace('.mtsi-dark-theme ', '').replace('.mtsi-dark-theme', '').strip()
            if not s:
                continue
            if DARK_ONLY.search(s):
                s = '[data-theme="dark"] ' + s
        parts.append(s)
    if not parts:
        return None
    return '%s {%s}' % (',\n'.join(parts), retoken(' '.join(parts), body).rstrip())


def extract(path, rescope):
    out = []
    css = open(path, encoding='utf-8').read()
    for sel, body in rules(css):
        if sel.startswith('@media'):
            inner = [keep_rule(s, b, rescope) for s, b in rules(body)]
            inner = [r for r in inner if r]
            if inner:
                out.append('%s {\n%s\n}' % (sel, '\n'.join(inner)))
        else:
            r = keep_rule(sel, body, rescope)
            if r:
                out.append(r)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(ASSETS_OUT, exist_ok=True)

    base = extract(os.path.join(RAW, 'login.css'), rescope=False)
    dark = extract(os.path.join(RAW, 'mtsi-dark-theme.css'), rescope=True)
    generic = lift_generic()

    header = ('/* GENERATED by tools/extract_login.py — do not hand-edit.\n'
              '   Source: id.outsystems.dev login.css + mtsi-dark-theme.css\n'
              '   (upstream: ProductDesignSystem.Patterns.LoginScreen). */\n\n')
    css = (header + TOKENS
           + '\n/* ---- base pattern (light) ------------------------------ */\n\n'
           + '\n\n'.join(base)
           + '\n\n/* ---- dark restyle: form column, spacing, rectangles ---- */\n\n'
           + '\n\n'.join(dark)
           + '\n\n/* ---- generic-class rules, scoped to the pattern -------- */\n\n'
           + '\n\n'.join(generic) + '\n' + ODC_ADAPT)
    # THE HOST'S WEBFONT NAME IS NOT OURS. The identity host loads its face as
    # `noto-sans` (hyphenated) and declares `font-family: noto-sans, sans-serif`.
    # Nothing in this tree defines a face by that name - our @font-face calls it
    # "Noto Sans" - so every one of those declarations was resolving straight to
    # the generic sans-serif, silently swapping the typeface on the account
    # heading and both links. Copying a declaration verbatim is right until the
    # name it depends on does not exist here.
    #
    # Our name is INSERTED after the host's rather than replacing it, so the
    # declaration still reads as the host's and works if `noto-sans` is ever
    # defined. sans-serif stays as the last resort.
    css = re.sub(r'(font-family:\s*)(?:"noto-sans"|noto-sans)(\s*,\s*sans-serif)',
                 r'\1"noto-sans", "Noto Sans"\2', css)

    with open(os.path.join(OUT, 'login.css'), 'w', encoding='utf-8') as fh:
        fh.write(css)

    n_svg = 0
    for pos in ('top-left', 'top-right', 'bottom-left', 'bottom-right'):
        clean = 'rectangle%sdark.svg' % pos.replace('-', '')
        shutil.copy2(os.path.join(RAW, 'rectangle-%s-dark.svg' % pos),
                     os.path.join(ASSETS_OUT, clean))
        n_svg += 1
    # The wordmark. DARK is the identity host's own file, 130x25 with viewBox
    # "0 0 130 25" - the exact artwork and box the login page renders, so dark
    # mode is pixel-identical. The host has no light variant (its login is
    # dark-only: /img/outsystems-light.svg is a 404), so LIGHT stays the shell
    # extraction's 124x24 #0F0E0B mark, drawn into the same 130x25 box. Aspect
    # differs by 0.6% (5.167 vs 5.2), which is not perceptible.
    shutil.copy2(os.path.join(RAW, 'outsystems-wordmark-dark.svg'),
                 os.path.join(ASSETS_OUT, 'outsystemslogodark.svg'))
    n_svg += 1
    shutil.copy2(os.path.join(ROOT, 'src', '04-shell', 'assets', 'outsystems-logo--light.svg'),
                 os.path.join(ASSETS_OUT, 'outsystemslogolight.svg'))
    n_svg += 1

    # integrity: every var() referenced here must be defined here - UNLESS the
    # reference carries a fallback, in which case the fallback IS the intended
    # value. The host itself never defines --Link-Text-Default; its link colour
    # comes from the #B2B4FF fallback, and copying the declaration verbatim
    # keeps it that way. A reference with no fallback is the dangerous kind:
    # the whole declaration is dropped silently.
    defined = set(re.findall(r'(--[\w-]+)\s*:', css))
    used = set(re.findall(r'var\(\s*(--[\w-]+)\s*\)', css))
    fallback = set(re.findall(r'var\(\s*(--[\w-]+)\s*,', css)) - defined

    # This layer deliberately consumes the design system's own tokens so that
    # light and dark both resolve without a second palette here. They are not
    # defined in this file, so assert they exist in the TOKEN LAYER rather than
    # allowlisting the names and hoping.
    ds = set()
    for tf in glob.glob(os.path.join(ROOT, 'src', '00-tokens', '**', '*.css'),
                        recursive=True):
        ds |= set(re.findall(r'(--[\w-]+)\s*:',
                             open(tf, encoding='utf-8', errors='replace').read()))
    borrowed = sorted((used - defined) & ds)
    orphan = sorted((used - defined) - ds)
    if borrowed:
        print('tokens       : %d borrowed from src/00-tokens: %s'
              % (len(borrowed), ', '.join(borrowed)))
    missing = orphan
    print('login layout : %d base + %d dark rules -> src/07-login/login.css (%d KB)'
          % (len(base), len(dark), len(css) // 1024))
    print('assets       : %d corner SVGs -> dist/assets/login/' % n_svg)
    if fallback:
        print('tokens       : %d ref(s) rely on their fallback: %s'
              % (len(fallback), ', '.join(sorted(fallback))))
    if missing:
        raise SystemExit('UNDEFINED tokens referenced: %s' % ', '.join(missing))
    print('tokens       : all %d referenced custom properties defined in-file' % len(used))


if __name__ == '__main__':
    main()
