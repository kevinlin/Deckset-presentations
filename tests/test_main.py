"""Tests for CLI argument parsing, --validate, and graceful degradation."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from main import DecksetWebsiteGenerator, main
from models import GeneratorConfig, PresentationInfo


class TestValidateConfiguration:
    """Tests for DecksetWebsiteGenerator.validate_configuration."""

    def test_validate_passes_with_real_templates(self):
        generator = DecksetWebsiteGenerator()
        issues = generator.validate_configuration()
        assert issues == [], f"Unexpected validation issues: {issues}"

    def test_validate_fails_missing_template(self, tmp_path):
        tpl_dir = tmp_path / "templates"
        tpl_dir.mkdir()
        (tpl_dir / "homepage.html").write_text("", encoding="utf-8")
        (tpl_dir / "presentation.html").write_text("", encoding="utf-8")
        # slide.html is deliberately missing

        config = GeneratorConfig(template_dir=str(tpl_dir))
        generator = DecksetWebsiteGenerator(config)
        issues = generator.validate_configuration()

        assert any("slide.html" in i for i in issues)

    def test_validate_fails_missing_asset(self, tmp_path):
        """slide_styles.css and other assets must be checked."""
        tpl_dir = tmp_path / "templates"
        tpl_dir.mkdir()
        for name in ("homepage.html", "presentation.html", "slide.html"):
            (tpl_dir / name).write_text("", encoding="utf-8")
        # no slide_styles.css

        config = GeneratorConfig(template_dir=str(tpl_dir))
        generator = DecksetWebsiteGenerator(config)
        issues = generator.validate_configuration()

        assert any("slide_styles.css" in i for i in issues)

    def test_validate_nonexistent_template_dir(self, tmp_path):
        config = GeneratorConfig(template_dir=str(tmp_path / "nope"))
        generator = DecksetWebsiteGenerator(config)
        issues = generator.validate_configuration()

        assert any("does not exist" in i for i in issues)


class TestGracefulDegradation:
    """One failing deck must not kill the build."""

    def test_failing_deck_is_logged_and_skipped(self, tmp_path):
        root = tmp_path / "repo"
        root.mkdir()

        good_dir = root / "good-deck"
        good_dir.mkdir()
        (good_dir / "good-deck.md").write_text("# Hello\n", encoding="utf-8")

        bad_dir = root / "bad-deck"
        bad_dir.mkdir()
        (bad_dir / "bad-deck.md").write_text("# Bad\n", encoding="utf-8")

        output = tmp_path / "site"
        config = GeneratorConfig(output_dir=str(output))
        generator = DecksetWebsiteGenerator(config)

        original_process = generator.processor.process_presentation

        def mock_process(info):
            if "bad-deck" in info.folder_name:
                raise RuntimeError("Simulated failure")
            return original_process(info)

        with patch.object(
            generator.processor, "process_presentation", side_effect=mock_process
        ):
            result = generator.generate_website(str(root), str(output))

        assert result["success"] is True
        assert result["presentations_failed"] >= 1
        assert result["presentations_processed"] >= 1


class TestCLIArgParsing:
    """Verify the argparse setup in main()."""

    def test_default_args(self):
        with patch("sys.argv", ["main.py"]):
            with patch.object(
                DecksetWebsiteGenerator, "generate_website", return_value={"success": True}
            ) as mock_gen:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0
                mock_gen.assert_called_once()

    def test_validate_flag_exits_zero(self):
        with patch("sys.argv", ["main.py", "--validate"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_validate_flag_exits_nonzero_on_bad_config(self, tmp_path):
        with patch(
            "sys.argv", ["main.py", "--validate", "--root", str(tmp_path)]
        ):
            with patch.object(
                DecksetWebsiteGenerator,
                "validate_configuration",
                return_value=["missing template"],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1
