"""
Unit tests for the PresentationProcessor class.

Tests various markdown processing scenarios including slide splitting,
note extraction, and metadata parsing.
"""

import pytest
from unittest.mock import mock_open, patch
from datetime import datetime

from processor import PresentationProcessor
from models import PresentationInfo, Slide, ProcessedPresentation, PresentationProcessingError


class TestPresentationProcessor:
    """Test cases for PresentationProcessor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = PresentationProcessor()
        self.sample_presentation_info = PresentationInfo(
            folder_name="test-presentation",
            folder_path="/path/to/test-presentation",
            markdown_path="/path/to/test-presentation/test-presentation.md",
            title="Test Presentation"
        )
    
    def test_extract_slides_standard_separator(self):
        """Test slide extraction with standard --- separator."""
        content = """# First Slide
This is the first slide.

---

# Second Slide
This is the second slide.

---

# Third Slide
This is the third slide."""
        
        slides = self.processor.extract_slides(content)
        
        assert len(slides) == 3
        assert slides[0].index == 1
        assert "First Slide" in slides[0].content
        assert slides[1].index == 2
        assert "Second Slide" in slides[1].content
        assert slides[2].index == 3
        assert "Third Slide" in slides[2].content
    
    def test_extract_slides_with_newlines(self):
        """Test slide extraction with newline-surrounded separators."""
        content = """# First Slide
Content here

---

# Second Slide
More content"""
        
        slides = self.processor.extract_slides(content)
        
        assert len(slides) == 2
        assert "First Slide" in slides[0].content
        assert "Second Slide" in slides[1].content
    
    def test_extract_slides_multiple_dashes(self):
        """Test slide extraction with multiple dash separators."""
        content = """# First Slide
Content

----

# Second Slide
Content"""
        
        slides = self.processor.extract_slides(content)
        
        assert len(slides) == 2
        assert "First Slide" in slides[0].content
        assert "Second Slide" in slides[1].content
    
    def test_extract_slides_single_slide(self):
        """Test handling of content with no separators (single slide)."""
        content = """# Only Slide
This is the only slide in the presentation."""
        
        slides = self.processor.extract_slides(content)
        
        assert len(slides) == 1
        assert slides[0].index == 1
        assert "Only Slide" in slides[0].content
    
    def test_extract_slides_with_frontmatter(self):
        """Test slide extraction when frontmatter is present."""
        content = """---
title: Test Presentation
author: Test Author
---

# First Slide
Content

---

# Second Slide
More content"""
        
        slides = self.processor.extract_slides(content)
        
        assert len(slides) == 2
        assert "First Slide" in slides[0].content
        assert "Second Slide" in slides[1].content
        # Frontmatter should not appear in slides
        assert "title:" not in slides[0].content
    
    def test_extract_notes_standard_format(self):
        """Test note extraction with standard ^ format."""
        slide_content = """# Test Slide
This is slide content.

^ This is a speaker note.
^ This is another note."""
        
        notes = self.processor.extract_notes(slide_content)
        
        assert "This is a speaker note." in notes
        assert "This is another note." in notes
        # Notes should be converted to HTML
        assert "<p>" in notes
    
    def test_extract_notes_with_spaces(self):
        """Test note extraction with various spacing formats."""
        slide_content = """# Test Slide
Content here.

^This note has no space after ^
^ This note has one space
^  This note has multiple spaces
  ^ This note has leading spaces"""
        
        notes = self.processor.extract_notes(slide_content)
        
        assert "This note has no space" in notes
        assert "This note has one space" in notes
        assert "This note has multiple spaces" in notes
        assert "This note has leading spaces" in notes
    
    def test_extract_notes_legacy_format(self):
        """Test note extraction with legacy multiline format."""
        slide_content = """# Test Slide
This is slide content.

^ This is a legacy note
^ that spans multiple lines
^ and should be combined."""
        
        notes = self.processor.extract_notes(slide_content)
        
        assert "legacy note" in notes
        assert "multiple lines" in notes
        assert "combined" in notes
    
    def test_extract_notes_no_notes(self):
        """Test note extraction when no notes are present."""
        slide_content = """# Test Slide
This slide has no notes."""
        
        notes = self.processor.extract_notes(slide_content)
        
        assert notes == ""
    
    def test_extract_metadata_yaml_frontmatter(self):
        """Test metadata extraction from YAML frontmatter."""
        content = """---
title: Test Presentation
author: John Doe
slidenumbers: true
footer: Company Name
theme: dark
---

# First Slide
Content here."""
        
        metadata = self.processor.extract_metadata(content)
        
        assert metadata["title"] == "Test Presentation"
        assert metadata["author"] == "John Doe"
        assert metadata["slidenumbers"] is True
        assert metadata["footer"] == "Company Name"
        assert metadata["theme"] == "dark"
    
    def test_extract_metadata_deckset_style(self):
        """Test metadata extraction from Deckset-style configuration."""
        content = """autoscale: true
footer: Zuhlke Engineering Singapore
slidenumbers: true
theme: business-class

# [fit] FIX Messaging
# by **_Kevin Lin_**

---

# What I will talk about"""
        
        metadata = self.processor.extract_metadata(content)
        
        assert metadata["autoscale"] is True
        assert metadata["footer"] == "Zuhlke Engineering Singapore"
        assert metadata["slidenumbers"] is True
        assert metadata["theme"] == "business-class"
    
    def test_extract_metadata_mixed_types(self):
        """Test metadata parsing with different value types."""
        content = """---
title: "Quoted String"
count: 42
percentage: 85.5
enabled: true
disabled: false
---

# Content"""
        
        metadata = self.processor.extract_metadata(content)
        
        assert metadata["title"] == "Quoted String"
        assert metadata["count"] == 42
        assert metadata["percentage"] == 85.5
        assert metadata["enabled"] is True
        assert metadata["disabled"] is False
    
    def test_extract_metadata_no_metadata(self):
        """Test metadata extraction when no metadata is present."""
        content = """# First Slide
Just content, no metadata."""
        
        metadata = self.processor.extract_metadata(content)
        
        assert metadata == {}
    
    def test_remove_notes_from_content(self):
        """Test that notes are properly removed from slide content."""
        slide_content = """# Test Slide
This is visible content.

^ This is a note that should be removed.
^ Another note to remove.

More visible content."""
        
        clean_content = self.processor._remove_notes_from_content(slide_content)
        
        assert "This is visible content." in clean_content
        assert "More visible content." in clean_content
        assert "This is a note" not in clean_content
        assert "Another note" not in clean_content
        assert "^" not in clean_content
    
    def test_remove_frontmatter(self):
        """Test frontmatter removal from content."""
        content = """---
title: Test
author: Author
---

# First Slide
Content here."""
        
        clean_content = self.processor._remove_frontmatter(content)
        
        assert "title:" not in clean_content
        assert "author:" not in clean_content
        assert "First Slide" in clean_content
    
    def test_remove_frontmatter_deckset_style(self):
        """Test Deckset-style configuration removal."""
        content = """autoscale: true
footer: Company
slidenumbers: true

# First Slide
Content here."""
        
        clean_content = self.processor._remove_frontmatter(content)
        
        assert "First Slide" in clean_content
        assert "Content here." in clean_content
        # Configuration should be removed
        assert "autoscale:" not in clean_content
    
    @patch("builtins.open", new_callable=mock_open, read_data="""---
title: Test Presentation
---

# First Slide
Content

---

# Second Slide
^ This is a note""")
    def test_process_presentation_success(self, mock_file):
        """Test successful presentation processing."""
        result = self.processor.process_presentation(self.sample_presentation_info)
        
        assert isinstance(result, ProcessedPresentation)
        assert result.info == self.sample_presentation_info
        assert len(result.slides) == 2
        assert result.metadata["title"] == "Test Presentation"
        assert self.sample_presentation_info.slide_count == 2
    
    @patch("builtins.open", side_effect=IOError("File not found"))
    def test_process_presentation_file_error(self, mock_file):
        """Test presentation processing with file read error."""
        with pytest.raises(PresentationProcessingError) as exc_info:
            self.processor.process_presentation(self.sample_presentation_info)
        
        assert "Failed to read markdown file" in str(exc_info.value)
    
    def test_complex_presentation_processing(self):
        """Test processing a complex presentation with various elements."""
        complex_content = """---
title: Complex Presentation
author: Test Author
slidenumbers: true
---

# [fit] Title Slide
## Subtitle here

^ Opening notes for the presentation

---

![left, 50%](image1.jpg)

# Content Slide
- Bullet point 1
- Bullet point 2

^ This slide has an image
^ And multiple notes

---

# Code Slide

```python
def hello():
    print("Hello, World!")
```

^ Code example slide
^ With syntax highlighting

---

# Final Slide
Thank you!

^ Closing remarks"""
        
        slides = self.processor.extract_slides(complex_content)
        metadata = self.processor.extract_metadata(complex_content)
        
        # Check metadata
        assert metadata["title"] == "Complex Presentation"
        assert metadata["author"] == "Test Author"
        assert metadata["slidenumbers"] is True
        
        # Check slides
        assert len(slides) == 4
        
        # First slide
        assert "[fit] Title Slide" in slides[0].content
        assert "Opening notes" in slides[0].notes
        
        # Second slide with image
        assert "Content Slide" in slides[1].content
        assert "image1.jpg" in slides[1].content
        assert "This slide has an image" in slides[1].notes
        
        # Code slide
        assert "Code Slide" in slides[2].content
        assert "def hello" in slides[2].content
        assert "Code example" in slides[2].notes
        
        # Final slide
        assert "Final Slide" in slides[3].content
        assert "Closing remarks" in slides[3].notes
    
    def test_edge_cases(self):
        """Test various edge cases in processing."""
        # Empty content
        empty_slides = self.processor.extract_slides("")
        assert len(empty_slides) == 0
        
        # Only separators
        separator_only = self.processor.extract_slides("---\n---\n---")
        assert len(separator_only) == 0
        
        # Malformed frontmatter
        malformed = """---
title: Test
invalid line without colon
author: Test
---

# Slide"""
        metadata = self.processor.extract_metadata(malformed)
        assert metadata["title"] == "Test"
        assert metadata["author"] == "Test"
        
        # Notes without content
        notes_only = self.processor.extract_notes("^ Note 1\n^ Note 2")
        assert "Note 1" in notes_only
        assert "Note 2" in notes_only


if __name__ == "__main__":
    pytest.main([__file__])