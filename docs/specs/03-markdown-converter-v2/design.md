# v2 Design — Deckset Website Generator

Date: 2026-07-11
Status: implemented
Requirements: `docs/specs/03-markdown-converter-v2/requirements.md`

## Background: gap analysis (2026-07-11)

Audit of v1 against the original spec found three problem clusters:

1. **Fidelity gaps.** Slide bodies are rendered by a hand-rolled regex parser in `enhanced_templates.py` (lines 262-397), so tables, blockquotes, strikethrough, sub/sup, h5/h6, manual line breaks, and footnote links are missing or broken. The `markdown` library is a dependency but only used for speaker notes. Several parsed configs (`theme`, `build-lists`, global `background-image`) are never rendered. Image grids exist as dead code. Emoji support is 16 hardcoded shortcodes.
2. **Architecture debt.** Slide HTML lives in ~14 Python f-string methods; Jinja templates are thin shells. Dead models (`ProcessedPresentation`, basic `Slide`), duplicate `DecksetParsingError` classes (models.py and deckset_parser.py define different classes with the same name), three unused ABCs, math processed up to three times per slide, footnotes twice.
3. **Bugs.** Media filename collisions (all files flatten into one folder per deck keyed by basename), `--single` deletes other decks' output during cleanup, `total_slides` never passed so `slidecount` would render "/ 1", `--validate` misses required templates, highlight.js/MathJax CDNs in production pages.

Approach chosen: **strangler rewrite** inside the existing repo. Keep the pipeline shape, replace the rendering core, phase by phase, CI green throughout. Rejected alternatives: greenfield rewrite (two codebases, stalling risk), patch-in-place (every fix fights the regex parser), markdown-it-py core (new dependency for little gain since Deckset directives live outside the markdown body).

## Architecture

Pipeline shape is kept; modules now live under `src/`:

```
Scanner → DecksetParser → Processor → MarkdownRenderer → Jinja templates → Generator → site/
```

### Module responsibilities

All application modules live in `src/`. pytest discovers them via `pythonpath = ["src"]` in `pyproject.toml`; CI and CLI invoke `python src/main.py`.

- **`src/scanner.py`** — unchanged role. Fix slide counting (frontmatter miscount), remove dead frontmatter-title code.
- **`src/deckset_parser.py`** — directive parsing only. Strips frontmatter and `<!-- -->` blocks, parses global commands, splits slides (`---` and `slide-dividers:`, composable), parses per-slide commands, extracts speaker notes (multi-line: a `^` line starts a note that continues until a blank line) and media tokens. Output per slide: body markdown text + directive set + media references. No HTML generation.
- **`src/markdown_renderer.py`** — one configured python-markdown instance rendering slide body text to HTML. Extensions: `tables`, `footnotes` (scoped per slide, duplicate-ID warning), `pymdownx.tilde` (strikethrough/sub), `pymdownx.caret` (sup), `nl2br` behavior for manual line breaks, custom inline processors for emoji (via the `emoji` package) and `[fit]` heading markers, blockquote attribution treeprocessor (`-- Author` → `<cite>`). The sanitizer allowlist grows to cover `sub/sup/br/cite/mark`.
- **`src/enhanced_processor.py`** — orchestration only. Each concern (media, code, math, footnotes, emoji, fit) runs exactly once per slide. The inline-figure and readability-filter heuristics survive but run inside their owning processor, not as extra passes.
- **`src/media_processor.py`** — gains: multiple backgrounds per slide (model field becomes a list), global `background-image:` fallback, image-grid assembly (consecutive inline image lines → grid rows), explicit `filtered`/`original` handling (heuristic only when neither present).
- **`src/code_processor.py`** — associates each `[.code-highlight]` directive with the block it precedes. Server-side emits plain `<pre><code class="language-x">` with line spans for highlighted lines; tokenization is client-side highlight.js only (kills double processing).
- **`src/slide_processor.py`** — parses slide commands, extracts speaker notes, processes columns and background images, removes code blocks. **Does not** wrap content in HTML (e.g. `<div>` for autoscale); autoscale is handled via `data-autoscale="true"` on the `<section>` in the Jinja template and CSS/JS.
- **`src/enhanced_templates.py`** — shrinks to a thin Jinja engine: loads templates, exposes filters, renders pages. All 14 f-string HTML builders move to Jinja macros under `templates/macros/` (media.html, columns.html, footnotes.html, chrome.html for footer/slide-number). Changing markup means editing templates.
- **`src/generator.py` / `src/file_manager.py`** — new output layout (below), per-deck media dirs preserving relative subpaths (fixes collisions), `--single` writes only its own deck's files, vendored asset copying.
- **`src/models.py`** — single model set: `PresentationInfo`, `EnhancedPresentation`, `ProcessedSlide`, config classes. Delete `ProcessedPresentation`, basic `Slide`, all three interface ABCs. One exception hierarchy under `GeneratorError`; `DecksetParsingError`, `MediaProcessingError`, `SlideProcessingError` move under it; the duplicate class in `deckset_parser.py` is deleted.

### Data flow per presentation

1. Scanner finds the folder and markdown file.
2. Parser strips frontmatter/comments, reads global config, splits into slides, extracts per-slide directives, notes, and media tokens.
3. Processor runs media/code/math processors once per slide; body text goes through `markdown_renderer`.
4. Jinja renders slide macros into a page; generator writes `site/<deck-slug>/index.html` and copies media into `site/<deck-slug>/media/`.
5. Homepage renders from the collected `PresentationInfo` list.

### Preview image handling

Preview images shown on the homepage cards follow a two-stage pipeline:

1. **Scanner** discovers a candidate image per presentation: first image referenced in the markdown (via `extract_first_image_from_markdown`), falling back to `find_preview_image` which globs the source folder.
2. **FileManager.copy_preview_image()** copies the source file to `site/<slug>/preview.<ext>` and sets `info.preview_image` to the web-accessible path relative to the site root (e.g. `examples/10-deckset-basics/preview.jpg`).
3. **Generator._process_preview_images()** runs during homepage generation as a validation/fallback step: it checks that any path set by FileManager resolves to an existing file under the output directory. If the file is missing (source image didn't exist) it clears the path and attempts a folder-glob fallback, copying the first image found into `site/<slug>/preview.<ext>`.

The homepage template renders `<img src="{{ preview_image }}">` directly, so paths are always relative to `site/index.html`.

## Themes and viewer

- Three built-in themes as CSS files (`light`, `dark`, `minimal`) sharing a base stylesheet; `theme:` picks one per deck, homepage uses the site default. Unknown names warn and fall back. A deck folder may ship `custom.css`, linked after the theme.
- Homepage and presentation header styling use Tailwind CSS via CDN for utility classes.
- Viewer JS keeps navigation/notes/fit-text/readability features; adds transition handling driven by `data-transition` (`fade`, `push`); duplicated homepage-search code collapses to one implementation. Speaker notes (`<aside class="speaker-notes">`) render **outside** the `<section class="slide">` element (sibling, paired via `data-for-slide`), so they are not clipped by the slide's `overflow: hidden` / `aspect-ratio: 16/9`. The viewer's `_updateNotesVisibility()` shows only the active slide's notes when toggled on.
- highlight.js and MathJax are vendored under `site/assets/vendor/` at pinned versions.
- Print CSS verified with a real browser (one slide per page, notes optional).

## Project layout

```
src/                          # All Python application modules
  main.py  scanner.py  deckset_parser.py  enhanced_processor.py
  markdown_renderer.py  media_processor.py  code_processor.py
  math_processor.py  slide_processor.py  enhanced_templates.py
  generator.py  file_manager.py  models.py
templates/                    # Jinja2 templates and static assets
tests/                        # pytest + Jest test suites
```

## Output layout

```
site/
  index.html
  assets/
    css/  js/  vendor/highlight/  vendor/mathjax/
  <deck-slug>/
    index.html
    media/<original relative paths>
```

Deck slug derives from the folder name as today (nested folders keep their path segments). v1 URLs (`presentations/<name>.html`) are not preserved.

## Testing

- **Regression harness (built first):** render every deck in the repo (including `Examples/`), assert structure with BeautifulSoup (slide counts, headings, media elements, footers). No byte-snapshots; output is meant to change at feature milestones. The harness is the safety net for every later phase.
- **Fidelity tests:** one structural test per R2-R6 requirement (e.g. "pipe table renders `<table>` with right-aligned third column").
- **Unit tests:** existing per-module suites stay; new dedicated suites for `enhanced_processor`, `file_manager`, `main` CLI (`--single` non-destruction, `--validate` completeness).
- **Jest:** existing viewer suites plus transition tests.
- **CI:** unchanged workflow; deploy only from master as today.

## Error handling

Unchanged philosophy: graceful degradation. One failing deck logs and skips; template or asset failures degrade to an error page for that deck. All exceptions under `GeneratorError` carry a context dict.

## Phases

Each phase is independently shippable with CI green.

1. **Foundation** — model/exception consolidation, dead-code removal, regression harness over all repo decks.
2. **Rendering core** — `markdown_renderer.py`, Jinja macro migration, fidelity features (R1-R6). Largest phase.
3. **Website layer** — output layout, themes, self-hosted assets, homepage CSS (R7, R9).
4. **Viewer** — transitions, print/PDF verification, JS dedup (R8).
5. **Polish** — CLI fixes, README rewrite, doc cleanup (R10, remaining R11).

## Risks

- **Phase 2 size.** Mitigation: the regression harness lands before any rendering change, and the phase splits into parser/renderer/template sub-steps in the task plan.
- **python-markdown extension behavior vs Deckset quirks** (e.g. footnote scoping per slide). Mitigation: fidelity tests written from Deckset's documented behavior before wiring each extension; custom extension code where stock behavior differs.
- **Existing decks relying on v1 quirks** (e.g. literal `|` text now becoming tables). Mitigation: regression harness diff review at each milestone; fix decks or renderer case by case.
