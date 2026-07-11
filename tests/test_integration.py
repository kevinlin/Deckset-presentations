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
    ProcessedSlide,
    EnhancedPresentation,
    DecksetConfig,
    GeneratorConfig,
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
        slides_dir="slides"
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
        ProcessedSlide(index=1, content="# Presentation 1", notes=""),
        ProcessedSlide(index=2, content="Slide 2", notes="Notes for slide 2"),
    ]

    pres1 = EnhancedPresentation(
        info=pres1_info,
        slides=pres1_slides,
        config=DecksetConfig(),
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
        ProcessedSlide(index=1, content="# Presentation 2", notes=""),
        ProcessedSlide(index=2, content="Slide 2", notes=""),
    ]

    pres2 = EnhancedPresentation(
        info=pres2_info,
        slides=pres2_slides,
        config=DecksetConfig(),
    )
    
    return [pres1, pres2]


class TestFileManagement:
    """Integration tests for file management."""
    
    def test_directory_structure_creation(self, config, test_output_dir):
        """Test creation of output directory structure."""
        file_manager = FileManager(config)
        file_manager.setup_output_directories()

        assert (test_output_dir / "assets").exists()
        assert (test_output_dir / "assets" / "css").exists()
        assert (test_output_dir / "assets" / "js").exists()
    

    
    def test_presentation_file_processing(self, config, presentations, test_output_dir):
        """Test processing files for a presentation via enhanced path."""
        file_manager = FileManager(config)
        file_manager.setup_output_directories()
        file_manager.process_presentation_files(presentations[0])

        slug = presentations[0].info.slug
        assert (test_output_dir / slug / "media").exists()
    
    def test_preview_image_copying(self, config, presentations, test_output_dir):
        """Test copying of preview images."""
        file_manager = FileManager(config)

        file_manager.copy_preview_image(presentations[0].info)
        file_manager.copy_preview_image(presentations[1].info)

        slug0 = presentations[0].info.slug
        slug1 = presentations[1].info.slug
        assert (test_output_dir / slug0 / "preview.png").exists()
        assert (test_output_dir / slug1 / "preview.jpg").exists()
        assert slug0 in presentations[0].info.preview_image
        assert slug1 in presentations[1].info.preview_image
    
    def test_cleanup_output_directory(self, config, presentations, test_output_dir):
        """Test cleanup of unused files."""
        file_manager = FileManager(config)

        old_deck = test_output_dir / "old-presentation"
        old_deck.mkdir(parents=True)
        (old_deck / "index.html").write_text("<html>old</html>")

        file_manager.cleanup_output_directory(presentations)

        assert not old_deck.exists()
    
    def test_complete_file_management_workflow(self, config, presentations, test_output_dir):
        """Test the complete file management workflow."""
        file_manager = FileManager(config)

        file_manager.setup_output_directories()
        file_manager.process_all_presentations(presentations)

        assert (test_output_dir / "assets").exists()
        slug0 = presentations[0].info.slug
        assert (test_output_dir / slug0 / "media").exists()
    
    def test_integration_with_generator(self, config, presentations, test_output_dir, monkeypatch):
        """Test integration with WebPageGenerator."""
        from unittest.mock import patch

        with patch.object(WebPageGenerator, '_render_enhanced_presentation', return_value="<html>Test</html>"), \
             patch('enhanced_templates.EnhancedTemplateEngine.render_homepage', return_value="<html>Homepage</html>"):

            generator = WebPageGenerator(config)
            stats = generator.generate_all_pages(presentations)

            assert stats["total"] == 2
            assert stats["successful"] == 2
            assert stats["failed"] == 0

            assert (test_output_dir / "assets").exists()

            slug0 = presentations[0].info.slug
            slug1 = presentations[1].info.slug
            assert (test_output_dir / slug0 / "index.html").exists()
            assert (test_output_dir / slug1 / "index.html").exists()
            assert (test_output_dir / "index.html").exists()

    def test_website_generation_with_mixed_single_and_multiple_presentations(self, tmp_path):
        """Test that website generation works correctly with both single and multiple presentations."""
        from main import DecksetWebsiteGenerator
        from models import GeneratorConfig
        
        config = GeneratorConfig()
        config.exclude_folders = [f for f in config.exclude_folders if f != "Examples"]
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
        
        # Verify new output layout: <slug>/index.html
        single_html = output_dir / "single_presentation" / "index.html"
        assert single_html.exists()

        example1_html = output_dir / "examples" / "10-first-example" / "index.html"
        example2_html = output_dir / "examples" / "20-second-example" / "index.html"
        assert example1_html.exists()
        assert example2_html.exists()

        for path, name in [
            (single_html, "single"),
            (example1_html, "example1"),
            (example2_html, "example2"),
        ]:
            content = path.read_text(encoding="utf-8")
            assert "presentation-container" in content, f"{name} missing presentation container"
            assert "slide-content" in content, f"{name} missing slide content structure"
            assert "slide_styles.css" in content, f"{name} missing enhanced styles"
            assert "MathJax" in content, f"{name} missing MathJax support"
            assert "highlight" in content, f"{name} missing code highlighting"

        homepage = output_dir / "index.html"
        assert homepage.exists()
        homepage_content = homepage.read_text(encoding="utf-8")
        assert "Single Presentation" in homepage_content
        assert "Example - First Example" in homepage_content
        assert "Example - Second Example" in homepage_content

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
        
        config = GeneratorConfig()
        config.exclude_folders = [f for f in config.exclude_folders if f != "Examples"]
        generator = DecksetWebsiteGenerator(config)
        output_dir = test_repo / "output"
        result = generator.generate_website(str(test_repo), str(output_dir))
        
        assert result.get("success", False), f"Generation failed: {result.get('error', 'Unknown error')}"
        
        # New layout: <slug>/index.html
        single_html = output_dir / "single_presentation" / "index.html"
        assert single_html.exists()

        example1_html = output_dir / "examples" / "10-first-example" / "index.html"
        example2_html = output_dir / "examples" / "20-second-example" / "index.html"
        assert example1_html.exists()
        assert example2_html.exists()

        single_content = single_html.read_text(encoding="utf-8")
        example1_content = example1_html.read_text(encoding="utf-8")

        # Single: site/single_presentation/index.html → ../slide_styles.css
        assert 'href="../slide_styles.css"' in single_content
        assert 'src="../assets/js/slide-viewer.js"' in single_content

        # Nested: site/examples/10-first-example/index.html → ../../slide_styles.css
        assert 'href="../../slide_styles.css"' in example1_content
        assert 'src="../../assets/js/slide-viewer.js"' in example1_content

        # Cross-check incorrect depths
        assert 'href="../slide_styles.css"' not in example1_content
        assert 'href="../../slide_styles.css"' not in single_content