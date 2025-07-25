"""
Unit tests for the MediaProcessor class.

Tests cover image processing, video/audio processing, modifier parsing,
and all core functionality required for Deckset media compatibility.
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from media_processor import MediaProcessor
from models import (
    ProcessedImage, ProcessedVideo, ProcessedAudio, ImageModifiers, MediaModifiers,
    ImageGrid, SlideContext, DecksetConfig, SlideConfig, MediaProcessingError
)


class TestMediaProcessor:
    """Test suite for MediaProcessor functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = MediaProcessor(base_path=self.temp_dir, output_path=os.path.join(self.temp_dir, "docs"))
        
        # Create test slide context
        self.slide_context = SlideContext(
            slide_index=1,
            total_slides=5,
            presentation_path=os.path.join(self.temp_dir, "test-presentation"),
            config=DecksetConfig(),
            slide_config=SlideConfig()
        )
        
        # Create test presentation directory
        os.makedirs(self.slide_context.presentation_path, exist_ok=True)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_parse_image_modifiers_background_default(self):
        """Test parsing image modifiers with default background placement."""
        modifiers = self.processor.parse_image_modifiers("")
        
        assert modifiers.placement == "background"
        assert modifiers.scaling == "cover"
        assert modifiers.filter == "original"
        assert modifiers.corner_radius is None
    
    def test_parse_image_modifiers_inline(self):
        """Test parsing inline image modifiers."""
        modifiers = self.processor.parse_image_modifiers("inline")
        
        assert modifiers.placement == "inline"
        assert modifiers.scaling == "fit"
        assert modifiers.filter == "original"
    
    def test_parse_image_modifiers_left_right(self):
        """Test parsing left and right placement modifiers."""
        left_modifiers = self.processor.parse_image_modifiers("left")
        right_modifiers = self.processor.parse_image_modifiers("right")
        
        assert left_modifiers.placement == "left"
        assert right_modifiers.placement == "right"
    
    def test_parse_image_modifiers_scaling(self):
        """Test parsing scaling modifiers."""
        fit_modifiers = self.processor.parse_image_modifiers("fit")
        fill_modifiers = self.processor.parse_image_modifiers("fill")
        original_modifiers = self.processor.parse_image_modifiers("original")
        
        assert fit_modifiers.scaling == "fit"
        assert fill_modifiers.scaling == "fill"
        assert original_modifiers.scaling == "original"
    
    def test_parse_image_modifiers_percentage(self):
        """Test parsing percentage scaling modifiers."""
        modifiers = self.processor.parse_image_modifiers("inline 50%")
        
        assert modifiers.placement == "inline"
        assert modifiers.scaling == "50%"
    
    def test_parse_image_modifiers_filter(self):
        """Test parsing filter modifiers."""
        filtered_modifiers = self.processor.parse_image_modifiers("filtered")
        original_modifiers = self.processor.parse_image_modifiers("original")
        
        assert filtered_modifiers.filter == "filtered"
        assert original_modifiers.filter == "original"
    
    def test_parse_image_modifiers_corner_radius(self):
        """Test parsing corner radius modifiers."""
        modifiers = self.processor.parse_image_modifiers("corner-radius(10)")
        
        assert modifiers.corner_radius == 10
    
    def test_parse_image_modifiers_complex(self):
        """Test parsing complex modifier combinations."""
        modifiers = self.processor.parse_image_modifiers("inline fill filtered corner-radius(15)")
        
        assert modifiers.placement == "inline"
        assert modifiers.scaling == "fill"
        assert modifiers.filter == "filtered"
        assert modifiers.corner_radius == 15
    
    def test_parse_media_modifiers_default(self):
        """Test parsing media modifiers with defaults."""
        modifiers = self.processor.parse_media_modifiers("")
        
        assert modifiers.placement == "inline"
        assert modifiers.scaling == "fit"
        assert modifiers.autoplay is False
        assert modifiers.loop is False
        assert modifiers.mute is False
        assert modifiers.hide is False
    
    def test_parse_media_modifiers_placement(self):
        """Test parsing media placement modifiers."""
        left_modifiers = self.processor.parse_media_modifiers("left")
        right_modifiers = self.processor.parse_media_modifiers("right")
        background_modifiers = self.processor.parse_media_modifiers("background")
        
        assert left_modifiers.placement == "left"
        assert right_modifiers.placement == "right"
        assert background_modifiers.placement == "background"
    
    def test_parse_media_modifiers_playback(self):
        """Test parsing media playback modifiers."""
        modifiers = self.processor.parse_media_modifiers("autoplay loop mute hide")
        
        assert modifiers.autoplay is True
        assert modifiers.loop is True
        assert modifiers.mute is True
        assert modifiers.hide is True
    
    def test_parse_media_modifiers_scaling(self):
        """Test parsing media scaling modifiers."""
        fit_modifiers = self.processor.parse_media_modifiers("fit")
        fill_modifiers = self.processor.parse_media_modifiers("fill")
        percentage_modifiers = self.processor.parse_media_modifiers("75%")
        
        assert fit_modifiers.scaling == "fit"
        assert fill_modifiers.scaling == "fill"
        assert percentage_modifiers.scaling == "75%"
    
    def test_process_image_basic(self):
        """Test basic image processing."""
        # Create test image file
        test_image_path = os.path.join(self.slide_context.presentation_path, "test.jpg")
        with open(test_image_path, 'w') as f:
            f.write("fake image content")
        
        image_syntax = "![](test.jpg)"
        processed = self.processor.process_image(image_syntax, self.slide_context)
        
        assert isinstance(processed, ProcessedImage)
        assert processed.src_path == test_image_path
        assert processed.web_path == "slides/test-presentation/test.jpg"
        assert processed.modifiers.placement == "background"
        assert processed.alt_text == ""
    
    def test_process_image_with_modifiers(self):
        """Test image processing with modifiers."""
        # Create test image file
        test_image_path = os.path.join(self.slide_context.presentation_path, "test.jpg")
        with open(test_image_path, 'w') as f:
            f.write("fake image content")
        
        image_syntax = "![inline fit filtered](test.jpg)"
        processed = self.processor.process_image(image_syntax, self.slide_context)
        
        assert processed.modifiers.placement == "inline"
        assert processed.modifiers.scaling == "fit"
        assert processed.modifiers.filter == "filtered"
        assert processed.alt_text == "inline fit filtered"
    
    def test_process_image_invalid_syntax(self):
        """Test image processing with invalid syntax."""
        with pytest.raises(MediaProcessingError) as exc_info:
            self.processor.process_image("invalid syntax", self.slide_context)
        
        assert "Invalid image syntax" in str(exc_info.value)
    
    def test_process_video_local(self):
        """Test local video processing."""
        # Create test video file
        test_video_path = os.path.join(self.slide_context.presentation_path, "test.mp4")
        with open(test_video_path, 'w') as f:
            f.write("fake video content")
        
        video_syntax = "![autoplay loop](test.mp4)"
        processed = self.processor.process_video(video_syntax, self.slide_context)
        
        assert isinstance(processed, ProcessedVideo)
        assert processed.src_path == test_video_path
        assert processed.web_path == "slides/test-presentation/test.mp4"
        assert processed.embed_type == "local"
        assert processed.embed_url is None
        assert processed.modifiers.autoplay is True
        assert processed.modifiers.loop is True
    
    def test_process_video_youtube(self):
        """Test YouTube video processing."""
        video_syntax = "![autoplay](https://www.youtube.com/watch?v=dQw4w9WgXcQ)"
        processed = self.processor.process_video(video_syntax, self.slide_context)
        
        assert processed.embed_type == "youtube"
        assert processed.embed_url == "https://www.youtube.com/embed/dQw4w9WgXcQ"
        assert processed.modifiers.autoplay is True
    
    def test_process_video_youtube_short_url(self):
        """Test YouTube short URL processing."""
        video_syntax = "![](https://youtu.be/dQw4w9WgXcQ)"
        processed = self.processor.process_video(video_syntax, self.slide_context)
        
        assert processed.embed_type == "youtube"
        assert processed.embed_url == "https://www.youtube.com/embed/dQw4w9WgXcQ"
    
    def test_process_video_youtube_embed_url(self):
        """Test YouTube embed URL processing."""
        video_syntax = "![](https://www.youtube.com/embed/dQw4w9WgXcQ)"
        processed = self.processor.process_video(video_syntax, self.slide_context)
        
        assert processed.embed_type == "youtube"
        assert processed.embed_url == "https://www.youtube.com/embed/dQw4w9WgXcQ"
    
    def test_process_video_invalid_syntax(self):
        """Test video processing with invalid syntax."""
        with pytest.raises(MediaProcessingError) as exc_info:
            self.processor.process_video("invalid syntax", self.slide_context)
        
        assert "Invalid video syntax" in str(exc_info.value)
    
    def test_process_audio_basic(self):
        """Test basic audio processing."""
        # Create test audio file
        test_audio_path = os.path.join(self.slide_context.presentation_path, "test.mp3")
        with open(test_audio_path, 'w') as f:
            f.write("fake audio content")
        
        audio_syntax = "![autoplay mute](test.mp3)"
        processed = self.processor.process_audio(audio_syntax, self.slide_context)
        
        assert isinstance(processed, ProcessedAudio)
        assert processed.src_path == test_audio_path
        assert processed.web_path == "slides/test-presentation/test.mp3"
        assert processed.modifiers.autoplay is True
        assert processed.modifiers.mute is True
    
    def test_process_audio_invalid_syntax(self):
        """Test audio processing with invalid syntax."""
        with pytest.raises(MediaProcessingError) as exc_info:
            self.processor.process_audio("invalid syntax", self.slide_context)
        
        assert "Invalid audio syntax" in str(exc_info.value)
    
    @patch('shutil.copy2')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_optimize_image_for_web_success(self, mock_makedirs, mock_exists, mock_copy):
        """Test successful image optimization."""
        mock_exists.return_value = True
        
        input_path = "/path/to/input.jpg"
        output_path = "/path/to/output.jpg"
        
        result = self.processor.optimize_image_for_web(input_path, output_path)
        
        assert result == output_path
        mock_makedirs.assert_called_once()
        mock_copy.assert_called_once_with(input_path, output_path)
    
    @patch('os.path.exists')
    def test_optimize_image_for_web_missing_file(self, mock_exists):
        """Test image optimization with missing file."""
        mock_exists.return_value = False
        
        with pytest.raises(MediaProcessingError) as exc_info:
            self.processor.optimize_image_for_web("/nonexistent.jpg", "/output.jpg")
        
        assert "Image file not found" in str(exc_info.value)
    
    def test_create_image_grid_single_image(self):
        """Test image grid creation with single image."""
        image = ProcessedImage(
            src_path="/test.jpg",
            web_path="slides/test.jpg",
            modifiers=ImageModifiers("inline", "fit", "original")
        )
        
        grid = self.processor.create_image_grid([image])
        
        assert grid.columns == 1
        assert len(grid.images) == 1
        assert grid.images[0].grid_position == (0, 0)
    
    def test_create_image_grid_two_images(self):
        """Test image grid creation with two images."""
        images = [
            ProcessedImage("/test1.jpg", "slides/test1.jpg", ImageModifiers("inline", "fit", "original")),
            ProcessedImage("/test2.jpg", "slides/test2.jpg", ImageModifiers("inline", "fit", "original"))
        ]
        
        grid = self.processor.create_image_grid(images)
        
        assert grid.columns == 2
        assert len(grid.images) == 2
        assert grid.images[0].grid_position == (0, 0)
        assert grid.images[1].grid_position == (0, 1)
    
    def test_create_image_grid_four_images(self):
        """Test image grid creation with four images."""
        images = [
            ProcessedImage(f"/test{i}.jpg", f"slides/test{i}.jpg", ImageModifiers("inline", "fit", "original"))
            for i in range(1, 5)
        ]
        
        grid = self.processor.create_image_grid(images)
        
        assert grid.columns == 2
        assert len(grid.images) == 4
        assert grid.images[0].grid_position == (0, 0)
        assert grid.images[1].grid_position == (0, 1)
        assert grid.images[2].grid_position == (1, 0)
        assert grid.images[3].grid_position == (1, 1)
    
    def test_create_image_grid_six_images(self):
        """Test image grid creation with six images."""
        images = [
            ProcessedImage(f"/test{i}.jpg", f"slides/test{i}.jpg", ImageModifiers("inline", "fit", "original"))
            for i in range(1, 7)
        ]
        
        grid = self.processor.create_image_grid(images)
        
        assert grid.columns == 3
        assert len(grid.images) == 6
        assert grid.images[0].grid_position == (0, 0)
        assert grid.images[1].grid_position == (0, 1)
        assert grid.images[2].grid_position == (0, 2)
        assert grid.images[3].grid_position == (1, 0)
        assert grid.images[4].grid_position == (1, 1)
        assert grid.images[5].grid_position == (1, 2)
    
    def test_create_image_grid_empty(self):
        """Test image grid creation with empty list."""
        grid = self.processor.create_image_grid([])
        
        assert grid.columns == 1
        assert len(grid.images) == 0
    
    def test_get_web_path(self):
        """Test web path generation."""
        web_path = self.processor._get_web_path("image.jpg", "/path/to/presentation-folder")
        
        assert web_path == "slides/presentation-folder/image.jpg"
    
    def test_is_video_file(self):
        """Test video file detection."""
        assert self.processor._is_video_file("test.mp4") is True
        assert self.processor._is_video_file("test.mov") is True
        assert self.processor._is_video_file("test.avi") is True
        assert self.processor._is_video_file("test.webm") is True
        assert self.processor._is_video_file("test.jpg") is False
        assert self.processor._is_video_file("test.mp3") is False
    
    def test_is_audio_file(self):
        """Test audio file detection."""
        assert self.processor._is_audio_file("test.mp3") is True
        assert self.processor._is_audio_file("test.wav") is True
        assert self.processor._is_audio_file("test.ogg") is True
        assert self.processor._is_audio_file("test.m4a") is True
        assert self.processor._is_audio_file("test.jpg") is False
        assert self.processor._is_audio_file("test.mp4") is False
    
    def test_is_youtube_url(self):
        """Test YouTube URL detection."""
        assert self.processor._is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True
        assert self.processor._is_youtube_url("https://youtu.be/dQw4w9WgXcQ") is True
        assert self.processor._is_youtube_url("https://www.youtube.com/embed/dQw4w9WgXcQ") is True
        assert self.processor._is_youtube_url("https://example.com/video.mp4") is False
        assert self.processor._is_youtube_url("local_video.mp4") is False


class TestMediaProcessingError:
    """Test suite for MediaProcessingError exception."""
    
    def test_error_with_media_info(self):
        """Test error creation with media path and type."""
        error = MediaProcessingError("Test error", media_path="/test.jpg", media_type="image")
        
        assert str(error) == "Test error"
        assert error.media_path == "/test.jpg"
        assert error.media_type == "image"
    
    def test_error_minimal(self):
        """Test error creation with minimal information."""
        error = MediaProcessingError("Simple error")
        
        assert str(error) == "Simple error"
        assert error.media_path is None
        assert error.media_type is None


class TestMediaProcessorIntegration:
    """Integration tests for MediaProcessor with real file scenarios."""
    
    def setup_method(self):
        """Set up test fixtures with real files."""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = MediaProcessor(base_path=self.temp_dir, output_path=os.path.join(self.temp_dir, "docs"))
        
        # Create test presentation directory
        self.presentation_path = os.path.join(self.temp_dir, "test-presentation")
        os.makedirs(self.presentation_path, exist_ok=True)
        
        self.slide_context = SlideContext(
            slide_index=1,
            total_slides=5,
            presentation_path=self.presentation_path,
            config=DecksetConfig(),
            slide_config=SlideConfig()
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complex_image_processing_workflow(self):
        """Test complex image processing workflow."""
        # Create test images
        for i in range(3):
            image_path = os.path.join(self.presentation_path, f"image{i}.jpg")
            with open(image_path, 'w') as f:
                f.write(f"fake image {i} content")
        
        # Process different types of images
        background_image = self.processor.process_image("![filtered](image0.jpg)", self.slide_context)
        inline_image = self.processor.process_image("![inline fit](image1.jpg)", self.slide_context)
        positioned_image = self.processor.process_image("![left 50% corner-radius(10)](image2.jpg)", self.slide_context)
        
        # Verify background image
        assert background_image.modifiers.placement == "background"
        assert background_image.modifiers.filter == "filtered"
        
        # Verify inline image
        assert inline_image.modifiers.placement == "inline"
        assert inline_image.modifiers.scaling == "fit"
        
        # Verify positioned image
        assert positioned_image.modifiers.placement == "left"
        assert positioned_image.modifiers.scaling == "50%"
        assert positioned_image.modifiers.corner_radius == 10
        
        # Create image grid
        inline_images = [inline_image, positioned_image]
        grid = self.processor.create_image_grid(inline_images)
        
        assert grid.columns == 2
        assert len(grid.images) == 2
    
    def test_mixed_media_processing(self):
        """Test processing of mixed media types."""
        # Create test files
        image_path = os.path.join(self.presentation_path, "test.jpg")
        video_path = os.path.join(self.presentation_path, "test.mp4")
        audio_path = os.path.join(self.presentation_path, "test.mp3")
        
        with open(image_path, 'w') as f:
            f.write("fake image")
        with open(video_path, 'w') as f:
            f.write("fake video")
        with open(audio_path, 'w') as f:
            f.write("fake audio")
        
        # Process different media types
        image = self.processor.process_image("![inline](test.jpg)", self.slide_context)
        video = self.processor.process_video("![autoplay loop](test.mp4)", self.slide_context)
        audio = self.processor.process_audio("![mute](test.mp3)", self.slide_context)
        youtube = self.processor.process_video("![](https://youtu.be/dQw4w9WgXcQ)", self.slide_context)
        
        # Verify all media processed correctly
        assert isinstance(image, ProcessedImage)
        assert isinstance(video, ProcessedVideo)
        assert isinstance(audio, ProcessedAudio)
        assert isinstance(youtube, ProcessedVideo)
        
        assert image.modifiers.placement == "inline"
        assert video.modifiers.autoplay is True
        assert video.modifiers.loop is True
        assert audio.modifiers.mute is True
        assert youtube.embed_type == "youtube"


if __name__ == "__main__":
    pytest.main([__file__])