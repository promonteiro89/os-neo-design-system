// Widget probe — run in the browser console on BOTH the portal and our app,
// then diff the two JSON results.
//
// METHOD NOTES, learned the hard way:
//
//  1. Compare like with like. The portal's `.avatar` in the header is styled by
//     `.unified-header-login-avatar span` in prod.unified.css — the SHELL, not the
//     avatar widget. Probing `.avatar` there and calling the difference a defect
//     was wrong.
//
//  2. Exclude app-specific stylesheets. A portal page loads `<app>.<Screen>_Th`
//     (e.g. `usersaccess.Users_Th`), which is that screen's own CSS and NOT part
//     of the design system. `.table { background: transparent }` came from there;
//     the design system's own rule is `var(--surface-1-default)`, which is what we
//     ship. Treating the rendered value as the spec produced a false defect.
//
//  3. Build the specimen from the portal's ACTUAL markup. `.form-control` is only
//     styled via `.form-control[data-input]`; a bare <input class="form-control">
//     renders as an unstyled browser default and looks like a catastrophic gap.
//     Copy outerHTML from the portal, don't guess.
//
// DESIGN-SYSTEM SHEETS (everything else is app or platform):
//   NeoDesignSystem.OutSystemsUITheme        NeoDesignSystem.Old_NeoDesignSystem
//   NeoDesignSystem.Legacy_NeoTheme          NeoDesignSystem.NeoDesignSystem
//   prod.unified.css  (host shell only — never page widgets)

const PROPS = ['display','background-color','color','border-top-width','border-top-style',
  'border-top-color','border-radius','padding','margin','font','height','min-height',
  'box-shadow','gap','text-transform'];

function probe(root, selectors) {
  const out = {};
  for (const sel of selectors) {
    const e = (root || document).querySelector(sel);
    if (!e) { out[sel] = 'ABSENT'; continue; }
    const c = getComputedStyle(e), r = e.getBoundingClientRect();
    const rec = { tag: e.tagName.toLowerCase(), size: Math.round(r.width) + 'x' + Math.round(r.height) };
    for (const p of PROPS) {
      const v = c.getPropertyValue(p);
      if (v && v !== 'none' && v !== 'normal' && v !== '0px' && v !== 'auto') rec[p] = v.slice(0, 60);
    }
    out[sel] = rec;
  }
  return out;
}

// Specimens copied verbatim from the portal's rendered DOM.
const RIG = `
<button class="btn btn-primary">Invite user</button>
<input data-input="" class="form-control input-small OSFillParent" type="search" placeholder="Search" value="">
<span class="avatar avatar-amber">RM</span>
<div data-container="" class="ds-avatar avatar-format-circle avatar-color-red avatar-size-xs OSInline" role="img"><span data-expression="">UU</span></div>
<table class="table table-no-responsive table-layout-fixed">
  <thead><tr class="table-header"><th class="sortable">User</th><th class="sortable">Access</th></tr></thead>
  <tbody><tr class="table-row"><td>Unnamed User</td><td>End user</td></tr></tbody>
</table>`;

const SELECTORS = ['.btn','.btn-primary','.form-control','.avatar','.avatar-format-circle',
                   '.table','.table-header','.table-row'];

// On OUR app: inject the rig (no publish needed) and probe it.
function probeOurs() {
  document.getElementById('rig')?.remove();
  const rig = document.createElement('div');
  rig.id = 'rig';
  rig.style.cssText = 'position:absolute;left:0;top:2000px;width:1112px;';
  rig.innerHTML = RIG;
  document.body.appendChild(rig);
  void document.body.offsetHeight;
  const res = probe(rig, SELECTORS);
  const cell = s => { const e = rig.querySelector(s); return e ? getComputedStyle(e).padding : null; };
  return { theme: document.documentElement.getAttribute('data-theme'), widgets: res,
           cellPadding: { th: cell('th'), td: cell('td') } };
}

// On the PORTAL: probe in place (the page already renders real specimens).
function probePortal() {
  const cell = s => { const e = document.querySelector(s); return e ? getComputedStyle(e).padding : null; };
  return { page: location.pathname, theme: document.documentElement.getAttribute('data-theme'),
           widgets: probe(document, SELECTORS),
           cellPadding: { th: cell('.table-header th'), td: cell('.table-row td') } };
}
