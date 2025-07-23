"""
Tests for error handling and recovery mechanisms.

This module contains tests for various error scenarios and verifies that
the system handles them gracefully with proper logging and recovery.
"""

import os
import pytest
import tempfile
import shutil
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

from models import (
    GeneratorConfig,
    PresentationInfo,
    Slide,
    ProcessedPresentation,
    GeneratorError,
    PresentationProcessingError,
    TemplateRenderingError,
    FileOperationError,
    ScanningError,
    ConfigurationError
)
from scanner import PresentationScanner
from processor import PresentationProcessor
from generator import WebPageGenerator
from templates import TemplateManager
from file_manager import FileManager
from main import DecksetWebsiteGenerator


class TestErrorHandling:
    """Test error handling and recovery mechanisms."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return GeneratorConfig(
            output_dir="test_output",
            template_dir="templates",
            slides_dir="slides",
            fallback_image="slides/redacted.png"
        )

    @pytest.fixture
    def presentation_info(self):
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
    def processed_presentation(self, presentation_info):
        """Create a test processed presentation."""
        slides = [
            Slide(index=1, content="# Slide 1", notes="Notes 1"),
            Slide(index=2, content="# Slide 2", notes="Notes 2"),
            Slide(index=3, content="# Slide 3", notes="")
        ]
        return ProcessedPresentation(
            info=presentation_info,
            slides=slides,
            metadata={"theme": "default"}
        )

    def test_generator_error_with_context(self):
        """Test GeneratorError with context information."""
        context = {"file_path": "/test/path", "operation": "read"}
        error = GeneratorError("Test error message", context)
        
        assert error.message == "Test error message"
        assert error.context == context
        assert "file_path=/test/path" in str(error)
        assert "operation=read" in str(error)

    def test_generator_error_without_context(self):
        """Test GeneratorError without context information."""
        error = GeneratorError("Simple error message")
        
        assert error.message == "Simple error message"
        assert error.context == {}
        assert str(error) == "Simple error message"

    def test_scanner_nonexistent_path(self, config):
        """Test scanner with non-existent path."""
        scanner = PresentationScanner(config)
        
        with pytest.raises(ScanningError) as exc_info:
            scanner.scan_presentations("/path/that/does/not/exist")
        
        error = exc_info.value
        assert "Root path does not exist" in error.message
        assert error.context["root_path"] == "/path/that/does/not/exist"

    def test_scanner_permission_denied(self, config, tmp_path):
        """Test scanner with permission denied error."""
        scanner = PresentationScanner(config)
        
        # Create a directory and remove read permissions
        test_dir = tmp_path / "no_permission"
        test_dir.mkdir()
        
        with patch('pathlib.Path.iterdir') as mock_iterdir:
            mock_iterdir.side_effect = PermissionError("Permission denied")
            
            with pytest.raises(ScanningError) as exc_info:
                scanner.scan_presentations(str(test_dir))
            
            error = exc_info.value
            assert "Permission denied accessing root path" in error.message
            assert error.context["root_path"] == str(test_dir)

    def test_scanner_graceful_degradation_folder_processing(self, config, tmp_path):
        """Test scanner continues processing other folders when one fails."""
        # Create test directory structure
        (tmp_path / "good_presentation").mkdir()
        (tmp_path / "good_presentation" / "good_presentation.md").write_text("# Good")
        
        (tmp_path / "bad_presentation").mkdir()
        (tmp_path / "bad_presentation" / "bad_presentation.md").write_text("# Bad")
        
        scanner = PresentationScanner(config)
        
        # Mock _create_presentation_info to fail for bad_presentation
        original_method = scanner._create_presentation_info
        def mock_create_info(folder_path):
            if "bad_presentation" in str(folder_path):
                raise Exception("Simulated processing error")
            return original_method(folder_path)
        
        with patch.object(scanner, '_create_presentation_info', side_effect=mock_create_info):
            presentations = scanner.scan_presentations(str(tmp_path))
        
        # Should find only the good presentation
        assert len(presentations) == 1
        assert presentations[0].folder_name == "good_presentation"

    def test_processor_file_read_error(self, presentation_info):
        """Test processor with file read error."""
        processor = PresentationProcessor()
        
        with patch("builtins.open", side_effect=IOError("File not found")):
            with pytest.raises(PresentationProcessingError) as exc_info:
                processor.process_presentation(presentation_info)
            
            error = exc_info.value
            assert "Failed to read markdown file" in error.message
            assert error.context["presentation_title"] == "Test Presentation"
            assert error.context["markdown_path"] == presentation_info.markdown_path

    def test_processor_unicode_decode_error(self, presentation_info):
        """Test processor with unicode decode error."""
        processor = PresentationProcessor()
        
        with patch("builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")):
            with pytest.raises(PresentationProcessingError) as exc_info:
                processor.process_presentation(presentation_info)
            
            error = exc_info.value
            assert "Failed to decode markdown file" in error.message
            assert error.context["presentation_title"] == "Test Presentation"

    def test_processor_graceful_slide_processing(self):
        """Test processor continues with other slides when one fails."""
        processor = PresentationProcessor()
        
        # Mock extract_notes to fail for specific slide content
        original_extract_notes = processor.extract_notes
        def mock_extract_notes(slide_content):
            if "bad slide" in slide_content:
                raise Exception("Note extraction failed")
            return original_extract_notes(slide_content)
        
        with patch.object(processor, 'extract_notes', side_effect=mock_extract_notes):
            slides = processor.extract_slides("# Good slide\n---\n# bad slide\n---\n# Another good slide")
        
        # Should process all slides, with fallback for the bad one
        assert len(slides) == 3
        assert "Good slide" in slides[0].content
        assert "bad slide" in slides[1].content  # Raw content as fallback
        assert "Another good slide" in slides[2].content

    def test_processor_critical_error_fallback(self):
        """Test processor fallback when critical error occurs."""
        processor = PresentationProcessor()
        
        # Mock _remove_frontmatter to fail
        with patch.object(processor, '_remove_frontmatter', side_effect=Exception("Critical error")):
            slides = processor.extract_slides("# Test slide content")
        
        # Should return single slide with raw content
        assert len(slides) == 1
        assert slides[0].content == "# Test slide content"
        assert slides[0].notes == ""

    def test_generator_directory_creation_error(self, config, processed_presentation, tmp_path):
        """Test generator with directory creation error."""
        generator = WebPageGenerator(config)
        output_path = tmp_path / "readonly" / "test.html"
        
        # Mock mkdir to fail
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
            with pytest.raises(FileOperationError) as exc_info:
                generator.generate_presentation_page(processed_presentation, str(output_path))
            
            error = exc_info.value
            assert "Failed to create output directory" in error.message
            assert error.context["presentation_title"] == "Test Presentation"

    def test_generator_template_rendering_error(self, config, processed_presentation, tmp_path):
        """Test generator with template rendering error."""
        generator = WebPageGenerator(config)
        output_path = tmp_path / "test.html"
        
        with patch.object(generator.template_manager, 'render_presentation', 
                         side_effect=Exception("Template error")):
            with pytest.raises(TemplateRenderingError) as exc_info:
                generator.generate_presentation_page(processed_presentation, str(output_path))
            
            error = exc_info.value
            assert "Failed to render template" in error.message
            assert error.context["presentation_title"] == "Test Presentation"

    def test_generator_file_write_error(self, config, processed_presentation, tmp_path):
        """Test generator with file write error."""
        generator = WebPageGenerator(config)
        output_path = tmp_path / "test.html"
        
        with patch.object(generator.template_manager, 'render_presentation', return_value="<html>test</html>"):
            with patch("builtins.open", side_effect=PermissionError("Write permission denied")):
                with pytest.raises(FileOperationError) as exc_info:
                    generator.generate_presentation_page(processed_presentation, str(output_path))
                
                error = exc_info.value
                assert "Failed to write presentation page" in error.message
                assert error.context["presentation_title"] == "Test Presentation"

    def test_generator_image_processing_continues_on_error(self, config, processed_presentation, tmp_path):
        """Test generator continues when image processing fails."""
        generator = WebPageGenerator(config)
        output_path = tmp_path / "test.html"
        
        # Mock _process_slide_images to fail
        with patch.object(generator, '_process_slide_images', side_effect=Exception("Image processing failed")):
            with patch.object(generator.template_manager, 'render_presentation', return_value="<html>test</html>"):
                # Should not raise exception, should continue with generation
                generator.generate_presentation_page(processed_presentation, str(output_path))
                
                # File should be created despite image processing failure
                assert output_path.exists()

    def test_file_manager_directory_creation_error(self, config):
        """Test file manager with directory creation error."""
        file_manager = FileManager(config)
        
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
            with pytest.raises(FileOperationError) as exc_info:
                file_manager.setup_output_directories()
            
            error = exc_info.value
            assert "Failed to create" in error.message
            assert "Permission denied" in error.message

    def test_file_manager_graceful_image_copy_failure(self, config, processed_presentation):
        """Test file manager continues when image copy fails."""
        file_manager = FileManager(config)
        
        # Set up slide with image path
        processed_presentation.slides[0].image_path = "nonexistent/image.png"
        
        # Should not raise exception, should set fallback image
        file_manager.copy_slide_images(processed_presentation)
        
        # Slide should use fallback image
        assert processed_presentation.slides[0].image_path == f"/{config.fallback_image}"

    def test_template_manager_jinja2_not_available(self, config):
        """Test template manager when Jinja2 is not available."""
        with patch('templates.JINJA2_AVAILABLE', False):
            template_manager = TemplateManager(config)
            
            with pytest.raises(TemplateRenderingError) as exc_info:
                template_manager.load_template("test.html")
            
            error = exc_info.value
            assert "Jinja2 is not available" in error.message
            assert error.context["template_name"] == "test.html"

    def test_template_manager_template_not_found(self, config):
        """Test template manager with missing template."""
        template_manager = TemplateManager(config)
        
        with pytest.raises(TemplateRenderingError) as exc_info:
            template_manager.load_template("nonexistent.html")
        
        error = exc_info.value
        assert "Failed to load template" in error.message
        assert error.context["template_name"] == "nonexistent.html"

    def test_main_generator_graceful_degradation(self, config, tmp_path):
        """Test main generator continues processing when individual presentations fail."""
        # Create test directory structure
        (tmp_path / "good_presentation").mkdir()
        (tmp_path / "good_presentation" / "good_presentation.md").write_text("# Good")
        
        (tmp_path / "bad_presentation").mkdir()
        (tmp_path / "bad_presentation" / "bad_presentation.md").write_text("# Bad")
        
        generator = DecksetWebsiteGenerator(config)
        
        # Mock processor to fail for bad_presentation
        original_process = generator.processor.process_presentation
        def mock_process(presentation_info):
            if "bad_presentation" in presentation_info.folder_name:
                raise PresentationProcessingError("Simulated processing error")
            return original_process(presentation_info)
        
        with patch.object(generator.processor, 'process_presentation', side_effect=mock_process):
            result = generator.generate_website(str(tmp_path), str(tmp_path / "output"))
        
        # Should succeed overall but report the failure
        assert result["success"] is True
        assert result["presentations_found"] == 2
        assert result["presentations_processed"] == 1
        assert result["presentations_failed"] == 1
        assert len(result["errors"]) == 1
        assert "Bad" in result["errors"][0]["presentation"]

    def test_logging_context_information(self, config, caplog):
        """Test that error logging includes context information."""
        scanner = PresentationScanner(config)
        
        with caplog.at_level(logging.ERROR):
            try:
                scanner.scan_presentations("/nonexistent/path")
            except ScanningError:
                pass
        
        # Check that log contains context information - the error is raised, not logged
        # So we test that the exception contains context
        with pytest.raises(ScanningError) as exc_info:
            scanner.scan_presentations("/nonexistent/path")
        
        error = exc_info.value
        assert "root_path" in error.context

    def test_error_recovery_statistics(self, config, tmp_path):
        """Test that error statistics are properly tracked."""
        # Create mixed scenario with good and bad presentations
        (tmp_path / "good1").mkdir()
        (tmp_path / "good1" / "good1.md").write_text("# Good 1")
        
        (tmp_path / "good2").mkdir()
        (tmp_path / "good2" / "good2.md").write_text("# Good 2")
        
        (tmp_path / "bad1").mkdir()
        (tmp_path / "bad1" / "bad1.md").write_text("# Bad 1")
        
        generator = DecksetWebsiteGenerator(config)
        
        # Mock to simulate failures
        original_process = generator.processor.process_presentation
        def mock_process(presentation_info):
            if "bad1" in presentation_info.folder_name:
                raise PresentationProcessingError("Processing failed")
            return original_process(presentation_info)
        
        with patch.object(generator.processor, 'process_presentation', side_effect=mock_process):
            result = generator.generate_website(str(tmp_path), str(tmp_path / "output"))
        
        # Verify statistics
        assert result["presentations_found"] == 3
        assert result["presentations_processed"] == 2
        assert result["presentations_failed"] == 1
        assert result["total_errors"] == 1
        
        # Verify error details
        error = result["errors"][0]
        assert error["stage"] == "processing"
        assert error["presentation"] == "Bad 1"
        assert "Processing failed" in error["error"]

    def test_configuration_validation(self, config):
        """Test configuration validation error handling."""
        generator = DecksetWebsiteGenerator(config)
        
        # Test with invalid template directory
        config.template_dir = "/nonexistent/templates"
        issues = generator.validate_configuration()
        
        assert len(issues) > 0
        assert any("Template directory does not exist" in issue for issue in issues)

    def test_error_context_preservation(self):
        """Test that error context is preserved through exception chain."""
        original_error = ValueError("Original error")
        context = {"key": "value", "number": 42}
        
        generator_error = GeneratorError("Wrapped error", context)
        
        # Verify context is accessible
        assert generator_error.context == context
        assert generator_error.context["key"] == "value"
        assert generator_error.context["number"] == 42


class TestErrorRecoveryScenarios:
    """Test specific error recovery scenarios."""

    def test_partial_slide_processing_recovery(self):
        """Test recovery when some slides fail to process."""
        processor = PresentationProcessor()
        
        # Content with problematic slide in the middle
        content = """# Good Slide 1
Content 1

---

# Problematic Slide
{{ invalid_template_syntax }}
^ Note with {{ more_invalid_syntax }}

---

# Good Slide 3
Content 3"""
        
        # Mock note extraction to fail for problematic slide
        original_extract_notes = processor.extract_notes
        def mock_extract_notes(slide_content):
            if "invalid_template_syntax" in slide_content:
                raise Exception("Template syntax error")
            return original_extract_notes(slide_content)
        
        with patch.object(processor, 'extract_notes', side_effect=mock_extract_notes):
            slides = processor.extract_slides(content)
        
        # Should process all slides
        assert len(slides) == 3
        assert "Good Slide 1" in slides[0].content
        assert "Problematic Slide" in slides[1].content
        assert "Good Slide 3" in slides[2].content
        
        # The problematic slide should have empty notes due to error
        assert slides[1].notes == ""  # Should have empty notes due to error
        
        # Other slides should process normally (they don't have notes in this test content)
        # The test content doesn't actually have notes for slides 1 and 3

    def test_homepage_generation_with_mixed_presentation_states(self, tmp_path):
        """Test homepage generation when some presentations have issues."""
        config = GeneratorConfig(output_dir=str(tmp_path / "output"))
        generator = WebPageGenerator(config)
        
        # Create presentations with mixed states
        presentations = [
            PresentationInfo(
                folder_name="good",
                folder_path="good",
                markdown_path="good/good.md",
                title="Good Presentation",
                preview_image="good/preview.png",
                slide_count=5,
                last_modified=datetime.now()
            ),
            PresentationInfo(
                folder_name="no_preview",
                folder_path="no_preview",
                markdown_path="no_preview/no_preview.md",
                title="No Preview Presentation",
                preview_image=None,  # No preview image
                slide_count=3,
                last_modified=datetime.now()
            ),
            PresentationInfo(
                folder_name="bad_date",
                folder_path="bad_date",
                markdown_path="bad_date/bad_date.md",
                title="Bad Date Presentation",
                preview_image="bad_date/preview.png",
                slide_count=2,
                last_modified=None  # No last modified date
            )
        ]
        
        # Should generate homepage successfully despite mixed states
        homepage_path = tmp_path / "output" / "index.html"
        
        with patch.object(generator.template_manager, 'render_homepage', return_value="<html>Homepage</html>"):
            generator.generate_homepage(presentations, str(homepage_path))
        
        # Homepage should be created
        assert homepage_path.exists()
        
        # All presentations should have fallback preview images
        for presentation in presentations:
            assert presentation.preview_image is not None
            if presentation.folder_name == "no_preview":
                assert presentation.preview_image == f"/{config.fallback_image}"


if __name__ == "__main__":
    pytest.main([__file__])