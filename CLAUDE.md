# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Deckset-compatible Markdown → HTML static site generator. It scans the repo for presentation folders, parses Deckset markdown syntax, and renders a responsive website (homepage + one page per presentation). Output goes to `site/` and is deployed to GitHub Pages via GitHub Actions.

Python 3.12+, managed with **uv**. Runtime deps: `jinja2`, `markdown`. A JavaScript slide viewer (`templates/assets/js/slide-viewer.js`) is tested separately with Jest.

## Commands

```bash
uv sync                              # install deps (creates .venv)

# Run the generator
uv run python src/main.py                # scan cwd, generate site/
uv run python src/main.py --root <dir>   # scan a specific directory
uv run python src/main.py --output <dir> # custom output dir (default: site)
uv run python src/main.py --single <folder>   # build one presentation only
uv run python src/main.py --validate     # validate config and exit
uv run python src/main.py --verbose      # debug logging

# Python tests (pytest)
uv run pytest                        # all Python tests
uv run pytest tests/test_scanner.py  # single file
uv run pytest tests/test_scanner.py::TestScanner::test_name   # single test
uv run pytest --cov=src --cov-report=html                      # coverage

# JavaScript tests (Jest) — only covers site/templates JS assets
npm test                             # alias: npm run test:js
npm test -- -t "navigation"          # tests matching a name
npm run test:js:coverage
```

Add deps with `uv add <pkg>` (runtime) or `uv add --dev <pkg>`.

## Architecture

Modular pipeline, orchestrated by `DecksetWebsiteGenerator` in `src/main.py`:

```
Scanner → Parser → EnhancedProcessor → [specialized processors] → Templates → Generator → static site
```

All application modules live in `src/`. pytest resolves them via `pythonpath = ["src"]` in `pyproject.toml`.

- **`src/scanner.py`** (`PresentationScanner`) — discovers presentation folders. A folder is a presentation if it contains a `.md` file. When several exist, it prefers `<folder-name>.md`, else the first alphabetically. `exclude_folders` in `GeneratorConfig` filters folders out.
- **`src/deckset_parser.py`** (`DecksetParser`) — parses Deckset global commands and per-slide commands, splits slides on `---`.
- **`src/enhanced_processor.py`** (`EnhancedPresentationProcessor`) — the orchestrator. `process_presentation()` drives the parse + all specialized processors and returns an `EnhancedPresentation`.
- **Specialized processors** (each owns one concern):
  - `src/slide_processor.py` — slide content, columns, layout
  - `src/media_processor.py` — images/video/audio and placement modifiers
  - `src/code_processor.py` — syntax highlighting, line emphasis
  - `src/math_processor.py` — LaTeX math
- **`src/enhanced_templates.py`** — template engine. **Note:** slide/page/homepage HTML is generated from string templates defined *inside this module*, not only from the files in `templates/`. When changing rendered HTML, check here first.
- **`src/generator.py`** (`WebPageGenerator`) — writes presentation pages, the homepage, and copies assets.
- **`src/file_manager.py`** — filesystem operations, asset copying, web path resolution.
- **`src/models.py`** — all `@dataclass` data models, the config classes, and the exception hierarchy. Read this first to understand data flow.

### Key data models (`models.py`)

`PresentationInfo` (discovery metadata) → `EnhancedPresentation` / `ProcessedPresentation` (fully processed, holds `ProcessedSlide`s). Config split into two layers: `GeneratorConfig` (global: `output_dir`, `template_dir`, `exclude_folders`) vs `DecksetConfig` (per-presentation Deckset settings) and `SlideConfig` (per-slide overrides).

### Exceptions

Custom hierarchy rooted at `GeneratorError` (`ScanningError`, `PresentationProcessingError`, `TemplateRenderingError`, `FileOperationError`, `ConfigurationError`). Processing uses graceful degradation — one failing presentation folder is logged and skipped, not fatal. Wrap-and-reraise with context: `raise ProcessingError(f"...: {e}") from e`.

## Conventions

- **All application modules under `src/`** (not a package — no `__init__.py` — just a source directory).
- Interfaces are `ABC` + `@abstractmethod` (see `DecksetParserInterface`, `MediaProcessorInterface`, `SlideProcessorInterface` in `models.py`).
- Use `pathlib.Path` for all file ops; open files with explicit `encoding='utf-8'`.
- Each component sets up `self.logger = logging.getLogger(...)`; use it with contextual messages.
- Style: Black formatting (88 cols), snake_case functions, PascalCase classes, type hints on all signatures, `Optional[T]` over `T | None`.

## Presentation folders

Presentation content lives in numbered/named folders (`01-fix-messaging/`, `RAG Workshop/`, `Examples/`, …), each with a `.md` file plus its media assets. These are input data, not application code. `Examples/` holds reference presentations exercising Deckset syntax; `tests/` holds the test suite; `sample_output/` and `test_output/` are generated artifacts.

Supported Deckset syntax (see `.cursor/rules/deckset-syntax.mdc` for the full list): global commands (`theme:`, `footer:`, `slide-dividers:`, …), slide commands (`[.background-image:]`, `[.column]`, …), `[fit]` headers, `^` speaker notes, image modifiers (`![background]`, `![fit]`, `![left]`, `![75%]`, …), code highlight (`[.code-highlight: 1,3-5]`), inline/display math, footnotes, emoji shortcodes.

## Testing conventions

- pytest: one `test_<component>.py` per module, `TestClassName` classes, `setup_method`/`teardown_method` with `tempfile.mkdtemp()`; mock externals with `unittest.mock`. Integration coverage in `test_integration.py` / `test_end_to_end.py`.
- Jest (`jsdom` env): `tests/test_*.js` covering the slide viewer's navigation, accessibility, and functionality.

## CI/CD

`.github/workflows/generate-website.yml` runs on push/PR to `main`/`master`: runs pytest + Jest, then generates and deploys `site/` to GitHub Pages. Repo: https://github.com/kevinlin/Deckset-presentations

Branch naming: `feature/`, `fix/`, `site/`, `test/`. Conventional commit messages.

## Design Context

The generated website is a brand-register surface (a talk portfolio, not a neutral tool). Before UI work, read:

- `PRODUCT.md` — register (brand), audience (peers/evaluators), positioning ("a working portfolio of serious technical talks; the archive itself is the evidence"), anti-references (corporate slideware, generic SaaS landing, bare docs site), WCAG 2.1 AA target.
- `DESIGN.md` — visual spec ("The Projection Booth"): token-contract rule (all colors/fonts/radii via `var(--…)`, themeable across 16 themes), Cue Blue accent reserved for interaction, strict 16:9 slides, lifted-stage elevation.
