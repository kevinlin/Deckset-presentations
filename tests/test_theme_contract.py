"""Tests for the theme variable contract (D1).

Verifies that theme CSS files use only :root selectors and define the
full set of required CSS custom properties.
"""

import re
from pathlib import Path

import pytest

THEMES_DIR = Path(__file__).resolve().parent.parent / "templates" / "assets" / "css" / "themes"

REQUIRED_VARS = [
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

SELECTOR_RE = re.compile(r"^\s*([^{}/]+?)\s*\{", re.MULTILINE)


class TestThemeContract:
    """Every theme file must be var-only (:root selector only)."""

    def _theme_files(self):
        return sorted(THEMES_DIR.glob("*.css"))

    def test_theme_files_are_var_only(self):
        """Each theme CSS file should only contain :root selectors."""
        theme_files = self._theme_files()
        assert len(theme_files) >= 3, f"Expected >=3 theme files, got {len(theme_files)}"

        for css_file in theme_files:
            content = css_file.read_text(encoding="utf-8")
            selectors = SELECTOR_RE.findall(content)
            for sel in selectors:
                cleaned = sel.strip()
                assert cleaned == ":root", (
                    f"{css_file.name}: found selector '{cleaned}', "
                    f"expected only ':root'"
                )

    def test_light_theme_defines_required_vars(self):
        """light.css must define every variable in the contract."""
        light = THEMES_DIR / "light.css"
        assert light.exists(), "light.css not found"
        content = light.read_text(encoding="utf-8")
        for var in REQUIRED_VARS:
            assert f"{var}:" in content, (
                f"light.css missing required variable '{var}'"
            )

    def test_dark_theme_defines_required_vars(self):
        """dark.css must define every variable in the contract."""
        dark = THEMES_DIR / "dark.css"
        assert dark.exists(), "dark.css not found"
        content = dark.read_text(encoding="utf-8")
        for var in REQUIRED_VARS:
            assert f"{var}:" in content, (
                f"dark.css missing required variable '{var}'"
            )

    def test_minimal_theme_defines_required_vars(self):
        """minimal.css must define every variable in the contract."""
        minimal = THEMES_DIR / "minimal.css"
        assert minimal.exists(), "minimal.css not found"
        content = minimal.read_text(encoding="utf-8")
        for var in REQUIRED_VARS:
            assert f"{var}:" in content, (
                f"minimal.css missing required variable '{var}'"
            )

    def test_slide_styles_uses_variables(self):
        """slide_styles.css should use var(--…) extensively (>40 occurrences)."""
        slide_css = (
            Path(__file__).resolve().parent.parent / "templates" / "slide_styles.css"
        )
        content = slide_css.read_text(encoding="utf-8")
        count = content.count("var(--")
        assert count > 40, (
            f"Expected >40 var(--…) usages in slide_styles.css, got {count}"
        )
