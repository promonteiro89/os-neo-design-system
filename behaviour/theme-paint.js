/* Theme paint. Canonical source: behaviour/theme-paint.js in the
   neo-design-system repo.

   UNLIKE THE OTHER TWO FILES HERE, THIS IS NOT AN OnReady NODE. It must be a
   library Script resource, so that it evaluates when the bundle loads. OnReady
   runs after the screen has rendered, which is far too late — being late is the
   entire bug this fixes.

   WHAT IT FIXES. Reloading with dark stored paints a light page for ~372ms
   before flipping to dark. The cause is not a late `data-theme` write: measured
   on the harness, the light frame is painted while `data-theme` is ALREADY
   `dark`. NeoBase is the only stylesheet that defines `[data-theme="dark"]`,
   and it goes live ~125ms after OutSystemsUI's, although both arrive within a
   millisecond of each other. For that window the page is styled by
   OutSystemsUI alone, which is light. Setting the attribute sooner cannot help
   when nothing is reading it yet.

   An inline style is the only write that needs no stylesheet, so it is the only
   thing that can paint before NeoBase is live. Measured: 372ms -> 8ms.

   This is what the ODC Portal itself does. Its index.html is the same shape as
   ours — same platform scripts and stylesheets, byte-identical hashes, no
   inline head script — and it paints `background-color` inline on its body
   while only the platform stylesheet is live, then removes the property once
   its own stylesheets and `data-theme` are in place. See
   docs/theme-flash-on-reload.md for both measurements.

   WHY `html` AND NOT `body`. The portal paints body because its CSS does.
   Ours does not: 01-base/reset.css puts `background-color: var(--page-background)`
   on `html` and sets `body` transparent. Paint where the stylesheet paints, or
   the handover is visible.

   WHY NO `color-scheme`. It would darken the browser canvas and form controls,
   but NeoBase never declares it, so removing it at handover would visibly flip
   scrollbars back. It also does not help: the ~370ms of pure white before ANY
   stylesheet is unreachable from an ODC app either way — nothing of ours exists
   yet — and adding `color-scheme` to this script measured no better than
   leaving it out. */

(function () {
    'use strict';

    var root = document.documentElement;
    if (!root || root.dataset.neoThemePaint) return;
    root.dataset.neoThemePaint = '1';

    /* Must match src/00-tokens: --page-background resolves to --neutral-0 and
       --text-primary to --neutral-10, which are exact inverses between themes.
       tools/test.py asserts these four values against the token files, because
       a silent drift here paints the wrong colour for a third of a second and
       then corrects itself, which is exactly the bug it is meant to prevent. */
    var PAINT = {
        light: { background: '#f9fafb', color: '#181a1f' },
        dark: { background: '#181a1f', color: '#f9fafb' }
    };

    /* TrueShade's own key if it has already evaluated, because it also honours
       an explicit app name that this derivation cannot see. The two scripts
       arrive together and their order is not guaranteed, so fall back to the
       same derivation TrueShade uses: the first path segment, as ODC's
       /<AppName>/ gives the app name. */
    function storageKey() {
        try {
            if (window.TrueShade && window.TrueShade.Theme &&
                    window.TrueShade.Theme.GetStorageKey) {
                return window.TrueShade.Theme.GetStorageKey();
            }
        } catch (_) { /* fall through */ }
        var segment = location.pathname.split('/').filter(Boolean)[0] || '';
        return '$OS_' + segment + '$layout-theme';
    }

    function resolvedTheme() {
        var raw = null;
        try { raw = localStorage.getItem(storageKey()); } catch (_) { /* blocked */ }
        if (raw === 'dark' || raw === 'light') return raw;
        try {
            return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        } catch (_) { return 'light'; }
    }

    var theme = resolvedTheme();
    var paint = PAINT[theme];
    root.style.setProperty('background-color', paint.background);
    root.style.setProperty('color', paint.color);

    /* Hand back to the stylesheet the moment it can take over, so a consumer
       overriding --page-background is not fighting an inline style forever.

       Two conditions, and both matter. `--page-background` resolving proves
       NeoBase is live. For dark, `data-theme` must ALSO be set, or removing the
       inline style hands the page to NeoBase's light default and reintroduces
       the flash we just closed. Light needs no such wait: light IS the default.

       setTimeout rather than requestAnimationFrame: rAF does not run in a
       background tab, which would strand the inline style on any page opened in
       one. The timeout is a safety valve for an app that ships NeoBase without
       TrueShade, where `data-theme` is never set at all. */
    var startedAt = Date.now();
    (function handOver() {
        var tokensLive = false;
        try {
            tokensLive = getComputedStyle(root)
                .getPropertyValue('--page-background').trim() !== '';
        } catch (_) { /* treat as not live */ }

        var themeApplied = theme === 'light' || !!root.getAttribute('data-theme');

        if ((tokensLive && themeApplied) || Date.now() - startedAt > 5000) {
            root.style.removeProperty('background-color');
            root.style.removeProperty('color');
            return;
        }
        setTimeout(handOver, 16);
    })();
})();
