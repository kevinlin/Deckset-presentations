# Theme System Implementation Plan

> **For agentic workers:** execute task-by-task with TDD (failing test first, minimal implementation, verify, commit). Checkboxes track progress. Each task is independently reviewable; each task ships with CI green.

**Status:** not started

**Goal:** Deliver the theme system per `docs/specs/theme-system/design.md`: compile the 13 `design-md/` token systems into CSS themes at build time, unify them with light/dark/minimal in one registry, re-plumb base CSS onto a variable contract, and add a visitor-side switcher.

**Architecture:** New `src/theme_compiler.py` parses `design-md/*/DESIGN.md` (YAML) into var-only CSS files plus a `themes.json` manifest. Base CSS consumes `var(--…)` only. `theme-switcher.js` swaps the single theme `<link>` and persists in localStorage.

**Tech stack:** Python 3.12 + uv, PyYAML (new runtime dep), Jinja2, Jest for switcher JS.

## Global constraints

- Conventions in `CLAUDE.md` apply: pathlib, `encoding='utf-8'`, type hints, Black 88 cols, per-module logger.
- Graceful degradation: a malformed DESIGN.md warns and is skipped; the build never fails because of one theme.
- Every task: run `uv run pytest` (and `npm test` when JS touched) before commit. Conventional commit messages.
- Regression harness (`tests/test_regression_site.py`) must pass at the end of every task; when a task changes output structure, update harness assertions in the same commit.
- Design references (D1–D6) point at the numbered sections of `docs/specs/theme-system/design.md`.

---

## Task 1: Base CSS onto the variable contract

Re-plumb existing CSS to consume the D1 token contract with fallback values equal to today's colors, so output is visually unchanged before any design theme exists. Rewrite built-in themes as var-only token sets.

**Files:**
- Modify: `templates/slide_styles.css` (858 lines — colors and fonts only)
- Modify: `templates/assets/css/homepage.css`
- Rewrite: `templates/assets/css/themes/light.css`, `dark.css`, `minimal.css`
- Test: `tests/test_theme_contract.py` (new)

**Interfaces (consumed by Tasks 3, 5, 6):** the variable names in the D1 contract table, exactly: `--color-canvas`, `--color-surface-1..3`, `--color-ink`, `--color-ink-muted`, `--color-ink-subtle`, `--color-accent`, `--color-on-accent`, `--color-accent-hover`, `--color-hairline`, `--color-hairline-strong`, `--color-link`, `--color-code-bg`, `--color-table-header-bg`, `--color-blockquote-border`, `--font-display`, `--font-body`, `--font-mono`, `--h1-size`, `--h2-size`, `--h3-size`, `--h1-weight`, `--h2-weight`, `--h3-weight`, `--h1-tracking`, `--h2-tracking`, `--h3-tracking`, `--radius-sm`, `--radius-md`, `--radius-lg`.

Steps:

- [ ] Write failing test `tests/test_theme_contract.py::test_theme_files_are_var_only`: parse each `templates/assets/css/themes/*.css`, assert the only selector is `:root` (regex `^\s*([^{}]+)\s*\{` over the file; every capture strips to `:root`).
- [ ] Write failing test `test_light_theme_defines_required_vars`: `light.css` defines every variable in the contract list above (assert `--color-canvas:` etc. present).
- [ ] Rewrite `light.css` as the full token set using today's effective light values from `slide_styles.css` (canvas `#fff`, ink `#374151`, ink-muted `#4b5563`, ink-subtle `#6b7280`, accent/link `#3b82f6`, hairline `#e5e7eb`, code-bg `#f3f4f6`, table-header-bg `#f9fafb`, body font = current system stack, mono = `'Monaco', 'Menlo', 'Ubuntu Mono', monospace`, h1/h2/h3 sizes = current rem values converted to em).
- [ ] Rewrite `dark.css` and `minimal.css` as `:root` token sets reproducing their current palettes (dark: canvas `#1a1a2e`, ink `#e0e0e0`, code-bg `#0d1117`, accent `#4a90d9`, link `#6db3f2`, table-header-bg `#21262d`, hairline `#30363d`; minimal: light palette + `--font-display: Georgia, 'Times New Roman', serif`, muted `#666`, hairline `#ccc`).
- [ ] Re-plumb `slide_styles.css`: every color and font-family becomes `var(--<role>, <current literal>)` per the D1 mapping (slide background → canvas, body text → ink, headings → ink + display font/sizes/weights, links → link, blockquote border → blockquote-border, code/pre → code-bg + mono, table header → table-header-bg, borders → hairline, footer/slide-number → ink-subtle). Leave non-themable rgba overlays (image filters, `--overlay-opacity` machinery) untouched.
- [ ] Re-plumb `homepage.css` hover shadow to use `--color-hairline` where it hardcodes rgba black at 10%; keep the rest.
- [ ] Run `uv run pytest tests/test_theme_contract.py tests/test_regression_site.py -v` — all pass.
- [ ] Manual spot check: build site, open one deck with `theme: dark` and one without; visuals match pre-change.
- [ ] Commit: `refactor: move base CSS onto theme variable contract`

Verify: full suite green; `grep -c "var(--" templates/slide_styles.css` is large (>40); theme files contain no selector besides `:root`.
_Design: D1, D3_

## Task 2: Theme compiler — parse and resolve DESIGN.md

**Files:**
- Create: `src/theme_compiler.py`
- Modify: `src/models.py` (add `ThemeCompileError`)
- Modify: `pyproject.toml` (`uv add pyyaml`)
- Test: `tests/test_theme_compiler.py` (new)

**Interfaces (produces):**

```python
class ThemeCompileError(GeneratorError): ...   # models.py, same context-dict pattern

# theme_compiler.py
def parse_design_file(path: Path) -> Dict[str, Any]:
    """Strip --- fences and trailing markdown notes, yaml.safe_load the body.
    Raises ThemeCompileError on unreadable/invalid YAML or non-dict result."""

def resolve_references(data: Dict[str, Any]) -> Dict[str, Any]:
    """Replace every '{section.key}' string with its target value.
    Iterative with a visited set; raises ThemeCompileError on cycles or
    unknown targets. Non-string and non-reference values pass through."""
```

Steps:

- [ ] `uv add pyyaml`.
- [ ] Failing tests, then implement `parse_design_file`:
  - `test_parse_real_design_file` — parses `design-md/linear.app/DESIGN.md` (repo fixture), returns dict with keys `colors`, `typography`, `rounded`.
  - `test_parse_strips_trailing_notes` — tmp file with `---\ncolors:\n  canvas: "#fff"\n---\n# Notes\ntext` parses to `{"colors": {"canvas": "#fff"}}`.
  - `test_parse_invalid_yaml_raises` — tmp file with `---\ncolors: [unclosed\n---` raises `ThemeCompileError`.
- [ ] Failing tests, then implement `resolve_references`:
  - `test_resolves_color_reference` — `{"colors": {"primary": "#5e6ad2"}, "components": {"b": {"backgroundColor": "{colors.primary}"}}}` → backgroundColor `"#5e6ad2"`.
  - `test_reference_cycle_raises` — `{"colors": {"a": "{colors.b}", "b": "{colors.a}"}}` raises `ThemeCompileError`.
  - `test_unknown_reference_raises` — `{colors.nope}` raises `ThemeCompileError`.
- [ ] Sanity test `test_all_repo_designs_parse` — loop `design-md/*/DESIGN.md`, `resolve_references(parse_design_file(p))` succeeds for all 13.
- [ ] `uv run pytest tests/test_theme_compiler.py -v` green; commit: `feat: theme compiler parses design-md DESIGN.md files`

_Design: D2 (steps 1–3)_

## Task 3: Theme compiler — map tokens, emit CSS and manifest

**Files:**
- Modify: `src/theme_compiler.py`
- Test: `tests/test_theme_compiler.py`

**Interfaces (produces, consumed by Task 4):**

```python
@dataclass
class ThemeInfo:
    slug: str
    name: str          # display name: folder name title-cased, dots/dashes → space
    swatches: Tuple[str, str]   # (canvas, accent) for the picker

REQUIRED_TOKENS = ("canvas", "ink", "primary")   # in colors:

def slugify(folder_name: str) -> str:
    """lowercase; any char outside [a-z0-9-] becomes '-'; collapse repeats;
    strip leading/trailing '-'.  'linear.app' -> 'linear-app'"""

def map_tokens(design: Dict[str, Any]) -> Dict[str, str]:
    """Resolved design -> {css variable name: value} per the D1 contract table,
    applying fallback chains (surface-2 -> surface-1 -> canvas, etc.), font
    stacks, and em-ratio heading sizes. Raises ThemeCompileError when a
    REQUIRED_TOKENS entry is missing."""

def render_css(variables: Dict[str, str]) -> str:
    """':root {\n  --name: value;\n  ...\n}\n' in contract-table order."""

class ThemeCompiler:
    def __init__(self, designs_dir: Path) -> None: ...
    def compile_all(self, css_out_dir: Path) -> List[ThemeInfo]:
        """Compile every design-md folder into css_out_dir/<slug>.css.
        Skips (warning log) on any ThemeCompileError or built-in slug
        collision. Writes css_out_dir/themes.json covering BUILTIN_THEMES
        (light/dark/minimal, swatches hardcoded) + compiled designs.
        Returns the full manifest list, built-ins first."""
```

Font mapping inside `map_tokens`:

```python
GENERIC_SANS = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
GENERIC_MONO = 'ui-monospace, "SF Mono", Menlo, Consolas, monospace'
FONT_STACKS = {
    "Linear Display": f'"SF Pro Display", Inter, {GENERIC_SANS}',
    "Linear Text": f'"SF Pro Text", Inter, {GENERIC_SANS}',
    # extend as designs are reviewed; unknown family falls through to:
}
def _font_stack(family: str, generic: str = GENERIC_SANS) -> str:
    return FONT_STACKS.get(family, f'"{family}", {generic}')
```

Heading ratios: `--h1-size = round(display-lg.fontSize / body.fontSize, 3)em` (display-md → h2, headline → h3); weights and letterSpacing copied from the same entries, tracking converted px → em against that entry's own fontSize.

Steps:

- [ ] Failing tests, then implement, in this order:
  - `test_slugify` — `linear.app` → `linear-app`; `Some_Folder` → `some-folder`.
  - `test_map_tokens_direct_and_fallback` — minimal design dict with only `canvas`, `ink`, `primary`, `body`/`display-lg` typography: `--color-surface-2` falls back through surface-1 to canvas; `--color-on-accent` defaults `#ffffff`; `--h1-size` = `3.5em` for 56px over 16px body.
  - `test_map_tokens_missing_required_raises` — no `colors.ink` → `ThemeCompileError`.
  - `test_font_stack_known_and_unknown` — `Linear Display` → starts with `"SF Pro Display"`; `Mystery Sans` → `'"Mystery Sans", -apple-system'` prefix.
  - `test_render_css_var_only` — output matches `^:root \{` and contains no other `{`.
  - `test_compile_all_writes_css_and_manifest` — tmp designs dir with one valid + one broken design: valid slug CSS exists, broken skipped, `themes.json` lists 3 built-ins + 1 design with slug/name/swatches.
  - `test_compile_all_builtin_collision_skipped` — design folder named `dark` is skipped with a warning (caplog).
- [ ] `test_compile_all_real_designs` — run against repo `design-md/`: 13 CSS files, manifest has 16 entries.
- [ ] `uv run pytest tests/test_theme_compiler.py -v` green; commit: `feat: compile design-md tokens to theme CSS and manifest`

_Design: D1, D2 (steps 4–7)_

## Task 4: Pipeline integration — config, CLI, registry, homepage link

**Files:**
- Modify: `src/models.py` (`GeneratorConfig`), `src/main.py`, `src/generator.py`, `src/enhanced_templates.py`, `templates/homepage.html`, `templates/presentation.html`
- Test: `tests/test_main.py`, `tests/test_enhanced_templates.py`, `tests/test_regression_site.py`

**Interfaces:**

```python
# models.py
class GeneratorConfig:
    theme: str = "light"           # site default
    designs_dir: str = "design-md"

# enhanced_templates.py — replaces KNOWN_THEMES tuple probe
class EnhancedTemplateEngine:
    def set_theme_registry(self, slugs: Set[str], default_theme: str) -> None: ...
    # resolve_theme(name) now: known slug -> slug; falsy/unknown -> warn + default_theme
```

Steps:

- [ ] Add `theme: str = "light"` and `designs_dir: str = "design-md"` fields to `GeneratorConfig` (`src/models.py:46`).
- [ ] Failing test `tests/test_main.py::test_theme_cli_flag` — `--theme dark` sets `config.theme == "dark"`; then add `--theme` to the main.py argparser (default `"light"`) and thread into `GeneratorConfig`.
- [ ] Failing tests for registry resolution in `tests/test_enhanced_templates.py`: after `set_theme_registry({"light","dark","minimal","linear-app"}, "dark")` — `resolve_theme("linear-app") == "linear-app"`, `resolve_theme(None) == "dark"`, `resolve_theme("nope") == "dark"` with warning (caplog). Implement; delete the filesystem probe at `enhanced_templates.py:112-114` and the `KNOWN_THEMES` constant.
- [ ] Invoke compiler in `WebPageGenerator.generate_all_pages()` (`src/generator.py:308`) before page generation: `ThemeCompiler(Path(self.config.designs_dir)).compile_all(Path(self.config.output_dir)/"assets"/"css"/"themes")`; store manifest on `self.theme_manifest`; call `template_manager.set_theme_registry({t.slug for t in manifest}, self.config.theme)`. Both full build (`main.py:327`) and `--single` (`main.py:198`) route through here — no extra wiring.
- [ ] `theme_stylesheets()` (`enhanced_templates.py:118`) emits the theme link as `<link id="theme-css" rel="stylesheet" href="{prefix}assets/css/themes/{theme}.css" data-default-href="{same}">`; custom.css link unchanged.
- [ ] Homepage gets the site-default theme: add to `generate_homepage()` context `default_theme=self.template_manager.resolve_theme(self.config.theme)`; in `templates/homepage.html` after the `homepage.css` link add `<link id="theme-css" rel="stylesheet" href="assets/css/themes/{{ default_theme }}.css" data-default-href="assets/css/themes/{{ default_theme }}.css">`.
- [ ] `--validate` (`main.py:436` `required_assets`): add `assets/css/themes/dark.css`, `assets/css/themes/minimal.css` (built-in templates; compiled themes are build-time-validated, D4).
- [ ] Regression harness additions (same commit): built site has `assets/css/themes/themes.json` and ≥16 `themes/*.css`; homepage links `themes/light.css` with `id="theme-css"`; a fixture deck with `theme: notion` links `themes/notion.css`.
- [ ] `uv run pytest` green; `uv run python src/main.py --validate` exits 0; commit: `feat: theme registry, --theme flag, compiled themes in build`

_Design: D2, D4_

## Task 5: Header colors off Tailwind utilities

Color utilities in the two page headers/footers move to var-driven classes so themes restyle chrome; Tailwind keeps layout/spacing only (D3).

**Files:**
- Modify: `templates/homepage.html`, `templates/presentation.html`, `templates/assets/css/homepage.css`
- Test: `tests/test_regression_site.py`

Steps:

- [ ] Add to `homepage.css` (loaded by both pages after this task — also add `<link rel="stylesheet" href="{{ asset_path_prefix }}assets/css/homepage.css">` to `presentation.html`):

```css
body { background: var(--color-canvas, #f9fafb); color: var(--color-ink, #374151); }
.site-header { background: var(--color-surface-1, #fff); border-bottom: 1px solid var(--color-hairline, #e5e7eb); }
.site-header a, .site-title { color: var(--color-ink, #111827); font-family: var(--font-display, inherit); }
.site-nav-link { color: var(--color-ink-muted, #4b5563); }
.site-nav-link:hover { color: var(--color-ink, #111827); }
.site-footer { background: var(--color-surface-1, #fff); border-top: 1px solid var(--color-hairline, #e5e7eb); color: var(--color-ink-subtle, #6b7280); }
.presentation-card { background: var(--color-surface-1, #fff); border-radius: var(--radius-lg, 0.5rem); }
.card-title a { color: var(--color-ink, #111827); }
.card-title a:hover { color: var(--color-link, #2563eb); }
.card-meta { color: var(--color-ink-muted, #4b5563); }
.card-cta { background: var(--color-accent, #dbeafe); color: var(--color-on-accent, #1d4ed8); border-radius: var(--radius-sm, 0.375rem); }
.card-cta:hover { background: var(--color-accent-hover, #bfdbfe); }
```

- [ ] In both templates, strip the color utilities these classes replace (`bg-white`, `bg-gray-50`, `text-gray-900/600/500`, `hover:text-gray-900`, `border-b`, `text-blue-700 bg-blue-100 hover:bg-blue-200`, card `bg-white`) and add the new class names (`site-header`, `site-nav-link`, `site-footer`, `card-title`, `card-meta`, `card-cta`, `body` styles come free). Layout utilities (`flex`, `px-*`, `max-w-*`, `shadow-*`, `rounded-md` on non-themed bits) stay.
- [ ] Harness (same commit): assert homepage header has `class~="site-header"` and no `bg-white` on it; presentation page header likewise.
- [ ] `uv run pytest` green; manual: build, homepage renders identically under light; commit: `refactor: theme-variable classes replace header color utilities`

_Design: D3_

## Task 6: Visitor theme switcher

**Files:**
- Create: `templates/assets/js/theme-switcher.js`
- Modify: `templates/homepage.html`, `templates/presentation.html`, `src/generator.py`, `templates/assets/css/homepage.css`, `src/main.py` (`--validate` list)
- Test: `tests/test_theme_switcher.js` (Jest), `tests/test_regression_site.py`

**Interfaces:**
- Storage key: `localStorage["deckset-site-theme"]` = slug, absent = page default.
- Manifest inline in both pages: `<script type="application/json" id="theme-manifest">{{ theme_manifest_json | safe }}</script>` where `theme_manifest_json = json.dumps([{"slug": t.slug, "name": t.name, "swatches": list(t.swatches)} for t in self.theme_manifest])` added to both page contexts in `generator.py` (homepage context and `_render_enhanced_presentation` context, `generator.py:411`).
- Markup in both headers: `<select id="theme-select" class="site-nav-link" aria-label="Theme"></select>`.

`theme-switcher.js` behavior (implement exactly):

```js
// On DOMContentLoaded:
// 1. Read manifest JSON from #theme-manifest; bail silently if absent.
// 2. Populate #theme-select: first <option value="">Page default</option>,
//    then one option per manifest entry (value=slug, text=name).
// 3. stored = localStorage.getItem('deckset-site-theme')
//    link = document.getElementById('theme-css')
//    If stored && manifest has stored: swap link.href — replace the trailing
//    '<slug>.css' segment of link.dataset.defaultHref with '<stored>.css' —
//    and select the option.
// 4. On change: value '' → removeItem + restore link.dataset.defaultHref;
//    else setItem and swap href as above.
```

Steps:

- [ ] Jest failing tests in `tests/test_theme_switcher.js` (jsdom, mirror existing viewer test setup): populates options from inline manifest (17 incl. "Page default"); selecting `notion` swaps href to `…/themes/notion.css` and persists; stored value applied on load; "Page default" clears storage and restores `data-default-href`; missing manifest script is a no-op.
- [ ] Implement `theme-switcher.js`; add `<script src="…assets/js/theme-switcher.js"></script>` before `</body>` in both templates (homepage: plain path, presentation: `{{ asset_path_prefix }}` prefix).
- [ ] Add manifest injection in `generator.py` (both contexts) and the `<select>` + manifest `<script>` tags to both templates. Style `#theme-select` in `homepage.css` with var-driven colors (`background: var(--color-surface-1); color: var(--color-ink); border: 1px solid var(--color-hairline); border-radius: var(--radius-sm)`).
- [ ] `--validate`: add `assets/js/theme-switcher.js` to `required_assets` (`main.py:436`).
- [ ] Harness (same commit): both page types contain `#theme-select`, `#theme-manifest`, and the switcher script tag.
- [ ] `npm test` and `uv run pytest` green; commit: `feat: visitor theme switcher with localStorage persistence`

_Design: D5_

## Task 7: Docs, manual pass, final sweep

**Files:**
- Modify: `README.md`, `docs/specs/theme-system/design.md` (status → implemented), `docs/specs/theme-system/tasks.md` (status)

Steps:

- [ ] README theme section: list the 16 themes, `--theme` flag, deck `theme:` directive, visitor switcher, how to add a design (drop a getdesign.md-format folder into `design-md/`), non-consumed sections (`spacing`, `components`), font-stack substitution note.
- [ ] Manual pass (D6): build the repo site; on homepage flip through ≥4 themes including `linear-app` (near-black) and `notion` (light) — check card/text contrast; open one deck, switch themes, navigate slides, check code block + table readability; print-preview one deck (switcher hidden by existing `no-print` handling — add class if missed); reload page and confirm persisted theme applies.
- [ ] Coverage: `uv run pytest --cov=src --cov-report=term` — `theme_compiler.py` ≥ 85%.
- [ ] Full verify: `uv run pytest && npm test && uv run python src/main.py --validate`.
- [ ] Commit: `docs: theme system usage and spec status`

_Design: D6 + spec closeout_

---

## Task → design coverage

| Design section | Tasks |
|---|---|
| D1 token contract | 1, 3 |
| D2 compiler | 2, 3, 4 |
| D3 base CSS re-plumb | 1, 5 |
| D4 resolution/config | 4 |
| D5 switcher | 6 |
| D6 testing | 1–7 (harness per task), 7 (manual) |
