"""
Unit tests for the DecksetParser class.

Tests cover global command parsing, slide command parsing, and all core functionality
required for Deckset markdown compatibility.
"""

import pytest
from deckset_parser import DecksetParser, DecksetConfig, SlideConfig, DecksetParsingError


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
        assert 'class="fit-text"' in processed
        assert '# <span class="fit-text">Large Title</span>' in processed
        assert '## <span class="fit-text">Subtitle</span>' in processed
        assert '### Normal Header' in processed  # Unchanged
    
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
        assert '😊' in processed
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
        assert 'class="fit-text"' in processed
        assert '😊' in processed


class TestDecksetParsingError:
    """Test suite for DecksetParsingError exception."""
    
    def test_error_with_line_number_and_context(self):
        """Test error creation with line number and context."""
        error = DecksetParsingError("Test error", line_number=42, context="test context")
        
        assert str(error) == "Test error"
        assert error.line_number == 42
        assert error.context == "test context"
    
    def test_error_minimal(self):
        """Test error creation with minimal information."""
        error = DecksetParsingError("Simple error")
        
        assert str(error) == "Simple error"
        assert error.line_number is None
        assert error.context is None


if __name__ == "__main__":
    pytest.main([__file__])