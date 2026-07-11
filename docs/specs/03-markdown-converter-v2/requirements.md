# v2 Requirements — Deckset Website Generator

Date: 2026-07-11
Status: draft, pending review
Supersedes: `docs/requirements/Deckset-markdown-to-HTML-generator-specificaiton.md` (v1 spec) as the active requirement source. The v1 spec described a single-file markdown-to-HTML converter; the implementation has since grown into a multi-presentation static site generator. v2 formalizes that scope.

## Scope statement

The tool scans a repository for presentation folders, converts each Deckset-compatible markdown file into a slide-based HTML page, and produces a static website (homepage + one page per presentation) deployable to GitHub Pages.

Fidelity bar: **common-use Deckset parity**. Every feature a typical deck uses renders correctly. Exotic presenter-mode features are explicit non-goals with documented fallback behavior.

## R1 — Slide structure

- Split slides on `---` (blank line above and below required, per Deckset).
- `slide-dividers: #, ##, ...` splits on the listed heading levels. Works alone and combined with `---` separators in the same file.
- YAML frontmatter is stripped before slide splitting and never miscounted as a separator.
- Content inside `<!-- ... -->` is removed from output entirely (hidden slides/content). It must not leak into the generated HTML as comments.

## R2 — Text rendering

Slide body HTML must come from a real markdown engine (python-markdown + extensions), not a hand-rolled parser.

- Headings h1 through h6.
- `[fit]` on a heading and global `fit-header:` (accept both `fit-header` and `fit-headers` spellings) scale the heading to slide width.
- Bold, italic, combined bold+italic, strikethrough (`~~`), inline code, links.
- `<sub>`/`<sup>` and `<br>` HTML tags pass through; the sanitizer must not strip them.
- A manual line break inside a paragraph produces `<br>` in output (Deckset respects source line breaks).
- Emoji shortcodes (`:smile:`) resolve against a full emoji database, not a hardcoded subset. Unknown codes pass through unchanged.

## R3 — Block elements

- Nested ordered and unordered lists.
- Blockquotes; a following `-- Author` line renders as attribution (`<cite>` or equivalent).
- Pipe tables with `:` alignment markers mapped to cell text alignment.
- Footnotes: `[^1]` and named labels. References render as superscript links; definitions render at the bottom of the slide where referenced. Duplicate IDs are detected and warned, never silently overwritten. A definition on one slide satisfies a reference on another.
- Display math `$$...$$` and inline math, rendered by MathJax. Math is processed exactly once per slide.

## R4 — Media

- Background images: bare `![](img)` covers the slide; `fit` letterboxes; `left`/`right` covers half with content on the other half; `N%` zooms; `filtered`/`original` control the darkening overlay explicitly (heuristic only applies when neither keyword is given).
- Multiple background images on one slide are layered in source order.
- Global `background-image:` applies to every slide without its own background; per-slide `[.background-image:]` overrides it.
- Inline images: `![inline]`, `![inline fill]`, `![inline N%]`, `corner-radius(n)`.
- Consecutive inline images form a grid (row per source line).
- Video: local files as `<video>` with controls; YouTube URLs as embed iframes; modifiers `left/right/fit/fill/N%/hide/autoplay/loop/mute` honored. Autoplay implies muted (browser policy).
- Audio: `<audio>` with controls; same modifiers where meaningful.
- Media files are copied per deck; identical filenames in different decks or subfolders never collide.

## R5 — Code

- Fenced blocks with language class; `code-language:` sets the default for unlabeled blocks.
- One `[.code-highlight: N, X-Y, all, none]` directive per code block highlights those lines, applied to the block it precedes (not every block on the slide).
- Exactly one syntax-highlighting mechanism (no server-side + client-side double processing).

## R6 — Global and per-slide commands

- Global: `slidenumbers`, `slidecount` (renders "X / N" with the correct total), `footer`, `autoscale`, `theme`, `slide-transition`, `build-lists` (parsed, see non-goals).
- Per-slide: `[.background-image:]`, `[.footer:]`, `[.hide-footer]`, `[.slidenumbers: false]` (Deckset spelling; keep `[.hide-slide-numbers]` as an alias), `[.autoscale:]`, `[.slide-transition:]`, `[.column]`.

## R7 — Themes

- `theme:` selects a built-in CSS theme: `light` (default), `dark`, `minimal`.
- Unknown theme names fall back to default with a warning.
- A custom CSS hook lets a deck or the site owner add stylesheet overrides without editing generator code.

## R8 — Viewer

- Slide navigation: keyboard, touch, URL hash, slide counter (as in v1 viewer).
- `slide-transition:` values `fade` and `push` animate slide changes in the JS viewer; `none`/absent means no animation.
- Speaker notes hidden by default, toggleable.
- Print/PDF: one slide per page, notes optional, verified against real browser print output.

## R9 — Website output

- Layout: `site/index.html`, `site/assets/` (own CSS/JS plus vendored highlight.js and MathJax), `site/<deck-slug>/index.html`, `site/<deck-slug>/media/`.
- No CDN dependencies; the site works offline.
- Homepage: card grid with preview image, title, slide count, last-modified date, client-side search.
- URL stability with v1 output is not required.

## R10 — CLI and operations

- `--root`, `--output`, `--single`, `--validate`, `--verbose` as in v1.
- `--single` regenerates one deck without deleting other decks' output.
- `--validate` checks every template and asset the render step needs.
- Graceful degradation: one failing deck is logged and skipped; the build continues.

## R11 — Code quality

- One presentation/slide model set; delete unused models and interfaces.
- One exception hierarchy rooted at `GeneratorError`; no duplicate exception classes.
- Each processing concern (math, footnotes, emoji, fit headers) runs exactly once per slide.
- All slide/page HTML defined in Jinja templates or macros; no HTML built in Python f-strings.
- Dedicated test suites for the processor orchestration, file manager, and CLI in addition to existing per-module tests.
- README describes the actual system.

## Non-goals

- Stepped `[.code-highlight]` reveals: the last directive before a block wins; documented.
- Video `autoadvance`.
- `build-lists` progressive reveal: all list items always visible.
- Cloning Deckset's built-in visual themes.
- Vimeo and other non-YouTube embed providers.
- Presenter console / dual-screen mode.
- Redirects from v1 URLs (can be added later if broken links become a problem).
