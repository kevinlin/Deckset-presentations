"""
Tests for the WebPageGenerator class.

This module contains tests for the HTML generation functionality,
including presentation pages and homepage generation.
"""

import os
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from models import (
    PresentationInfo,
    Slide,
    ProcessedPresentation,
    GeneratorConfig,
    TemplateRenderingError
)
from generator import WebPageGenerator


@pytest.fixture
def config():
    """Create a test configuration."""
    return GeneratorConfig(
        output_dir="test_output",
        template_dir="templates",
        slides_dir="slides",
        fallback_image="slides/redacted.png"
    )


@pytest.fixture
def presentation_info():
    """Create a test presentation info."""
    return PresentationInfo(
        folder_name="test-presentation",
        folder_path="test-presentation",
        markdown_path="test-presentation/test.md",
        title="Test Presentation",
        preview_image="test-presentation/preview.png",
        slide_count=3,
        last_modified=datetime.now()
    )


@pytest.fixture
def slides():
    """Create test slides."""
    return [
        Slide(index=1, content="# Slide 1", notes="Notes for slide 1", image_path="test-presentation/slide1.png"),
        Slide(index=2, content="# Slide 2", notes="Notes for slide 2", image_path="test-presentation/slide2.png"),
        Slide(index=3, content="# Slide 3", notes="", image_path=None)
    ]


@pytest.fixture
def processed_presentation(presentation_info, slides):
    """Create a test processed presentation."""
    return ProcessedPresentation(
        info=presentation_info,
        slides=slides,
        metadata={"theme": "default"}
    )


@pytest.fixture
def presentation_list(presentation_info):
    """Create a list of presentation infos."""
    return [
        presentation_info,
        PresentationInfo(
            folder_name="another-presentation",
            folder_path="another-presentation",
            markdown_path="another-presentation/another.md",
            title="Another Presentation",
            preview_image=None,
            slide_count=2,
            last_modified=datetime.now()
        )
    ]


class TestWebPageGenerator:
    """Tests for the WebPageGenerator class."""

    def test_init(self, config):
        """Test initialization of WebPageGenerator."""
        generator = WebPageGenerator(config)
        assert generator.config == config
        assert generator.template_manager is not None

    @patch('templates.TemplateManager.render_presentation')
    def test_generate_presentation_page(self, mock_render, config, processed_presentation, tmp_path):
        """Test generating a presentation page."""
        # Setup
        mock_render.return_value = "<html>Test content</html>"
        generator = WebPageGenerator(config)
        output_path = tmp_path / "test.html"
        
        # Execute
        generator.generate_presentation_page(processed_presentation, output_path)
        
        # Verify
        assert output_path.exists()
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert content == "<html>Test content</html>"
        
        # Verify template manager was called correctly
        mock_render.assert_called_once()
        args, _ = mock_render.call_args
        assert args[0] == processed_presentation

    @patch('templates.TemplateManager.render_presentation')
    def test_generate_presentation_page_error(self, mock_render, config, processed_presentation, tmp_path):
        """Test error handling when generating a presentation page."""
        # Setup
        mock_render.side_effect = Exception("Template rendering failed")
        generator = WebPageGenerator(config)
        output_path = tmp_path / "test.html"
        
        # Execute and verify
        with pytest.raises(TemplateRenderingError):
            generator.generate_presentation_page(processed_presentation, output_path)
        
        # Verify file was not created
        assert not output_path.exists()

    @patch('templates.TemplateManager.render_homepage')
    def test_generate_homepage(self, mock_render, config, presentation_list, tmp_path):
        """Test generating the homepage."""
        # Setup
        mock_render.return_value = "<html>Homepage content</html>"
        generator = WebPageGenerator(config)
        output_path = tmp_path / "index.html"
        
        # Execute
        generator.generate_homepage(presentation_list, output_path)
        
        # Verify
        assert output_path.exists()
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert content == "<html>Homepage content</html>"
        
        # Verify template manager was called correctly
        mock_render.assert_called_once()
        args, _ = mock_render.call_args
        assert len(args[0]) == len(presentation_list)

    @patch('templates.TemplateManager.render_homepage')
    def test_generate_homepage_error(self, mock_render, config, presentation_list, tmp_path):
        """Test error handling when generating the homepage."""
        # Setup
        mock_render.side_effect = Exception("Homepage rendering failed")
        generator = WebPageGenerator(config)
        output_path = tmp_path / "index.html"
        
        # Execute and verify
        with pytest.raises(TemplateRenderingError):
            generator.generate_homepage(presentation_list, output_path)
        
        # Verify file was not created
        assert not output_path.exists()

    def test_process_slide_images(self, config, processed_presentation):
        """Test processing slide images with fallbacks."""
        # Setup
        generator = WebPageGenerator(config)
        
        # Execute
        generator._process_slide_images(processed_presentation)
        
        # Verify fallback image is set for missing image
        assert processed_presentation.slides[2].image_path == f"/{config.fallback_image}"
        
        # Verify other slides have web paths
        assert processed_presentation.slides[0].image_path.startswith(f"/{config.slides_dir}/")
        assert processed_presentation.slides[1].image_path.startswith(f"/{config.slides_dir}/")
        
    def test_process_preview_images(self, config, presentation_list, tmp_path, monkeypatch):
        """Test processing preview images with fallbacks."""
        # Setup
        generator = WebPageGenerator(config)
        
        # Create a temporary image file for testing
        test_image_dir = tmp_path / "test-presentation"
        test_image_dir.mkdir(parents=True)
        test_image_path = test_image_dir / "slide1.png"
        with open(test_image_path, 'w') as f:
            f.write("dummy image content")
            
        # Update the first presentation to use the test image
        presentation_list[0].preview_image = str(test_image_path)
        
        # Patch the exists method to return True for our test image
        original_exists = Path.exists
        def mock_exists(self):
            if str(self) == str(test_image_path):
                return True
            return original_exists(self)
        monkeypatch.setattr(Path, "exists", mock_exists)
        
        # Execute
        generator._process_preview_images(presentation_list)
        
        # Verify preview image paths are updated
        assert presentation_list[0].preview_image.startswith("/images/")
        assert presentation_list[0].preview_image.endswith("-preview.png")
        
        # Verify fallback image is set for missing preview
        assert presentation_list[1].preview_image == f"/{config.fallback_image}"

    @patch('generator.WebPageGenerator.generate_presentation_page')
    @patch('generator.WebPageGenerator.generate_homepage')
    def test_generate_all_pages(self, mock_homepage, mock_presentation, config, processed_presentation):
        """Test generating all pages."""
        # Setup
        generator = WebPageGenerator(config)
        presentations = [processed_presentation]
        
        # Execute
        stats = generator.generate_all_pages(presentations)
        
        # Verify
        assert stats["total"] == 1
        assert stats["successful"] == 1
        assert stats["failed"] == 0
        assert len(stats["errors"]) == 0
        
        # Verify methods were called
        mock_presentation.assert_called_once()
        mock_homepage.assert_called_once()

    @patch('generator.WebPageGenerator.generate_presentation_page')
    @patch('generator.WebPageGenerator.generate_homepage')
    def test_generate_all_pages_with_errors(self, mock_homepage, mock_presentation, config, processed_presentation):
        """Test generating all pages with errors."""
        # Setup
        mock_presentation.side_effect = TemplateRenderingError("Failed to render")
        generator = WebPageGenerator(config)
        presentations = [processed_presentation]
        
        # Execute
        stats = generator.generate_all_pages(presentations)
        
        # Verify
        assert stats["total"] == 1
        assert stats["successful"] == 0
        assert stats["failed"] == 1
        assert len(stats["errors"]) == 1
        assert "Failed to render" in stats["errors"][0]["error"]
        
        # Verify homepage was still attempted
        mock_homepage.assert_called_once()
        
    def test_homepage_with_multiple_presentations(self, config, tmp_path):
        """Test generating homepage with multiple presentations."""
        # Setup
        generator = WebPageGenerator(config)
        
        # Create multiple presentations with different last_modified dates
        presentations = [
            PresentationInfo(
                folder_name="presentation1",
                folder_path="presentation1",
                markdown_path="presentation1/test.md",
                title="Presentation 1",
                preview_image=None,
                slide_count=5,
                last_modified=datetime(2023, 1, 1)
            ),
            PresentationInfo(
                folder_name="presentation2",
                folder_path="presentation2",
                markdown_path="presentation2/test.md",
                title="Presentation 2",
                preview_image=None,
                slide_count=3,
                last_modified=datetime(2023, 2, 1)
            ),
            PresentationInfo(
                folder_name="presentation3",
                folder_path="presentation3",
                markdown_path="presentation3/test.md",
                title="Presentation 3",
                preview_image=None,
                slide_count=7,
                last_modified=datetime(2023, 3, 1)
            )
        ]
        
        # Mock the template manager's render_homepage method
        with patch('templates.TemplateManager.render_homepage') as mock_render:
            mock_render.return_value = "<html>Homepage with multiple presentations</html>"
            output_path = tmp_path / "index.html"
            
            # Execute
            generator.generate_homepage(presentations, output_path)
            
            # Verify
            mock_render.assert_called_once()
            args, _ = mock_render.call_args
            
            # Verify presentations are sorted by last_modified (newest first)
            sorted_presentations = args[0]
            assert len(sorted_presentations) == 3
            assert sorted_presentations[0].folder_name == "presentation3"
            assert sorted_presentations[1].folder_name == "presentation2"
            assert sorted_presentations[2].folder_name == "presentation1"
            
            # Verify all presentations have preview images set (fallbacks)
            for presentation in sorted_presentations:
                assert presentation.preview_image is not None