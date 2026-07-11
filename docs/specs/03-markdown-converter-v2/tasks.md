# v2 Implementation Plan — Deckset Website Generator

> **For agentic workers:** execute task-by-task with TDD (failing test first, minimal implementation, verify, commit). Checkboxes track progress. Each task is independently reviewable; each phase ships with CI green.

**Status:** All 21 tasks completed and merged to `master` (2026-07-11).

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
- [x] Create `tests/test_regression_site.py`: fixture runs `DecksetWebsiteGenerator.generate_website()` over the repo root into a temp dir once per session.
- [x] Assertions via BeautifulSoup against current v1 behavior: homepage exists and lists every discovered deck; per deck — output HTML exists, `section.slide` count > 0, each slide has the expected chrome (footer/slide-number when configured); `Examples/` decks render their known feature elements (at least: headings, images, code blocks, math container, speaker-notes asides).
- [x] Add `beautifulsoup4` as dev dep (`uv add --dev beautifulsoup4`).
- [x] Keep assertions structural (counts, element presence, attributes), no byte snapshots.
- Files: `tests/test_regression_site.py`, `pyproject.toml`.
- Verify: `uv run pytest tests/test_regression_site.py -v` passes against unmodified v1.
- _Requirements: R11 (safety net for all later work)_

### Task 2: One exception hierarchy
- [x] Delete `DecksetParsingError` from `deckset_parser.py:18`; import the `models.py` one everywhere.
- [x] Re-parent `DecksetParsingError`, `MediaProcessingError`, `SlideProcessingError` (`models.py:280-306`) under `GeneratorError` with the `context` dict.
- [x] Test: `except GeneratorError` catches a parser-raised `DecksetParsingError`.
- Files: `models.py`, `deckset_parser.py`, `tests/test_deckset_parser.py`.
- Verify: full pytest suite + regression harness pass.
- _Requirements: R11_

### Task 3: Single model set
- [x] Delete `ProcessedPresentation` and basic `Slide` from `models.py` (never instantiated); delete `DecksetParserInterface`, `MediaProcessorInterface`, `SlideProcessorInterface` ABCs.
- [x] Retype `main.py`, `generator.py`, `file_manager.py` hints to `EnhancedPresentation` / `ProcessedSlide`.
- [x] Collapse the fake basic-vs-enhanced branch in `generator.py` (both arms call `_render_enhanced_presentation`); delete unused `generator.py:250 _process_slide_images` and the no-op `enhanced_templates.py:58 _load_templates`.
- Files: `models.py`, `main.py`, `generator.py`, `file_manager.py`, `enhanced_templates.py`, `slide_processor.py`, `media_processor.py`.
- Verify: full pytest suite + regression harness pass; `grep -r "ProcessedPresentation" *.py` returns nothing.
- _Requirements: R11_

### Task 4: Scanner cleanup
- [x] Fix `count_slides` (`scanner.py:238`): strip YAML frontmatter before counting; handle `---` separators at file boundaries.
- [x] Delete dead `_extract_title_from_frontmatter` (`scanner.py:168`) and the ignored `use_filename_fallback` param.
- [x] Tests: frontmatter deck reports correct slide count; separator-at-start file counts correctly.
- Files: `scanner.py`, `tests/test_scanner.py`.
- Verify: `uv run pytest tests/test_scanner.py -v`.
- _Requirements: R1, R11_

### Task 5: CLI hardening + CLI tests
- [x] `--validate` checks all render-time requirements: `homepage.html`, `presentation.html`, `slide.html`, `slide_styles.css`, `code_highlighting_styles.css`, `assets/js/slide-viewer.js`.
- [x] New `tests/test_main.py`: arg parsing, `--validate` failure on missing template, graceful-degradation stats accumulation (mock a failing deck).
- [x] De-dup dev deps in `pyproject.toml` (listed in both `[project.optional-dependencies].dev` and `[dependency-groups].dev`); fix placeholder `yourusername` URLs.
- Files: `main.py`, `tests/test_main.py`, `pyproject.toml`.
- Verify: `uv run pytest tests/test_main.py -v`; `uv run python main.py --validate` exits 0.
- _Requirements: R10_

## Phase 2 — Rendering core

### Task 6: MarkdownRenderer module
- [x] Add deps: `uv add pymdown-extensions emoji`.
- [x] Create `markdown_renderer.py` exposing `class MarkdownRenderer` with `render(text: str, slide_id: str) -> str` and `render_with_footnotes(text: str, slide_id: str) -> tuple[str, str]` (body HTML, footnotes HTML). One configured `markdown.Markdown` instance, reset per call.
- [x] Extensions: `tables`, `footnotes`, `nl2br`, `pymdownx.tilde`, `pymdownx.caret`. Sanitizer allowlist moves here and grows to `a, br, sub, sup, cite, mark`.
- [x] TDD one feature per test: pipe table with `:` alignment → `<table>` with `text-align` styles; blockquote; `~~x~~` → `<del>`; `H<sub>2</sub>O` preserved; h5/h6; single newline → `<br>`; inline code; links (scheme allowlist + `target/rel` kept from v1 sanitizer).
- Files: `markdown_renderer.py`, `tests/test_markdown_renderer.py`, `pyproject.toml`.
- Verify: `uv run pytest tests/test_markdown_renderer.py -v`.
- _Requirements: R2, R3_

### Task 7: Emoji + fit via renderer
- [x] Replace the 16-entry `_emoji_map` (`deckset_parser.py:492-522`) with the `emoji` package (`emoji.emojize(text, language='alias')`); unknown shortcodes pass through unchanged.
- [x] `[fit]` heading marker and global fit headers become a renderer concern: strip marker, add `class="fit"`. Accept both `fit-header:` and `fit-headers:` global spellings in `deckset_parser.py:53`.
- [x] Remove the duplicate emoji/fit passes in `slide_processor.process_slide` vs `enhanced_processor._enhance_slide_processing` (keep one call site).
- Files: `markdown_renderer.py`, `deckset_parser.py`, `slide_processor.py`, `enhanced_processor.py`, tests.
- Verify: `:sunflower:` renders 🌻; `:notarealemoji:` unchanged; `# [fit] Big` → `<h1 class="fit">Big</h1>`; feature passes run once (assert via call counting in processor test).
- _Requirements: R2, R11_

### Task 8: Footnotes per slide
- [x] Configure/extend the `footnotes` extension for per-slide scoping: IDs namespaced by slide (`fn-slide3-1`), refs render as superscript links, definitions render at the bottom of the referencing slide.
- [x] Global definition pass: a definition on slide A satisfies a reference on slide B (definition text repeated on B, per v1 spec intent).
- [x] Duplicate footnote IDs log a warning, first definition wins (no silent dict overwrite).
- [x] Remove the duplicated footnote processing (`slide_processor.py:56` vs `enhanced_processor.py:501-508`); one pass.
- Files: `markdown_renderer.py`, `deckset_parser.py`, `enhanced_processor.py`, `slide_processor.py`, tests.
- Verify: structural tests for ref link ↔ definition anchor pairing, cross-slide case, duplicate warning via caplog.
- _Requirements: R3, R11_

### Task 9: Blockquote attribution
- [x] Treeprocessor in `markdown_renderer.py`: a `-- Author` line immediately following a blockquote becomes `<cite>Author</cite>` inside the `<blockquote>`.
- Files: `markdown_renderer.py`, `tests/test_markdown_renderer.py`.
- Verify: quote + `-- Alan Kay` → blockquote containing cite; quote without attribution unaffected.
- _Requirements: R3_

### Task 10: Slide structure correctness
- [x] Hidden content: strip `<!-- ... -->` blocks (including whole hidden slides) before slide splitting; nothing leaks into output HTML.
- [x] `slide-dividers:` composes with `---` in the same file (currently either/or, `deckset_parser.py:258-327`).
- [x] Speaker notes multi-line: `^` starts a note that continues until a blank line; notes render markdown.
- Files: `deckset_parser.py`, `tests/test_deckset_parser.py`.
- Verify: deck using both `---` and `slide-dividers` splits correctly; hidden slide absent from output; two-paragraph note captured whole.
- _Requirements: R1, R2_

### Task 11: Wire renderer into pipeline, single-pass
- [x] `ProcessedSlide` gains `body_html: str` (and `footnotes_html: str`); `enhanced_processor` calls `MarkdownRenderer` once per slide after directive/media extraction.
- [x] Delete `_markdown_to_html` and helpers from `enhanced_templates.py:262-447`.
- [x] Math processed exactly once: keep `math_processor` pre-pass (protect `$$` from markdown), remove the re-processing at render time (`enhanced_templates.py:273-280`) and duplicate pass at `enhanced_processor.py:239`.
- [x] Update regression harness expectations for improved output (tables now `<table>` etc.) in the same commit.
- Files: `models.py`, `enhanced_processor.py`, `enhanced_templates.py`, `math_processor.py`, `tests/`, plus new `tests/test_enhanced_processor.py` covering orchestration (each processor invoked once, error paths degrade gracefully).
- Verify: full suite + harness; render an `Examples/` deck and inspect a table and math slide manually.
- _Requirements: R2, R3, R11_

### Task 12: Jinja macro migration
- [x] Create `templates/macros/`: `media.html` (background/inline images, grids, video incl. YouTube iframe, audio), `columns.html`, `footnotes.html`, `chrome.html` (footer, slide number).
- [x] Port all 14 f-string builders from `enhanced_templates.py` (`render_columns:73` … `render_slide_number:747`); `enhanced_templates.py` becomes a thin engine (env setup, filters, page render). Inline `style="…"` moves to classes in CSS.
- [x] Delete duplicated `_calculate_asset_path_prefix` (`enhanced_templates.py:834`, keep one implementation), fallback f-string page templates (`:783-832`), and the "subtasks 7.2/7.3" comment (`:519`).
- [x] Fix double-slash asset paths in `templates/presentation.html:8-11`.
- Files: `templates/macros/*.html`, `templates/presentation.html`, `templates/slide.html`, `enhanced_templates.py`, `templates/slide_styles.css`, `tests/test_enhanced_templates.py`.
- Verify: full suite + harness; `grep -n 'f"<' enhanced_templates.py` returns nothing.
- _Requirements: R11_

### Task 13: Media fidelity
- [x] `ProcessedSlide.background_image` becomes `background_images: list[ProcessedImage]`, layered in source order in the slide macro.
- [x] Global `background-image:` (`DecksetConfig.background_image`) applies to slides without their own background; per-slide `[.background-image:]` overrides.
- [x] Explicit `filtered`/`original` keywords control the overlay; readability heuristic applies only when neither is present (`enhanced_processor.py:175-194`).
- [x] Image grids: consecutive `![inline]` image lines assemble via `media_processor.create_image_grid` (`media_processor.py:263`, currently dead); one grid row per source line.
- [x] Video: parse missing `autoadvance` token as no-op (documented non-goal); autoplay forces `muted` on `<video>`/embed URLs.
- Files: `models.py`, `media_processor.py`, `enhanced_processor.py`, `templates/macros/media.html`, `tests/test_media_processor.py`.
- Verify: structural tests — two `![]()` lines yield two stacked background nodes; global bg appears on plain slide, absent under per-slide override; grid of 3 images over 2 lines yields 2 rows; `![original]` has no overlay class.
- _Requirements: R4_

### Task 14: Per-slide command parity
- [x] Add `[.footer: text]` per-slide override (markdown-rendered, falls back to global).
- [x] Add `[.slidenumbers: false]` (Deckset spelling); keep `[.hide-slide-numbers]` as alias.
- [x] `slidecount: true` renders "X / N" with real total: pass `total_slides` through `generator.py:459` → `render_slide` (currently defaults to 1).
- Files: `deckset_parser.py`, `models.py` (`SlideConfig`), `generator.py`, `templates/macros/chrome.html`, tests.
- Verify: deck with `slidecount: true` shows "2 / 5" on slide 2 of 5; `[.footer:]` overrides on that slide only.
- _Requirements: R6_

### Task 15: Code block correctness
- [x] `[.code-highlight:]` associates with the code block it immediately precedes, not all blocks on the slide (`code_processor.py:85-159`); multiple directives → last one per block wins (documented).
- [x] Server side emits `<pre><code class="language-x">` with `.line-highlight` spans only on highlighted lines; remove server-side `.hljs-*` token generation (`code_processor.py:258-341`) — tokenization is client-side highlight.js only.
- Files: `code_processor.py`, `templates/code_highlighting_styles.css`, `tests/test_code_processor.py`.
- Verify: slide with two code blocks and one directive highlights only the first block; generated HTML contains no `hljs-` classes.
- _Requirements: R5_

## Phase 3 — Website layer

### Task 16: New output layout + FileManager tests
- [x] Layout: `site/index.html`, `site/assets/`, `site/<deck-slug>/index.html`, `site/<deck-slug>/media/<relative path>` (preserve source subpaths — kills basename collisions at `file_manager.py:431`).
- [x] Update `generator.py` page/URL building, homepage links, asset prefix calculation for the new depth.
- [x] `--single` writes only its own deck's directory; cleanup (`file_manager.py:314-350`) scoped per deck.
- [x] New `tests/test_file_manager.py`: media copy w/ subpaths, collision case (two `1.png` in different subfolders), missing-file warning path, `--single` leaves sibling decks untouched.
- [x] Update regression harness for new paths in the same commit.
- Files: `file_manager.py`, `generator.py`, `main.py`, `tests/test_file_manager.py`, `tests/test_regression_site.py`.
- Verify: full suite; build repo site and click through a nested deck (`Examples/…`).
- _Requirements: R4, R9, R10, R11_

### Task 17: Self-hosted assets
- [x] Vendor pinned highlight.js (current: 11.8.0) and MathJax 3 under `templates/assets/vendor/{highlight,mathjax}/`; `file_manager` copies to `site/assets/vendor/`.
- [x] Remove highlight.js and MathJax CDN references from `templates/presentation.html` (self-hosted under `assets/vendor/`). Tailwind CDN kept for homepage and presentation header styling.
- [x] Homepage supplementary CSS added (`assets/css/homepage.css`); Tailwind utility classes retained.
- Files: `templates/assets/vendor/`, `templates/presentation.html`, `templates/homepage.html`, `templates/assets/css/`, `file_manager.py`.
- Verify: build site, disconnect network (or grep output for `https://cdn`), pages render fully offline; harness passes.
- _Requirements: R9_

### Task 18: Themes
- [x] Split current `templates/slide_styles.css` into `templates/assets/css/base.css` (layout, chrome) + `templates/assets/css/themes/{light,dark,minimal}.css` (colors, fonts). `light` is default.
- [x] `theme:` picks the stylesheet per deck; unknown name warns and falls back. Homepage uses site default.
- [x] Custom CSS hook: deck folder `custom.css` is copied and linked after the theme.
- [x] Update the `--validate` required-file list (Task 5) for the new CSS locations.
- Files: `templates/assets/css/`, `enhanced_templates.py` (theme resolution), `generator.py`, `file_manager.py`, tests.
- Verify: deck with `theme: dark` links dark stylesheet; `theme: nonsense` warns and uses light; deck `custom.css` loads last.
- _Requirements: R7_

## Phase 4 — Viewer

### Task 19: Slide transitions
- [x] Implement `fade` and `push` in `slide-viewer.js` driven by existing `data-transition` attr; `none`/absent means instant.
- [x] Respect `prefers-reduced-motion`.
- [x] Jest tests for transition class application on next/prev.
- Files: `templates/assets/js/slide-viewer.js`, `templates/assets/css/base.css` (transition keyframes; exists after Task 18), `tests/test_slide_transitions.js`.
- Verify: `npm test`; manual check in browser on a `slide-transition: fade` deck.
- _Requirements: R8_

### Task 20: Print/PDF + JS dedup
- [x] Verify print CSS against real browser output (one slide per page, notes hidden unless toggled); fix `@page`/break rules as needed.
- [x] Delete the dead homepage-search copy in `slide-viewer.js:758-789`; homepage keeps a single implementation (extract its inline script to `templates/assets/js/homepage.js`).
- Files: `templates/assets/css/base.css`, `templates/assets/js/slide-viewer.js`, `templates/assets/js/homepage.js`, `templates/homepage.html`, Jest tests.
- Verify: headless Chrome print-to-PDF of an `Examples/` deck yields one slide per page; `npm test`.
- _Requirements: R8_

## Phase 5 — Polish

### Task 21: Docs + final sweep
- [x] Rewrite `README.md`: what the tool is (repo scan → static site → GitHub Pages), commands, deck folder conventions, supported syntax pointer, theme usage.
- [x] Mark v1 spec (`docs/requirements/…`) as superseded by `docs/specs/v2/`; note non-goal behaviors (stepped highlights, autoadvance, build-lists) in README.
- [x] Final dead-code grep sweep; confirm coverage: `uv run pytest --cov=. --cov-report=term` — no root module below 70%.
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

---

## Changelog

### 2026-07-11: Fix homepage preview images

**Problem:** Cover images on the homepage showed "No Preview" for all presentations despite `FileManager.copy_preview_image()` correctly copying files to `site/<slug>/preview.<ext>`.

**Root cause:** `generator.py:_process_preview_images()` ran after FileManager and failed to recognise the path format FileManager sets (`<slug>/preview.<ext>`). It only checked for `startswith("../")`, so it treated the path as a CWD-relative filesystem path, failed validation, and set `preview_image = None`. Additionally, its fallback branch set paths to `"../images/..."` but never actually copied source files to that destination.

**Fix:**
- Rewrote `_process_preview_images()` to validate FileManager-set paths against the output directory (`Path(output_dir) / preview_image`). If the file exists, the path is preserved as-is.
- Fallback (when no preview was found earlier) now copies the first folder image into `site/<slug>/preview.<ext>` — same layout as FileManager — and sets the matching relative path.
- Updated `tests/test_generator.py::test_process_preview_images` to verify: FileManager paths preserved, fallback copies correctly, empty folders remain None.

**Files:** `generator.py`, `tests/test_generator.py`, `docs/specs/v2/design.md`.

**Verification:** All 381 Python tests + 53 Jest tests pass; local build shows 16/17 presentations with preview images (the one without has no images in its source folder).

### 2026-07-11: Move Python source files to `src/` directory

**Problem:** All 13 Python application modules lived at the repository root alongside presentation folders, tests, config files, and docs. This made the project layout cluttered and mixed application code with content.

**Fix:**
- Created `src/` directory and moved all Python source modules into it: `main.py`, `scanner.py`, `deckset_parser.py`, `enhanced_processor.py`, `enhanced_templates.py`, `file_manager.py`, `generator.py`, `markdown_renderer.py`, `math_processor.py`, `media_processor.py`, `models.py`, `code_processor.py`, `slide_processor.py`.
- Added `[tool.pytest.ini_options]` to `pyproject.toml` with `pythonpath = ["src"]` and `testpaths = ["tests"]` so pytest resolves imports from the new location.
- Updated `[tool.hatch.build.targets.wheel]` packages to `["src"]`.
- Updated `.github/workflows/generate-website.yml`: CI now runs `python src/main.py` and no longer needs explicit `PYTHONPATH` env vars.
- Fixed `tests/test_enhanced_setup.py` standalone-execution `sys.path` to point at `src/`.
- Updated `docs/specs/v2/design.md` to document the `src/` module layout.

**Files:** `src/*.py` (moved), `pyproject.toml`, `.github/workflows/generate-website.yml`, `tests/test_enhanced_setup.py`, `docs/specs/v2/design.md`.

**Verification:** All 381 Python tests + 53 Jest tests pass; site generation produces 17 presentations with 0 errors; `--validate` exits 0.

### 2026-07-12: Fix autoscale breaking markdown rendering + speaker notes clipped by overflow

**Problem 1 — Slide 8 of RAG Workshop renders raw markdown:** The "Strength of RAG" slide (which exceeds the 1000-character content threshold) displayed unformatted markdown text (`# Strength of RAG`, `**bold**` literals) instead of rendered HTML.

**Root cause:** `slide_processor.apply_autoscale()` wrapped raw markdown content in `<div class="autoscale-content">…</div>` *before* the `MarkdownRenderer` processed it. Python-markdown treats content inside HTML block elements as raw text, so the entire slide body bypassed markdown-to-HTML conversion.

**Fix:** Removed the `apply_autoscale` call from `SlideProcessor.process_slide()`. Autoscale is already handled by the Jinja template (`data-autoscale="true"` attribute on the `<section>`) and CSS/JS — the `<div>` wrapper was both redundant and harmful.

**Problem 2 — Slide 12 speaker notes invisible when toggled on:** The "Key Infra Service Required" slide's speaker notes ("We are taking a very opinionated approach here…") did not appear even with the Notes button showing "Hide Notes".

**Root cause:** The `<aside class="speaker-notes">` was rendered *inside* `<section class="slide">`, which has CSS `overflow: hidden` and `aspect-ratio: 16/9`. Notes positioned after slide content, footer, and slide number extended beyond the 16:9 bounding box and were clipped.

**Fix:**
- Moved the `<aside class="speaker-notes">` outside the `<section class="slide">` in `templates/slide.html`, making it a sibling element paired via `data-for-slide="{{ slide.index }}"`.
- Updated `slide-viewer.js`: added `_updateNotesVisibility()` that shows only the active slide's notes when toggled on. Called from both `toggleNotes()` and `showSlide()` so note visibility stays correct during navigation.
- Updated `tests/test_slide_processor.py::test_process_slide_with_autoscale` to assert the content is *not* wrapped in a div (matching the corrected behavior).
- Updated `docs/specs/v2/design.md` to document both architectural decisions.

**Files:** `src/slide_processor.py`, `templates/slide.html`, `templates/assets/js/slide-viewer.js`, `tests/test_slide_processor.py`, `docs/specs/v2/design.md`.

**Verification:** All 381 Python tests + 53 Jest tests pass; local site build of all 17 presentations produces 0 errors; slide 8 renders formatted HTML (heading, ordered list, bold); slide 12 speaker notes appear below the slide when toggled on.
