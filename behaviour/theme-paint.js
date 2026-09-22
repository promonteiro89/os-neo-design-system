/* Theme paint. Canonical source: behaviour/theme-paint.js in the
   neo-design-system repo. The NeoDesignSystem library holds a copy as the
   Script `NeoThemePaint`, but NOT PUBLIC - see below - so it is not consumed
   from there.

   WHERE IT GOES - AND THIS IS THE WHOLE TRICK. In each CONSUMING APP, as a
   Script element listed in the app root's `RequiredScripts`. Not a block's
   RequiredScripts, not an OnReady node.

   That is how the ODC Portal does it. Each portal app carries its own Script
   called `Layout`, listed in its app root's RequiredScripts, and the app's
   compiled bundle index passes it to the Application's initialisation:

       executeRequiredScripts: [ "scripts/apps.UserScripts.Layout.js" ]

   so it runs at app init, before any screen loads and before the stylesheets
   are live. Measured on the harness, the alternatives are too late:

       a library block's RequiredScripts   downloads 413ms, EVALUATES 818ms
                                           (when the block renders; after paint)
       a block's OnReady                   later still

   WHY EACH APP NEEDS ITS OWN COPY. Making the library's copy public, so apps
   could reference it, is rejected by ODC's validator:

       (Error) Invalid app (type: IScript, location:
       /NeoDesignSystem/NeoThemePaint) - The app uses 'Public Property of UI
       Elements', which is not supported on this version.

   If a later platform version supports public Scripts, flip the library copy
   to public and have apps reference it instead of pasting this.

   WHAT IT DOES. Paints the stored theme's page colour inline on <body> (and
   <html>) immediately, so the screen is the right colour from the first frame
   the stylesheets would otherwise paint light, then hands back to the
   stylesheets once they can take over.

   WHY `body`. The first version of this painted <html> only, because
   01-base/reset.css paints html and declares body transparent. It did nothing:
   body's computed background at that moment is rgb(249,250,251), which covered
   the html paint completely. The portal paints body. `important` because the
   rule being beaten is a stylesheet rule the page may mark !important. */

(function () {
    'use strict';

    var root = document.documentElement;
    if (!root || root.dataset.neoThemePaint) return;
    root.dataset.neoThemePaint = '1';

    /* Must match src/00-tokens: --page-background resolves to --neutral-0 and
       --text-primary to --neutral-10. The portal's own script uses the same two
       page colours (#F9FAFB / #181A1F). tools/test.py asserts these against the
       token files: a drifted literal paints the wrong colour for half a second
       and then corrects itself, which is this bug in disguise. */
    var PAINT = {
        light: { background: '#f9fafb', color: '#181a1f' },
        dark: { background: '#181a1f', color: '#f9fafb' }
    };

    /* TrueShade's key: at app init TrueShade has not loaded yet, so derive it
       the way TrueShade does - the first path segment, which ODC's /<AppName>/
       makes the app name. If TrueShade is somehow already present, prefer its
       own answer, since it also honours an explicit app name. */
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
    var targets = [root, document.body].filter(Boolean);
    targets.forEach(function (el) {
        el.style.setProperty('background-color', paint.background, 'important');
        el.style.setProperty('color', paint.color, 'important');
    });

    /* Hand back to the stylesheets once they can take over, so a consumer
       overriding --page-background is not fighting an inline !important
       forever. The portal does this from a client action
       (document.body.style.removeProperty("background-color")); doing it here
       keeps the whole thing in one file with nothing else to wire.

       `--page-background` resolving proves NeoBase is live. For dark,
       `data-theme` must ALSO be set, or removing this hands the page to
       NeoBase's light default and reintroduces the flash. Light is the default,
       so it needs no such wait.

       setTimeout rather than requestAnimationFrame: rAF does not run in a
       background tab, which would strand the paint on a page opened in one. The
       timeout is a safety valve for an app without TrueShade, where
       `data-theme` is never set. */
    var startedAt = Date.now();
    (function handOver() {
        var tokensLive = false;
        try {
            tokensLive = getComputedStyle(root)
                .getPropertyValue('--page-background').trim() !== '';
        } catch (_) { /* treat as not live */ }

        var themeApplied = theme === 'light' || !!root.getAttribute('data-theme');

        if ((tokensLive && themeApplied) || Date.now() - startedAt > 5000) {
            targets.forEach(function (el) {
                el.style.removeProperty('background-color');
                el.style.removeProperty('color');
            });
            return;
        }
        setTimeout(handOver, 16);
    })();
})();
