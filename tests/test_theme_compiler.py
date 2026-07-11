"""Tests for theme_compiler: DESIGN.md parsing, reference resolution,
token mapping, CSS emission, and manifest generation."""

import json
import tempfile
import shutil
from pathlib import Path

import pytest

from theme_compiler import (
    parse_design_file,
    resolve_references,
    slugify,
    map_tokens,
    render_css,
    ThemeCompiler,
    ThemeInfo,
    _font_stack,
    GENERIC_SANS,
)
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


# ---- Task 3 tests ----


class TestSlugify:
    def test_slugify_dot(self):
        assert slugify("linear.app") == "linear-app"

    def test_slugify_underscore(self):
        assert slugify("Some_Folder") == "some-folder"

    def test_slugify_spaces(self):
        assert slugify("My Theme Name") == "my-theme-name"

    def test_slugify_collapse_repeats(self):
        assert slugify("a--b..c") == "a-b-c"


class TestFontStack:
    def test_known_family(self):
        result = _font_stack("Linear Display")
        assert result.startswith('"SF Pro Display"')

    def test_unknown_family(self):
        result = _font_stack("Mystery Sans")
        assert result.startswith('"Mystery Sans"')
        assert "-apple-system" in result


class TestMapTokens:
    def _minimal_design(self) -> dict:
        return {
            "colors": {
                "canvas": "#010102",
                "ink": "#f7f8f8",
                "primary": "#5e6ad2",
            },
            "typography": {
                "display-lg": {
                    "fontFamily": "Test Display",
                    "fontSize": "56px",
                    "fontWeight": 600,
                    "letterSpacing": "-1.8px",
                },
                "body": {
                    "fontFamily": "Test Body",
                    "fontSize": "16px",
                    "fontWeight": 400,
                },
            },
        }

    def test_map_tokens_direct_and_fallback(self):
        design = self._minimal_design()
        result = map_tokens(design)
        assert result["--color-canvas"] == "#010102"
        assert result["--color-ink"] == "#f7f8f8"
        assert result["--color-accent"] == "#5e6ad2"
        assert result["--color-surface-2"] == "#010102"
        assert result["--color-on-accent"] == "#ffffff"
        assert result["--h1-size"] == "3.5em"

    def test_map_tokens_missing_required_raises(self):
        design = {
            "colors": {"canvas": "#fff", "primary": "#abc"},
            "typography": {},
        }
        with pytest.raises(ThemeCompileError, match="Missing required.*ink"):
            map_tokens(design)


class TestRenderCss:
    def test_render_css_var_only(self):
        variables = {
            "--color-canvas": "#fff",
            "--color-ink": "#000",
            "--color-accent": "#abc",
        }
        css = render_css(variables)
        assert css.startswith(":root {")
        lines = css.split("\n")
        brace_lines = [l for l in lines if "{" in l and ":root" not in l.split("{")[0].strip()]
        assert len(brace_lines) == 0


class TestCompileAll:
    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.css_out = self.temp_dir / "css_out"
        self.designs = self.temp_dir / "designs"

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_design(self, folder: str, yaml_content: str) -> None:
        d = self.designs / folder
        d.mkdir(parents=True, exist_ok=True)
        (d / "DESIGN.md").write_text(
            f"---\n{yaml_content}\n---\n# Notes\n", encoding="utf-8"
        )

    def test_compile_all_writes_css_and_manifest(self):
        self._write_design(
            "good-design",
            'colors:\n  canvas: "#fff"\n  ink: "#000"\n  primary: "#abc"\n'
            "typography:\n  body:\n    fontFamily: Test\n    fontSize: 16px\n    fontWeight: 400\n",
        )
        self._write_design(
            "broken",
            'colors:\n  canvas: "#fff"\n',
        )
        compiler = ThemeCompiler(self.designs)
        manifest = compiler.compile_all(self.css_out)

        assert (self.css_out / "good-design.css").exists()
        assert not (self.css_out / "broken.css").exists()

        manifest_path = self.css_out / "themes.json"
        assert manifest_path.exists()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        slugs = [e["slug"] for e in data]
        assert "light" in slugs
        assert "dark" in slugs
        assert "minimal" in slugs
        assert "good-design" in slugs
        assert len(data) == 4

    def test_compile_all_builtin_collision_skipped(self, caplog):
        self._write_design(
            "dark",
            'colors:\n  canvas: "#111"\n  ink: "#eee"\n  primary: "#abc"\n'
            "typography:\n  body:\n    fontFamily: X\n    fontSize: 16px\n    fontWeight: 400\n",
        )
        compiler = ThemeCompiler(self.designs)
        manifest = compiler.compile_all(self.css_out)
        slugs = [t.slug for t in manifest]
        assert slugs.count("dark") == 1
        assert "collides with built-in" in caplog.text

    def test_compile_all_real_designs(self):
        if not DESIGN_MD_DIR.exists():
            pytest.skip("design-md/ not found")
        compiler = ThemeCompiler(DESIGN_MD_DIR)
        manifest = compiler.compile_all(self.css_out)
        css_files = list(self.css_out.glob("*.css"))
        assert len(css_files) >= 13, f"Expected >=13 CSS files, got {len(css_files)}"
        assert len(manifest) >= 16, f"Expected >=16 manifest entries, got {len(manifest)}"
        manifest_data = json.loads(
            (self.css_out / "themes.json").read_text(encoding="utf-8")
        )
        assert len(manifest_data) >= 16
