# Design Overhaul — Implementation Changelog - v2.2.0

Date: 2026-07-12
Status: implemented
Related: `DESIGN.md` (The Projection Booth), `PRODUCT.md`, `docs/specs/04-theme-system/design.md` (D5 switcher, extended here)

## Scope

Delight pass over the generated site (`/impeccable delight`). Adds personality to the viewer and homepage without breaking the two-world discipline: every touch is booth machinery made tangible. All styling stays on the D1 token contract, so the 16 themes restyle everything below without changes.

## Changes

### Slide viewer

- **Blackout (`B`)**: projectionist's shutter. A fixed overlay fades the screen to black; any key or click resumes without navigating. Announced via the existing `aria-live` region. Color themeable through `--color-blackout` (defaults to black).
  - `templates/assets/js/slide-viewer.js`: `setupBoothControls()`, `toggleBlackout()`
  - `templates/slide_styles.css`: `.booth-blackout`
- **Booth controls card (`?`)**: keyboard-shortcut reference. Rises from the nav pill; keycap-styled `<kbd>` chips; modal while open (nav keys inert, Tab held on Close, Escape/backdrop/Close dismiss, focus restored on close). Also reachable from a new `?` button in the nav pill.
  - `templates/assets/js/slide-viewer.js`: `toggleHelp()`, `_ensureHelpCard()`
  - `templates/slide_styles.css`: `.booth-help`, `.booth-help-backdrop`, kbd styles
  - `templates/presentation.html`: `#show-help` button
- **Slide counter**: `font-variant-numeric: tabular-nums` plus a 0.2s tick animation on change.
- **Nav buttons**: 1px press on `:active`.
- **Progress bar**: now `var(--color-accent, #3b82f6)` instead of hardcoded hex; follows the active theme.
- Z-order added above the progress bar (1000): help backdrop 1000, help card 1010, shutter 1100.

### Theme switcher (both page types)

- **House-lights crossfade**: switching themes transitions `background-color` / `color` / `border-color` / `fill` over 0.35s instead of snapping. `theme-switcher.js` sets `html.theme-fading` around the stylesheet swap and removes it after the new sheet settles; skipped entirely under reduced motion.
  - `templates/assets/js/theme-switcher.js`: `_withHouseLights()`
  - `templates/assets/css/homepage.css`: shared-chrome section

### Homepage

- **Projector-light hover**: hovering or focusing a card scales the 16:9 preview to 1.03 inside its clipped frame, composing with the existing lift and title-color cue (`.hp-preview` now `overflow: hidden`).
- **Search echo**: the no-results title reads `Nothing matches "term"`.
- **Console signature**: styled, theme-aware devtools message (deck count, generator repo link) in `homepage.js`.

### Accessibility

- Every new animation has a `prefers-reduced-motion: reduce` fallback.
- The pre-existing `slideIn` keyframe joined the reduce block (it had no fallback).
- Help card: `role="dialog"`, `aria-modal`, labelled, `:focus-visible` ring only.

## Bug fix (pre-existing)

`initializeMathJax()` called `MathJax.typesetPromise()` while `window.MathJax` was still only the config object (async script not yet loaded). The uncaught TypeError aborted `init()` before `showSlide(0)`, leaving a blank stage. Reproduced on the committed `site/` build, so it also affected production. Fixed with a `typeof MathJax.typesetPromise === 'function'` guard; MathJax typesets on its own startup, so the manual call is safely skipped.

## Verification

- Jest: 67 pass, including 9 new in `tests/test_booth_controls.js` (blackout toggle/exit/announce; card open/close/modality/aria).
- pytest: 426 pass.
- Browser (Chrome DevTools MCP against a fresh build): blackout, controls card in light and dark themes, crossfade class lifecycle, counter tick, hover transforms, console signature, search echo.

## Known issues, out of scope

- `slide-viewer.js` logs debug noise (fit-text scaling) on every resize.
- `.nav-button:disabled` hardcodes `#9ca3af` (token-contract violation, predates this pass).
- `presentation.html` loads the Tailwind CDN, against the vendored-assets rule.
- `CLAUDE.md` documents `npm test`, but `package.json` only defines `test:js`.
