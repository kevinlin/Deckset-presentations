"""
File and asset management for the Deckset Website Generator.

This module handles file operations such as copying slide images,
creating directory structures, and managing assets for the generated website.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Set

from models import GeneratorConfig, ProcessedPresentation, PresentationInfo, FileOperationError


class FileManager:
    """Manages file operations for the website generator."""
    
    def __init__(self, config: GeneratorConfig):
        """
        Initialize the file manager with configuration.
        
        Args:
            config: Generator configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def setup_output_directories(self) -> None:
        """
        Create the necessary output directory structure.
        
        Creates the following directories:
        - output_dir (e.g., docs/)
        - presentations directory (e.g., docs/presentations/)
        - slides directory (e.g., docs/slides/)
        - images directory (e.g., docs/images/)
        - assets directory (e.g., docs/assets/)
        
        Raises:
            FileOperationError: If directory creation fails
        """
        output_dir = Path(self.config.output_dir)
        
        directories_to_create = [
            (output_dir, "main output"),
            (output_dir / "presentations", "presentations"),
            (output_dir / self.config.slides_dir, "slides"),
            (output_dir / "images", "images"),
            (output_dir / "assets", "assets"),
            (output_dir / "assets" / "css", "assets/css"),
            (output_dir / "assets" / "js", "assets/js")
        ]
        
        for dir_path, description in directories_to_create:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Created {description} directory: {dir_path}")
            except (OSError, PermissionError) as e:
                raise FileOperationError(
                    f"Failed to create {description} directory {dir_path}: {e}",
                    context={
                        "directory_path": str(dir_path),
                        "directory_type": description,
                        "output_dir": self.config.output_dir
                    }
                )
        
        self.logger.info(f"Successfully set up output directory structure in {output_dir}")
        
    def ensure_fallback_image(self) -> None:
        """
        Ensure the fallback image exists in the output directory.
        
        If the fallback image doesn't exist, create a simple placeholder.
        """
        fallback_path = Path(self.config.output_dir) / self.config.fallback_image
        
        # Create parent directories if they don't exist
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if fallback image exists
        if not fallback_path.exists():
            # Copy from source if available
            source_path = Path("slides/redacted.png")
            if source_path.exists() and source_path.stat().st_size > 0:
                shutil.copy2(source_path, fallback_path)
                self.logger.info(f"Copied fallback image from {source_path} to {fallback_path}")
            else:
                # Create a simple placeholder image
                self._create_placeholder_image(fallback_path)
                self.logger.info(f"Created placeholder fallback image at {fallback_path}")
    
    def _create_placeholder_image(self, path: Path) -> None:
        """
        Create a simple placeholder image.
        
        This creates a minimal valid PNG file as a fallback.
        For a real implementation, you would use a library like Pillow.
        
        Args:
            path: Path where the placeholder image should be created
        """
        # Minimal valid PNG file (1x1 transparent pixel)
        minimal_png = bytes.fromhex(
            '89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4'
            '890000000d4944415478da63f8ffff3f0300050001013c0b8b0000000049454e44ae426082'
        )
        
        with open(path, 'wb') as f:
            f.write(minimal_png)
    
    def copy_slide_images(self, presentation: ProcessedPresentation) -> None:
        """
        Copy slide images from source folders to output directory.
        
        Args:
            presentation: Processed presentation with slides
        """
        output_slides_dir = Path(self.config.output_dir) / self.config.slides_dir / presentation.info.folder_name
        
        try:
            output_slides_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            self.logger.error(
                f"Failed to create slides directory for '{presentation.info.title}': {e}",
                extra={
                    "presentation_title": presentation.info.title,
                    "slides_directory": str(output_slides_dir),
                    "error_type": type(e).__name__
                }
            )
            # Set all slides to use fallback image (graceful degradation)
            for slide in presentation.slides:
                slide.image_path = f"../{self.config.fallback_image}"
            return
        
        for slide in presentation.slides:
            # Skip slides with no image path or using fallback
            if not slide.image_path or slide.image_path.startswith(self.config.fallback_image) or slide.image_path.startswith(f"{self.config.slides_dir}/"):
                continue
                
            try:
                # Get the source image path - this should be the original relative path from the markdown
                source_path = Path(slide.image_path)
                if not source_path.is_absolute() and not str(source_path).startswith('/'):
                    # If it's a relative path, resolve it relative to the presentation folder
                    source_path = Path(presentation.info.folder_path) / source_path
                
                # Skip if source doesn't exist
                if not source_path.exists():
                    self.logger.warning(
                        f"Source image not found for slide {slide.index}: {source_path}",
                        extra={
                            "presentation_title": presentation.info.title,
                            "slide_index": slide.index,
                            "source_path": str(source_path)
                        }
                    )
                    # Update slide to use fallback image (graceful degradation)
                    slide.image_path = f"../{self.config.fallback_image}"
                    continue
                    
                # Determine destination path
                dest_filename = source_path.name
                dest_path = output_slides_dir / dest_filename
                
                # Copy the image
                try:
                    shutil.copy2(source_path, dest_path)
                    self.logger.debug(f"Copied slide image: {source_path} -> {dest_path}")
                    
                    # Update the image path to use the web-accessible path
                    rel_path = f"{presentation.info.folder_name}/{dest_filename}"
                    slide.image_path = f"../{self.config.slides_dir}/{rel_path}"
                    
                except (OSError, PermissionError, shutil.Error) as e:
                    self.logger.error(
                        f"Failed to copy slide image {source_path}: {e}",
                        extra={
                            "presentation_title": presentation.info.title,
                            "slide_index": slide.index,
                            "source_path": str(source_path),
                            "dest_path": str(dest_path),
                            "error_type": type(e).__name__
                        }
                    )
                    # Update slide to use fallback image (graceful degradation)
                    slide.image_path = f"../{self.config.fallback_image}"
                    
            except Exception as e:
                self.logger.error(
                    f"Unexpected error processing slide {slide.index} image: {e}",
                    extra={
                        "presentation_title": presentation.info.title,
                        "slide_index": slide.index,
                        "error_type": type(e).__name__
                    }
                )
                # Update slide to use fallback image (graceful degradation)
                slide.image_path = f"../{self.config.fallback_image}"
    
    def copy_preview_image(self, presentation: PresentationInfo) -> None:
        """
        Copy preview image from source folder to output directory.
        
        Args:
            presentation: Presentation info with preview image
        """
        # Skip if no preview image or using fallback
        if not presentation.preview_image or presentation.preview_image.startswith(f"../{self.config.fallback_image}"):
            return
            
        # Get the source image path
        source_path = Path(presentation.preview_image)
        if not source_path.is_absolute():
            # If it's a relative path, resolve it relative to the presentation folder
            source_path = Path(presentation.folder_path) / source_path
        
        # Skip if source doesn't exist
        if not source_path.exists():
            self.logger.warning(f"Preview image not found: {source_path}")
            presentation.preview_image = f"../{self.config.fallback_image}"
            return
        
        # Determine destination path
        preview_dir = Path(self.config.output_dir) / "images"
        preview_dir.mkdir(parents=True, exist_ok=True)
        
        preview_filename = f"{presentation.folder_name}-preview{source_path.suffix}"
        dest_path = preview_dir / preview_filename
        
        # Copy the image
        try:
            shutil.copy2(source_path, dest_path)
            self.logger.debug(f"Copied preview image: {source_path} -> {dest_path}")
            
            # Update preview image path to web-accessible path
            presentation.preview_image = f"../images/{preview_filename}"
        except Exception as e:
            self.logger.error(f"Failed to copy preview image {source_path}: {e}")
            # Update to use fallback image
            presentation.preview_image = f"../{self.config.fallback_image}"
    
    def cleanup_output_directory(self, presentations: List[ProcessedPresentation]) -> None:
        """
        Clean up the output directory by removing unused files.
        
        This helps keep the generated website organized and removes old files
        that are no longer needed.
        
        Args:
            presentations: List of processed presentations
        """
        # Get list of valid presentation folders
        valid_folders = {p.info.folder_name for p in presentations}
        
        # Clean up slides directory
        slides_dir = Path(self.config.output_dir) / self.config.slides_dir
        if slides_dir.exists():
            for item in slides_dir.iterdir():
                if item.is_dir() and item.name not in valid_folders:
                    # This is a slides folder for a presentation that no longer exists
                    try:
                        shutil.rmtree(item)
                        self.logger.info(f"Removed unused slides directory: {item}")
                    except Exception as e:
                        self.logger.error(f"Failed to remove directory {item}: {e}")
        
        # Clean up presentations directory
        presentations_dir = Path(self.config.output_dir) / "presentations"
        if presentations_dir.exists():
            valid_html_files = {f"{name}.html" for name in valid_folders}
            for item in presentations_dir.iterdir():
                if item.is_file() and item.suffix == '.html' and item.name not in valid_html_files:
                    # This is an HTML file for a presentation that no longer exists
                    try:
                        item.unlink()
                        self.logger.info(f"Removed unused presentation file: {item}")
                    except Exception as e:
                        self.logger.error(f"Failed to remove file {item}: {e}")
    
    def process_presentation_files(self, presentation: ProcessedPresentation) -> None:
        """
        Process all files for a presentation.
        
        This is a convenience method that handles all file operations for a single presentation.
        
        Args:
            presentation: Processed presentation
        """
        # Check if this is an enhanced presentation with media processing
        if hasattr(presentation, 'config') and hasattr(presentation, 'slides'):
            # Enhanced presentation - process all media types
            self._process_enhanced_presentation_media(presentation)
        else:
            # Basic presentation - use legacy image processing
            # Copy slide images first (while paths are still original)
            self.copy_slide_images(presentation)
            
            # Then update slide image paths to web-accessible paths
            self._update_slide_image_paths(presentation)
        
        # Copy preview image
        self.copy_preview_image(presentation.info)
    
    def _process_enhanced_presentation_media(self, presentation) -> None:
        """
        Process media files for enhanced presentations with full Deckset support.
        
        Args:
            presentation: EnhancedPresentation object
        """
        try:
            from media_processor import MediaProcessor
            media_processor = MediaProcessor()
            
            # Create output directories for this presentation
            output_slides_dir = Path(self.config.output_dir) / self.config.slides_dir / presentation.info.folder_name
            output_slides_dir.mkdir(parents=True, exist_ok=True)
            
            # Process each slide's media
            for slide in presentation.slides:
                # Process background image
                if slide.background_image:
                    self._copy_processed_image(slide.background_image, output_slides_dir, presentation.info.folder_name)
                
                # Process inline images
                for image in slide.inline_images:
                    self._copy_processed_image(image, output_slides_dir, presentation.info.folder_name)
                
                # Process videos
                for video in slide.videos:
                    if video.embed_type == "local":
                        self._copy_processed_video(video, output_slides_dir, presentation.info.folder_name)
                
                # Process audio
                for audio in slide.audio:
                    self._copy_processed_audio(audio, output_slides_dir, presentation.info.folder_name)
            
            self.logger.info(f"Processed enhanced media for presentation: {presentation.info.title}")
            
        except ImportError:
            self.logger.warning("Enhanced media processor not available, falling back to basic image processing")
            # Fallback to basic processing
            self.copy_slide_images(presentation)
            self._update_slide_image_paths(presentation)
        except Exception as e:
            self.logger.error(f"Failed to process enhanced media for {presentation.info.title}: {e}")
            # Fallback to basic processing
            self.copy_slide_images(presentation)
            self._update_slide_image_paths(presentation)
    
    def _copy_processed_image(self, processed_image, output_dir: Path, presentation_folder: str) -> None:
        """Copy a processed image to the output directory."""
        try:
            source_path = Path(processed_image.src_path)
            if not source_path.exists():
                self.logger.warning(f"Processed image source not found: {source_path}")
                return
            
            dest_filename = source_path.name
            dest_path = output_dir / dest_filename
            
            # Copy the image
            shutil.copy2(source_path, dest_path)
            
            # Update web path to be relative to presentations directory
            processed_image.web_path = f"../{self.config.slides_dir}/{presentation_folder}/{dest_filename}"
            
            self.logger.debug(f"Copied processed image: {source_path} -> {dest_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to copy processed image {processed_image.src_path}: {e}")
    
    def _copy_processed_video(self, processed_video, output_dir: Path, presentation_folder: str) -> None:
        """Copy a processed video to the output directory."""
        try:
            source_path = Path(processed_video.src_path)
            if not source_path.exists():
                self.logger.warning(f"Processed video source not found: {source_path}")
                return
            
            dest_filename = source_path.name
            dest_path = output_dir / dest_filename
            
            # Copy the video
            shutil.copy2(source_path, dest_path)
            
            # Update web path to be relative to presentations directory
            processed_video.web_path = f"../{self.config.slides_dir}/{presentation_folder}/{dest_filename}"
            
            self.logger.debug(f"Copied processed video: {source_path} -> {dest_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to copy processed video {processed_video.src_path}: {e}")
    
    def _copy_processed_audio(self, processed_audio, output_dir: Path, presentation_folder: str) -> None:
        """Copy a processed audio file to the output directory."""
        try:
            source_path = Path(processed_audio.src_path)
            if not source_path.exists():
                self.logger.warning(f"Processed audio source not found: {source_path}")
                return
            
            dest_filename = source_path.name
            dest_path = output_dir / dest_filename
            
            # Copy the audio
            shutil.copy2(source_path, dest_path)
            
            # Update web path to be relative to presentations directory
            processed_audio.web_path = f"../{self.config.slides_dir}/{presentation_folder}/{dest_filename}"
            
            self.logger.debug(f"Copied processed audio: {source_path} -> {dest_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to copy processed audio {processed_audio.src_path}: {e}")
        
    def _update_slide_image_paths(self, presentation: ProcessedPresentation) -> None:
        """
        Update slide image paths to use web-accessible paths.
        This should be called after copy_slide_images().
        
        Args:
            presentation: Processed presentation
        """
        output_slides_dir = Path(self.config.output_dir) / self.config.slides_dir / presentation.info.folder_name
        
        for slide in presentation.slides:
            # If the slide has no image path, set the fallback image
            if not slide.image_path:
                slide.image_path = f"../{self.config.fallback_image}"
                continue
                
            # Skip slides already using fallback image or web paths
            if slide.image_path.startswith(f"../{self.config.fallback_image}") or slide.image_path.startswith(f"../{self.config.slides_dir}/"):
                continue
                
            # Resolve image path relative to presentation folder if needed
            image_path = Path(slide.image_path)
            if not image_path.is_absolute() and not str(image_path).startswith('/'):
                resolved_image_path = Path(presentation.info.folder_path) / image_path
            else:
                resolved_image_path = image_path
                
            # Check if the image was successfully copied to the output directory
            dest_filename = resolved_image_path.name
            dest_path = output_slides_dir / dest_filename
            
            if dest_path.exists():
                # Image was successfully copied, update to web-accessible path
                rel_path = f"{presentation.info.folder_name}/{dest_filename}"
                slide.image_path = f"../{self.config.slides_dir}/{rel_path}"
            else:
                # Image was not copied (probably failed), use fallback
                slide.image_path = f"../{self.config.fallback_image}"
    
    def process_all_presentations(self, presentations: List[ProcessedPresentation]) -> None:
        """
        Process files for all presentations.
        
        Args:
            presentations: List of processed presentations
        """
        # Set up output directories
        self.setup_output_directories()
        
        # Ensure fallback image exists
        self.ensure_fallback_image()
        
        # Process each presentation
        for presentation in presentations:
            self.process_presentation_files(presentation)
        
        # Clean up unused files
        self.cleanup_output_directory(presentations)