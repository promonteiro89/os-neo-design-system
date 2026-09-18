/* ==========================================================================
   dropdown-empty — the behaviour the portal's CSS expects
   --------------------------------------------------------------------------
   The portal's dropdown is CSS plus a state contract. The CSS ships in
   dist/neobase.css (recovered by tools/extract_legacy_widgets.py); this is the
   other half, and it is OURS rather than copied: the portal drives the same
   contract from compiled ODC client actions, which are not source you can
   take. What IS recoverable is the contract, and the CSS states it exactly:

       .dropdown-empty.is--open ... .svg-code      { transform: rotate(-180deg) }
       .dropdown-empty.is--open .dropdown-empty-button.input
                                                   { border-color: …focus;
                                                     box-shadow: …focus }
       .dropdown-empty-popover.is--open            { opacity: 1;
                                                     transform: translateY(0);
                                                     pointer-events: auto }
       .dropdown-empty.is--open .dropdown-empty-backdrop { z-index: 101 }

   So the whole job is: put `is--open` on the wrapper and the popover, take it
   off again, and position the popover — which is `position: fixed`, so it has
   to be placed from script. Everything visual, including both transitions, is
   already in the CSS.

   TWO THINGS THIS DELIBERATELY DOES NOT DO.

   It keeps no state of its own. State is read back from the DOM every time,
   because ODC re-renders a screen's markup freely and rewrites any attribute
   bound to a variable — a JS flag would go stale behind a re-render while the
   class on the element stays true. The class IS the state.

   It binds nothing per element. One delegated listener set on `document`,
   installed once, so dropdowns that appear later (inside an If, a List, a
   popover that ODC only renders when shown) work with no re-initialisation
   and no MutationObserver.

   TAB ORDER. virtual-select leaks focusable elements: its wrapper and every
   option carry tabindex=0, and before it is switched to keep-always-open it
   also parks a dropbox on <body>. Inside a closed popover those are invisible
   tab stops sitting right after our trigger, so Tab appears to fall into a
   void. The portal works around it by giving every field on the page an
   explicit positive tabindex (1,2,3,5,6,…), which pushes all tabindex=0
   elements to the end of the page order. We fix it at source instead, so a
   consumer needs no tabindex at all: the closed popover is marked `inert`,
   which removes its whole subtree from the tab order, and the list is moved
   inline at install rather than on first open so no <body> dropbox ever
   exists. Net effect matches the portal: trigger, then the next real field.

   KEYBOARD SUPPORT IS A HAND-OFF, NOT AN IMPLEMENTATION. The trigger is a
   div, so the block gives it tabindex=0 and role=combobox and this script
   opens on Enter or Space. Everything after that — arrow keys, type-ahead,
   Enter to choose — is virtual-select's own `onKeyDown`/`navigateOptions`,
   which only ever runs when focus is inside its search input. So on open we
   move focus there and get the full behaviour for free; reimplementing option
   navigation here would be duplicating working code and would drift from it.

   SCOPED TO THE .dropdown-empty FAMILY. The library also has a DropdownEmpty
   block — the icon-button row-actions menu — whose trigger carries
   `dropdown-empty-trigger` but whose root is `fusion-dropdown-empty`. The
   click handler therefore matches its trigger and then finds no
   `.dropdown-empty` ancestor, so it returns before preventDefault and leaves
   that block to drive itself. Keep that order if you touch it.
   ========================================================================== */
(function () {
  'use strict';

  if (window.__neoDropdownEmpty) return;      // idempotent: safe on every OnReady
  window.__neoDropdownEmpty = true;

  var OPEN = 'is--open';
  /* Measured on the host with its popover open and opening downward: popover
     top 503, trigger bottom 495. The CSS's own closed-state offset is `top:
     44px` against a 40px trigger, which reads as 4 and is what this used to be
     - but the host's script positions the OPEN popover itself, at 8. */
  var GAP = 8;                                 // --space-2, measured on the host

  function wrapperOf(el) { return el.closest('.dropdown-empty'); }
  function popoverOf(w)  { return w && w.querySelector('.dropdown-empty-popover'); }
  function triggerOf(w)  { return w && w.querySelector('.dropdown-empty-trigger'); }
  function isOpen(w)     { return !!w && w.classList.contains(OPEN); }

  /* The popover is position:fixed, so it is placed against the viewport.
     Flips above the trigger when there is more room there, which is what the
     `top` in the CSS cannot do on its own. */
  function place(w) {
    var trigger = triggerOf(w), pop = popoverOf(w);
    if (!trigger || !pop) return;

    var t = trigger.getBoundingClientRect();

    /* Width follows the trigger for the input-shaped variant — the CSS says as
       much with `.dropdown-empty:has(.dropdown-empty-trigger.input)
       .dropdown-empty-popover-fit { width: 100% }`, which cannot resolve
       against a fixed element. The explicit size variants keep their width. */
    var sized = /dropdown-empty-popover-(xs|s|m|l)\b/.test(pop.className);
    if (!sized) pop.style.width = Math.round(t.width) + 'px';

    pop.style.left = Math.round(t.left) + 'px';

    var h = pop.offsetHeight;
    var below = window.innerHeight - t.bottom - GAP;
    if (h > below && t.top - GAP > below) {
      pop.style.top = Math.round(t.top - h - GAP) + 'px';   // flip up
    } else {
      pop.style.top = Math.round(t.bottom + GAP) + 'px';
    }
  }

  /* ---- vscomp: make the list render inside the popover -------------------
     ODC's DropdownSearch initialises virtual-select with show-dropbox-as-popup,
     so the list mounts on <body> — outside the popover, and out of reach of
     anything scoped to it. The portal runs the same widget the other way, in
     keep-always-open, which its own CSS states outright:

         .dropdown-empty-popover-content .vscomp-wrapper.keep-always-open
           .vscomp-dropbox { border: none }

     keepAlwaysOpen is read once, at init, so assigning the field afterwards
     does nothing — the dropbox has already been portaled. So re-initialise.
     destroy() unmounts the body wrapper and empties the div WITHOUT removing
     it, which is what makes this safe: the platform's own change handler is
     bound to that div, not to anything vscomp built, so it survives and the
     new instance dispatches to it exactly as before. Verified live — a
     setValue() after re-init still fires one change event on the element.

     Runs at most once per element: the guard is the flag we are setting. */
  /* The platform's own provider config for this widget, or null when the OSUI
     instance is not registered yet. */
  function providerConfigFor(w) {
    var inst = osuiInstanceFor(w);
    if (!inst || !inst.configs || typeof inst.configs.getProviderConfig !== 'function') return null;
    try { return inst.configs.getProviderConfig(); } catch (e) { return null; }
  }

  function inlineList(w) {
    var ele = w.querySelector('.dropdown-empty-popover-content .vscomp-ele');
    var vs = ele && ele.virtualSelect;
    if (!vs || vs.keepAlwaysOpen) return false;
    if (!window.VirtualSelect || typeof window.VirtualSelect.init !== 'function') return false;

    /* Take the props from the PLATFORM's own config object rather than copying
       a dozen of them off the live instance by hand. `getProviderConfig()` is
       what the block itself would hand VirtualSelect: the full option records
       with their groups, descriptions and icons, the prompts, and - the reason
       this matters - whatever a consumer passed to SetVirtualSelectConfigs,
       already merged in. The hand-copied list silently dropped all of that, so
       a config set through the client action survived the redraw and was then
       thrown away by our own re-init: measured noOptionsText back at its
       default right after the action reported success.

       Only three things are overridden, and they are the three we own: the list
       stays inline (keepAlwaysOpen, no dropbox popup) and it renders against
       the element rather than the '#id' selector the config carries. */
    var props = {};
    var base = providerConfigFor(w);
    if (base) {
      for (var k in base) {
        if (Object.prototype.hasOwnProperty.call(base, k)) props[k] = base[k];
      }
    } else {
      /* No OSUI instance to read from - fall back to the live widget. */
      props.options = vs.options
        .filter(function (o) { return !o.isGroupTitle && !o.isNew; })
        .map(function (o) { return { label: o.label, value: o.value }; });
      props.placeholder = vs.placeholder;
      props.search = vs.hasSearch;
      props.searchPlaceholderText = vs.searchPlaceholderText;
      props.noSearchResultsText = vs.noSearchResultsText;
      props.hideClearButton = vs.hideClearButton;
      props.multiple = vs.multiple;
      props.zIndex = vs.zIndex;
    }
    props.ele = ele;
    props.selectedValue = vs.getValue();
    props.keepAlwaysOpen = true;
    props.showDropboxAsPopup = false;
    /* The block's config asks for the dropbox to be wrapped on <body>; that is
       exactly the portal-escape this component exists to avoid. */
    delete props.dropboxWrapper;
    vs.destroy();
    window.VirtualSelect.init(props);
    return true;
  }

  /* `inert` takes the whole closed popover out of the tab order and out of
     hit-testing in one attribute, which is what stops virtual-select's
     tabindex=0 wrapper and options from becoming invisible tab stops. */
  function setInert(w, value) {
    var pop = popoverOf(w);
    if (pop) pop.inert = value;
  }

  /* At rest the portal has no <body> dropbox and its list already lives in the
     popover, so do the same: try to inline every field's list as soon as the
     script installs, and mark every closed popover inert. Retried a few times
     because the platform's DropdownSearch initialises in its own OnReady and
     may not have produced an instance yet. */
  function settleAll(attempt) {
    var fields = document.querySelectorAll('.dropdown-empty');
    var pending = false;
    for (var i = 0; i < fields.length; i++) {
      var w = fields[i];
      if (!isOpen(w)) setInert(w, true);
      if (w.querySelector('.dropdown-empty-popover-content')) {
        if (!inlineList(w)) {
          var ele = w.querySelector('.dropdown-empty-popover-content .vscomp-ele');
          if (!ele || !ele.virtualSelect) pending = true;   // not initialised yet
        }
      }
      /* The OSUI instance is registered by the platform, on its own schedule -
         keep coming back until it is there, or the client actions arrive
         unbridged. */
      if (!bridgeInstance(w)) pending = true;
    }
    if (pending && attempt < 20) setTimeout(function () { settleAll(attempt + 1); }, 150);
  }

  function open(w) {
    closeAll(w);
    var pop = popoverOf(w), trigger = triggerOf(w);
    if (!pop) return;
    var relaid = inlineList(w);
    setInert(w, false);                         // must precede focusList()
    w.classList.add(OPEN);
    place(w);                                   // place BEFORE the class that
    pop.classList.add(OPEN);                    // starts the opacity transition
    if (trigger) trigger.setAttribute('aria-expanded', 'true');
    /* A first open that just moved the list in measured the popover before it
       had one, so its height — and therefore any flip — was wrong. */
    if (relaid) setTimeout(function () { place(w); }, 0);

    /* Hand the keyboard to virtual-select. Deferred because on the open that
       re-initialised it the search input does not exist yet. */
    setTimeout(function () { focusList(w); }, 0);
  }

  /* Focus virtual-select's search input, which is what arms its own arrow-key
     and type-ahead handling. Falls back to the first option when the list was
     built without a search box. */
  function focusList(w) {
    var pop = popoverOf(w);
    if (!pop) return;
    var search = pop.querySelector('.vscomp-search-input');
    if (search) { search.focus(); return; }
    var opt = pop.querySelector('.vscomp-option:not(.disabled)');
    if (opt) opt.focus();
  }

  function close(w) {
    var pop = popoverOf(w), trigger = triggerOf(w);
    w.classList.remove(OPEN);
    if (pop) { pop.classList.remove(OPEN); pop.inert = true; }
    if (trigger) trigger.setAttribute('aria-expanded', 'false');
  }

  function closeAll(except) {
    var opened = document.querySelectorAll('.dropdown-empty.' + OPEN);
    for (var i = 0; i < opened.length; i++) {
      if (opened[i] !== except) close(opened[i]);
    }
  }

  /* ---- OutSystemsUI/Dropdowns client actions ----------------------------
     The block wraps a REAL OSUI DropdownSearch: the platform registers it with
     OutSystems.OSUI.Patterns.DropdownAPI under the inner widget's id, and every
     one of the thirteen OutSystemsUI/Dropdowns client actions resolves that
     instance and calls a method on it. So the actions already reach us. What
     they do once they arrive is the question, and it was measured one at a time
     against a live DropdownField:

       DropdownGetSelectedValues   worked - full DropdownOption structure back
       DropdownSetValue            worked - value AND our trigger label
       DropdownClear               worked - value and label back to placeholder
       SetVirtualSelectEvent       worked - callback fired on change
       UnsetVirtualSelectEvent     worked - callback stopped

       DropdownOpen / DropdownClose    reported success, did NOTHING. They drive
                                       the vscomp's own dropbox, and ours runs
                                       keepAlwaysOpen inside OUR popover, so
                                       there is no dropbox for them to move.
       DropdownNotValid                put `osui-dropdown--not-valid` and the
       DropdownClearValidation         message element on the INNER element,
                                       which lives inside the popover - so the
                                       error was invisible while closed.
       DropdownDisable / Enable        set the vscomp's disabled attribute, but
                                       our trigger kept its enabled styling and
                                       stayed interactive.
       DropdownTogglePopup             flips ShowDropboxAsPopup and REDRAWS.
       SetVirtualSelectConfigs         redraws too, and the redraw rebuilds the
                                       provider from the block's own configs,
                                       which do not carry our arrangement:
                                       measured keepAlwaysOpen false,
                                       showDropboxAsPopup true, the list gone
                                       from our popover. The component silently
                                       reverted to ODC's portal-to-<body> popup.

     The five that work are left alone. The rest are bridged below by wrapping
     the instance's own methods, so the consumer keeps calling the stock client
     actions and needs no special casing. */

  function osuiApi() {
    var OS = window.OutSystems;
    return (OS && OS.OSUI && OS.OSUI.Patterns && OS.OSUI.Patterns.DropdownAPI) || null;
  }

  /* The instance whose element lives inside this wrapper. Matching by
     containment rather than by id: the inner widget's id is generated by the
     block (`b2-InnerDropdown`) and nothing outside can predict it. */
  function osuiInstanceFor(w) {
    var api = osuiApi();
    if (!api || typeof api.GetAllDropdowns !== 'function') return null;
    var ids;
    try { ids = api.GetAllDropdowns(); } catch (e) { return null; }
    for (var i = 0; i < ids.length; i++) {
      var inst = api.GetDropdownById(ids[i]);
      if (inst && inst.selfElement && w.contains(inst.selfElement)) return inst;
    }
    return null;
  }

  /* DropdownNotValid / DropdownClearValidation. OSUI's own validation() still
     runs, so its state stays truthful; this mirrors it onto the markup the
     portal's CSS actually styles: the message becomes a sibling <span
     class="validation-message"> - the same shape ODC renders for a failed
     Input, and already styled in the bundle. Tagged with a data attribute so we
     never remove a message the consumer put there. The trigger itself is left
     alone on purpose; see the note inside applyValidation. */
  /* WHERE the message goes matters. `.dropdown-empty` is a flex ROW, so a span
     dropped in beside the trigger lays out next to it, 119px wide, not beneath
     it - measured. It belongs after the block's own root instead, which in a
     normal stacked form is a child of the field's column container, and is
     exactly where ODC puts the `validation-message` span for a failed Input. */
  function messageHost(w) {
    return w.closest('.OSBlockWidget') || w;
  }

  function ownMessage(w) {
    var next = messageHost(w).nextElementSibling;
    return (next && next.hasAttribute && next.hasAttribute('data-neo-dropdown-message'))
      ? next : null;
  }

  function applyValidation(w, isValid, message) {
    var trigger = triggerOf(w);
    if (!trigger) return;
    var own = ownMessage(w);
    if (isValid === false) {
      /* The red border is a DEVIATION FROM THE HOST'S SCREEN, chosen
         deliberately. Its signup page shows the message under an otherwise
         untouched country box - measured, submitted empty: host trigger
         rgb(70,75,86) while every Input beside it is rgb(239,78,56) - because
         it validates that field through a private record passed into its own
         block rather than through DropdownNotValid, so nothing ever sets the
         class.

         Its design system disagrees with its own screen. The rule
         `.dropdown-empty-trigger.input.not-valid { border-color:
         var(--input-error-border-default) }` is extracted from the host's
         sheet, so red IS what it says an invalid dropdown looks like, and that
         is also what every Input on the form does. This was removed once to
         match the screen and put back by request; the stylesheet wins. */
      trigger.classList.add('not-valid');
      if (!own) {
        var host = messageHost(w);
        own = document.createElement('span');
        own.className = 'validation-message';
        own.setAttribute('data-neo-dropdown-message', '');
        if (host.parentNode) host.parentNode.insertBefore(own, host.nextSibling);
      }
      own.textContent = message || '';
    } else {
      trigger.classList.remove('not-valid');
      if (own && own.parentNode) own.parentNode.removeChild(own);
    }
  }

  /* DropdownDisable / DropdownEnable. The class goes on BOTH the wrapper and
     the trigger on purpose: the CSS keys on the trigger
     (`.dropdown-empty-trigger.input.dropdown-empty--disabled`, which is also
     what sets pointer-events: none), while this script's own guards read the
     wrapper. tabindex goes with it, or a disabled field would still be a tab
     stop that opens on focus. */
  function setDisabled(w, off) {
    var trigger = triggerOf(w);
    w.classList.toggle('dropdown-empty--disabled', off);
    if (trigger) {
      trigger.classList.toggle('dropdown-empty--disabled', off);
      trigger.setAttribute('tabindex', off ? '-1' : '0');
    }
    if (off) close(w);
  }

  /* A redraw rebuilds the provider without our arrangement. Every path that
     redraws - setProviderConfigs, togglePopup, changeProperty - funnels through
     redraw(), and it defers its work through AsyncInvocation, so the repair has
     to wait for the rebuild rather than run beside it. */
  function reinlineAfterRedraw(w, attempt) {
    setTimeout(function () {
      var ele = w.querySelector('.dropdown-empty-popover-content .vscomp-ele');
      var vs = ele && ele.virtualSelect;
      if (vs && !vs.keepAlwaysOpen) {
        inlineList(w);
        if (isOpen(w)) place(w);
        return;
      }
      if (attempt < 20) reinlineAfterRedraw(w, attempt + 1);
    }, 50);
  }

  function bridgeInstance(w) {
    var inst = osuiInstanceFor(w);
    if (!inst) return false;
    if (inst.__neoBridged) return true;
    inst.__neoBridged = true;

    var origValidation = inst.validation,
        origDisable    = inst.disable,
        origEnable     = inst.enable,
        origRedraw     = inst.redraw,
        origSetValue   = inst.setValue,
        origClear      = inst.clear;

    /* DropdownSetValue and DropdownClear both default `silentOnChangedEvent` to
       TRUE, and that leaves this component showing a lie.

       A stock DropdownSearch renders its selection inside virtual-select, so
       setting the value is enough to repaint it. Ours renders the label in its
       own trigger, from a variable the block fills in its OnChanged handler -
       so a silent set moves the value and never tells the trigger. Measured on
       the lab screen, through the real client actions:

         DropdownSetValue   value ES,  trigger still "Select your country",
                            stock reading "Spain"
         DropdownClear      value "",  trigger still "Portugal"

       So the event is forced on. Repainting the trigger from here instead was
       the other option and is worse: the label is framework-rendered, so a DOM
       write is reverted the next time ODC re-renders the block. Going through
       the event keeps the variable and the markup in step, which is the only
       version that survives a re-render.

       The cost is that a consumer asking for a silent set does not get one -
       OnChanged fires. For this component silence was never really available:
       it would just mean a stale trigger. */
    inst.setValue = function (optionsToSelect) {
      origSetValue.call(inst, optionsToSelect, false);
    };
    inst.clear = function () {
      origClear.call(inst, false);
    };

    /* Open/Close drive OUR popover. The originals are not called at all: with
       keepAlwaysOpen there is no dropbox of their own to act on. */
    inst.open  = function () { open(w); };
    inst.close = function () { close(w); };

    /* DropdownTogglePopup is a DISPLAY-MODE switch, not open/close - it sets
       ShowDropboxAsPopup and redraws. This component always renders its list
       inline in its own popover, so the setting has nothing to select between
       and the redraw only tears the list out. Deliberately inert. */
    inst.togglePopup = function () { };

    inst.validation = function (isValid, message) {
      try { origValidation.call(inst, isValid, message); } catch (e) { }
      applyValidation(w, isValid, message);
    };
    inst.disable = function () { try { origDisable.call(inst); } catch (e) { } setDisabled(w, true); };
    inst.enable  = function () { try { origEnable.call(inst); } catch (e) { } setDisabled(w, false); };

    inst.redraw = function () {
      try { origRedraw.call(inst); } catch (e) { }
      reinlineAfterRedraw(w, 0);
    };

    return true;
  }

  /* ---- keyboard entry, matched to the portal ----------------------------
     Measured on the host's own VerifyEmail with real Tab presses:

       Tab onto the trigger        the popover OPENS, focus stays on the trigger
       a moment later              focus moves into the vscomp search input
       Tab from inside the open    the popover CLOSES and focus goes to the NEXT
                                   FORM FIELD, never to an option

     So on the host the dropdown is reached by Tab ALONE: no Enter, no
     ArrowDown. Ours only opened on a key, which is what "keyboard navigation to
     the dropdown is not the same" meant - the stop was reachable and drew a
     focus ring, but it stayed shut. `.focus()` on the host's trigger from the
     console opens it too, so what it hangs the behaviour on is the focus event,
     not a key.

     Its mouse behaviour is a plain toggle - click opens, click again closes,
     and focus sits on the trigger throughout - and that is the constraint on
     the handler below. A click on an unfocused trigger fires focus BEFORE
     click, so opening on that focus and then toggling on the click would land
     closed and a first click would look dead. Hence the pointer guard: the
     focus path is for keyboard focus only. */

  var pointerFocus = false;   /* a pointer press is driving the focus that follows */
  var silentFocus = false;    /* we are moving focus ourselves - do not re-open */

  function armPointer() {
    pointerFocus = true;
    /* Cleared on the next task. The focus a press causes is dispatched as the
       default action of that same press, so it always arrives first. */
    setTimeout(function () { pointerFocus = false; }, 0);
  }
  document.addEventListener('pointerdown', armPointer, true);
  document.addEventListener('mousedown', armPointer, true);
  document.addEventListener('touchstart', armPointer, true);

  /* Focus the trigger without the focusin handler below reading it as the user
     arriving by keyboard and re-opening what we have just closed. */
  function focusTrigger(w) {
    var t = triggerOf(w);
    if (!t) return;
    silentFocus = true;
    t.focus();
    setTimeout(function () { silentFocus = false; }, 0);
  }

  document.addEventListener('focusin', function (e) {
    var t = e.target.closest && e.target.closest('.dropdown-empty-trigger');
    if (!t) return;
    var w = wrapperOf(t);
    if (!w || w.classList.contains('dropdown-empty--disabled')) return;
    if (pointerFocus || silentFocus || isOpen(w)) return;
    open(w);
  });

  /* Everything tabbable EXCEPT what lives inside a `.dropdown-empty`, in
     document order. The exclusion is the whole point: while the popover is open
     its search box and its rendered options are tabbable, and the host never
     lands on any of them - Tab there leaves for the next form field. */
  function outsideTabbables() {
    var all = document.querySelectorAll(
      'a[href], button, input, select, textarea, [tabindex]');
    var out = [];
    for (var i = 0; i < all.length; i++) {
      var el = all[i];
      if (el.disabled || el.tabIndex < 0) continue;
      if (!el.offsetWidth && !el.offsetHeight && !el.getClientRects().length) continue;
      if (el.closest('.dropdown-empty')) continue;
      out.push(el);
    }
    return out;
  }

  /* Move focus to the field that follows the whole widget, or precedes it for
     Shift+Tab. */
  function focusBeyond(w, backwards) {
    var trigger = triggerOf(w) || w;
    var list = outsideTabbables();
    var after = -1;
    for (var i = 0; i < list.length; i++) {
      if (trigger.compareDocumentPosition(list[i]) & Node.DOCUMENT_POSITION_FOLLOWING) {
        after = i;
        break;
      }
    }
    var target = backwards
      ? (after === -1 ? list[list.length - 1] : list[after - 1])
      : (after === -1 ? null : list[after]);
    if (target) target.focus();
  }

  /* ---- delegated listeners, installed once ------------------------------ */

  document.addEventListener('click', function (e) {
    var trigger = e.target.closest && e.target.closest('.dropdown-empty-trigger');
    if (trigger) {
      var w = wrapperOf(trigger);
      /* No `.dropdown-empty` ancestor means this is the fusion menu block's
         own trigger, which drives itself — return before preventDefault and
         leave the event alone. `--disabled` and the read-only variants are
         inert too: the CSS already sets pointer-events:none on them, but a
         keyboard-driven click still arrives, so the guard is here as well. */
      if (!w || w.classList.contains('dropdown-empty--disabled')) return;
      e.preventDefault();
      isOpen(w) ? close(w) : open(w);
      return;
    }
    /* A click inside a popover must not close it — the list, the search box and
       the footer buttons all live in there. */
    if (e.target.closest && e.target.closest('.dropdown-empty-popover')) return;
    closeAll(null);
  }, true);

  /* Picking a value closes the popover, as it does on the portal. A
     multi-select stays open — the user is still choosing. */
  document.addEventListener('change', function (e) {
    var ele = e.target;
    if (!ele.classList || !ele.classList.contains('vscomp-ele')) return;
    var w = wrapperOf(ele);
    if (!w || !isOpen(w)) return;
    if (ele.virtualSelect && ele.virtualSelect.multiple) return;
    close(w);
    /* Hand focus back to the trigger, silently. Focus was inside the popover,
       which close() makes inert, and a browser will not hold focus inside an
       inert subtree - it drops to <body>, so the user's next Tab restarts at
       the TOP OF THE DOCUMENT. Measured on the host after picking a country by
       keyboard: focus stays on its own search input and the next Tab still
       moves FORWARD through the form. We cannot copy that, since inert is what
       keeps the closed popover's search box and options out of the tab order in
       the first place, so the trigger is where focus goes instead - one stop
       earlier than the host, and moving the same direction.

       Via focusTrigger(), never trigger.focus(): the focusin handler opens on
       keyboard focus and would re-open the dropdown the selection just closed. */
    focusTrigger(w);
  }, true);

  document.addEventListener('keydown', function (e) {
    /* Tab from an open dropdown closes it and carries on through the FORM,
       never into the list - what the host does from its search input and from
       an option alike. Without this the next stop is the search box and then
       every rendered option in turn.

       One deliberate deviation: on the host, tabbing off the trigger within the
       moment before focus has moved into the search box leaves the popover
       hanging open with focus two fields away. That is a race, not a designed
       behaviour, so this closes on the way out either way. */
    if (e.key === 'Tab') {
      var wtab = e.target.closest && e.target.closest('.dropdown-empty');
      if (!wtab || !isOpen(wtab)) return;
      e.preventDefault();
      close(wtab);
      focusBeyond(wtab, e.shiftKey);
      return;
    }

    /* Enter or Space on a focused trigger opens it, the way a native combobox
       behaves. Space has to be prevented or the page scrolls. */
    if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
      var t = e.target.closest && e.target.closest('.dropdown-empty-trigger');
      if (t) {
        var wt = wrapperOf(t);
        if (!wt || wt.classList.contains('dropdown-empty--disabled')) return;
        e.preventDefault();
        isOpen(wt) ? close(wt) : open(wt);
      }
      return;
    }

    /* ArrowDown on a closed trigger opens it and lands in the list, again as a
       native combobox does. */
    if (e.key === 'ArrowDown') {
      var td = e.target.closest && e.target.closest('.dropdown-empty-trigger');
      var wd = td && wrapperOf(td);
      if (wd && !isOpen(wd)) { e.preventDefault(); open(wd); }
      return;
    }

    if (e.key !== 'Escape') return;
    /* NOTE: this local must NOT be called `open`. `var` hoists to the top of
       this handler, so a local named `open` shadows the open() function above
       for the WHOLE function — including the Enter and ArrowDown branches,
       where it is still undefined. That shipped once: clicking worked, Escape
       worked, and Enter threw "open is not a function" silently. */
    var opened = document.querySelector('.dropdown-empty.' + OPEN);
    if (!opened) return;
    close(opened);
    /* Via focusTrigger, not trigger.focus(): the focusin handler above opens on
       keyboard focus, so a bare focus() here would re-open what Escape just
       closed. */
    focusTrigger(opened);                       // ESC returns focus to the trigger
  });

  /* Fixed positioning does not follow the page, so an open popover has to be
     re-placed on scroll and resize. Capture phase catches scrolling inside
     ODC's own scroll container, which does not bubble to window. */
  function reposition() {
    var opened = document.querySelectorAll('.dropdown-empty.' + OPEN);
    for (var i = 0; i < opened.length; i++) place(opened[i]);
  }
  window.addEventListener('scroll', reposition, true);
  window.addEventListener('resize', reposition);

  settleAll(0);
})();
