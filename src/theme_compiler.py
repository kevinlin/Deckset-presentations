"""Theme compiler: parse design-md DESIGN.md files and compile to CSS themes.

Reads YAML token systems from design-md/*/DESIGN.md, resolves internal
references, maps tokens to the CSS variable contract, and emits per-theme
CSS files plus a themes.json manifest.
"""

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from models import ThemeCompileError

logger = logging.getLogger(__name__)

_REFERENCE_RE = re.compile(r"\{([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_.-]+)\}")


def parse_design_file(path: Path) -> Dict[str, Any]:
    """Strip ``---`` fences and trailing markdown notes, then YAML-parse the body.

    Raises :class:`ThemeCompileError` on unreadable/invalid YAML or
    non-dict result.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ThemeCompileError(
            f"Cannot read design file: {exc}", context={"path": str(path)}
        ) from exc

    lines = raw.split("\n")

    fence_indices = [i for i, line in enumerate(lines) if line.strip() == "---"]
    if len(fence_indices) < 2:
        raise ThemeCompileError(
            "Design file missing YAML fences (expected two '---' lines)",
            context={"path": str(path)},
        )

    yaml_body = "\n".join(lines[fence_indices[0] + 1 : fence_indices[1]])

    try:
        data = yaml.safe_load(yaml_body)
    except yaml.YAMLError as exc:
        raise ThemeCompileError(
            f"Invalid YAML in design file: {exc}", context={"path": str(path)}
        ) from exc

    if not isinstance(data, dict):
        raise ThemeCompileError(
            f"Expected a YAML mapping, got {type(data).__name__}",
            context={"path": str(path)},
        )

    return data


def resolve_references(data: Dict[str, Any]) -> Dict[str, Any]:
    """Replace every ``{section.key}`` string with its target value.

    Iterative with a visited set; raises :class:`ThemeCompileError` on
    cycles or unknown targets. Non-string and non-reference values pass
    through unchanged.
    """
    flat: Dict[str, Any] = {}
    _flatten(data, "", flat)

    MAX_ITERATIONS = len(flat) + 1
    for _ in range(MAX_ITERATIONS):
        changed = False
        for key, value in list(flat.items()):
            if not isinstance(value, str):
                continue
            match = _REFERENCE_RE.search(value)
            if not match:
                continue
            ref_key = f"{match.group(1)}.{match.group(2)}"
            if ref_key not in flat:
                is_nested = any(
                    k.startswith(ref_key + ".") for k in flat
                )
                if is_nested:
                    continue
                raise ThemeCompileError(
                    f"Unknown reference '{{{ref_key}}}' in key '{key}'"
                )
            target = flat[ref_key]
            if isinstance(target, str) and _REFERENCE_RE.search(target):
                changed = True
                continue
            new_value = value[: match.start()] + str(target) + value[match.end() :]
            if new_value != value:
                flat[key] = new_value
                changed = True
        if not changed:
                truly_unresolved = []
                for k, v in flat.items():
                    if not isinstance(v, str):
                        continue
                    m = _REFERENCE_RE.search(v)
                    if not m:
                        continue
                    rk = f"{m.group(1)}.{m.group(2)}"
                    is_nested = any(
                        fk.startswith(rk + ".") for fk in flat
                    )
                    if not is_nested:
                        truly_unresolved.append(k)
                if truly_unresolved:
                    raise ThemeCompileError(
                        f"Circular reference detected involving: {truly_unresolved}"
                    )
                break
    else:
        truly_unresolved = []
        for k, v in flat.items():
            if not isinstance(v, str):
                continue
            m = _REFERENCE_RE.search(v)
            if not m:
                continue
            rk = f"{m.group(1)}.{m.group(2)}"
            is_nested = any(fk.startswith(rk + ".") for fk in flat)
            if not is_nested:
                truly_unresolved.append(k)
        if truly_unresolved:
            raise ThemeCompileError(
                f"Circular references detected: {truly_unresolved}"
            )

    return _unflatten(flat)


def _flatten(
    obj: Any, prefix: str, out: Dict[str, Any]
) -> None:
    """Recursively flatten a nested dict into dotted keys."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{prefix}.{k}" if prefix else k
            _flatten(v, new_key, out)
    else:
        out[prefix] = obj


def _unflatten(flat: Dict[str, Any]) -> Dict[str, Any]:
    """Rebuild nested dict from dotted keys."""
    result: Dict[str, Any] = {}
    for key, value in flat.items():
        parts = key.split(".")
        current = result
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value
    return result


# ---------------------------------------------------------------------------
# Task 3: slugify, map_tokens, render_css, ThemeInfo, ThemeCompiler
# ---------------------------------------------------------------------------

GENERIC_SANS = (
    '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
)
GENERIC_MONO = 'ui-monospace, "SF Mono", Menlo, Consolas, monospace'

FONT_STACKS = {
    "Linear Display": f'"SF Pro Display", Inter, {GENERIC_SANS}',
    "Linear Text": f'"SF Pro Text", Inter, {GENERIC_SANS}',
    "Linear Mono": f'"JetBrains Mono", {GENERIC_MONO}',
    "Notion Sans": f'Inter, {GENERIC_SANS}',
}

REQUIRED_TOKENS = ("canvas", "ink", "primary")

BUILTIN_THEMES = ("light", "dark", "minimal")
BUILTIN_SWATCHES = {
    "light": ("#ffffff", "#3b82f6"),
    "dark": ("#1a1a2e", "#4a90d9"),
    "minimal": ("#ffffff", "#3b82f6"),
}

CONTRACT_ORDER = [
    "--color-canvas",
    "--color-surface-1",
    "--color-surface-2",
    "--color-surface-3",
    "--color-ink",
    "--color-ink-muted",
    "--color-ink-subtle",
    "--color-accent",
    "--color-on-accent",
    "--color-accent-hover",
    "--color-hairline",
    "--color-hairline-strong",
    "--color-link",
    "--color-code-bg",
    "--color-table-header-bg",
    "--color-blockquote-border",
    "--font-display",
    "--font-body",
    "--font-mono",
    "--h1-size",
    "--h2-size",
    "--h3-size",
    "--h1-weight",
    "--h2-weight",
    "--h3-weight",
    "--h1-tracking",
    "--h2-tracking",
    "--h3-tracking",
    "--radius-sm",
    "--radius-md",
    "--radius-lg",
]


@dataclass
class ThemeInfo:
    """Metadata for one compiled or built-in theme."""

    slug: str
    name: str
    swatches: Tuple[str, str]


def slugify(folder_name: str) -> str:
    """Lowercase; any char outside ``[a-z0-9-]`` becomes ``-``; collapse
    repeats; strip leading/trailing ``-``."""
    slug = re.sub(r"[^a-z0-9-]", "-", folder_name.lower())
    slug = re.sub(r"-{2,}", "-", slug)
    return slug.strip("-")


def _font_stack(family: str, generic: str = GENERIC_SANS) -> str:
    """Return a CSS font-stack string for *family*."""
    return FONT_STACKS.get(family, f'"{family}", {generic}')


def _get_color(
    colors: Dict[str, Any], key: str, fallback: Optional[str] = None
) -> Optional[str]:
    """Get a color value from the colors dict, following the fallback."""
    val = colors.get(key)
    if val is not None:
        return str(val)
    return fallback


def _get_typography(
    typo: Dict[str, Any], *keys: str
) -> Optional[Dict[str, Any]]:
    """Return the first typography entry found among *keys*."""
    for k in keys:
        entry = typo.get(k)
        if isinstance(entry, dict):
            return entry
    return None


def _px_to_float(val: Any) -> Optional[float]:
    """Parse a px value like '56px' or 56 to a float."""
    if val is None:
        return None
    s = str(val).strip().lower()
    if s.endswith("px"):
        s = s[:-2]
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _tracking_em(letter_spacing: Any, font_size: Any) -> str:
    """Convert px letterSpacing to em relative to fontSize."""
    ls = _px_to_float(letter_spacing)
    fs = _px_to_float(font_size)
    if ls is None or fs is None or fs == 0:
        return "normal"
    em = round(ls / fs, 4)
    if em == 0:
        return "normal"
    return f"{em}em"


def map_tokens(design: Dict[str, Any]) -> Dict[str, str]:
    """Map a resolved design dict to ``{css_variable: value}`` per the
    D1 contract table.

    Raises :class:`ThemeCompileError` when a required token is missing.
    """
    colors = design.get("colors", {})
    typo = design.get("typography", {})
    rounded = design.get("rounded", {})

    for req in REQUIRED_TOKENS:
        if req not in colors:
            raise ThemeCompileError(f"Missing required color token: {req}")

    canvas = str(colors["canvas"])
    ink = str(colors["ink"])
    primary = str(colors["primary"])

    surface1 = _get_color(colors, "surface-1", canvas)
    surface2 = _get_color(colors, "surface-2", surface1)
    surface3 = _get_color(colors, "surface-3", surface2)
    ink_muted = _get_color(colors, "ink-muted", ink)
    ink_subtle = _get_color(colors, "ink-subtle", ink_muted)
    on_primary = _get_color(colors, "on-primary", "#ffffff")
    primary_hover = _get_color(colors, "primary-hover", primary)
    hairline = _get_color(colors, "hairline", ink_subtle)
    hairline_strong = _get_color(colors, "hairline-strong", hairline)

    variables: Dict[str, str] = {
        "--color-canvas": canvas,
        "--color-surface-1": surface1,
        "--color-surface-2": surface2,
        "--color-surface-3": surface3,
        "--color-ink": ink,
        "--color-ink-muted": ink_muted,
        "--color-ink-subtle": ink_subtle,
        "--color-accent": primary,
        "--color-on-accent": on_primary,
        "--color-accent-hover": primary_hover,
        "--color-hairline": hairline,
        "--color-hairline-strong": hairline_strong,
        "--color-link": _get_color(colors, "link", primary),
        "--color-code-bg": _get_color(colors, "surface-1", surface1),
        "--color-table-header-bg": _get_color(colors, "surface-2", surface2),
        "--color-blockquote-border": primary,
    }

    # Typography
    display_lg = _get_typography(typo, "display-lg", "headline", "body")
    display_md = _get_typography(typo, "display-md", "headline", "body")
    headline = _get_typography(typo, "headline", "display-md", "body")
    body = _get_typography(typo, "body") or {}
    mono = _get_typography(typo, "mono")

    body_size = _px_to_float(body.get("fontSize", 16)) or 16.0

    if display_lg:
        family = display_lg.get("fontFamily", body.get("fontFamily", ""))
        variables["--font-display"] = _font_stack(family) if family else GENERIC_SANS
    else:
        variables["--font-display"] = GENERIC_SANS

    body_family = body.get("fontFamily", "")
    variables["--font-body"] = _font_stack(body_family) if body_family else GENERIC_SANS

    if mono:
        mono_family = mono.get("fontFamily", "")
        variables["--font-mono"] = (
            _font_stack(mono_family, GENERIC_MONO)
            if mono_family
            else GENERIC_MONO
        )
    else:
        variables["--font-mono"] = GENERIC_MONO

    # Heading sizes as em ratios
    for var, entry in [
        ("--h1-size", display_lg),
        ("--h2-size", display_md),
        ("--h3-size", headline),
    ]:
        if entry:
            fs = _px_to_float(entry.get("fontSize"))
            if fs:
                variables[var] = f"{round(fs / body_size, 3)}em"
            else:
                variables[var] = "2em"
        else:
            variables[var] = "2em"

    for var, entry in [
        ("--h1-weight", display_lg),
        ("--h2-weight", display_md),
        ("--h3-weight", headline),
    ]:
        if entry and entry.get("fontWeight"):
            variables[var] = str(entry["fontWeight"])
        else:
            variables[var] = "600"

    for var, entry in [
        ("--h1-tracking", display_lg),
        ("--h2-tracking", display_md),
        ("--h3-tracking", headline),
    ]:
        if entry:
            variables[var] = _tracking_em(
                entry.get("letterSpacing"), entry.get("fontSize")
            )
        else:
            variables[var] = "normal"

    # Radius
    for var, key, default in [
        ("--radius-sm", "sm", "0.375rem"),
        ("--radius-md", "md", "0.5rem"),
        ("--radius-lg", "lg", "0.75rem"),
    ]:
        val = rounded.get(key)
        if val is not None:
            variables[var] = str(val)
        else:
            variables[var] = default

    return variables


def render_css(variables: Dict[str, str]) -> str:
    """Render a ``:root { … }`` block in contract-table order."""
    lines = [":root {"]
    for var_name in CONTRACT_ORDER:
        value = variables.get(var_name, "")
        if value:
            lines.append(f"  {var_name}: {value};")
    lines.append("}\n")
    return "\n".join(lines)


class ThemeCompiler:
    """Compile ``design-md/*/DESIGN.md`` files into CSS theme files and a
    ``themes.json`` manifest."""

    def __init__(self, designs_dir: Path) -> None:
        self.designs_dir = designs_dir
        self.logger = logging.getLogger(self.__class__.__name__)

    def compile_all(self, css_out_dir: Path) -> List[ThemeInfo]:
        """Compile every design folder into *css_out_dir*/<slug>.css.

        Skips (with warning) on any :class:`ThemeCompileError` or built-in
        slug collision. Writes ``themes.json`` covering built-in themes
        plus compiled designs. Returns the full manifest list, built-ins
        first.
        """
        css_out_dir.mkdir(parents=True, exist_ok=True)

        manifest: List[ThemeInfo] = [
            ThemeInfo(slug=slug, name=slug.capitalize(), swatches=BUILTIN_SWATCHES[slug])
            for slug in BUILTIN_THEMES
        ]

        if not self.designs_dir.exists():
            self.logger.warning(
                f"Designs directory not found: {self.designs_dir}"
            )
            self._write_manifest(css_out_dir, manifest)
            return manifest

        design_files = sorted(self.designs_dir.glob("*/DESIGN.md"))
        for design_path in design_files:
            folder_name = design_path.parent.name
            slug = slugify(folder_name)

            if slug in BUILTIN_THEMES:
                self.logger.warning(
                    f"Skipping design '{folder_name}': slug '{slug}' "
                    f"collides with built-in theme"
                )
                continue

            try:
                data = parse_design_file(design_path)
                resolved = resolve_references(data)
                variables = map_tokens(resolved)
                css_content = render_css(variables)

                out_file = css_out_dir / f"{slug}.css"
                out_file.write_text(css_content, encoding="utf-8")

                name = folder_name.replace(".", " ").replace("-", " ").replace("_", " ").title()
                canvas = variables.get("--color-canvas", "#ffffff")
                accent = variables.get("--color-accent", "#000000")

                manifest.append(
                    ThemeInfo(slug=slug, name=name, swatches=(canvas, accent))
                )
                self.logger.info(f"Compiled theme: {slug} ({name})")

            except ThemeCompileError as exc:
                self.logger.warning(
                    f"Skipping design '{folder_name}': {exc}"
                )
            except Exception as exc:
                self.logger.warning(
                    f"Unexpected error compiling '{folder_name}': {exc}"
                )

        self._write_manifest(css_out_dir, manifest)
        return manifest

    def _write_manifest(
        self, css_out_dir: Path, manifest: List[ThemeInfo]
    ) -> None:
        """Write ``themes.json`` manifest."""
        entries = [
            {
                "slug": t.slug,
                "name": t.name,
                "swatches": list(t.swatches),
            }
            for t in manifest
        ]
        manifest_path = css_out_dir / "themes.json"
        manifest_path.write_text(
            json.dumps(entries, indent=2) + "\n", encoding="utf-8"
        )
