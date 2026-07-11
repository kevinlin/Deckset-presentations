# Theme System — design-md Designs

Date: 2026-07-12
Status: draft
Related: `docs/specs/04-theme-system/design.md` (Task 18 built the light/dark/minimal themes this extends)

## Requirement

Let the site take its look and feel from any design under `design-md/`. That directory holds 13 design-token systems exported from getdesign.md (airtable, cal, clay, figma, framer, intercom, linear.app, mintlify, miro, notion, resend, webflow, zapier). Decisions from the brainstorming session:

- **Selection:** site-wide default at build time (config/CLI), plus a visitor-side switcher in the rendered site.
- **Depth:** the theme restyles everything — homepage, presentation page chrome, and slide content (backgrounds, headings, body, code blocks, tables, blockquotes).
- **Pool:** one unified registry. The 13 design themes join `light`/`dark`/`minimal` (16 total). A deck's `theme:` directive picks from the same pool; unknown names warn and fall back, as today.
- **Fonts:** proprietary families map to system font stacks. No font downloads, no new CDN dependencies.

## Input format

Each `design-md/<folder>/DESIGN.md` is a YAML document between `---` fences, followed by markdown notes that the compiler ignores. All 13 share the same top-level keys: `version`, `name`, `description`, `colors`, `typography`, `rounded`, `spacing`, `components`. Values may reference other tokens with `{colors.x}` / `{typography.x}` / `{rounded.x}` syntax. Verified 2026-07-12: all 13 parse with PyYAML once the fence and trailing notes are stripped.

`README.md` in each folder is a link stub; it is not consumed.

## Architecture

```
design-md/*/DESIGN.md ─┐
                       ├─ ThemeCompiler ──► site/assets/css/themes/<slug>.css   (one per design)
templates/assets/css/  │                 ──► themes.json manifest (all 16)
  themes/{light,dark,  ┘
  minimal}.css (var-only, hand-authored)

base CSS (slide_styles.css, homepage.css, chrome) consumes var(--…) only
theme-switcher.js swaps the single theme <link>, persists choice in localStorage
```

### 1. Token contract

A fixed CSS custom-property vocabulary is the interface between theme files and base CSS. Theme files contain **only** `:root { … }` variable definitions and no other selectors. That keeps the visitor switcher a one-line stylesheet swap and keeps print/no-JS rendering correct.

Color roles, with source token and fallback chain (first present wins):

| Variable | Source token | Fallback |
|---|---|---|
| `--color-canvas` | `colors.canvas` | required |
| `--color-ink` | `colors.ink` | required |
| `--color-accent` | `colors.primary` | required |
| `--color-surface-1` | `colors.surface-1` | canvas |
| `--color-surface-2` | `colors.surface-2` | surface-1 |
| `--color-surface-3` | `colors.surface-3` | surface-2 |
| `--color-ink-muted` | `colors.ink-muted` | ink |
| `--color-ink-subtle` | `colors.ink-subtle` | ink-muted |
| `--color-on-accent` | `colors.on-primary` | `#ffffff` |
| `--color-accent-hover` | `colors.primary-hover` | accent |
| `--color-hairline` | `colors.hairline` | ink-subtle |
| `--color-hairline-strong` | `colors.hairline-strong` | hairline |
| `--color-link` | `colors.primary` | accent |
| `--color-code-bg` | `colors.surface-1` | (chain above) |
| `--color-table-header-bg` | `colors.surface-2` | (chain above) |
| `--color-blockquote-border` | `colors.primary` | accent |

A theme missing any of the three required tokens is skipped with a warning.

Typography roles:

- `--font-display` ← `typography.display-lg.fontFamily` (falls back to `headline`, then `body`)
- `--font-body` ← `typography.body.fontFamily`
- `--font-mono` ← `typography.mono.fontFamily`, falling back to a `ui-monospace` stack
- `--h1-size` / `--h2-size` / `--h3-size` are em ratios computed from the design's px scale against `body` (display-lg → h1, display-md → h2, headline → h3), so slide CSS keeps its own responsive base and multiplies. Matching `--hN-weight` and `--hN-tracking` come from the same scale entries.

Shape: `--radius-sm/md/lg` ← `rounded.sm/md/lg` (used by homepage cards, code blocks, buttons).

Non-goals: the `spacing` and `components` sections of DESIGN.md are not consumed. Spacing there describes marketing-page rhythm, and components (pricing cards, CTAs) have no counterpart in this site. highlight.js token colors also stay as shipped; only code-block background, border, and base text come from theme variables.

### 2. Theme compiler — `src/theme_compiler.py` (new)

Runs inside `generate_website()` before asset copying; also runs for `--single` (deck pages need theme CSS).

1. Discover `design-md/*/DESIGN.md` under the scan root.
2. Strip the YAML fence and trailing notes; parse with PyYAML (new runtime dep).
3. Resolve `{section.key}` references (one level of indirection is sufficient for all current files; nested references resolve iteratively with a cycle guard).
4. Map tokens → role variables per the contract table.
5. Map font families through a stack dictionary. Known proprietary names get curated stacks (e.g. `Linear Display` → `"SF Pro Display", Inter, system-ui, sans-serif`). Unknown names are kept and get a generic suffix (`"<Name>", system-ui, sans-serif`), so browsers fall back naturally.
6. Emit `site/assets/css/themes/<slug>.css`. Slug = folder name lowercased, characters outside `[a-z0-9-]` replaced with `-` (`linear.app` → `linear-app`).
7. Emit `site/assets/css/themes/themes.json`: `[{slug, name, swatches: [canvas, accent]}, …]` covering built-ins plus compiled designs, used by the switcher dropdown.

Built-ins: `templates/assets/css/themes/{light,dark,minimal}.css` are rewritten by hand as var-only files in the same vocabulary and copied unchanged. A design folder whose slug collides with a built-in is skipped with a warning (built-ins win).

Failure handling follows the repo's graceful-degradation rule: a malformed or incomplete DESIGN.md logs a warning and is left out of the registry; the build continues.

### 3. Base CSS re-plumb

- `templates/slide_styles.css` (slide content), `templates/assets/css/homepage.css`, and presentation chrome styles replace hardcoded colors and fonts with `var(--…)`. Light-theme values become the `light.css` token set, so a page with no theme link still renders sensibly via `var()` fallback values.
- The existing `dark.css`/`minimal.css` selector-override files are deleted and replaced by token sets.
- Tailwind (CDN) keeps layout and spacing utilities only. Color utilities currently used in `templates/homepage.html` and `templates/presentation.html` headers move to small var-driven classes in `homepage.css`/base CSS.

### 4. Resolution and configuration

- `GeneratorConfig` gains `theme: str = "light"` (site default) and `designs_dir: str = "design-md"`. New CLI flag `--theme <name>`.
- The registry (built-ins + compiled designs) replaces the directory probe in `enhanced_templates.resolve_theme()`. Deck `theme:` directive resolves against it; unknown names warn and fall back to the site default.
- Homepage links the site-default theme. Each presentation page links its resolved theme.
- `--validate` additionally checks the built-in theme templates and `theme-switcher.js` exist. Compiled themes are validated at build time, not by `--validate` (it runs without a build).

### 5. Visitor switcher

- `templates/assets/js/theme-switcher.js` (new) plus a dropdown in the homepage header and presentation page header.
- The generator inlines the manifest as `<script type="application/json" id="theme-manifest">` in each page, so the switcher works from `file://` as well as GitHub Pages.
- The theme `<link>` gets `id="theme-css"` and a `data-default-href` attribute. On load, a stored choice in `localStorage["deckset-site-theme"]` overrides the href; the dropdown's "Page default" entry clears storage and restores `data-default-href`.
- Without JS the page renders its build-time theme; printing is unaffected.

### 6. Testing

- **pytest** — `tests/test_theme_compiler.py`: fence/notes stripping, reference resolution, fallback chains, missing-required-token skip, malformed-YAML skip, slug rules, collision with built-in, manifest content, font-stack mapping. Registry resolution tests in `tests/test_enhanced_templates.py`. Regression harness additions: built site contains 16 theme CSS files and the manifest; a deck with `theme: notion` links `notion.css`; homepage links the site default.
- **Jest** — `tests/test_theme_switcher.js`: dropdown populates from inline manifest, selection swaps the link href, choice persists via localStorage, "Page default" resets.
- **Manual** — build the repo site, flip through several themes on the homepage and one deck, check slide readability on a dark design (linear-app) and a light one (notion), print-preview one deck.

## Risks

- **Slide readability on extreme palettes.** Some designs are near-black (linear.app `#010102`) or heavily tinted. The role mapping keeps body text on `canvas`/`ink` pairs taken directly from each design, which those systems already guarantee readable; the manual test pass covers the worst cases.
- **Tailwind color-utility migration.** Header markup relies on utility classes today; moving color to var-driven classes touches templates that the regression harness only partially covers. Mitigation: harness assertions on header structure before the migration commit.
- **DESIGN.md schema drift.** Files are `version: alpha` exports. The compiler validates required tokens and skips incompatible files instead of failing the build.
