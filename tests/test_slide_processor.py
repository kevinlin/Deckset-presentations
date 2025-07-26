"""
Unit tests for the SlideProcessor class.

Tests cover slide processing, column layout, background images, code blocks,
math formulas, and autoscaling functionality.
"""

import pytest
from unittest.mock import Mock, patch
from slide_processor import SlideProcessor
from models import (
    ProcessedSlide, ColumnContent, ProcessedImage, ProcessedCodeBlock, MathFormula,
    DecksetConfig, SlideConfig, SlideProcessingError, ImageModifiers
)


class TestSlideProcessor:
    """Test suite for SlideProcessor functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = SlideProcessor()
        self.config = DecksetConfig()
    
    def test_process_slide_basic(self):
        """Test basic slide processing without special features."""
        content = """
# Basic Slide
This is basic slide content.
        """
        
        with patch('deckset_parser.DecksetParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            mock_parser.parse_slide_commands.return_value = SlideConfig()
            mock_parser.process_speaker_notes.return_value = (content.strip(), "")
            mock_parser.process_footnotes.return_value = (content.strip(), {})
            mock_parser.process_fit_headers.return_value = content.strip()
            mock_parser.process_emoji_shortcodes.return_value = content.strip()
            
            slide = self.processor.process_slide(content, 0, self.config)
            
            assert isinstance(slide, ProcessedSlide)
            assert slide.index == 0
            assert "# Basic Slide" in slide.content
            assert slide.notes == ""
            assert len(slide.footnotes) == 0
            assert len(slide.columns) == 0
    
    def test_process_slide_with_speaker_notes(self):
        """Test slide processing with speaker notes."""
        content = """
# Slide with Notes
Main content here.
        """
        notes = "This is a speaker note"
        
        with patch('deckset_parser.DecksetParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            mock_parser.parse_slide_commands.return_value = SlideConfig()
            mock_parser.process_speaker_notes.return_value = (content.strip(), notes)
            mock_parser.process_footnotes.return_value = (content.strip(), {})
            mock_parser.process_fit_headers.return_value = content.strip()
            mock_parser.process_emoji_shortcodes.return_value = content.strip()
            
            slide = self.processor.process_slide(content, 1, self.config)
            
            assert slide.notes == notes
    
    def test_process_slide_with_footnotes(self):
        """Test slide processing with footnotes."""
        content = """
# Slide with Footnotes
Content with reference[^1].
        """
        footnotes = {"1": "This is a footnote"}
        
        with patch('deckset_parser.DecksetParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            mock_parser.parse_slide_commands.return_value = SlideConfig()
            mock_parser.process_speaker_notes.return_value = (content.strip(), "")
            mock_parser.process_footnotes.return_value = (content.strip(), footnotes)
            mock_parser.process_fit_headers.return_value = content.strip()
            mock_parser.process_emoji_shortcodes.return_value = content.strip()
            
            slide = self.processor.process_slide(content, 2, self.config)
            
            assert slide.footnotes == footnotes
    
    def test_process_slide_with_columns(self):
        """Test slide processing with column layout."""
        content = """
# Multi-Column Slide
First column content
[.column]
Second column content
        """
        
        with patch('deckset_parser.DecksetParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            slide_config = SlideConfig(columns=True)
            mock_parser.parse_slide_commands.return_value = slide_config
            mock_parser.process_speaker_notes.return_value = (content.strip(), "")
            mock_parser.process_footnotes.return_value = (content.strip(), {})
            mock_parser.process_fit_headers.return_value = content.strip()
            mock_parser.process_emoji_shortcodes.return_value = content.strip()
            
            slide = self.processor.process_slide(content, 3, self.config)
            
            assert slide.slide_config.columns is True
            assert len(slide.columns) > 0
    
    def test_process_slide_with_background_image(self):
        """Test slide processing with background image."""
        content = """
[.background-image: test-bg.jpg]
# Slide with Background
Content over background image.
        """
        
        with patch('deckset_parser.DecksetParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            mock_parser.parse_slide_commands.return_value = SlideConfig()
            mock_parser.process_speaker_notes.return_value = (content.strip(), "")
            mock_parser.process_footnotes.return_value = (content.strip(), {})
            mock_parser.process_fit_headers.return_value = content.strip()
            mock_parser.process_emoji_shortcodes.return_value = content.strip()
            
            slide = self.processor.process_slide(content, 4, self.config)
            
            assert slide.background_image is not None
            assert slide.background_image.src_path == "test-bg.jpg"
            assert slide.background_image.modifiers.placement == "background"
    
    def test_process_slide_with_autoscale(self):
        """Test slide processing with autoscale enabled."""
        content = "# Long Slide\n" + "Very long content. " * 100  # Make it long
        config = DecksetConfig(autoscale=True)
        
        with patch('deckset_parser.DecksetParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            mock_parser.parse_slide_commands.return_value = SlideConfig()
            mock_parser.process_speaker_notes.return_value = (content.strip(), "")
            mock_parser.process_footnotes.return_value = (content.strip(), {})
            # Mock these to return the input unchanged (preserving autoscale wrapper)
            mock_parser.process_fit_headers.side_effect = lambda x, config: x
            mock_parser.process_emoji_shortcodes.side_effect = lambda x: x
            
            slide = self.processor.process_slide(content, 5, config)
            
            # Should have autoscale applied due to long content
            assert 'autoscale-content' in slide.content
    
    def test_process_slide_error_handling(self):
        """Test error handling in slide processing."""
        content = "# Test Slide"
        
        with patch('deckset_parser.DecksetParser') as mock_parser_class:
            mock_parser_class.side_effect = Exception("Parser error")
            
            with pytest.raises(SlideProcessingError) as exc_info:
                self.processor.process_slide(content, 6, self.config)
            
            assert "Error processing slide 6" in str(exc_info.value)
            assert exc_info.value.slide_index == 6


class TestSlideProcessorColumns:
    """Test suite for column processing functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = SlideProcessor()
    
    def test_process_columns_basic(self):
        """Test basic column processing."""
        content = """
Header content
[.column]
First column content
[.column]
Second column content
        """
        
        columns = self.processor.process_columns(content)
        
        assert len(columns) == 2
        assert columns[0].index == 0
        assert columns[1].index == 1
        assert "First column content" in columns[0].content
        assert "Second column content" in columns[1].content
        # Header content should not be in any column
        for column in columns:
            assert "Header content" not in column.content
    
    def test_process_columns_equal_width(self):
        """Test column processing with equal width distribution."""
        content = """
[.column]
Column A
[.column]
Column B
        """
        
        columns = self.processor.process_columns(content)
        
        assert len(columns) == 2
        assert columns[0].width_percentage == 50.0
        assert columns[1].width_percentage == 50.0
    
    def test_process_columns_three_columns(self):
        """Test processing with three columns."""
        content = """
[.column]
First
[.column]
Second
[.column]
Third
        """
        
        columns = self.processor.process_columns(content)
        
        assert len(columns) == 3
        for column in columns:
            assert abs(column.width_percentage - 33.333333333333336) < 0.001
    
    def test_process_columns_empty_content(self):
        """Test column processing with empty content."""
        content = ""
        
        columns = self.processor.process_columns(content)
        
        assert len(columns) == 0
    
    def test_process_columns_no_column_markers(self):
        """Test content without column markers."""
        content = """
Single column content
No column markers here
        """
        
        columns = self.processor.process_columns(content)
        
        # With no column markers, no columns should be created
        assert len(columns) == 0
    
    def test_process_columns_clean_content(self):
        """Test that column markers are cleaned from content."""
        content = """
Header content
[.column]
First column content
[.column]
Second column content
        """
        
        columns = self.processor.process_columns(content)
        
        # Should have 2 columns
        assert len(columns) == 2
        # Column markers should be removed from content
        assert "[.column]" not in columns[0].content
        assert "[.column]" not in columns[1].content
        # Header content should not be in any column
        for column in columns:
            assert "Header content" not in column.content
    
    def test_process_columns_error_handling(self):
        """Test error handling in column processing."""
        # This should not raise an error, but handle gracefully
        content = "[.column]" * 1000  # Extreme case
        
        try:
            columns = self.processor.process_columns(content)
            # Should handle gracefully
            assert isinstance(columns, list)
        except SlideProcessingError:
            # This is also acceptable
            pass


class TestSlideProcessorBackgroundImage:
    """Test suite for background image processing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = SlideProcessor()
    
    def test_process_background_image_basic(self):
        """Test basic background image processing."""
        content = """
[.background-image: background.jpg]
# Slide Title
Content here
        """
        
        bg_image = self.processor.process_background_image(content)
        
        assert bg_image is not None
        assert bg_image.src_path == "background.jpg"
        assert bg_image.modifiers.placement == "background"
        assert bg_image.modifiers.scaling == "cover"
        assert bg_image.alt_text == "Background image"
    
    def test_process_background_image_with_spaces(self):
        """Test background image with spaces in filename."""
        content = """
[.background-image: my background image.jpg]
# Slide Title
        """
        
        bg_image = self.processor.process_background_image(content)
        
        assert bg_image is not None
        assert bg_image.src_path == "my background image.jpg"
    
    def test_process_background_image_none(self):
        """Test content without background image."""
        content = """
# Regular Slide
No background image here
        """
        
        bg_image = self.processor.process_background_image(content)
        
        assert bg_image is None
    
    def test_process_background_image_multiple(self):
        """Test content with multiple background image directives."""
        content = """
[.background-image: first.jpg]
[.background-image: second.jpg]
# Slide Title
        """
        
        bg_image = self.processor.process_background_image(content)
        
        # Should return the first match
        assert bg_image is not None
        assert bg_image.src_path == "first.jpg"
    
    def test_process_background_image_error_handling(self):
        """Test error handling in background image processing."""
        # This should handle gracefully even with malformed content
        content = "[.background-image: ]"  # Empty filename
        
        try:
            bg_image = self.processor.process_background_image(content)
            # Should handle gracefully, might return None or empty path
            assert bg_image is None or bg_image.src_path == ""
        except SlideProcessingError:
            # This is also acceptable
            pass


class TestSlideProcessorAutoscale:
    """Test suite for autoscale functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = SlideProcessor()
        self.config = DecksetConfig()
    
    def test_apply_autoscale_short_content(self):
        """Test autoscale with short content (should not trigger)."""
        content = "# Short Slide\nBrief content."
        
        processed = self.processor.apply_autoscale(content, self.config)
        
        assert processed == content  # Should be unchanged
        assert 'autoscale-content' not in processed
    
    def test_apply_autoscale_long_content(self):
        """Test autoscale with long content (should trigger)."""
        content = "# Long Slide\n" + "Very long content. " * 100
        
        processed = self.processor.apply_autoscale(content, self.config)
        
        assert 'autoscale-content' in processed
        assert '<div class="autoscale-content">' in processed
    
    def test_apply_autoscale_threshold(self):
        """Test autoscale threshold behavior."""
        # Content just under threshold
        short_content = "x" * (self.processor.content_length_threshold - 1)
        processed_short = self.processor.apply_autoscale(short_content, self.config)
        assert 'autoscale-content' not in processed_short
        
        # Content just over threshold
        long_content = "x" * (self.processor.content_length_threshold + 1)
        processed_long = self.processor.apply_autoscale(long_content, self.config)
        assert 'autoscale-content' in processed_long
    
    def test_apply_autoscale_error_handling(self):
        """Test error handling in autoscale processing."""
        content = "# Test Content"
        
        try:
            processed = self.processor.apply_autoscale(content, self.config)
            assert isinstance(processed, str)
        except SlideProcessingError:
            # Should not happen with normal content, but acceptable if it does
            pass


class TestSlideProcessorHelperMethods:
    """Test suite for helper methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = SlideProcessor()
    
    def test_parse_highlight_lines_single(self):
        """Test parsing single line highlight."""
        lines = self.processor._parse_highlight_lines("5")
        assert lines == [5]
    
    def test_parse_highlight_lines_range(self):
        """Test parsing line range highlight."""
        lines = self.processor._parse_highlight_lines("2-5")
        assert lines == [2, 3, 4, 5]
    
    def test_parse_highlight_lines_multiple(self):
        """Test parsing multiple line highlights."""
        lines = self.processor._parse_highlight_lines("1,3,5")
        assert set(lines) == {1, 3, 5}
    
    def test_parse_highlight_lines_mixed(self):
        """Test parsing mixed line highlights."""
        lines = self.processor._parse_highlight_lines("1,3-5,8")
        assert set(lines) == {1, 3, 4, 5, 8}
    
    def test_parse_highlight_lines_all(self):
        """Test parsing 'all' directive."""
        lines = self.processor._parse_highlight_lines("all")
        assert lines == [-1]  # Special value for all lines
    
    def test_parse_highlight_lines_none(self):
        """Test parsing 'none' directive."""
        lines = self.processor._parse_highlight_lines("none")
        assert lines == []
    
    def test_estimate_content_overflow_short(self):
        """Test overflow estimation with short content."""
        content = "# Short slide\nBrief content."
        overflow = self.processor._estimate_content_overflow(content)
        assert overflow is False
    
    def test_estimate_content_overflow_long_lines(self):
        """Test overflow estimation with long lines."""
        content = "# Slide\n" + "x" * 100 + "\n" + "y" * 100
        overflow = self.processor._estimate_content_overflow(content)
        # With 2 long lines (>80 chars), score = 2*2 + 3*0.5 + 0*10 = 5.5, which is < 50
        # Let's make it longer to trigger overflow
        long_content = "# Slide\n" + ("x" * 100 + "\n") * 30  # 30 long lines
        overflow = self.processor._estimate_content_overflow(long_content)
        assert overflow is True
    
    def test_estimate_content_overflow_many_lines(self):
        """Test overflow estimation with many lines."""
        content = "# Slide\n" + "\n".join([f"Line {i}" for i in range(100)])
        overflow = self.processor._estimate_content_overflow(content)
        assert overflow is True
    
    def test_estimate_content_overflow_code_blocks(self):
        """Test overflow estimation with code blocks."""
        content = """
# Slide
```python
code block 1
```
```javascript
code block 2
```
```java
code block 3
```
```cpp
code block 4
```
```go
code block 5
```
```rust
code block 6
```
        """
        overflow = self.processor._estimate_content_overflow(content)
        # With 6 code blocks, score = 0*2 + lines*0.5 + 6*10 = 60+ which is > 50
        assert overflow is True


if __name__ == "__main__":
    pytest.main([__file__])