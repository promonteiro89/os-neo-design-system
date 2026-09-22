/* Theme paint. Canonical source: behaviour/theme-paint.js in the
   neo-design-system repo.

   UNLIKE THE OTHER TWO FILES HERE, THIS IS NOT AN OnReady NODE, AND IT IS NOT A
   BLOCK'S RequiredScripts EITHER. Both run too late. Measured on the harness, a
   script attached through a block's RequiredScripts downloads with the bundle at
   413ms but does not EVALUATE until 818ms, when the block renders - 374ms after
   first paint. It must evaluate when the bundle evaluates.

   WHAT IT FIXES. Reloading with dark stored shows a light screen for ~780ms.
   Roughly half of that is reachable and half is not:

     ~145 - 528ms   pure white, before any stylesheet applies. Nothing in an ODC
                    app can reach it: the generated index.html carries only
                    platform files, so no app or library code exists yet.
     ~528 - 920ms   the light theme, painted because `data-theme` is not set
                    until the shell's OnReady. THIS is what this script closes,
                    to ~17ms.

   WHY A STYLE ELEMENT AND NOT AN INLINE STYLE ON `html`. The first version of
   this painted `document.documentElement` inline, because 01-base/reset.css
   puts `background-color: var(--page-background)` on `html` and declares `body`
   transparent. It had NO measurable effect. `body` is not transparent at that
   moment: its computed background is rgb(249,250,251) at 441ms, so it covers
   the html paint completely. Paint both, and `!important` because the rule
   being overridden is a stylesheet rule, not an inline one.

   A style element also works before `<body>` exists, which an inline write on
   `document.body` would not.

   WHY NOT JUST SET `data-theme` EARLY. Measured: no effect at all (776ms vs a
   784ms baseline). The stylesheet that reads it is live, but the screen is light
   for reasons that resolve later regardless. Only painting closes the window.

   This is what the ODC Portal does: its index.html is the same shape as ours,
   and it paints `background-color` on its body while only the platform
   stylesheet is live, then removes the property once its own stylesheets and
   `data-theme` are in place. See docs/theme-flash-on-reload.md. */

(function () {
    'use strict';

    var root = document.documentElement;
    if (!root || root.dataset.neoThemePaint) return;
    root.dataset.neoThemePaint = '1';

    /* Must match src/00-tokens: --page-background resolves to --neutral-0 and
       --text-primary to --neutral-10. tools/test.py asserts these against the
       token files, because a silent drift here paints the wrong colour for half
       a second and then corrects itself, which is this bug in disguise. */
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

    /* Light needs no paint: light is what the stylesheets do by default, so
       there is no wrong colour to suppress and nothing to hand back later. */
    var theme = resolvedTheme();
    if (theme !== 'dark') return;

    var paint = PAINT.dark;
    var style = document.createElement('style');
    style.textContent = 'html,body{background-color:' + paint.background +
        ' !important;color:' + paint.color + ' !important}';
    (document.head || root).appendChild(style);

    /* Hand back to the stylesheets the moment they can take over, so a consumer
       overriding --page-background is not fighting an !important rule forever.

       Two conditions, and both matter. `--page-background` resolving proves
       NeoBase is live. `data-theme` must ALSO be set, or removing this hands the
       page to NeoBase's light default and reintroduces the flash just closed.

       setTimeout rather than requestAnimationFrame: rAF does not run in a
       background tab, which would strand the override on any page opened in one.
       The timeout is a safety valve for an app that ships NeoBase without
       TrueShade, where `data-theme` is never set at all. */
    var startedAt = Date.now();
    (function handOver() {
        var tokensLive = false;
        try {
            tokensLive = getComputedStyle(root)
                .getPropertyValue('--page-background').trim() !== '';
        } catch (_) { /* treat as not live */ }

        if ((tokensLive && root.getAttribute('data-theme')) || Date.now() - startedAt > 5000) {
            if (style.parentNode) style.parentNode.removeChild(style);
            return;
        }
        setTimeout(handOver, 16);
    })();
})();
