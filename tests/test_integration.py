"""
Integration tests for the Deckset Website Generator.

This module contains tests for the complete file management workflow,
including directory creation, image copying, and cleanup.
"""

import os
import shutil
import pytest
from pathlib import Path
from datetime import datetime

from models import (
    PresentationInfo,
    Slide,
    ProcessedPresentation,
    GeneratorConfig
)
from file_manager import FileManager
from generator import WebPageGenerator


@pytest.fixture
def test_output_dir(tmp_path):
    """Create a temporary output directory for testing."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    yield output_dir
    # Clean up after tests
    if output_dir.exists():
        shutil.rmtree(output_dir)


@pytest.fixture
def test_input_dir(tmp_path):
    """Create a temporary input directory with test files."""
    input_dir = tmp_path / "test_input"
    input_dir.mkdir()
    
    # Create test presentation folders
    pres1_dir = input_dir / "presentation1"
    pres1_dir.mkdir()
    pres2_dir = input_dir / "presentation2"
    pres2_dir.mkdir()
    
    # Create test markdown files
    with open(pres1_dir / "presentation1.md", "w") as f:
        f.write("# Presentation 1\n\n---\n\nSlide 2\n\n^Notes for slide 2")
    
    with open(pres2_dir / "presentation2.md", "w") as f:
        f.write("# Presentation 2\n\n---\n\nSlide 2")
    
    # Create test slide images
    slides1_dir = pres1_dir / "slides"
    slides1_dir.mkdir()
    
    # Create test image files
    for i in range(1, 3):
        with open(slides1_dir / f"{i}.png", "wb") as f:
            # Simple PNG header
            f.write(bytes.fromhex(
                '89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4'
                '890000000d4944415478da63f8ffff3f0300050001013c0b8b0000000049454e44ae426082'
            ))
    
    # Create a test image in the second presentation folder
    with open(pres2_dir / "preview.jpg", "wb") as f:
        # Simple JPEG header
        f.write(bytes.fromhex('ffd8ffe000104a46494600010101006000600000ffdb004300'))
    
    yield input_dir


@pytest.fixture
def config(test_output_dir):
    """Create a test configuration."""
    return GeneratorConfig(
        output_dir=str(test_output_dir),
        template_dir="templates",
        slides_dir="slides",
        fallback_image="slides/redacted.png"
    )


@pytest.fixture
def presentations(test_input_dir):
    """Create test processed presentations."""
    pres1_info = PresentationInfo(
        folder_name="presentation1",
        folder_path=str(test_input_dir / "presentation1"),
        markdown_path=str(test_input_dir / "presentation1" / "presentation1.md"),
        title="Presentation 1",
        preview_image=str(test_input_dir / "presentation1" / "slides" / "1.png"),
        slide_count=2,
        last_modified=datetime.now()
    )
    
    pres1_slides = [
        Slide(
            index=1, 
            content="# Presentation 1", 
            notes="", 
            image_path=str(test_input_dir / "presentation1" / "slides" / "1.png")
        ),
        Slide(
            index=2, 
            content="Slide 2", 
            notes="Notes for slide 2", 
            image_path=str(test_input_dir / "presentation1" / "slides" / "2.png")
        )
    ]
    
    pres1 = ProcessedPresentation(
        info=pres1_info,
        slides=pres1_slides,
        metadata={}
    )
    
    pres2_info = PresentationInfo(
        folder_name="presentation2",
        folder_path=str(test_input_dir / "presentation2"),
        markdown_path=str(test_input_dir / "presentation2" / "presentation2.md"),
        title="Presentation 2",
        preview_image=str(test_input_dir / "presentation2" / "preview.jpg"),
        slide_count=2,
        last_modified=datetime.now()
    )
    
    pres2_slides = [
        Slide(
            index=1, 
            content="# Presentation 2", 
            notes="", 
            image_path=None  # Missing image to test fallback
        ),
        Slide(
            index=2, 
            content="Slide 2", 
            notes="", 
            image_path="nonexistent.png"  # Invalid image to test fallback
        )
    ]
    
    pres2 = ProcessedPresentation(
        info=pres2_info,
        slides=pres2_slides,
        metadata={}
    )
    
    return [pres1, pres2]


class TestFileManagement:
    """Integration tests for file management."""
    
    def test_directory_structure_creation(self, config, test_output_dir):
        """Test creation of output directory structure."""
        file_manager = FileManager(config)
        file_manager.setup_output_directories()
        
        # Check that all required directories were created
        assert (test_output_dir / "presentations").exists()
        assert (test_output_dir / "slides").exists()
        assert (test_output_dir / "images").exists()
        assert (test_output_dir / "assets").exists()
        assert (test_output_dir / "assets" / "css").exists()
        assert (test_output_dir / "assets" / "js").exists()
    
    def test_fallback_image_creation(self, config, test_output_dir):
        """Test creation of fallback image."""
        file_manager = FileManager(config)
        file_manager.ensure_fallback_image()
        
        # Check that fallback image was created
        fallback_path = test_output_dir / "slides" / "redacted.png"
        assert fallback_path.exists()
        assert fallback_path.stat().st_size > 0
    
    def test_slide_image_copying(self, config, presentations, test_output_dir):
        """Test copying of slide images."""
        file_manager = FileManager(config)
        
        # Process the first presentation with valid images
        file_manager.copy_slide_images(presentations[0])
        
        # Check that slide images were copied
        pres1_slides_dir = test_output_dir / "slides" / "presentation1"
        assert pres1_slides_dir.exists()
        assert (pres1_slides_dir / "1.png").exists()
        assert (pres1_slides_dir / "2.png").exists()
        
        # Process the second presentation with missing images
        file_manager.copy_slide_images(presentations[1])
        
        # Check that no images were copied for the second presentation
        # (since it has no valid images)
        pres2_slides_dir = test_output_dir / "slides" / "presentation2"
        if pres2_slides_dir.exists():
            assert len(list(pres2_slides_dir.glob("*.png"))) == 0
    
    def test_preview_image_copying(self, config, presentations, test_output_dir):
        """Test copying of preview images."""
        file_manager = FileManager(config)
        
        # Process preview images
        file_manager.copy_preview_image(presentations[0].info)
        file_manager.copy_preview_image(presentations[1].info)
        
        # Check that preview images were copied
        images_dir = test_output_dir / "images"
        assert images_dir.exists()
        assert (images_dir / "presentation1-preview.png").exists()
        assert (images_dir / "presentation2-preview.jpg").exists()
        
        # Check that paths were updated
        assert presentations[0].info.preview_image == "../images/presentation1-preview.png"
        assert presentations[1].info.preview_image == "../images/presentation2-preview.jpg"
    
    def test_cleanup_output_directory(self, config, presentations, test_output_dir):
        """Test cleanup of unused files."""
        file_manager = FileManager(config)
        
        # Create some directories and files that should be cleaned up
        slides_dir = test_output_dir / "slides"
        slides_dir.mkdir(parents=True, exist_ok=True)
        
        old_pres_dir = slides_dir / "old-presentation"
        old_pres_dir.mkdir()
        with open(old_pres_dir / "test.png", "wb") as f:
            f.write(b"test")
        
        presentations_dir = test_output_dir / "presentations"
        presentations_dir.mkdir(parents=True, exist_ok=True)
        with open(presentations_dir / "old-presentation.html", "w") as f:
            f.write("<html>Old presentation</html>")
        
        # Run cleanup
        file_manager.cleanup_output_directory(presentations)
        
        # Check that old files were removed
        assert not old_pres_dir.exists()
        assert not (presentations_dir / "old-presentation.html").exists()
    
    def test_complete_file_management_workflow(self, config, presentations, test_output_dir):
        """Test the complete file management workflow."""
        file_manager = FileManager(config)
        
        # Set up directories
        file_manager.setup_output_directories()
        
        # Ensure fallback image
        file_manager.ensure_fallback_image()
        
        # Process all presentations
        for presentation in presentations:
            # Update image paths to use absolute paths for testing
            for slide in presentation.slides:
                if slide.image_path and not slide.image_path.startswith('/'):
                    slide_path = Path(presentation.info.folder_path) / slide.image_path
                    if slide_path.exists():
                        slide.image_path = str(slide_path)
        
        file_manager.process_all_presentations(presentations)
        
        # Check directory structure
        assert (test_output_dir / "presentations").exists()
        assert (test_output_dir / "slides").exists()
        assert (test_output_dir / "images").exists()
        assert (test_output_dir / "assets").exists()
        
        # Check fallback image
        assert (test_output_dir / "slides" / "redacted.png").exists()
        
        # Check that paths were updated
        assert presentations[0].info.preview_image.startswith("../images/")
        assert presentations[1].info.preview_image.startswith("../images/")
        
        # Check that slide paths were updated
        assert presentations[0].slides[0].image_path.startswith("../slides/")
        assert presentations[0].slides[1].image_path.startswith("../slides/")
        assert presentations[1].slides[0].image_path == f"../{config.fallback_image}"
        assert presentations[1].slides[1].image_path == f"../{config.fallback_image}"
    
    def test_integration_with_generator(self, config, presentations, test_output_dir, monkeypatch):
        """Test integration with WebPageGenerator."""
        # Mock the template rendering to avoid actual HTML generation
        from unittest.mock import patch
        
        with patch('enhanced_templates.EnhancedTemplateEngine.render_presentation', return_value="<html>Test</html>"), \
             patch('enhanced_templates.EnhancedTemplateEngine.render_homepage', return_value="<html>Homepage</html>"):
            
            # Create generator
            generator = WebPageGenerator(config)
            
            # Update image paths to use absolute paths for testing
            for presentation in presentations:
                for slide in presentation.slides:
                    if slide.image_path and not slide.image_path.startswith('/'):
                        slide_path = Path(presentation.info.folder_path) / slide.image_path
                        if slide_path.exists():
                            slide.image_path = str(slide_path)
            
            # Generate all pages
            stats = generator.generate_all_pages(presentations)
            
            # Check stats
            assert stats["total"] == 2
            assert stats["successful"] == 2
            assert stats["failed"] == 0
            
            # Check directory structure
            assert (test_output_dir / "presentations").exists()
            assert (test_output_dir / "slides").exists()
            assert (test_output_dir / "images").exists()
            assert (test_output_dir / "assets").exists()
            
            # Check fallback image
            assert (test_output_dir / "slides" / "redacted.png").exists()
            
            # Check HTML files
            assert (test_output_dir / "presentations" / "presentation1.html").exists()
            assert (test_output_dir / "presentations" / "presentation2.html").exists()
            assert (test_output_dir / "index.html").exists()

    def test_website_generation_with_mixed_single_and_multiple_presentations(self, tmp_path):
        """Test that website generation works correctly with both single and multiple presentations."""
        from main import DecksetWebsiteGenerator
        from models import GeneratorConfig
        
        # Create configuration
        config = GeneratorConfig()
        generator = DecksetWebsiteGenerator(config)
        
        # Create test repository
        test_repo = tmp_path / "test_repo"
        test_repo.mkdir()
        
        # Create a single presentation folder
        single_dir = test_repo / "single_presentation"
        single_dir.mkdir()
        single_md = single_dir / "single_presentation.md"
        with open(single_md, 'w', encoding='utf-8') as f:
            f.write("""# Single Presentation Test

This is a single presentation.

---

# Slide 2

More content here.

^ Speaker notes for slide 2
""")
        
        # Create a multiple presentations folder (Examples-like)
        examples_dir = test_repo / "Examples"
        examples_dir.mkdir()
        
        example1_md = examples_dir / "10 First Example.md"
        with open(example1_md, 'w', encoding='utf-8') as f:
            f.write("""# First Example

This is the first example presentation.

---

# Example Slide 2

Content for first example.

^ Notes for first example
""")
        
        example2_md = examples_dir / "20 Second Example.md"
        with open(example2_md, 'w', encoding='utf-8') as f:
            f.write("""# Second Example

This is the second example presentation.

---

# Another Slide

Content for second example.

^ Notes for second example
""")
        
        # Generate website
        output_dir = test_repo / "output"
        result = generator.generate_website(str(test_repo), str(output_dir))
        
        # Verify successful generation
        assert result["success"] is True
        assert result["presentations_found"] >= 3  # At least our 3 test presentations
        assert result["presentations_processed"] >= 3
        assert result["presentations_failed"] == 0
        
        # Verify output structure
        presentations_dir = output_dir / "presentations"
        assert presentations_dir.exists()
        
        # Check single presentation file
        single_html = presentations_dir / "single_presentation.html"
        assert single_html.exists()
        
        # Check multiple presentations files in subdirectory
        examples_subdir = presentations_dir / "Examples"
        assert examples_subdir.exists()
        
        example1_html = examples_subdir / "10 First Example.html"
        example2_html = examples_subdir / "20 Second Example.html"
        assert example1_html.exists()
        assert example2_html.exists()
        
        # Verify content consistency - all should have enhanced features
        with open(single_html, 'r', encoding='utf-8') as f:
            single_content = f.read()
        
        with open(example1_html, 'r', encoding='utf-8') as f:
            example1_content = f.read()
        
        with open(example2_html, 'r', encoding='utf-8') as f:
            example2_content = f.read()
        
        # All should use the same template structure and enhanced features
        for content, name in [(single_content, "single"), (example1_content, "example1"), (example2_content, "example2")]:
            assert "presentation-container" in content, f"{name} missing presentation container"
            assert "slide-content" in content, f"{name} missing slide content structure"
            assert "enhanced_slide_styles.css" in content, f"{name} missing enhanced styles"
            assert "MathJax" in content, f"{name} missing MathJax support"
            assert "highlight.js" in content, f"{name} missing code highlighting"
        
        # Verify homepage lists all presentations
        homepage = output_dir / "index.html"
        assert homepage.exists()
        
        with open(homepage, 'r', encoding='utf-8') as f:
            homepage_content = f.read()
        
        # Should contain all presentation titles
        assert "Single Presentation Test" in homepage_content
        assert "First Example" in homepage_content
        assert "Second Example" in homepage_content

    def test_asset_paths_for_subdirectory_presentations(self, tmp_path):
        """Test that asset paths are correct for presentations in subdirectories like Examples."""
        from main import DecksetWebsiteGenerator
        from models import GeneratorConfig
        
        # Create test repository
        test_repo = tmp_path / "test_repo"
        test_repo.mkdir()
        
        # Create a single presentation folder
        single_dir = test_repo / "single_presentation" 
        single_dir.mkdir()
        single_md = single_dir / "single_presentation.md"
        with open(single_md, 'w', encoding='utf-8') as f:
            f.write("""# Single Presentation
            
This is a single presentation.

---

## Slide 2

Another slide.
            """)
        
        # Create a multiple presentations folder (Examples-like)
        examples_dir = test_repo / "Examples"
        examples_dir.mkdir()
        
        example1_md = examples_dir / "10 First Example.md"
        with open(example1_md, 'w', encoding='utf-8') as f:
            f.write("""# First Example
            
This is the first example.

---

## Example Slide

Example content.
            """)
        
        example2_md = examples_dir / "20 Second Example.md"
        with open(example2_md, 'w', encoding='utf-8') as f:
            f.write("""# Second Example
            
This is the second example.

---

## Another Example

More content.
            """)
        
        # Generate website
        config = GeneratorConfig()
        generator = DecksetWebsiteGenerator(config)
        output_dir = test_repo / "output"
        result = generator.generate_website(str(test_repo), str(output_dir))
        
        assert result.get("success", False), f"Generation failed: {result.get('error', 'Unknown error')}"
        
        # Check that all presentations were generated
        presentations_dir = output_dir / "presentations"
        assert presentations_dir.exists()
        
        # Check single presentation
        single_html = presentations_dir / "single_presentation.html"
        assert single_html.exists()
        
        # Check multiple presentations in subdirectory
        examples_subdir = presentations_dir / "Examples"
        assert examples_subdir.exists()
        
        example1_html = examples_subdir / "10 First Example.html"
        example2_html = examples_subdir / "20 Second Example.html"
        assert example1_html.exists()
        assert example2_html.exists()
        
        # Verify asset paths are correct
        single_content = single_html.read_text(encoding='utf-8')
        example1_content = example1_html.read_text(encoding='utf-8')
        example2_content = example2_html.read_text(encoding='utf-8')
        
        # Single presentation should use "../" for assets (one level up)
        assert 'href="../enhanced_slide_styles.css"' in single_content, "Single presentation should use ../enhanced_slide_styles.css"
        assert 'src="../assets/js/enhanced-slide-viewer.js"' in single_content, "Single presentation should use ../assets/js/enhanced-slide-viewer.js"
        
        # Multiple presentations in subdirectory should use "../../" for assets (two levels up)
        assert 'href="../../enhanced_slide_styles.css"' in example1_content, "Subdirectory presentation should use ../../enhanced_slide_styles.css"
        assert 'src="../../assets/js/enhanced-slide-viewer.js"' in example1_content, "Subdirectory presentation should use ../../assets/js/enhanced-slide-viewer.js"
        
        assert 'href="../../enhanced_slide_styles.css"' in example2_content, "Subdirectory presentation should use ../../enhanced_slide_styles.css"
        assert 'src="../../assets/js/enhanced-slide-viewer.js"' in example2_content, "Subdirectory presentation should use ../../assets/js/enhanced-slide-viewer.js"
        
        # Make sure we don't have incorrect paths
        assert 'href="../enhanced_slide_styles.css"' not in example1_content, "Subdirectory presentation should not use ../enhanced_slide_styles.css"
        assert 'href="../enhanced_slide_styles.css"' not in example2_content, "Subdirectory presentation should not use ../enhanced_slide_styles.css"
        assert 'href="../../enhanced_slide_styles.css"' not in single_content, "Single presentation should not use ../../enhanced_slide_styles.css"