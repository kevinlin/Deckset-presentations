"""Tests for theme_compiler: DESIGN.md parsing, reference resolution,
token mapping, CSS emission, and manifest generation."""

import tempfile
import shutil
from pathlib import Path

import pytest

from theme_compiler import parse_design_file, resolve_references
from models import ThemeCompileError

DESIGN_MD_DIR = Path(__file__).resolve().parent.parent / "design-md"


class TestParseDesignFile:
    """Tests for parse_design_file()."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_real_design_file(self):
        """Parses design-md/linear.app/DESIGN.md and returns dict with
        keys colors, typography, rounded."""
        path = DESIGN_MD_DIR / "linear.app" / "DESIGN.md"
        if not path.exists():
            pytest.skip("linear.app/DESIGN.md not found")
        result = parse_design_file(path)
        assert isinstance(result, dict)
        assert "colors" in result
        assert "typography" in result
        assert "rounded" in result

    def test_parse_strips_trailing_notes(self):
        """Content after the closing fence is discarded."""
        content = "---\ncolors:\n  canvas: \"#fff\"\n---\n# Notes\ntext"
        path = self.temp_dir / "DESIGN.md"
        path.write_text(content, encoding="utf-8")
        result = parse_design_file(path)
        assert result == {"colors": {"canvas": "#fff"}}

    def test_parse_invalid_yaml_raises(self):
        """Invalid YAML inside fences raises ThemeCompileError."""
        content = "---\ncolors: [unclosed\n---"
        path = self.temp_dir / "DESIGN.md"
        path.write_text(content, encoding="utf-8")
        with pytest.raises(ThemeCompileError, match="Invalid YAML"):
            parse_design_file(path)

    def test_parse_missing_fences_raises(self):
        """File without two --- fences raises ThemeCompileError."""
        content = "colors:\n  canvas: '#fff'\n"
        path = self.temp_dir / "DESIGN.md"
        path.write_text(content, encoding="utf-8")
        with pytest.raises(ThemeCompileError, match="missing YAML fences"):
            parse_design_file(path)

    def test_parse_non_dict_raises(self):
        """YAML that parses to a non-dict raises ThemeCompileError."""
        content = "---\n- item1\n- item2\n---"
        path = self.temp_dir / "DESIGN.md"
        path.write_text(content, encoding="utf-8")
        with pytest.raises(ThemeCompileError, match="Expected a YAML mapping"):
            parse_design_file(path)


class TestResolveReferences:
    """Tests for resolve_references()."""

    def test_resolves_color_reference(self):
        """Simple {colors.primary} references resolve to the target value."""
        data = {
            "colors": {"primary": "#5e6ad2"},
            "components": {"b": {"backgroundColor": "{colors.primary}"}},
        }
        result = resolve_references(data)
        assert result["components"]["b"]["backgroundColor"] == "#5e6ad2"

    def test_reference_cycle_raises(self):
        """{colors.a} -> {colors.b} -> {colors.a} raises ThemeCompileError."""
        data = {"colors": {"a": "{colors.b}", "b": "{colors.a}"}}
        with pytest.raises(ThemeCompileError, match="[Cc]ircular"):
            resolve_references(data)

    def test_unknown_reference_raises(self):
        """Reference to non-existent key raises ThemeCompileError."""
        data = {"colors": {"x": "{colors.nope}"}}
        with pytest.raises(ThemeCompileError, match="Unknown reference"):
            resolve_references(data)

    def test_non_string_values_pass_through(self):
        """Numeric and boolean values are not altered."""
        data = {"typography": {"body": {"fontSize": 16, "bold": True}}}
        result = resolve_references(data)
        assert result["typography"]["body"]["fontSize"] == 16
        assert result["typography"]["body"]["bold"] is True

    def test_chained_reference(self):
        """A -> B -> literal resolves in two passes."""
        data = {
            "colors": {
                "primary": "#abc",
                "link": "{colors.primary}",
            },
            "theme": {"link-color": "{colors.link}"},
        }
        result = resolve_references(data)
        assert result["theme"]["link-color"] == "#abc"


class TestAllRepoDesignsParse:
    """Sanity check: all 13 repo design files parse and resolve."""

    def test_all_repo_designs_parse(self):
        if not DESIGN_MD_DIR.exists():
            pytest.skip("design-md/ not found")
        design_files = sorted(DESIGN_MD_DIR.glob("*/DESIGN.md"))
        assert len(design_files) >= 13, f"Expected >=13, got {len(design_files)}"
        for path in design_files:
            data = parse_design_file(path)
            resolved = resolve_references(data)
            assert isinstance(resolved, dict), f"Failed for {path.parent.name}"
            assert "colors" in resolved, f"No colors in {path.parent.name}"
