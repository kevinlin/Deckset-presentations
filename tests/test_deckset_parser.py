"""
Unit tests for the DecksetParser class.

Tests cover global command parsing, slide command parsing, and all core functionality
required for Deckset markdown compatibility.
"""

import pytest
from deckset_parser import DecksetParser, DecksetConfig, SlideConfig
from models import DecksetParsingError, GeneratorError


class TestDecksetParser:
    """Test suite for DecksetParser functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = DecksetParser()
    
    def test_parse_global_commands_basic(self):
        """Test parsing of basic global commands."""
        content = """
theme: Zurich
autoscale: true
slidenumbers: false
footer: My Presentation Footer
        """
        
        config = self.parser.parse_global_commands(content)
        
        assert config.theme == "Zurich"
        assert config.autoscale is True
        assert config.slide_numbers is False
        assert config.footer == "My Presentation Footer"
    
    def test_parse_global_commands_boolean_variations(self):
        """Test parsing of boolean values with different formats."""
        test_cases = [
            ("autoscale: true", True),
            ("autoscale: yes", True),
            ("autoscale: on", True),
            ("autoscale: 1", True),
            ("autoscale: false", False),
            ("autoscale: no", False),
            ("autoscale: off", False),
            ("autoscale: 0", False),
        ]
        
        for content, expected in test_cases:
            config = self.parser.parse_global_commands(content)
            assert config.autoscale == expected, f"Failed for content: {content}"
    
    def test_parse_global_commands_list_values(self):
        """Test parsing of list-type global commands."""
        content = """
fit-headers: #, ##, ###
slide-dividers: #, ##
        """
        
        config = self.parser.parse_global_commands(content)
        
        assert config.fit_headers == ["#", "##", "###"]
        assert config.slide_dividers == ["#", "##"]
    
    def test_parse_global_commands_case_insensitive(self):
        """Test that global command parsing is case insensitive."""
        content = """
THEME: Zurich
AutoScale: TRUE
SlideNumbers: FALSE
        """
        
        config = self.parser.parse_global_commands(content)
        
        assert config.theme == "Zurich"
        assert config.autoscale is True
        assert config.slide_numbers is False
    
    def test_parse_global_commands_empty_content(self):
        """Test parsing with empty content."""
        config = self.parser.parse_global_commands("")
        
        # Should return default config
        assert config.theme is None
        assert config.autoscale is False
        assert config.slide_numbers is False
        assert config.footer is None
    
    def test_parse_slide_commands_basic(self):
        """Test parsing of basic slide commands."""
        content = """
# My Slide Title

[.column]
Some content here

[.background-image: background.jpg]
        """
        
        config = self.parser.parse_slide_commands(content)
        
        assert config.columns is True
        assert config.background_image == "background.jpg"
    
    def test_parse_slide_commands_boolean_flags(self):
        """Test parsing of boolean flag slide commands."""
        content = """
[.hide-footer]
[.hide-slide-numbers]
[.autoscale: true]
        """
        
        config = self.parser.parse_slide_commands(content)
        
        assert config.hide_footer is True
        assert config.hide_slide_numbers is True
        assert config.autoscale is True
    
    def test_parse_slide_commands_case_insensitive(self):
        """Test that slide command parsing is case insensitive."""
        content = """
[.COLUMN]
[.BACKGROUND-IMAGE: test.jpg]
[.HIDE-FOOTER]
        """
        
        config = self.parser.parse_slide_commands(content)
        
        assert config.columns is True
        assert config.background_image == "test.jpg"
        assert config.hide_footer is True

    def test_parse_slide_footer_override(self):
        content = "[.footer: **Custom** footer text]\nSome content"
        config = self.parser.parse_slide_commands(content)
        assert config.footer == "**Custom** footer text"

    def test_parse_slide_footer_empty(self):
        content = "[.footer:]\nSome content"
        config = self.parser.parse_slide_commands(content)
        assert config.footer == ""

    def test_slidenumbers_false_hides(self):
        content = "[.slidenumbers: false]\nContent"
        config = self.parser.parse_slide_commands(content)
        assert config.hide_slide_numbers is True

    def test_slidenumbers_false_case_insensitive(self):
        content = "[.SLIDENUMBERS: false]\nContent"
        config = self.parser.parse_slide_commands(content)
        assert config.hide_slide_numbers is True

    def test_extract_slide_separators_standard(self):
        """Test extraction of slides using standard --- separators."""
        content = """
# Slide 1
Content for slide 1

---

# Slide 2
Content for slide 2

---

# Slide 3
Content for slide 3
        """
        
        slides = self.parser.extract_slide_separators(content)
        
        assert len(slides) == 3
        assert "# Slide 1" in slides[0]
        assert "# Slide 2" in slides[1]
        assert "# Slide 3" in slides[2]
    
    def test_extract_slide_separators_multiple_dashes(self):
        """Test extraction with multiple dash separators."""
        content = """
# Slide 1
Content

----

# Slide 2
Content
        """
        
        slides = self.parser.extract_slide_separators(content)
        
        assert len(slides) == 2
        assert "# Slide 1" in slides[0]
        assert "# Slide 2" in slides[1]
    
    def test_extract_slide_separators_no_separators(self):
        """Test extraction when no separators are present."""
        content = """
# Single Slide
This is all one slide
        """
        
        slides = self.parser.extract_slide_separators(content)
        
        assert len(slides) == 1
        assert "# Single Slide" in slides[0]
    
    def test_detect_auto_slide_breaks_header_dividers(self):
        """Test auto slide breaks based on header levels."""
        content = """
# Introduction
Some intro content

## Section 1
Content for section 1

### Subsection
More content

## Section 2
Content for section 2
        """
        
        config = DecksetConfig(slide_dividers=["#", "##"])
        slides = self.parser.detect_auto_slide_breaks(content, config)
        
        # Should break at # and ## headers
        assert len(slides) >= 3  # At least intro, section 1, section 2
        assert "# Introduction" in slides[0]
        assert "## Section 1" in slides[1]
        assert "## Section 2" in slides[2]
    
    def test_detect_auto_slide_breaks_no_dividers(self):
        """Test auto slide breaks with no dividers configured."""
        content = """
# Slide 1
Content

---

# Slide 2
Content
        """
        
        config = DecksetConfig()  # No slide_dividers
        slides = self.parser.detect_auto_slide_breaks(content, config)
        
        # Should fall back to regular separator extraction
        assert len(slides) == 2
    
    def test_process_speaker_notes_basic(self):
        """Test extraction of basic speaker notes."""
        content = """
# Slide Title
Main slide content

^ This is a speaker note
^ Another speaker note
        """
        
        cleaned_content, notes_html = self.parser.process_speaker_notes(content)
        
        assert "^ This is a speaker note" not in cleaned_content
        assert "# Slide Title" in cleaned_content
        assert "Main slide content" in cleaned_content
        assert "This is a speaker note" in notes_html
        assert "Another speaker note" in notes_html
    
    def test_process_speaker_notes_variations(self):
        """Test speaker notes with different formats."""
        content = """
# Slide Title
Content

^Standard note
^ Note with space
  ^ Note with leading spaces
        """
        
        cleaned_content, notes_html = self.parser.process_speaker_notes(content)
        
        assert "^Standard note" not in cleaned_content
        assert "Standard note" in notes_html
        assert "Note with space" in notes_html
        assert "Note with leading spaces" in notes_html
    
    def test_process_footnotes_basic(self):
        """Test processing of footnotes."""
        content = """
# Slide Title
This has a footnote[^1] and another[^2].

[^1]: First footnote definition
[^2]: Second footnote definition
        """
        
        cleaned_content, footnotes = self.parser.process_footnotes(content)
        
        assert "[^1]: First footnote definition" not in cleaned_content
        assert "[^2]: Second footnote definition" not in cleaned_content
        assert "This has a footnote[^1]" in cleaned_content
        assert footnotes["1"] == "First footnote definition"
        assert footnotes["2"] == "Second footnote definition"
    
    def test_process_footnotes_missing_definitions(self):
        """Test footnotes with missing definitions."""
        content = """
This has a footnote[^1] with no definition.
        """
        
        cleaned_content, footnotes = self.parser.process_footnotes(content)
        
        assert "This has a footnote[^1]" in cleaned_content
        assert len(footnotes) == 0
    
    def test_process_fit_headers_basic(self):
        """Test processing of [fit] headers."""
        content = """
# [fit] Large Title
## [fit] Subtitle
### Normal Header
        """
        
        config = DecksetConfig()
        processed = self.parser.process_fit_headers(content, config)
        
        assert '[fit]' not in processed
        assert '{.fit}' in processed
        assert '# Large Title {.fit}' in processed
        assert '## Subtitle {.fit}' in processed
        assert '### Normal Header' in processed  # Unchanged
    
    def test_process_fit_headers_global_config(self):
        """Test processing of global fit-headers configuration."""
        content = """
# Title One
## Subtitle One
### Section Header
## Subtitle Two
        """
        
        config = DecksetConfig(fit_headers=["#", "##"])
        processed = self.parser.process_fit_headers(content, config)
        
        # All H1 and H2 headers should have fit markers
        assert '# Title One {.fit}' in processed
        assert '## Subtitle One {.fit}' in processed
        assert '## Subtitle Two {.fit}' in processed
        # H3 should not have fit marker
        assert '### Section Header' in processed
        assert '### Section Header {.fit}' not in processed
    
    def test_process_fit_headers_mixed_explicit_and_global(self):
        """Test processing with both explicit [fit] and global fit-headers."""
        content = """
# [fit] Explicit Fit Title
## Regular Subtitle
### [fit] Explicit Fit Section
        """
        
        config = DecksetConfig(fit_headers=["##"])
        processed = self.parser.process_fit_headers(content, config)
        
        # Explicit fit should work
        assert '# Explicit Fit Title {.fit}' in processed
        # Global config should apply to H2
        assert '## Regular Subtitle {.fit}' in processed
        # Explicit fit on H3 should work even though H3 not in global config
        assert '### Explicit Fit Section {.fit}' in processed
    
    def test_process_emoji_shortcodes_basic(self):
        """Test conversion of emoji shortcodes."""
        content = """
# Great Presentation :smile:
This is :fire: content!
:thumbs_up: for the audience
        """
        
        processed = self.parser.process_emoji_shortcodes(content)
        
        assert ':smile:' not in processed
        assert ':fire:' not in processed
        assert ':thumbs_up:' not in processed
        assert '😄' in processed
        assert '🔥' in processed
        assert '👍' in processed
    
    def test_process_emoji_shortcodes_unknown(self):
        """Test handling of unknown emoji shortcodes."""
        content = """
Unknown emoji :unknown_emoji: should remain unchanged.
        """
        
        processed = self.parser.process_emoji_shortcodes(content)
        
        assert ':unknown_emoji:' in processed  # Should remain unchanged
    
    def test_complex_integration(self):
        """Test integration of multiple parsing features."""
        content = """
theme: Zurich
autoscale: true
slidenumbers: true
footer: Test Footer

# [fit] Welcome :smile:
This is the introduction slide.

^ Speaker note for intro

---

[.column]
## Column 1
Content with footnote[^1]

[.column]
## Column 2
More content :fire:

[^1]: This is a footnote

---

[.background-image: final.jpg]
# Thank You!
Final slide content

^ Final speaker note
        """
        
        # Test global commands
        global_config = self.parser.parse_global_commands(content)
        assert global_config.theme == "Zurich"
        assert global_config.autoscale is True
        assert global_config.slide_numbers is True
        assert global_config.footer == "Test Footer"
        
        # Test slide extraction
        slides = self.parser.extract_slide_separators(content)
        assert len(slides) == 3
        
        # Test slide commands on second slide
        slide_config = self.parser.parse_slide_commands(slides[1])
        assert slide_config.columns is True
        
        # Test slide commands on third slide
        slide_config = self.parser.parse_slide_commands(slides[2])
        assert slide_config.background_image == "final.jpg"
        
        # Test speaker notes
        cleaned_content, notes = self.parser.process_speaker_notes(slides[0])
        assert "Speaker note for intro" in notes
        
        # Test footnotes
        cleaned_content, footnotes = self.parser.process_footnotes(slides[1])
        assert footnotes.get("1") == "This is a footnote"
        
        # Test fit headers and emojis
        processed = self.parser.process_fit_headers(slides[0], global_config)
        processed = self.parser.process_emoji_shortcodes(processed)
        assert '{.fit}' in processed
        assert '😄' in processed


class TestHtmlCommentStripping:
    """Tests for stripping <!-- … --> blocks before slide splitting."""

    def setup_method(self):
        self.parser = DecksetParser()

    def test_hidden_slide_removed(self):
        """A slide consisting only of a comment should vanish."""
        md = "# Slide 1\n\n---\n\n<!-- hidden slide -->\n\n---\n\n# Slide 3"
        slides = self.parser.extract_slide_separators(md)
        texts = [s.strip() for s in slides]
        assert "# Slide 1" in texts
        assert "# Slide 3" in texts
        assert not any("hidden" in s for s in texts)

    def test_inline_comment_stripped(self):
        """Comments within a slide should be stripped."""
        md = "# Title\n\nVisible <!-- secret --> content"
        slides = self.parser.extract_slide_separators(md)
        assert "secret" not in slides[0]
        assert "Visible" in slides[0]

    def test_multiline_comment_stripped(self):
        md = "# Title\n\n<!--\nmulti\nline\n-->\n\nContent"
        slides = self.parser.extract_slide_separators(md)
        assert "multi" not in slides[0]
        assert "Content" in slides[0]


class TestSlideDividerComposition:
    """Tests for slide-dividers composing with --- separators."""

    def setup_method(self):
        self.parser = DecksetParser()

    def test_both_separators_used(self):
        """A file using both --- and header-based dividers should split correctly."""
        md = (
            "# First\n\nContent one\n\n"
            "---\n\n"
            "Content two\n\n"
            "# Third\n\nContent three"
        )
        config = DecksetConfig(slide_dividers=["#"])
        slides = self.parser.detect_auto_slide_breaks(md, config)
        assert len(slides) == 3

    def test_divider_only(self):
        """slide-dividers without --- should still work."""
        md = "# One\n\nText\n\n# Two\n\nMore text"
        config = DecksetConfig(slide_dividers=["#"])
        slides = self.parser.detect_auto_slide_breaks(md, config)
        assert len(slides) == 2


class TestMultiLineSpeakerNotes:
    """Tests for multi-line speaker notes (^ continues until blank line)."""

    def setup_method(self):
        self.parser = DecksetParser()

    def test_single_line_note(self):
        content = "# Title\n\n^ A single-line note"
        cleaned, notes = self.parser.process_speaker_notes(content)
        assert "single-line" in notes
        assert "^" not in cleaned

    def test_multiline_note(self):
        """^ starts a note that continues until a blank line."""
        content = "# Title\n\n^ First line of note\nSecond line of note\nThird line\n\nVisible content"
        cleaned, notes = self.parser.process_speaker_notes(content)
        assert "First line" in notes
        assert "Second line" in notes
        assert "Third line" in notes
        assert "Visible content" in cleaned
        assert "First line" not in cleaned

    def test_two_note_blocks(self):
        """Two separate ^ blocks should be collected together."""
        content = "# Title\n\n^ Note A\n\nVisible\n\n^ Note B"
        cleaned, notes = self.parser.process_speaker_notes(content)
        assert "Note A" in notes
        assert "Note B" in notes
        assert "Visible" in cleaned


class TestDecksetParsingError:
    """Test suite for DecksetParsingError exception."""

    def test_error_with_line_number_and_context(self):
        """Test error creation with line number and context."""
        error = DecksetParsingError("Test error", line_number=42, context={"source": "test"})

        assert error.message == "Test error"
        assert error.line_number == 42
        assert error.context["line_number"] == 42
        assert error.context["source"] == "test"

    def test_error_minimal(self):
        """Test error creation with minimal information."""
        error = DecksetParsingError("Simple error")

        assert error.message == "Simple error"
        assert error.line_number is None
        assert error.context == {}

    def test_inherits_from_generator_error(self):
        """DecksetParsingError must be catchable as GeneratorError."""
        error = DecksetParsingError("parse fail", line_number=10)
        assert isinstance(error, GeneratorError)

        with pytest.raises(GeneratorError):
            raise error

    def test_parser_raises_catchable_as_generator_error(self):
        """A real parser failure should be catchable via GeneratorError."""
        parser = DecksetParser()
        try:
            parser.extract_slide_separators(None)
        except GeneratorError:
            pass
        except Exception:
            pytest.fail("Parser should raise a GeneratorError subclass")


class TestFootnoteResolution:
    """Tests for cross-slide footnote resolution in EnhancedPresentationProcessor."""

    def _make_slides(self, *contents_and_footnotes):
        """Build a list of ProcessedSlide objects for testing.

        Each argument is a ``(content, footnotes_dict)`` tuple.
        """
        from models import ProcessedSlide
        slides = []
        for idx, (content, fns) in enumerate(contents_and_footnotes, start=1):
            slides.append(ProcessedSlide(index=idx, content=content, footnotes=fns))
        return slides

    def setup_method(self):
        from enhanced_processor import EnhancedPresentationProcessor
        self.processor = EnhancedPresentationProcessor()

    def test_per_slide_namespacing(self):
        """Footnote keys are namespaced per slide."""
        slides = self._make_slides(
            ("Text[^1] here.", {"1": "First footnote"}),
        )
        self.processor._resolve_footnotes(slides)

        assert "fn-slide1-1" in slides[0].footnotes
        assert slides[0].footnotes["fn-slide1-1"] == "First footnote"

    def test_refs_become_superscript_links(self):
        """[^1] references are replaced with <sup><a> links."""
        slides = self._make_slides(
            ("Text[^1] more.", {"1": "A note"}),
        )
        self.processor._resolve_footnotes(slides)

        assert '<sup><a href="#fn-slide1-1">1</a></sup>' in slides[0].content
        assert "[^1]" not in slides[0].content

    def test_cross_slide_resolution(self):
        """A definition on slide 1 satisfies a reference on slide 2."""
        slides = self._make_slides(
            ("Defined here.\n\n[^1]: Global def", {"1": "Global def"}),
            ("Ref here[^1].", {}),
        )
        self.processor._resolve_footnotes(slides)

        assert "fn-slide2-1" in slides[1].footnotes
        assert slides[1].footnotes["fn-slide2-1"] == "Global def"

    def test_duplicate_footnote_warns(self, caplog):
        """Duplicate footnote IDs log a warning; first definition wins."""
        import logging
        slides = self._make_slides(
            ("Slide one[^x].", {"x": "first def"}),
            ("Slide two[^x].", {"x": "second def"}),
        )
        with caplog.at_level(logging.WARNING, logger="enhanced_processor"):
            pool = self.processor._resolve_footnotes(slides)

        assert pool["x"] == "first def"
        assert any("Duplicate footnote [^x]" in r.message for r in caplog.records)

    def test_missing_ref_warns(self, caplog):
        """A reference with no definition anywhere logs a warning."""
        import logging
        slides = self._make_slides(
            ("Ref[^missing] here.", {}),
        )
        with caplog.at_level(logging.WARNING, logger="enhanced_processor"):
            self.processor._resolve_footnotes(slides)

        assert any("has no definition" in r.message for r in caplog.records)
        assert slides[0].footnotes == {}

    def test_global_pool_returned(self):
        """_resolve_footnotes returns the full global pool (unnamespaced)."""
        slides = self._make_slides(
            ("A[^a].", {"a": "alpha"}),
            ("B[^b].", {"b": "beta"}),
        )
        pool = self.processor._resolve_footnotes(slides)

        assert pool == {"a": "alpha", "b": "beta"}


if __name__ == "__main__":
    pytest.main([__file__])