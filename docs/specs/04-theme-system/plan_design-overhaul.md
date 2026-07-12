# Design Overhaul — Implementation Changelog - v2.2.0

Date: 2026-07-12
Status: implemented
Related: `DESIGN.md` (The Projection Booth), `PRODUCT.md`, `docs/specs/04-theme-system/design.md` (D5 switcher, extended here)

## Scope

Two passes over the generated site, in order. All styling stays on the D1 token contract, so the 16 themes restyle everything below without changes.

1. **Homepage craft** (`/impeccable craft homepage`): restage the homepage as the Projection Booth's archive shelf.
2. **Delight pass** (`/impeccable delight`): personality for the viewer and homepage without breaking the two-world discipline: every touch is booth machinery made tangible.

## Part 1 — Homepage craft

### Homepage rebuild

- Two worlds staged correctly: page background is Booth Gray (`--color-surface-1`), cards are Canvas White on the stage-lift shadow, previews strictly 16:9. The old layout had this inverted (white page, gray cards).
  - `templates/homepage.html` (rewritten), `templates/assets/css/homepage.css` (rewritten; shared chrome selectors for `presentation.html` kept)
- Masthead replaces "Found N presentations with enhanced Deckset features": mono deck/slide counter echoing the viewer's counter, display headline, one supporting line.
- The latest deck opens the shelf as a full-width featured card: "Latest" kicker, headline-scale title, "Open the deck →" line. Each card is a single link; the old three-link card and its "View Presentation" chip are gone.
- Decks without a preview image render a typeset title slide (title plus `1 / n` counter) in the 16:9 frame instead of a document icon.
- Removed from the homepage: Tailwind CDN, "Enhanced" badge, gradient `.enhanced-indicator`. Search, theme switcher, analytics, and skip link kept on the same JS hooks.
- Entrance motion: masthead rises first, cards stagger in behind it; hover lifts the card. All of it off under `prefers-reduced-motion: reduce`.
- States covered: empty archive, empty search, skip link, whole-card Cue Blue focus ring (`:has(:focus-visible)`, inset-outline fallback).

### Theme token fixes (pre-existing)

- `light.css` / `minimal.css`: `--color-on-accent` `#1d4ed8` → `#ffffff`. The viewer's nav pill rendered dark-blue-on-blue in production.
- `light.css` / `minimal.css`: `--color-link` → `#2563eb` (Cue Blue Deep; at least 4.5:1 on canvas and surface-1).
- `minimal.css`: `--color-ink-subtle` `#aaaaaa` → `#737373` (2.3:1 → 4.8:1 on white; card metadata uses this token).

### Verification

- pytest: 426 pass. Jest: 58 pass (pre-delight suite).
- Browser (Chrome DevTools MCP): 1440 / 768 / 375 / 320 widths with no horizontal overflow; dark and linear-app themes; empty-search state; keyboard focus rings; no homepage console errors.

## Part 2 — Delight pass

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

### Bug fix (pre-existing)

`initializeMathJax()` called `MathJax.typesetPromise()` while `window.MathJax` was still only the config object (async script not yet loaded). The uncaught TypeError aborted `init()` before `showSlide(0)`, leaving a blank stage. Reproduced on the committed `site/` build, so it also affected production. Fixed with a `typeof MathJax.typesetPromise === 'function'` guard; MathJax typesets on its own startup, so the manual call is safely skipped.

### Verification

- Jest: 67 pass, including 9 new in `tests/test_booth_controls.js` (blackout toggle/exit/announce; card open/close/modality/aria).
- pytest: 426 pass.
- Browser (Chrome DevTools MCP against a fresh build): blackout, controls card in light and dark themes, crossfade class lifecycle, counter tick, hover transforms, console signature, search echo.

## Known issues, out of scope

- `slide-viewer.js` logs debug noise (fit-text scaling) on every resize.
- `.nav-button:disabled` hardcodes `#9ca3af` (token-contract violation, predates this pass).
- `presentation.html` loads the Tailwind CDN, against the vendored-assets rule.
- `CLAUDE.md` documents `npm test`, but `package.json` only defines `test:js`.
