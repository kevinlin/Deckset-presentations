"""
Media processor for handling images, videos, and audio in Deckset presentations.

This module provides processing capabilities for all types of media with Deckset-specific
modifiers and web optimization features.
"""

import re
import os
from typing import List, Optional
from urllib.parse import urlparse
from enhanced_models import (
    ProcessedImage, ProcessedVideo, ProcessedAudio, ImageModifiers, MediaModifiers,
    ImageGrid, SlideContext, MediaProcessingError, MediaProcessorInterface
)


class MediaProcessor(MediaProcessorInterface):
    """Processor for media files with Deckset modifier support."""
    
    def __init__(self, base_path: str = ".", output_path: str = "docs"):
        """Initialize the media processor."""
        self.base_path = base_path
        self.output_path = output_path
        
        # Image syntax pattern: ![modifiers](path)
        self.image_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
        
        # Video/audio extensions
        self.video_extensions = {'.mp4', '.mov', '.avi', '.webm', '.mkv', '.m4v'}
        self.audio_extensions = {'.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac'}
        
        # YouTube URL patterns
        self.youtube_patterns = [
            re.compile(r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)'),
            re.compile(r'youtube\.com/embed/([a-zA-Z0-9_-]+)'),
        ]
    
    def process_image(self, image_syntax: str, slide_context: SlideContext) -> ProcessedImage:
        """Process image with Deckset modifiers."""
        image_path = None
        try:
            match = self.image_pattern.match(image_syntax.strip())
            if not match:
                raise MediaProcessingError(f"Invalid image syntax: {image_syntax}")
            
            alt_text = match.group(1)
            image_path = match.group(2)
            
            # Parse modifiers from alt text
            modifiers = self.parse_image_modifiers(alt_text)
            
            # Resolve image path
            full_path = os.path.join(slide_context.presentation_path, image_path)
            web_path = self._get_web_path(image_path, slide_context.presentation_path)
            
            return ProcessedImage(
                src_path=full_path,
                web_path=web_path,
                modifiers=modifiers,
                alt_text=alt_text
            )
            
        except MediaProcessingError:
            raise
        except Exception as e:
            raise MediaProcessingError(f"Error processing image: {str(e)}", image_path, "image")
    
    def process_video(self, video_syntax: str, slide_context: SlideContext) -> ProcessedVideo:
        """Process video with Deckset modifiers."""
        video_path = None
        try:
            match = self.image_pattern.match(video_syntax.strip())
            if not match:
                raise MediaProcessingError(f"Invalid video syntax: {video_syntax}")
            
            alt_text = match.group(1)
            video_path = match.group(2)
            
            # Parse modifiers from alt text
            modifiers = self.parse_media_modifiers(alt_text)
            
            # Check if it's a YouTube URL
            embed_url = None
            embed_type = "local"
            
            for pattern in self.youtube_patterns:
                youtube_match = pattern.search(video_path)
                if youtube_match:
                    video_id = youtube_match.group(1)
                    embed_url = f"https://www.youtube.com/embed/{video_id}"
                    embed_type = "youtube"
                    break
            
            if embed_type == "local":
                # Local video file
                full_path = os.path.join(slide_context.presentation_path, video_path)
                web_path = self._get_web_path(video_path, slide_context.presentation_path)
            else:
                # External video
                full_path = video_path
                web_path = video_path
            
            return ProcessedVideo(
                src_path=full_path,
                web_path=web_path,
                modifiers=modifiers,
                embed_type=embed_type,
                embed_url=embed_url
            )
            
        except MediaProcessingError:
            raise
        except Exception as e:
            raise MediaProcessingError(f"Error processing video: {str(e)}", video_path, "video")
    
    def process_audio(self, audio_syntax: str, slide_context: SlideContext) -> ProcessedAudio:
        """Process audio with Deckset modifiers."""
        audio_path = None
        try:
            match = self.image_pattern.match(audio_syntax.strip())
            if not match:
                raise MediaProcessingError(f"Invalid audio syntax: {audio_syntax}")
            
            alt_text = match.group(1)
            audio_path = match.group(2)
            
            # Parse modifiers from alt text
            modifiers = self.parse_media_modifiers(alt_text)
            
            # Resolve audio path
            full_path = os.path.join(slide_context.presentation_path, audio_path)
            web_path = self._get_web_path(audio_path, slide_context.presentation_path)
            
            return ProcessedAudio(
                src_path=full_path,
                web_path=web_path,
                modifiers=modifiers
            )
            
        except MediaProcessingError:
            raise
        except Exception as e:
            raise MediaProcessingError(f"Error processing audio: {str(e)}", audio_path, "audio")
    
    def parse_image_modifiers(self, alt_text: str) -> ImageModifiers:
        """Parse image modifiers from alt text."""
        modifiers = ImageModifiers(
            placement="background",  # Default for images without modifiers
            scaling="cover",
            filter="original"
        )
        
        if not alt_text:
            return modifiers
        
        alt_lower = alt_text.lower()
        
        # Parse placement modifiers
        if "inline" in alt_lower:
            modifiers.placement = "inline"
            modifiers.scaling = "fit"  # Default for inline images
        elif "left" in alt_lower:
            modifiers.placement = "left"
        elif "right" in alt_lower:
            modifiers.placement = "right"
        
        # Parse scaling modifiers
        if "fit" in alt_lower:
            modifiers.scaling = "fit"
        elif "fill" in alt_lower:
            modifiers.scaling = "fill"
        elif "original" in alt_lower:
            modifiers.scaling = "original"
        
        # Parse percentage scaling
        percentage_match = re.search(r'(\d+)%', alt_text)
        if percentage_match:
            modifiers.scaling = f"{percentage_match.group(1)}%"
        
        # Parse filter modifiers
        if "filtered" in alt_lower:
            modifiers.filter = "filtered"
        elif "original" in alt_lower and "filter" not in alt_lower:
            modifiers.filter = "original"
        
        # Parse corner radius
        corner_match = re.search(r'corner-radius\((\d+)\)', alt_text)
        if corner_match:
            modifiers.corner_radius = int(corner_match.group(1))
        
        return modifiers
    
    def parse_media_modifiers(self, alt_text: str) -> MediaModifiers:
        """Parse media modifiers from alt text."""
        modifiers = MediaModifiers(
            placement="inline",
            scaling="fit"
        )
        
        if not alt_text:
            return modifiers
        
        alt_lower = alt_text.lower()
        
        # Parse placement modifiers
        if "left" in alt_lower:
            modifiers.placement = "left"
        elif "right" in alt_lower:
            modifiers.placement = "right"
        elif "background" in alt_lower:
            modifiers.placement = "background"
        
        # Parse playback modifiers
        if "autoplay" in alt_lower:
            modifiers.autoplay = True
        if "loop" in alt_lower:
            modifiers.loop = True
        if "mute" in alt_lower:
            modifiers.mute = True
        if "hide" in alt_lower:
            modifiers.hide = True
        
        # Parse scaling modifiers
        if "fit" in alt_lower:
            modifiers.scaling = "fit"
        elif "fill" in alt_lower:
            modifiers.scaling = "fill"
        
        # Parse percentage scaling
        percentage_match = re.search(r'(\d+)%', alt_text)
        if percentage_match:
            modifiers.scaling = f"{percentage_match.group(1)}%"
        
        return modifiers
    
    def optimize_image_for_web(self, image_path: str, output_path: str) -> str:
        """Optimize image for web delivery."""
        # For now, just copy the image to the output path
        # In a full implementation, this would resize, compress, and convert images
        try:
            import shutil
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Copy image to output path
            if os.path.exists(image_path):
                shutil.copy2(image_path, output_path)
                return output_path
            else:
                raise MediaProcessingError(f"Image file not found: {image_path}")
                
        except Exception as e:
            raise MediaProcessingError(f"Error optimizing image: {str(e)}", image_path, "image")
    
    def create_image_grid(self, images: List[ProcessedImage]) -> ImageGrid:
        """Create grid layout for consecutive inline images."""
        if not images:
            return ImageGrid(images=[], columns=1)
        
        # Determine grid columns based on number of images
        num_images = len(images)
        if num_images == 1:
            columns = 1
        elif num_images == 2:
            columns = 2
        elif num_images <= 4:
            columns = 2
        elif num_images <= 6:
            columns = 3
        else:
            columns = 3  # Max 3 columns for readability
        
        # Set grid positions
        for i, image in enumerate(images):
            row = i // columns
            col = i % columns
            image.grid_position = (row, col)
        
        return ImageGrid(
            images=images,
            columns=columns
        )
    
    def _get_web_path(self, media_path: str, presentation_path: str) -> str:
        """Convert local media path to web-accessible path."""
        # Extract presentation folder name
        presentation_folder = os.path.basename(presentation_path)
        
        # Create web path relative to docs/slides/
        web_path = f"slides/{presentation_folder}/{media_path}"
        
        return web_path
    
    def _is_video_file(self, path: str) -> bool:
        """Check if file is a video based on extension."""
        _, ext = os.path.splitext(path.lower())
        return ext in self.video_extensions
    
    def _is_audio_file(self, path: str) -> bool:
        """Check if file is an audio file based on extension."""
        _, ext = os.path.splitext(path.lower())
        return ext in self.audio_extensions
    
    def _is_youtube_url(self, url: str) -> bool:
        """Check if URL is a YouTube video."""
        for pattern in self.youtube_patterns:
            if pattern.search(url):
                return True
        return False