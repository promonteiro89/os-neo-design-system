# TrueShade patch — superseded

This document described a one-line addition to `TrueShade.UserScripts.TrueShade`
that applies the stored theme at script-evaluation time instead of waiting for
`Initialize()`:

```js
        // after: Theme.GetStorageKey = getStorageKey;
        try {
            applyTheme(ensureSeeded());
        } catch (_) { }
```

**Measured against real ODC, it does not fix the reload flash** — setting
`data-theme` earlier measured 776 ms of light screen against a 784 ms baseline.
What works is what the ODC Portal does: a Script in the consuming app's root
`RequiredScripts` that paints `<body>` at app init. See
[theme-flash-on-reload.md](theme-flash-on-reload.md).

## Should it be applied anyway?

It is harmless and marginally correct: it closes a real gap on apps whose
stylesheet is live before the script runs, which is the case for a small app
(measured on a throwaway consumer: 12 ms → 0 ms). It reuses `ensureSeeded()` and
`applyTheme()` rather than repeating their logic, `applyTheme()` skips the write
when the value is unchanged, and no event is emitted, so `Initialize()` still
emits `init` exactly once.

But it does not solve the problem it was written for, and it changes one
behaviour: `ensureSeeded()` may seed `system-default` into localStorage earlier
than before. Apply it on its own merits, not as a fix for the flash.

It is applied and published in `CloneOfTrueShade` (revision 2), which is where
it was measured. The original `TrueShade` is untouched.
