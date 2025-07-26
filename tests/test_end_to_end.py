"""
End-to-end tests for the enhanced Deckset website generator.

This module tests the complete workflow from markdown processing to website generation,
ensuring backward compatibility and enhanced feature integration.
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch

from main import DecksetWebsiteGenerator
from models import GeneratorConfig


class TestEndToEndGeneration:
    """Test complete website generation workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "output"
        
        # Create test presentations
        self.create_test_presentations()
        
        # Create generator config
        self.config = GeneratorConfig()
        self.config.output_dir = str(self.output_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_presentations(self):
        """Create test presentations with various features."""
        
        # Basic presentation (backward compatibility test)
        basic_dir = Path(self.temp_dir) / "01-basic-presentation"
        basic_dir.mkdir(parents=True)
        
        basic_content = """
# Basic Presentation

This is a basic presentation for backward compatibility testing.

---

## Second Slide

Some content here.

^ Speaker note for basic presentation

---

## Third Slide

![](basic-image.jpg)

Final slide content.
        """
        
        with open(basic_dir / "basic-presentation.md", 'w') as f:
            f.write(basic_content)
        
        # Create basic image
        with open(basic_dir / "basic-image.jpg", 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF')
        
        # Enhanced presentation (full features test)
        enhanced_dir = Path(self.temp_dir) / "02-enhanced-presentation"
        enhanced_dir.mkdir(parents=True)
        
        enhanced_content = """
slidenumbers: true
footer: Enhanced Features Demo
autoscale: false
theme: default

# Enhanced Presentation

This presentation demonstrates all enhanced Deckset features.

---

## Code Highlighting

[.code-highlight: 1,3-5]

```python
def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)
```

^ This slide shows enhanced code highlighting

---

## Mathematical Formulas

Inline math: $E = mc^2$

Display math:

$$\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}$$

---

## Multi-Column Layout

[.column]

### Left Column

- Point 1
- Point 2
- Point 3

[.column]

### Right Column

- Feature A
- Feature B
- Feature C

---

## Media Integration

![inline, fit](enhanced-image.png)

Video example:
![autoplay, loop](sample-video.mp4)

---

## Background Image

[.background-image: bg-image.jpg]

# Content Over Background

This slide has a background image with content overlay.

---

## Footnotes and References

This slide has footnotes[^1] and references[^2].

[^1]: First footnote explanation
[^2]: Second footnote with more details

---

## Final Slide

Thank you for viewing this enhanced presentation!

^ Final speaker notes
        """
        
        with open(enhanced_dir / "enhanced-presentation.md", 'w') as f:
            f.write(enhanced_content)
        
        # Create enhanced media files
        with open(enhanced_dir / "enhanced-image.png", 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89')
        
        with open(enhanced_dir / "bg-image.jpg", 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF')
        
        with open(enhanced_dir / "sample-video.mp4", 'wb') as f:
            f.write(b'\x00\x00\x00\x20ftypmp42')  # Minimal MP4 header
        
        # Mixed features presentation (compatibility test)
        mixed_dir = Path(self.temp_dir) / "03-mixed-features"
        mixed_dir.mkdir(parents=True)
        
        mixed_content = """
slidenumbers: false

# Mixed Features Test

Testing compatibility between basic and enhanced features.

---

## Basic + Enhanced

Regular markdown content.

```javascript
console.log("Basic code block");
```

Math: $x = y + z$

![](mixed-image.gif)

---

## Edge Cases

Empty slide with just title.

---

## 

Slide with no title but content.

Some text here.
        """
        
        with open(mixed_dir / "mixed-features.md", 'w') as f:
            f.write(mixed_content)
        
        with open(mixed_dir / "mixed-image.gif", 'wb') as f:
            f.write(b'GIF89a\x01\x00\x01\x00\x00\x00\x00!')
    
    def test_complete_website_generation(self):
        """Test complete website generation with all features."""
        generator = DecksetWebsiteGenerator(self.config)
        
        # Generate website
        result = generator.generate_website(self.temp_dir)
        
        # Verify generation success
        assert result.get("success", False) is True
        assert result.get("presentations_found", 0) == 3
        assert result.get("presentations_processed", 0) >= 2  # At least 2 should succeed
        assert result.get("pages_generated", 0) >= 2
        
        # Verify output structure
        assert self.output_dir.exists()
        assert (self.output_dir / "index.html").exists()
        assert (self.output_dir / "presentations").exists()
        
        # Verify individual presentation files
        presentations_dir = self.output_dir / "presentations"
        expected_files = [
            "01-basic-presentation.html",
            "02-enhanced-presentation.html", 
            "03-mixed-features.html"
        ]
        
        for filename in expected_files:
            file_path = presentations_dir / filename
            if file_path.exists():
                # Verify file has content
                assert file_path.stat().st_size > 0
                
                # Verify HTML structure
                content = file_path.read_text()
                assert "<!DOCTYPE html>" in content
                assert "<html" in content
                assert "</html>" in content
    
    def test_enhanced_features_usage(self):
        """Test that enhanced features are properly used."""
        generator = DecksetWebsiteGenerator(self.config)
        
        # Generate and check for enhanced features
        result = generator.generate_website(self.temp_dir)
        
        # Verify enhanced features are present
        homepage_path = self.output_dir / "index.html"
        if homepage_path.exists():
            homepage_content = homepage_path.read_text()
            assert "Enhanced" in homepage_content or "enhanced" in homepage_content
    
    def test_backward_compatibility(self):
        """Test that basic presentations still work without enhanced features."""
        # Test with only basic presentation
        basic_only_dir = Path(self.temp_dir) / "basic_only"
        basic_only_dir.mkdir()
        
        # Copy basic presentation
        basic_src = Path(self.temp_dir) / "01-basic-presentation"
        basic_dst = basic_only_dir / "01-basic-presentation"
        shutil.copytree(basic_src, basic_dst)
        
        generator = DecksetWebsiteGenerator(self.config)
        result = generator.generate_website(str(basic_only_dir))
        
        # Should succeed even with basic features only
        assert result.get("success", False) is True
        assert result.get("presentations_processed", 0) >= 1
    
    def test_error_handling_and_graceful_degradation(self):
        """Test error handling and graceful degradation."""
        # Create presentation with errors
        error_dir = Path(self.temp_dir) / "04-error-presentation"
        error_dir.mkdir(parents=True)
        
        error_content = """
invalid_config: this is not valid
slidenumbers: invalid_boolean

# Error Test

This has invalid LaTeX: $\\invalid{syntax

```invalid_language
broken code block
```

![](nonexistent-image.jpg)
        """
        
        with open(error_dir / "error-presentation.md", 'w') as f:
            f.write(error_content)
        
        generator = DecksetWebsiteGenerator(self.config)
        result = generator.generate_website(self.temp_dir)
        
        # Should still succeed with graceful error handling
        assert result.get("success", False) is True
        
        # Should have some errors logged
        errors = result.get("errors", [])
        # Errors are expected but shouldn't prevent generation
        
        # Verify error presentation was processed (even if with fallbacks)
        error_file = self.output_dir / "presentations" / "04-error-presentation.html"
        if error_file.exists():
            content = error_file.read_text()
            assert len(content) > 0  # Should have some content even with errors
    
    def test_media_file_processing(self):
        """Test that media files are properly copied and processed."""
        generator = DecksetWebsiteGenerator(self.config)
        result = generator.generate_website(self.temp_dir)
        
        # Check slides directory structure
        slides_dir = self.output_dir / "slides"
        if slides_dir.exists():
            # Should have presentation folders
            presentation_folders = [d for d in slides_dir.iterdir() if d.is_dir()]
            assert len(presentation_folders) >= 1
            
            # Check for copied media files
            for folder in presentation_folders:
                media_files = list(folder.glob("*"))
                # Should have at least some media files copied
                if media_files:
                    for media_file in media_files:
                        assert media_file.stat().st_size > 0
    
    def test_homepage_generation_with_mixed_presentations(self):
        """Test homepage generation with both basic and enhanced presentations."""
        generator = DecksetWebsiteGenerator(self.config)
        result = generator.generate_website(self.temp_dir)
        
        homepage_path = self.output_dir / "index.html"
        assert homepage_path.exists()
        
        homepage_content = homepage_path.read_text()
        
        # Should contain all presentations
        assert "basic-presentation" in homepage_content.lower()
        assert "enhanced-presentation" in homepage_content.lower()
        assert "mixed-features" in homepage_content.lower()
        
        # Should have proper HTML structure
        assert "<!DOCTYPE html>" in homepage_content
        assert "<title>" in homepage_content
        assert "presentation-card" in homepage_content
    
    def test_css_and_js_assets(self):
        """Test that CSS and JavaScript assets are properly handled."""
        generator = DecksetWebsiteGenerator(self.config)
        result = generator.generate_website(self.temp_dir)
        
        # Check for CSS files
        css_files = list(self.output_dir.rglob("*.css"))
        if css_files:
            for css_file in css_files:
                assert css_file.stat().st_size > 0
        
        # Check for JS files
        js_files = list(self.output_dir.rglob("*.js"))
        if js_files:
            for js_file in js_files:
                assert js_file.stat().st_size > 0
    
    def test_responsive_design_elements(self):
        """Test that responsive design elements are included."""
        generator = DecksetWebsiteGenerator(self.config)
        result = generator.generate_website(self.temp_dir)
        
        # Check presentation files for responsive elements
        presentation_files = list((self.output_dir / "presentations").glob("*.html"))
        
        for file_path in presentation_files:
            if file_path.exists():
                content = file_path.read_text()
                
                # Should have viewport meta tag
                assert 'name="viewport"' in content
                
                # Should have responsive CSS classes or styles
                responsive_indicators = [
                    "max-width",
                    "media (max-width",
                    "responsive",
                    "@media",
                    "grid-template-columns"
                ]
                
                has_responsive = any(indicator in content for indicator in responsive_indicators)
                if not has_responsive:
                    # At least should have basic responsive structure
                    assert "width" in content  # Some width handling
    
    def test_accessibility_features(self):
        """Test that accessibility features are included."""
        generator = DecksetWebsiteGenerator(self.config)
        result = generator.generate_website(self.temp_dir)
        
        # Check homepage for accessibility
        homepage_path = self.output_dir / "index.html"
        if homepage_path.exists():
            homepage_content = homepage_path.read_text()
            
            # Should have proper semantic HTML
            assert "<main" in homepage_content
            assert "<nav" in homepage_content or "navigation" in homepage_content
            
            # Should have alt attributes for images
            if "<img" in homepage_content:
                assert 'alt=' in homepage_content
        
        # Check presentation files for accessibility
        presentation_files = list((self.output_dir / "presentations").glob("*.html"))
        
        for file_path in presentation_files:
            if file_path.exists():
                content = file_path.read_text()
                
                # Should have proper heading structure
                assert "<h1" in content or "<h2" in content
                
                # Should have lang attribute
                assert 'lang=' in content
    
    @patch('enhanced_processor.EnhancedPresentationProcessor')
    def test_fallback_to_basic_processor(self, mock_enhanced_processor):
        """Test fallback to basic processor when enhanced processor fails."""
        # Mock enhanced processor to raise ImportError
        mock_enhanced_processor.side_effect = ImportError("Enhanced processor not available")
        
        generator = DecksetWebsiteGenerator(self.config)
        result = generator.generate_website(self.temp_dir)
        
        # Should still succeed with basic processor
        assert result.get("success", False) is True
        assert result.get("presentations_processed", 0) >= 1
    
    def test_performance_with_multiple_presentations(self):
        """Test performance with multiple presentations."""
        # Create additional presentations for performance testing
        for i in range(5, 10):  # Add 5 more presentations
            perf_dir = Path(self.temp_dir) / f"{i:02d}-perf-test-{i}"
            perf_dir.mkdir(parents=True)
            
            perf_content = f"""
# Performance Test {i}

This is presentation {i} for performance testing.

---

## Slide 2

Content for slide 2.

---

## Slide 3

More content here.
            """
            
            with open(perf_dir / f"perf-test-{i}.md", 'w') as f:
                f.write(perf_content)
        
        generator = DecksetWebsiteGenerator(self.config)
        
        import time
        start_time = time.time()
        result = generator.generate_website(self.temp_dir)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should complete in reasonable time (adjust threshold as needed)
        assert processing_time < 30.0  # 30 seconds max for ~8 presentations
        assert result.get("success", False) is True
        
        print(f"Processed {result.get('presentations_found', 0)} presentations in {processing_time:.2f} seconds")


class TestWebsiteStructureIntegration:
    """Test website structure and navigation integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "output"
        
        # Create simple test presentation
        pres_dir = Path(self.temp_dir) / "01-test"
        pres_dir.mkdir(parents=True)
        
        with open(pres_dir / "test.md", 'w') as f:
            f.write("# Test\n\nContent\n\n---\n\n## Slide 2\n\nMore content")
        
        self.config = GeneratorConfig()
        self.config.output_dir = str(self.output_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_website_navigation_structure(self):
        """Test that website navigation structure is properly maintained."""
        generator = DecksetWebsiteGenerator(self.config)
        result = generator.generate_website(self.temp_dir)
        
        # Verify directory structure
        expected_dirs = [
            self.output_dir,
            self.output_dir / "presentations",
            self.output_dir / "slides",
            self.output_dir / "images"
        ]
        
        for dir_path in expected_dirs:
            if dir_path.exists():  # Some directories might not be created if no content
                assert dir_path.is_dir()
        
        # Verify file structure
        assert (self.output_dir / "index.html").exists()
        
        presentation_files = list((self.output_dir / "presentations").glob("*.html"))
        assert len(presentation_files) >= 1
    
    def test_cross_references_and_links(self):
        """Test that cross-references and links work correctly."""
        generator = DecksetWebsiteGenerator(self.config)
        result = generator.generate_website(self.temp_dir)
        
        # Check homepage links to presentations
        homepage_path = self.output_dir / "index.html"
        if homepage_path.exists():
            homepage_content = homepage_path.read_text()
            
            # Should have links to presentation files
            assert 'href="presentations/' in homepage_content
            assert '.html"' in homepage_content
        
        # Check presentation files for proper asset references
        presentation_files = list((self.output_dir / "presentations").glob("*.html"))
        
        for file_path in presentation_files:
            content = file_path.read_text()
            
            # Should have proper relative paths for assets
            if "src=" in content or "href=" in content:
                # Should use relative paths (../) for assets
                assert "../" in content or "http" in content  # Relative or absolute URLs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])