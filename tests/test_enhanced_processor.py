"""Tests for the EnhancedPresentationProcessor orchestration.

Covers: each processor invoked once, body_html populated, error paths degrade
gracefully rather than crashing.
"""

import tempfile
from pathlib import Path

import pytest
from models import PresentationInfo, ProcessedSlide


@pytest.fixture
def processor():
    from enhanced_processor import EnhancedPresentationProcessor
    return EnhancedPresentationProcessor()


def _write_deck(tmp_path: Path, md: str) -> PresentationInfo:
    """Write markdown to a temp file and return PresentationInfo pointing at it."""
    md_file = tmp_path / "deck.md"
    md_file.write_text(md, encoding="utf-8")
    return PresentationInfo(
        title="test",
        folder_name="test",
        folder_path=str(tmp_path),
        markdown_path=str(md_file),
    )


class TestOrchestration:
    def test_body_html_populated(self, processor, tmp_path):
        """Each slide should have body_html set after processing."""
        info = _write_deck(tmp_path, "# Title\n\nHello **world**\n\n---\n\n# Slide 2\n\n- item")
        result = processor.process_presentation(info)

        assert len(result.slides) == 2
        assert "<h1>" in result.slides[0].body_html
        assert "<strong>world</strong>" in result.slides[0].body_html
        assert "<ul>" in result.slides[1].body_html or "<li>" in result.slides[1].body_html

    def test_math_processed_once(self, processor, tmp_path):
        """Math delimiters are converted exactly once by math_processor."""
        info = _write_deck(tmp_path, "Inline $E=mc^2$ here")
        result = processor.process_presentation(info)
        slide = result.slides[0]

        assert "\\(E=mc^2\\)" in slide.content
        assert "\\(E=mc^2\\)" in slide.body_html

    def test_emoji_resolved(self, processor, tmp_path):
        info = _write_deck(tmp_path, "Hello :heart:")
        result = processor.process_presentation(info)

        assert ":heart:" not in result.slides[0].content

    def test_footnotes_resolved_across_slides(self, processor, tmp_path):
        md = "Ref[^1] here.\n\n[^1]: Definition\n\n---\n\nAnother ref[^1]."
        info = _write_deck(tmp_path, md)
        result = processor.process_presentation(info)

        assert "fn-slide1-1" in result.slides[0].footnotes
        assert "fn-slide2-1" in result.slides[1].footnotes

    def test_graceful_degradation_on_bad_slide(self, processor, tmp_path):
        """A badly formed slide should not crash the entire presentation."""
        info = _write_deck(tmp_path, "# OK slide\n\n---\n\n![bad](missing.xyz)")
        result = processor.process_presentation(info)

        assert len(result.slides) >= 1


class TestErrorPaths:
    def test_missing_file_raises(self, processor):
        info = PresentationInfo(
            title="ghost",
            folder_name="ghost",
            folder_path="/nonexistent",
            markdown_path="/nonexistent/ghost.md",
        )
        from models import PresentationProcessingError
        with pytest.raises(PresentationProcessingError):
            processor.process_presentation(info)
