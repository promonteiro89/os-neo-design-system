/* Password reveal ("eye"). Canonical source: behaviour/password-reveal.js in the
   neo-design-system repo. This is the body of the `WirePasswordReveal`
   JavaScript node on NeoLayoutCheck's Login OnReady AND VerifyEmail OnReady —
   the two must stay character-identical, which is the whole point of the two
   fallbacks below.

   The eye is NOT a library block: the containers are harness-owned widgets, so
   the wiring is a screen-level JavaScript node rather than a block's OnReady.
   It is the markup that differs between screens, not the intent:

     Login        Container PasswordEyeIcon  + child PasswordEyeGlyph.ph.ph-eye
     VerifyEmail  Container PasswordEye      with "pds-login-password-eye ph ph-eye"
                  on the container itself, no child

   The first version of this script looked up only `PasswordEyeIcon` and only
   `eye.querySelector('.ph')`, so on VerifyEmail BOTH lookups missed and the eye
   was inert: no listener, and no role/tabindex/aria-label either, so it was not
   even reachable by keyboard. It looked fine, because the CSS positions it
   identically on both screens (16px glyph, right: 12px, dead centre) - which is
   also what the host does, on Login and VerifyEmail alike.

   Reported as "the eye icon doesn't have the same behavior in the login page".

   The fix adapts the SCRIPT, not the markup, so either shape works and a third
   screen can use whichever it has. */

var eye = document.getElementById('PasswordEye') || document.getElementById('PasswordEyeIcon');
var input = document.getElementById('PasswordInput');
if (eye && input && !eye.dataset.neoRevealWired) {
    eye.dataset.neoRevealWired = '1';
    eye.setAttribute('role', 'button');
    eye.setAttribute('tabindex', '0');
    eye.setAttribute('aria-label', 'Show password');
    /* `|| eye` is VerifyEmail: there the glyph classes are on the container. */
    var glyph = eye.querySelector('.ph') || eye;
    var toggle = function () {
        var revealed = input.getAttribute('type') === 'text';
        input.setAttribute('type', revealed ? 'password' : 'text');
        input.style.webkitTextSecurity = revealed ? 'disc' : 'none';
        eye.setAttribute('aria-label', revealed ? 'Show password' : 'Hide password');
        if (glyph) {
            glyph.classList.toggle('ph-eye', revealed);
            glyph.classList.toggle('ph-eye-slash', !revealed);
        }
    };
    eye.addEventListener('click', toggle);
    eye.addEventListener('keydown', function (ev) {
        if (ev.key === 'Enter' || ev.key === ' ') {
            ev.preventDefault();
            toggle();
        }
    });
}
