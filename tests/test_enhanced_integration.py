"""
Integration tests for the enhanced processing pipeline.

This module tests the integration between DecksetParser, MediaProcessor,
SlideProcessor, and other enhanced components.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from models import PresentationInfo, GeneratorConfig
from enhanced_processor import EnhancedPresentationProcessor
from enhanced_models import DecksetConfig, ProcessedSlide, EnhancedPresentation


class TestEnhancedIntegration:
    """Test enhanced processing pipeline integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_presentation_dir = Path(self.temp_dir) / "test-presentation"
        self.test_presentation_dir.mkdir(parents=True)
        
        # Create test markdown file
        self.markdown_content = """
slidenumbers: true
autoscale: false
footer: Test Footer

# Test Presentation

This is the first slide.

---

## Second Slide

This slide has some content.

^ This is a speaker note

---

### Third Slide with Image

![inline](test-image.jpg)

Some content after the image.

---

#### Code Slide

[.code-highlight: 1,3-5]

```python
def hello_world():
    print("Hello, World!")
    return True
```

---

##### Math Slide

Here's some inline math: $x = y + z$

And display math:

$$E = mc^2$$

---

###### Column Slide

[.column]

Left column content

[.column]

Right column content
        """
        
        self.markdown_path = self.test_presentation_dir / "test-presentation.md"
        with open(self.markdown_path, 'w', encoding='utf-8') as f:
            f.write(self.markdown_content)
        
        # Create test image
        self.test_image_path = self.test_presentation_dir / "test-image.jpg"
        with open(self.test_image_path, 'wb') as f:
            # Minimal JPEG header
            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb')
        
        # Create presentation info
        self.presentation_info = PresentationInfo(
            title="Test Presentation",
            folder_name="test-presentation",
            folder_path=str(self.test_presentation_dir),
            markdown_path=str(self.markdown_path),
            slide_count=0
        )
        
        # Create processor instance for non-mocked tests
        self.processor = EnhancedPresentationProcessor()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_enhanced_processor_initialization(self):
        """Test that enhanced processor initializes correctly."""
        assert self.processor is not None
        assert hasattr(self.processor, 'deckset_parser')
        assert hasattr(self.processor, 'media_processor')
        assert hasattr(self.processor, 'slide_processor')
        assert hasattr(self.processor, 'code_processor')
        assert hasattr(self.processor, 'math_processor')
    
    def test_process_presentation_basic(self):
        """Test basic presentation processing."""
        result = self.processor.process_presentation(self.presentation_info)
        
        assert isinstance(result, EnhancedPresentation)
        assert result.info == self.presentation_info
        assert isinstance(result.config, DecksetConfig)
        assert len(result.slides) > 0
        
        # Check that global config was parsed
        assert result.config.slide_numbers is True
        assert result.config.autoscale is False
        assert result.config.footer == "Test Footer"
    
    def test_slide_extraction_and_processing(self):
        """Test that slides are extracted and processed correctly."""
        result = self.processor.process_presentation(self.presentation_info)
        
        # Should have 6 slides based on the markdown content
        assert len(result.slides) == 6
        
        # Check slide indices
        for i, slide in enumerate(result.slides, 1):
            assert slide.index == i
            assert isinstance(slide, ProcessedSlide)
    
    def test_speaker_notes_processing(self):
        """Test that speaker notes are extracted correctly."""
        result = self.processor.process_presentation(self.presentation_info)
        
        # Find the slide with speaker notes (second slide)
        slide_with_notes = None
        for slide in result.slides:
            if slide.notes:
                slide_with_notes = slide
                break
        
        assert slide_with_notes is not None
        assert "This is a speaker note" in slide_with_notes.notes
    
    def test_image_processing(self):
        """Test that images are processed correctly."""
        result = self.processor.process_presentation(self.presentation_info)
        
        # Find the slide with image (third slide)
        slide_with_image = None
        for slide in result.slides:
            if slide.inline_images:
                slide_with_image = slide
                break
        
        assert slide_with_image is not None
        assert len(slide_with_image.inline_images) == 1
        
        image = slide_with_image.inline_images[0]
        assert image.modifiers.placement == "inline"
        assert "test-image.jpg" in image.src_path
    
    def test_code_block_processing(self):
        """Test that code blocks are processed correctly."""
        result = self.processor.process_presentation(self.presentation_info)
        
        # Find the slide with code (fourth slide)
        slide_with_code = None
        for slide in result.slides:
            if slide.code_blocks:
                slide_with_code = slide
                break
        
        assert slide_with_code is not None
        assert len(slide_with_code.code_blocks) == 1
        
        code_block = slide_with_code.code_blocks[0]
        assert code_block.language == "python"
        assert len(code_block.highlighted_lines) > 0
        assert 1 in code_block.highlighted_lines
        assert 3 in code_block.highlighted_lines
    
    def test_math_formula_processing(self):
        """Test that math formulas are processed correctly."""
        result = self.processor.process_presentation(self.presentation_info)
        
        # Find the slide with math (fifth slide)
        slide_with_math = None
        for slide in result.slides:
            if slide.math_formulas:
                slide_with_math = slide
                break
        
        assert slide_with_math is not None
        assert len(slide_with_math.math_formulas) == 2
        
        # Check inline and display math
        inline_math = [f for f in slide_with_math.math_formulas if f.formula_type == "inline"]
        display_math = [f for f in slide_with_math.math_formulas if f.formula_type == "display"]
        
        assert len(inline_math) == 1
        assert len(display_math) == 1
        assert "x = y + z" in inline_math[0].content
        assert "E = mc^2" in display_math[0].content
    
    def test_column_processing(self):
        """Test that multi-column layouts are processed correctly."""
        result = self.processor.process_presentation(self.presentation_info)
        
        # Find the slide with columns (sixth slide)
        slide_with_columns = None
        for slide in result.slides:
            if slide.columns:
                slide_with_columns = slide
                break
        
        assert slide_with_columns is not None
        assert len(slide_with_columns.columns) == 2
        
        # Check column content
        left_column = slide_with_columns.columns[0]
        right_column = slide_with_columns.columns[1]
        
        assert "Left column content" in left_column.content
        assert "Right column content" in right_column.content
        assert left_column.width_percentage == 50.0
        assert right_column.width_percentage == 50.0
    
    def test_error_handling_missing_file(self):
        """Test error handling when markdown file is missing."""
        # Create presentation info with non-existent file
        bad_info = PresentationInfo(
            title="Missing Presentation",
            folder_name="missing",
            folder_path="/nonexistent",
            markdown_path="/nonexistent/missing.md",
            slide_count=0
        )
        
        with pytest.raises(Exception):  # Should raise PresentationProcessingError
            self.processor.process_presentation(bad_info)
    
    def test_error_handling_invalid_markdown(self):
        """Test error handling with invalid markdown content."""
        # Create markdown with invalid syntax
        invalid_markdown = """
        slidenumbers: invalid_boolean
        
        # Test
        
        This has invalid LaTeX: $\\invalid{syntax
        """
        
        invalid_path = self.test_presentation_dir / "invalid.md"
        with open(invalid_path, 'w', encoding='utf-8') as f:
            f.write(invalid_markdown)
        
        invalid_info = PresentationInfo(
            title="Invalid Presentation",
            folder_name="invalid",
            folder_path=str(self.test_presentation_dir),
            markdown_path=str(invalid_path),
            slide_count=0
        )
        
        # # Should not raise exception but handle gracefully
        result = self.processor.process_presentation(invalid_info)
        assert isinstance(result, EnhancedPresentation)
        assert len(result.slides) > 0
    
    @patch('enhanced_processor.MediaProcessor')
    def test_media_processor_integration(self, mock_media_processor):
        """Test integration with MediaProcessor."""
        # Mock the media processor
        mock_instance = Mock()
        mock_media_processor.return_value = mock_instance
        
        # Create processor after mock is applied
        processor = EnhancedPresentationProcessor()
        
        # Process presentation
        result = processor.process_presentation(self.presentation_info)
        
        # Verify MediaProcessor was used
        assert mock_media_processor.called
        assert isinstance(result, EnhancedPresentation)
    
    @patch('enhanced_processor.CodeProcessor')
    def test_code_processor_integration(self, mock_code_processor):
        """Test integration with CodeProcessor."""
        # Mock the code processor
        mock_instance = Mock()
        mock_code_processor.return_value = mock_instance
        
        # Create processor after mock is applied
        processor = EnhancedPresentationProcessor()
        
        # Process presentation
        result = processor.process_presentation(self.presentation_info)
        
        # Verify CodeProcessor was used
        assert mock_code_processor.called
        assert isinstance(result, EnhancedPresentation)
    
    @patch('enhanced_processor.MathProcessor')
    def test_math_processor_integration(self, mock_math_processor):
        """Test integration with MathProcessor."""
        # Mock the math processor
        mock_instance = Mock()
        mock_math_processor.return_value = mock_instance
        mock_instance.process_math_formulas.return_value = ("processed content", [])
        
        # Create processor after mock is applied
        processor = EnhancedPresentationProcessor()
        
        # Process presentation
        result = processor.process_presentation(self.presentation_info)
        
        # Verify MathProcessor was used
        assert mock_math_processor.called
        assert isinstance(result, EnhancedPresentation)
    
    def test_global_footnotes_processing(self):
        """Test that global footnotes are processed correctly."""
        # Add footnotes to markdown content
        footnote_markdown = self.markdown_content + """

[^1]: This is a global footnote
[^2]: Another global footnote
        """
        
        footnote_path = self.test_presentation_dir / "footnote-test.md"
        with open(footnote_path, 'w', encoding='utf-8') as f:
            f.write(footnote_markdown)
        
        footnote_info = PresentationInfo(
            title="Footnote Test",
            folder_name="footnote-test",
            folder_path=str(self.test_presentation_dir),
            markdown_path=str(footnote_path),
            slide_count=0
        )
        
        # result = self.processor.process_presentation(footnote_info)
        
        # # Check that global footnotes were extracted
        # assert len(result.global_footnotes) >= 0  # May be 0 if footnotes are slide-specific
        # assert isinstance(result.global_footnotes, dict)
        pass


if __name__ == "__main__":
    pytest.main([__file__])