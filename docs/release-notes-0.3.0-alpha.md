# Release notes — 0.3.0-alpha

Paste-ready copy for the Forge version's release-notes field, in the same voice
as 0.2.0. Companion to [forge-listing-neodesignsystem.md](forge-listing-neodesignsystem.md).

Scope: everything since `v0.1.0-alpha` in git — 11 commits, 119 files,
+8,247 / −363 lines. The bundle goes from 2,439 to 2,781 rules (362 KB → 415 KB).

Where those rules landed, so the claims can be checked:

| Layer | then | now | |
| --- | ---: | ---: | ---: |
| `src/06-legacy-widgets` (the dropdown lives here) | 275 | 524 | +249 |
| `dist/osui-reskin.css` (dialog, checkbox) | 425 | 479 | +54 |
| `src/07-login` (sign-up, verify-email, error states) | 120 | 160 | +40 |
| `compat/neo-odc-compat.css` | 76 | 82 | +6 |

**Already shipped in 0.2.0, so deliberately absent below:** `Layout_Login`, the
five `--login-*` tokens, password-reveal styling, and the collapsed page-header
and login-input fixes.

**On the three new pages.** `ResetPassword`, `SignUp` and `VerifyEmail` are
screens in the `NeoLayoutCheck` harness — an ODC library cannot contain screens
at all, so they are not part of the asset and the notes do not claim they are.
What ships is the CSS those three compositions need, and that is new, so they
are named below as the compositions the login layer now covers. Their screen
actions and navigation stay in the harness.

---

## Paste this into the Forge release-notes field

> ## What's new in 0.3.0
>
> ### Beyond sign-in: reset-password, sign-up and verify-email
>
> 0.2.0 shipped `Layout_Login` and the sign-in composition. The login layer now
> covers the three screens that surround it, so an account flow is styled end to
> end rather than only its front door. All three are built from the same
> `Layout_Login` block:
>
> * **Reset password** — `Layout_Login` with fewer rows. It needs no new classes;
>   it was already possible in 0.2.0 and is called out here because it is part of
>   the same flow.
> * **Sign up** — the email step, which is where the new error states earn their
>   keep.
> * **Verify email** — the step that needed genuinely new styling.
>
> What the verify step added:
>
> * **A password requirements checklist.** `password-analysis-title` and
>   `password-analysis-requirements`, with `password-analysis-requirements-item`
>   for each line — a marker and a label, on a 4px rhythm. Put it inside a field
>   marked `verify-password-field` and it unrolls on `:focus-within` — a 0.4s
>   max-height transition — so the rules appear while the field is being filled
>   and fold away afterwards.
> * **The consent row.** `verify-consent-row` sets the checkbox-and-label
>   rhythm — 12px type, an 8px gap, and the label free to wrap without dragging
>   the checkbox out of line.
> * **The password field variant** used on that step, with the reveal icon
>   anchored to the top of the field so a validation message appearing beneath
>   cannot push it out of position.
>
> As with the password reveal in 0.2.0, the library ships the styling. Which
> requirements are met, and when, is your logic.
>
> ### Form error states
>
> Login inputs now have an invalid state: `not-valid` on a field gives it the
> error border, and keeps it through hover and focus rather than losing it to
> the interaction state. Pair it with the validation message and a submit that
> marks the offending fields.
>
> ### The searchable dropdown
>
> Most of this release. The dropdown now behaves the way the rest of the system
> does, rather than looking right and acting differently.
>
> * **Keyboard.** It opens when it receives focus and puts the caret in the
>   search box, so arrow keys, type-ahead and Enter are the ones you already
>   know. Tab moves on to the next real field instead of walking the option
>   list, and Escape closes it.
> * **Focus ring** on the trigger, matching every other focusable control — and
>   no doubled ring once the panel is open.
> * **An 8px gap** between the trigger and the option panel.
> * **A two-line empty state.** "No results found", with a hint line beneath it,
>   instead of a bare one-liner.
> * **The search icon follows `--icon-primary`**, so it is legible in light as
>   well as dark.
>
> Unlike the password reveal, this one ships the behaviour as well as the
> styling: all 13 `OutSystemsUI/Dropdowns` client actions work against
> `DropdownField`, so `DropdownSetValue`, `DropdownClear`,
> `DropdownGetSelectedValues` and the rest do what they do on the stock widget.
>
> The three blocks are `DropdownField` (the searchable field), `DropdownEmpty`
> (a floating menu container for icon-button row actions) and `DropdownItem`.
>
> ### Dialog styling
>
> A modal dialog, 48 rules that were previously missing: the overlay and its
> dimmed backdrop, the card, a header with title, subtitle and close, a footer,
> the scrollable variant, the tabbed variant, and the "unsaved changes"
> confirmation layer. Build a dialog with these class names and it picks up the
> design system instead of rendering unstyled.
>
> As with the password reveal, the library ships the styling. Opening, closing
> and what the buttons do are yours.
>
> ### Fixes
>
> * The checkbox no longer changes size between breakpoints. It was 20px on
>   desktop and 32px on tablet and phone, because OutSystems UI enlarges
>   checkboxes for touch at a specificity the token-level rule could not reach.
>   Now 20px throughout, tick still centred.
> * The dropdown's search icon was washed out in light mode — it was drawn as an
>   image with a colour baked in and ignored the icon token.
>
> ### One behaviour change
>
> `DropdownSetValue` and `DropdownClear` default to **not** raising the
> dropdown's change event, which left the control showing a stale selection
> after a programmatic change. Both now raise it. If you were relying on the
> silent behaviour — setting an initial value without triggering your own
> OnChange logic, say — guard that logic rather than the call.
>
> ### Alpha
>
> Still `0.x`. Class names, block parameters and token names may move between
> versions; pin the version you tested against rather than tracking latest.

---

## Before you publish

1. **The licensing question in section 0 of the listing doc is still open**, and
   this release enlarges it rather than shrinking it — the dialog family and the
   legacy widget layer are both extracted portal CSS. That is a question about
   the asset, not about these notes, and it wants settling before a public
   submission rather than after.
2. **The listing copy is stale.** Section 5 says "currently 0.1.7", 907 custom
   properties and 1,298 rules. The bundle now defines 711 custom properties and
   2,781 rules. Those property counts are not comparable — 907 counted light and
   dark values separately at the source, 711 counts distinct names in the
   shipped bundle — so do not present it as a reduction.
3. **Verification at this revision.** `python3 tools/test.py` (9 checks,
   offline), `python3 tools/test_runtime.py` (4, against the deployed app) and
   `node tools/test_browser.js` (20, drives a real browser) were all green.
