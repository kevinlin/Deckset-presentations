# Deckset Presentations

A static-site generator that scans a repository for [Deckset](https://www.deckset.com/)-compatible Markdown presentations, converts each one into an interactive HTML slide deck, and produces a website ready to deploy on GitHub Pages.

## What it does

```
repo scan  →  Markdown parsing  →  HTML rendering  →  static site
```

1. **Scan** — finds every folder containing a `.md` file (prefers `<folder-name>.md` when multiple exist).
2. **Parse** — reads Deckset global and per-slide commands, splits slides, extracts speaker notes and media tokens.
3. **Render** — converts slide bodies with `python-markdown`, processes media, code highlighting, and math.
4. **Generate** — writes a homepage (`site/index.html`) and one page per deck (`site/<slug>/index.html`) with all media copied to `site/<slug>/media/`.

## Quick start

```bash
# Install dependencies (requires Python 3.12+ and uv)
uv sync

# Generate the site from the current directory
uv run python main.py

# Generate from a specific root, outputting to a custom directory
uv run python main.py --root /path/to/decks --output public

# Build a single presentation only
uv run python main.py --single "My Presentation"

# Validate configuration and required assets
uv run python main.py --validate

# Verbose logging
uv run python main.py --verbose
```

## Deck folder conventions

Each presentation lives in its own folder at the repo root:

```
01-my-talk/
  my-talk.md          # Deckset Markdown source
  photo.jpg           # Media referenced in the markdown
  diagrams/arch.png   # Subfolder media (paths preserved)
  custom.css          # Optional per-deck stylesheet overrides
```

Folders whose names start with `.` or match common non-presentation directories (`node_modules`, `site`, `tests`, `templates`, `docs`, `.git`, etc.) are excluded automatically.

## Supported Deckset syntax

Full syntax documentation: [`.cursor/rules/deckset-syntax.mdc`](.cursor/rules/deckset-syntax.mdc)

### Global commands (top of file or YAML frontmatter)

`theme:`, `footer:`, `slidenumbers:`, `slidecount:`, `autoscale:`, `slide-dividers:`, `slide-transition:`, `build-lists:`, `background-image:`, `code-language:`, `fit-header:` / `fit-headers:`

### Per-slide commands

`[.background-image:]`, `[.footer:]`, `[.hide-footer]`, `[.slidenumbers: false]` / `[.hide-slide-numbers]`, `[.autoscale:]`, `[.slide-transition:]`, `[.column]`

### Text and blocks

- Headings h1–h6, `[fit]` auto-scaling headers
- Bold, italic, strikethrough, inline code, links, `<sub>`, `<sup>`, `<br>`
- Emoji shortcodes (`:smile:`, `:rocket:`, etc.)
- Ordered/unordered/nested lists
- Pipe tables with column alignment
- Blockquotes with `-- Author` attribution
- Footnotes (`[^1]`, named labels)
- Display and inline math (MathJax)
- Speaker notes (`^ note text`)

### Media

- Background images with modifiers: `fit`, `left`, `right`, `N%`, `filtered`, `original`
- Multiple background images per slide
- Inline images with `inline`, `inline fill`, `inline N%`, `corner-radius(n)`
- Image grids from consecutive inline images
- Video: local files and YouTube embeds with `autoplay`, `loop`, `mute`, `left/right/fit/fill`
- Audio with controls

### Code

- Fenced code blocks with syntax highlighting (highlight.js, client-side)
- `[.code-highlight: 1, 3-5, all, none]` line highlighting per block

### Themes

16 themes are available: 3 built-in (`light`, `dark`, `minimal`) plus 13 compiled from `design-md/` token systems (airtable, cal, clay, figma, framer, intercom, linear-app, mintlify, miro, notion, resend, webflow, zapier).

**Per-deck theme:** Set `theme: notion` (or any slug) in the markdown's global commands.

**Site default:** Use `--theme <slug>` on the CLI (default: `light`).

**Visitor switcher:** A dropdown in the site header lets visitors choose any theme. The choice is saved in `localStorage` and applied on subsequent page loads. "Page default" resets to the build-time theme.

**Adding a design theme:** Drop a [getdesign.md](https://getdesign.md)-format folder into `design-md/`. The `DESIGN.md` YAML between `---` fences is compiled at build time into a CSS variable file. The `spacing` and `components` sections of DESIGN.md are not consumed. Proprietary font families are mapped to system font stacks — no font downloads are added.

Drop a `custom.css` in a deck folder for per-presentation overrides on top of the theme.

### Slide transitions

`slide-transition: fade` or `slide-transition: push` animate navigation. Respects `prefers-reduced-motion`.

## Output layout

```
site/
  index.html                    # Homepage with card grid and search
  assets/
    css/                        # Stylesheets and themes
    js/                         # Viewer and homepage scripts
    vendor/highlight/           # Vendored highlight.js
    vendor/mathjax/             # Vendored MathJax
  my-talk/
    index.html                  # Slide deck page
    media/                      # Copied media files
```

## Testing

```bash
# Python tests
uv run pytest                          # all tests
uv run pytest tests/test_scanner.py    # single module
uv run pytest --cov=. --cov-report=html  # coverage

# JavaScript tests (slide viewer)
npm test
```

## CI/CD

GitHub Actions (`.github/workflows/generate-website.yml`) runs on push/PR to `main`/`master`: executes pytest + Jest, then generates and deploys the site to GitHub Pages.

## Architecture

Modular pipeline at the repo root (no `src/` package):

| Module | Role |
|--------|------|
| `scanner.py` | Discovers presentation folders |
| `deckset_parser.py` | Parses Deckset commands, splits slides |
| `markdown_renderer.py` | Renders slide body via python-markdown |
| `enhanced_processor.py` | Orchestrates per-slide processing |
| `media_processor.py` | Images, video, audio |
| `code_processor.py` | Code blocks and line highlighting |
| `math_processor.py` | LaTeX math formulas |
| `slide_processor.py` | Columns and slide layout |
| `enhanced_templates.py` | Jinja2 template engine |
| `theme_compiler.py` | Compiles design-md tokens to CSS themes |
| `generator.py` | Writes HTML pages and homepage |
| `file_manager.py` | Asset copying and output layout |
| `models.py` | Data classes, config, exceptions |
| `main.py` | CLI entry point |

## Non-goals

The following Deckset features are intentionally not implemented:

- **Stepped code highlights** — the last `[.code-highlight:]` directive before a block wins; earlier directives on the same slide are ignored.
- **`build-lists` progressive reveal** — the command is parsed and stored but all list items are always visible.
- **Video `autoadvance`** — parsed but not acted on.
- **Deckset's built-in visual themes** — the generator provides its own theme system (16 themes from design tokens) rather than cloning Deckset's proprietary themes.
- **Vimeo and non-YouTube embeds** — only YouTube URLs are recognized for iframe embedding.
- **Presenter console / dual-screen mode** — not applicable to a static site.

## Specifications

- Current: [`docs/specs/03-markdown-converter-v2/`](docs/specs/03-markdown-converter-v2/) — requirements, design, and task plan for the v2 rewrite.
- Legacy: [`docs/requirements/`](docs/requirements/) — original v1 spec (superseded by v2).

## License

MIT License
