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

from models import GeneratorConfig, ProcessedPresentation, PresentationInfo


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
        """
        output_dir = Path(self.config.output_dir)
        
        # Create main output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Created output directory: {output_dir}")
        
        # Create presentations directory
        presentations_dir = output_dir / "presentations"
        presentations_dir.mkdir(exist_ok=True)
        self.logger.info(f"Created presentations directory: {presentations_dir}")
        
        # Create slides directory
        slides_dir = output_dir / self.config.slides_dir
        slides_dir.mkdir(exist_ok=True)
        self.logger.info(f"Created slides directory: {slides_dir}")
        
        # Create images directory for preview images
        images_dir = output_dir / "images"
        images_dir.mkdir(exist_ok=True)
        self.logger.info(f"Created images directory: {images_dir}")
        
        # Create assets directory
        assets_dir = output_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        
        # Create subdirectories in assets
        (assets_dir / "css").mkdir(exist_ok=True)
        (assets_dir / "js").mkdir(exist_ok=True)
        self.logger.info(f"Created assets directory: {assets_dir}")
        
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
        output_slides_dir.mkdir(parents=True, exist_ok=True)
        
        for slide in presentation.slides:
            # Skip slides with no image path or using fallback
            if not slide.image_path or slide.image_path.startswith(f"/{self.config.fallback_image}"):
                continue
                
            # Get the source image path
            source_path = Path(slide.image_path)
            if not source_path.is_absolute() and not str(source_path).startswith('/'):
                # If it's a relative path, resolve it relative to the presentation folder
                source_path = Path(presentation.info.folder_path) / source_path
            
            # Skip if source doesn't exist
            if not source_path.exists():
                self.logger.warning(f"Source image not found: {source_path}")
                # Update slide to use fallback image
                slide.image_path = f"/{self.config.fallback_image}"
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
                slide.image_path = f"/{self.config.slides_dir}/{rel_path}"
            except Exception as e:
                self.logger.error(f"Failed to copy slide image {source_path}: {e}")
                # Update slide to use fallback image
                slide.image_path = f"/{self.config.fallback_image}"
    
    def copy_preview_image(self, presentation: PresentationInfo) -> None:
        """
        Copy preview image from source folder to output directory.
        
        Args:
            presentation: Presentation info with preview image
        """
        # Skip if no preview image or using fallback
        if not presentation.preview_image or presentation.preview_image.startswith(f"/{self.config.fallback_image}"):
            return
            
        # Get the source image path
        source_path = Path(presentation.preview_image)
        if not source_path.is_absolute():
            # If it's a relative path, resolve it relative to the presentation folder
            source_path = Path(presentation.folder_path) / source_path
        
        # Skip if source doesn't exist
        if not source_path.exists():
            self.logger.warning(f"Preview image not found: {source_path}")
            presentation.preview_image = f"/{self.config.fallback_image}"
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
            presentation.preview_image = f"/images/{preview_filename}"
        except Exception as e:
            self.logger.error(f"Failed to copy preview image {source_path}: {e}")
            # Update to use fallback image
            presentation.preview_image = f"/{self.config.fallback_image}"
    
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
        # Update slide image paths
        self._update_slide_image_paths(presentation)
        
        # Copy slide images
        self.copy_slide_images(presentation)
        
        # Copy preview image
        self.copy_preview_image(presentation.info)
        
    def _update_slide_image_paths(self, presentation: ProcessedPresentation) -> None:
        """
        Update slide image paths to use web-accessible paths.
        
        Args:
            presentation: Processed presentation
        """
        output_slides_dir = Path(self.config.output_dir) / self.config.slides_dir / presentation.info.folder_name
        
        for slide in presentation.slides:
            # If the slide has no image path, set the fallback image
            if not slide.image_path:
                slide.image_path = f"/{self.config.fallback_image}"
                continue
                
            # Check if the image exists
            image_path = Path(slide.image_path)
            if not image_path.exists():
                self.logger.warning(f"Source image not found: {image_path}")
                slide.image_path = f"/{self.config.fallback_image}"
                continue
                
            # Determine the destination path for the image
            rel_path = f"{presentation.info.folder_name}/{image_path.name}"
            
            # Update the image path to use the web-accessible path
            slide.image_path = f"/{self.config.slides_dir}/{rel_path}"
    
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