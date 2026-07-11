# v2 Implementation Plan — Deckset Website Generator

> **For agentic workers:** execute task-by-task with TDD (failing test first, minimal implementation, verify, commit). Checkboxes track progress. Each task is independently reviewable; each phase ships with CI green.

**Goal:** Deliver v2 per `docs/specs/v2/requirements.md` and `design.md`: common-use Deckset parity on a python-markdown rendering core, themes/transitions/print, self-hosted assets, restructured output, architecture cleanup.

**Architecture:** Strangler rewrite inside the existing flat-module pipeline (Scanner → Parser → Processor → Renderer → Jinja → Generator). Regression harness lands first and gates every later change.

**Tech stack:** Python 3.12 + uv, `markdown` + `pymdown-extensions` + `emoji`, Jinja2, `beautifulsoup4` (dev), Jest for viewer JS.

## Global constraints

- Conventions in `CLAUDE.md` apply: pathlib, `encoding='utf-8'`, type hints, Black 88 cols, per-module logger.
- Graceful degradation everywhere: a failing deck logs and skips, never kills the build.
- Every task: run `uv run pytest` (and `npm test` when JS touched) before commit. Conventional commit messages.
- Regression harness (Task 1) must pass at the end of every task. When a task intentionally changes output structure, update harness assertions in the same commit and say so in the commit body.
- Requirement references (R1-R11) point at `docs/specs/v2/requirements.md`.

---

## Phase 1 — Foundation

### Task 1: Regression harness
- [ ] Create `tests/test_regression_site.py`: fixture runs `DecksetWebsiteGenerator.generate_website()` over the repo root into a temp dir once per session.
- [ ] Assertions via BeautifulSoup against current v1 behavior: homepage exists and lists every discovered deck; per deck — output HTML exists, `section.slide` count > 0, each slide has the expected chrome (footer/slide-number when configured); `Examples/` decks render their known feature elements (at least: headings, images, code blocks, math container, speaker-notes asides).
- [ ] Add `beautifulsoup4` as dev dep (`uv add --dev beautifulsoup4`).
- [ ] Keep assertions structural (counts, element presence, attributes), no byte snapshots.
- Files: `tests/test_regression_site.py`, `pyproject.toml`.
- Verify: `uv run pytest tests/test_regression_site.py -v` passes against unmodified v1.
- _Requirements: R11 (safety net for all later work)_

### Task 2: One exception hierarchy
- [ ] Delete `DecksetParsingError` from `deckset_parser.py:18`; import the `models.py` one everywhere.
- [ ] Re-parent `DecksetParsingError`, `MediaProcessingError`, `SlideProcessingError` (`models.py:280-306`) under `GeneratorError` with the `context` dict.
- [ ] Test: `except GeneratorError` catches a parser-raised `DecksetParsingError`.
- Files: `models.py`, `deckset_parser.py`, `tests/test_deckset_parser.py`.
- Verify: full pytest suite + regression harness pass.
- _Requirements: R11_

### Task 3: Single model set
- [ ] Delete `ProcessedPresentation` and basic `Slide` from `models.py` (never instantiated); delete `DecksetParserInterface`, `MediaProcessorInterface`, `SlideProcessorInterface` ABCs.
- [ ] Retype `main.py`, `generator.py`, `file_manager.py` hints to `EnhancedPresentation` / `ProcessedSlide`.
- [ ] Collapse the fake basic-vs-enhanced branch in `generator.py` (both arms call `_render_enhanced_presentation`); delete unused `generator.py:250 _process_slide_images` and the no-op `enhanced_templates.py:58 _load_templates`.
- Files: `models.py`, `main.py`, `generator.py`, `file_manager.py`, `enhanced_templates.py`, `slide_processor.py`, `media_processor.py`.
- Verify: full pytest suite + regression harness pass; `grep -r "ProcessedPresentation" *.py` returns nothing.
- _Requirements: R11_

### Task 4: Scanner cleanup
- [ ] Fix `count_slides` (`scanner.py:238`): strip YAML frontmatter before counting; handle `---` separators at file boundaries.
- [ ] Delete dead `_extract_title_from_frontmatter` (`scanner.py:168`) and the ignored `use_filename_fallback` param.
- [ ] Tests: frontmatter deck reports correct slide count; separator-at-start file counts correctly.
- Files: `scanner.py`, `tests/test_scanner.py`.
- Verify: `uv run pytest tests/test_scanner.py -v`.
- _Requirements: R1, R11_

### Task 5: CLI hardening + CLI tests
- [ ] `--validate` checks all render-time requirements: `homepage.html`, `presentation.html`, `slide.html`, `slide_styles.css`, `code_highlighting_styles.css`, `assets/js/slide-viewer.js`.
- [ ] New `tests/test_main.py`: arg parsing, `--validate` failure on missing template, graceful-degradation stats accumulation (mock a failing deck).
- [ ] De-dup dev deps in `pyproject.toml` (listed in both `[project.optional-dependencies].dev` and `[dependency-groups].dev`); fix placeholder `yourusername` URLs.
- Files: `main.py`, `tests/test_main.py`, `pyproject.toml`.
- Verify: `uv run pytest tests/test_main.py -v`; `uv run python main.py --validate` exits 0.
- _Requirements: R10_

## Phase 2 — Rendering core

### Task 6: MarkdownRenderer module
- [ ] Add deps: `uv add pymdown-extensions emoji`.
- [ ] Create `markdown_renderer.py` exposing `class MarkdownRenderer` with `render(text: str, slide_id: str) -> str` and `render_with_footnotes(text: str, slide_id: str) -> tuple[str, str]` (body HTML, footnotes HTML). One configured `markdown.Markdown` instance, reset per call.
- [ ] Extensions: `tables`, `footnotes`, `nl2br`, `pymdownx.tilde`, `pymdownx.caret`. Sanitizer allowlist moves here and grows to `a, br, sub, sup, cite, mark`.
- [ ] TDD one feature per test: pipe table with `:` alignment → `<table>` with `text-align` styles; blockquote; `~~x~~` → `<del>`; `H<sub>2</sub>O` preserved; h5/h6; single newline → `<br>`; inline code; links (scheme allowlist + `target/rel` kept from v1 sanitizer).
- Files: `markdown_renderer.py`, `tests/test_markdown_renderer.py`, `pyproject.toml`.
- Verify: `uv run pytest tests/test_markdown_renderer.py -v`.
- _Requirements: R2, R3_

### Task 7: Emoji + fit via renderer
- [ ] Replace the 16-entry `_emoji_map` (`deckset_parser.py:492-522`) with the `emoji` package (`emoji.emojize(text, language='alias')`); unknown shortcodes pass through unchanged.
- [ ] `[fit]` heading marker and global fit headers become a renderer concern: strip marker, add `class="fit"`. Accept both `fit-header:` and `fit-headers:` global spellings in `deckset_parser.py:53`.
- [ ] Remove the duplicate emoji/fit passes in `slide_processor.process_slide` vs `enhanced_processor._enhance_slide_processing` (keep one call site).
- Files: `markdown_renderer.py`, `deckset_parser.py`, `slide_processor.py`, `enhanced_processor.py`, tests.
- Verify: `:sunflower:` renders 🌻; `:notarealemoji:` unchanged; `# [fit] Big` → `<h1 class="fit">Big</h1>`; feature passes run once (assert via call counting in processor test).
- _Requirements: R2, R11_

### Task 8: Footnotes per slide
- [ ] Configure/extend the `footnotes` extension for per-slide scoping: IDs namespaced by slide (`fn-slide3-1`), refs render as superscript links, definitions render at the bottom of the referencing slide.
- [ ] Global definition pass: a definition on slide A satisfies a reference on slide B (definition text repeated on B, per v1 spec intent).
- [ ] Duplicate footnote IDs log a warning, first definition wins (no silent dict overwrite).
- [ ] Remove the duplicated footnote processing (`slide_processor.py:56` vs `enhanced_processor.py:501-508`); one pass.
- Files: `markdown_renderer.py`, `deckset_parser.py`, `enhanced_processor.py`, `slide_processor.py`, tests.
- Verify: structural tests for ref link ↔ definition anchor pairing, cross-slide case, duplicate warning via caplog.
- _Requirements: R3, R11_

### Task 9: Blockquote attribution
- [ ] Treeprocessor in `markdown_renderer.py`: a `-- Author` line immediately following a blockquote becomes `<cite>Author</cite>` inside the `<blockquote>`.
- Files: `markdown_renderer.py`, `tests/test_markdown_renderer.py`.
- Verify: quote + `-- Alan Kay` → blockquote containing cite; quote without attribution unaffected.
- _Requirements: R3_

### Task 10: Slide structure correctness
- [ ] Hidden content: strip `<!-- ... -->` blocks (including whole hidden slides) before slide splitting; nothing leaks into output HTML.
- [ ] `slide-dividers:` composes with `---` in the same file (currently either/or, `deckset_parser.py:258-327`).
- [ ] Speaker notes multi-line: `^` starts a note that continues until a blank line; notes render markdown.
- Files: `deckset_parser.py`, `tests/test_deckset_parser.py`.
- Verify: deck using both `---` and `slide-dividers` splits correctly; hidden slide absent from output; two-paragraph note captured whole.
- _Requirements: R1, R2_

### Task 11: Wire renderer into pipeline, single-pass
- [ ] `ProcessedSlide` gains `body_html: str` (and `footnotes_html: str`); `enhanced_processor` calls `MarkdownRenderer` once per slide after directive/media extraction.
- [ ] Delete `_markdown_to_html` and helpers from `enhanced_templates.py:262-447`.
- [ ] Math processed exactly once: keep `math_processor` pre-pass (protect `$$` from markdown), remove the re-processing at render time (`enhanced_templates.py:273-280`) and duplicate pass at `enhanced_processor.py:239`.
- [ ] Update regression harness expectations for improved output (tables now `<table>` etc.) in the same commit.
- Files: `models.py`, `enhanced_processor.py`, `enhanced_templates.py`, `math_processor.py`, `tests/`, plus new `tests/test_enhanced_processor.py` covering orchestration (each processor invoked once, error paths degrade gracefully).
- Verify: full suite + harness; render an `Examples/` deck and inspect a table and math slide manually.
- _Requirements: R2, R3, R11_

### Task 12: Jinja macro migration
- [ ] Create `templates/macros/`: `media.html` (background/inline images, grids, video incl. YouTube iframe, audio), `columns.html`, `footnotes.html`, `chrome.html` (footer, slide number).
- [ ] Port all 14 f-string builders from `enhanced_templates.py` (`render_columns:73` … `render_slide_number:747`); `enhanced_templates.py` becomes a thin engine (env setup, filters, page render). Inline `style="…"` moves to classes in CSS.
- [ ] Delete duplicated `_calculate_asset_path_prefix` (`enhanced_templates.py:834`, keep one implementation), fallback f-string page templates (`:783-832`), and the "subtasks 7.2/7.3" comment (`:519`).
- [ ] Fix double-slash asset paths in `templates/presentation.html:8-11`.
- Files: `templates/macros/*.html`, `templates/presentation.html`, `templates/slide.html`, `enhanced_templates.py`, `templates/slide_styles.css`, `tests/test_enhanced_templates.py`.
- Verify: full suite + harness; `grep -n 'f"<' enhanced_templates.py` returns nothing.
- _Requirements: R11_

### Task 13: Media fidelity
- [ ] `ProcessedSlide.background_image` becomes `background_images: list[ProcessedImage]`, layered in source order in the slide macro.
- [ ] Global `background-image:` (`DecksetConfig.background_image`) applies to slides without their own background; per-slide `[.background-image:]` overrides.
- [ ] Explicit `filtered`/`original` keywords control the overlay; readability heuristic applies only when neither is present (`enhanced_processor.py:175-194`).
- [ ] Image grids: consecutive `![inline]` image lines assemble via `media_processor.create_image_grid` (`media_processor.py:263`, currently dead); one grid row per source line.
- [ ] Video: parse missing `autoadvance` token as no-op (documented non-goal); autoplay forces `muted` on `<video>`/embed URLs.
- Files: `models.py`, `media_processor.py`, `enhanced_processor.py`, `templates/macros/media.html`, `tests/test_media_processor.py`.
- Verify: structural tests — two `![]()` lines yield two stacked background nodes; global bg appears on plain slide, absent under per-slide override; grid of 3 images over 2 lines yields 2 rows; `![original]` has no overlay class.
- _Requirements: R4_

### Task 14: Per-slide command parity
- [ ] Add `[.footer: text]` per-slide override (markdown-rendered, falls back to global).
- [ ] Add `[.slidenumbers: false]` (Deckset spelling); keep `[.hide-slide-numbers]` as alias.
- [ ] `slidecount: true` renders "X / N" with real total: pass `total_slides` through `generator.py:459` → `render_slide` (currently defaults to 1).
- Files: `deckset_parser.py`, `models.py` (`SlideConfig`), `generator.py`, `templates/macros/chrome.html`, tests.
- Verify: deck with `slidecount: true` shows "2 / 5" on slide 2 of 5; `[.footer:]` overrides on that slide only.
- _Requirements: R6_

### Task 15: Code block correctness
- [ ] `[.code-highlight:]` associates with the code block it immediately precedes, not all blocks on the slide (`code_processor.py:85-159`); multiple directives → last one per block wins (documented).
- [ ] Server side emits `<pre><code class="language-x">` with `.line-highlight` spans only on highlighted lines; remove server-side `.hljs-*` token generation (`code_processor.py:258-341`) — tokenization is client-side highlight.js only.
- Files: `code_processor.py`, `templates/code_highlighting_styles.css`, `tests/test_code_processor.py`.
- Verify: slide with two code blocks and one directive highlights only the first block; generated HTML contains no `hljs-` classes.
- _Requirements: R5_

## Phase 3 — Website layer

### Task 16: New output layout + FileManager tests
- [ ] Layout: `site/index.html`, `site/assets/`, `site/<deck-slug>/index.html`, `site/<deck-slug>/media/<relative path>` (preserve source subpaths — kills basename collisions at `file_manager.py:431`).
- [ ] Update `generator.py` page/URL building, homepage links, asset prefix calculation for the new depth.
- [ ] `--single` writes only its own deck's directory; cleanup (`file_manager.py:314-350`) scoped per deck.
- [ ] New `tests/test_file_manager.py`: media copy w/ subpaths, collision case (two `1.png` in different subfolders), missing-file warning path, `--single` leaves sibling decks untouched.
- [ ] Update regression harness for new paths in the same commit.
- Files: `file_manager.py`, `generator.py`, `main.py`, `tests/test_file_manager.py`, `tests/test_regression_site.py`.
- Verify: full suite; build repo site and click through a nested deck (`Examples/…`).
- _Requirements: R4, R9, R10, R11_

### Task 17: Self-hosted assets
- [ ] Vendor pinned highlight.js (current: 11.8.0) and MathJax 3 under `templates/assets/vendor/{highlight,mathjax}/`; `file_manager` copies to `site/assets/vendor/`.
- [ ] Remove all CDN references from `templates/presentation.html:15-18` and `homepage.html:17` (highlight.js, MathJax, Tailwind).
- [ ] Homepage restyled with own CSS (card grid, search) replacing Tailwind utility classes.
- Files: `templates/assets/vendor/`, `templates/presentation.html`, `templates/homepage.html`, `templates/assets/css/`, `file_manager.py`.
- Verify: build site, disconnect network (or grep output for `https://cdn`), pages render fully offline; harness passes.
- _Requirements: R9_

### Task 18: Themes
- [ ] Split current `templates/slide_styles.css` into `templates/assets/css/base.css` (layout, chrome) + `templates/assets/css/themes/{light,dark,minimal}.css` (colors, fonts). `light` is default.
- [ ] `theme:` picks the stylesheet per deck; unknown name warns and falls back. Homepage uses site default.
- [ ] Custom CSS hook: deck folder `custom.css` is copied and linked after the theme.
- [ ] Update the `--validate` required-file list (Task 5) for the new CSS locations.
- Files: `templates/assets/css/`, `enhanced_templates.py` (theme resolution), `generator.py`, `file_manager.py`, tests.
- Verify: deck with `theme: dark` links dark stylesheet; `theme: nonsense` warns and uses light; deck `custom.css` loads last.
- _Requirements: R7_

## Phase 4 — Viewer

### Task 19: Slide transitions
- [ ] Implement `fade` and `push` in `slide-viewer.js` driven by existing `data-transition` attr; `none`/absent means instant.
- [ ] Respect `prefers-reduced-motion`.
- [ ] Jest tests for transition class application on next/prev.
- Files: `templates/assets/js/slide-viewer.js`, `templates/assets/css/base.css` (transition keyframes; exists after Task 18), `tests/test_slide_transitions.js`.
- Verify: `npm test`; manual check in browser on a `slide-transition: fade` deck.
- _Requirements: R8_

### Task 20: Print/PDF + JS dedup
- [ ] Verify print CSS against real browser output (one slide per page, notes hidden unless toggled); fix `@page`/break rules as needed.
- [ ] Delete the dead homepage-search copy in `slide-viewer.js:758-789`; homepage keeps a single implementation (extract its inline script to `templates/assets/js/homepage.js`).
- Files: `templates/assets/css/base.css`, `templates/assets/js/slide-viewer.js`, `templates/assets/js/homepage.js`, `templates/homepage.html`, Jest tests.
- Verify: headless Chrome print-to-PDF of an `Examples/` deck yields one slide per page; `npm test`.
- _Requirements: R8_

## Phase 5 — Polish

### Task 21: Docs + final sweep
- [ ] Rewrite `README.md`: what the tool is (repo scan → static site → GitHub Pages), commands, deck folder conventions, supported syntax pointer, theme usage.
- [ ] Mark v1 spec (`docs/requirements/…`) as superseded by `docs/specs/v2/`; note non-goal behaviors (stepped highlights, autoadvance, build-lists) in README.
- [ ] Final dead-code grep sweep; confirm coverage: `uv run pytest --cov=. --cov-report=term` — no root module below 70%.
- Files: `README.md`, `docs/requirements/Deckset-markdown-to-HTML-generator-specificaiton.md` (supersession note only), misc.
- Verify: full pytest + Jest + `--validate` + fresh site build; CI green on PR.
- _Requirements: R10, R11, non-goals documented_

---

## Task → requirement coverage

| Req | Tasks |
|-----|-------|
| R1 slide structure | 4, 10 |
| R2 text rendering | 6, 7, 10, 11 |
| R3 blocks | 6, 8, 9, 11 |
| R4 media | 13, 16 |
| R5 code | 15 |
| R6 commands | 14 |
| R7 themes | 18 |
| R8 viewer | 19, 20 |
| R9 output/site | 16, 17 |
| R10 CLI/ops | 5, 16, 21 |
| R11 quality | 1, 2, 3, 4, 5, 7, 8, 11, 12, 16, 21 |
