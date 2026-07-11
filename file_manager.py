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

from models import GeneratorConfig, EnhancedPresentation, PresentationInfo, FileOperationError


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
        - output_dir (e.g., site/)
        - presentations directory (e.g., site/presentations/)
        - slides directory (e.g., site/slides/)
        - images directory (e.g., site/images/)
        - assets directory (e.g., site/assets/)
        
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
        
        # Copy template assets (CSS files)
        self.copy_template_assets()
        
    def copy_template_assets(self) -> None:
        """
        Copy template assets (CSS, JS, and icon files) to the output directory.
        
        Copies:
        - code_highlighting_styles.css to output root
        - slide_styles.css to output root (if exists)
        - slide-viewer.js to assets/js/ directory
        - favicon.png and other icons to assets/ directory
        """
        output_dir = Path(self.config.output_dir)
        
        # List of CSS files to copy from templates directory to output root
        css_files = [
            "code_highlighting_styles.css",
            "slide_styles.css"
        ]
        
        for css_file in css_files:
            source_path = Path("templates") / css_file
            dest_path = output_dir / css_file
            
            if source_path.exists():
                try:
                    shutil.copy2(source_path, dest_path)
                    self.logger.debug(f"Copied CSS file: {source_path} -> {dest_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to copy CSS file {css_file}: {e}")
            else:
                self.logger.warning(f"CSS file not found: {source_path}")
        
        # Copy JavaScript files to assets/js directory
        js_source_dir = Path("templates") / "assets" / "js"
        js_dest_dir = output_dir / "assets" / "js"
        
        if js_source_dir.exists():
            try:
                # Ensure destination directory exists
                js_dest_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy all JavaScript files
                for js_file in js_source_dir.glob("*.js"):
                    dest_path = js_dest_dir / js_file.name
                    shutil.copy2(js_file, dest_path)
                    self.logger.debug(f"Copied JS file: {js_file} -> {dest_path}")
                    
            except Exception as e:
                self.logger.warning(f"Failed to copy JavaScript files: {e}")
        else:
            self.logger.warning(f"JavaScript source directory not found: {js_source_dir}")
        
        # Copy favicon and icon assets to assets/ directory
        self._copy_favicon_assets()
    
    def _copy_favicon_assets(self) -> None:
        """
        Copy favicon and icon assets to the output assets directory.
        
        Copies:
        - favicon.png to assets/ directory
        - Any other icon files found in templates/assets/
        """
        output_dir = Path(self.config.output_dir)
        assets_source_dir = Path("templates") / "assets"
        assets_dest_dir = output_dir / "assets"
        
        # Ensure assets destination directory exists
        assets_dest_dir.mkdir(parents=True, exist_ok=True)
        
        # List of icon files to copy
        icon_files = [
            "favicon.png",
            "apple-touch-icon.png",  # Common Apple touch icon name
            "icon-192x192.png",  # PWA icons
            "icon-512x512.png",
            "deckset-icon.png"
        ]
        
        for icon_file in icon_files:
            source_path = assets_source_dir / icon_file
            dest_path = assets_dest_dir / icon_file
            
            if source_path.exists():
                try:
                    shutil.copy2(source_path, dest_path)
                    self.logger.debug(f"Copied icon file: {source_path} -> {dest_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to copy icon file {icon_file}: {e}")
            else:
                # Only log debug for favicon.png since it's required, others are optional
                if icon_file == "favicon.png":
                    self.logger.warning(f"Required favicon file not found: {source_path}")
                else:
                    self.logger.debug(f"Optional icon file not found: {source_path}")
    

    def copy_preview_image(self, presentation: PresentationInfo) -> None:
        """
        Copy preview image from source folder to output directory.
        
        Args:
            presentation: Presentation info with preview image
        """
        # Skip if no preview image
        if not presentation.preview_image:
            return
            
        # Get the source image path
        source_path = Path(presentation.preview_image)
        if not source_path.is_absolute():
            # If it's a relative path, resolve it relative to the presentation folder
            source_path = Path(presentation.folder_path) / source_path
        
        # Skip if source doesn't exist
        if not source_path.exists():
            self.logger.warning(f"Preview image not found: {source_path}")
            presentation.preview_image = None
            return
        
        # Determine destination path
        preview_dir = Path(self.config.output_dir) / "images"
        
        # For multiple presentations (e.g., Examples/10 Deckset basics), create subdirectory
        if "/" in presentation.folder_name:
            # Create subdirectory in images folder (e.g., images/Examples/)
            subfolder = presentation.folder_name.split("/")[0]
            preview_subdir = preview_dir / subfolder
            preview_subdir.mkdir(parents=True, exist_ok=True)
            preview_filename = f"{presentation.folder_name}-preview{source_path.suffix}"
            dest_path = preview_dir / preview_filename
        else:
            # Single presentations go directly in images folder
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
            # Clear preview image on failure
            presentation.preview_image = None
    
    def cleanup_output_directory(self, presentations: List[EnhancedPresentation]) -> None:
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
    
    def process_presentation_files(self, presentation: EnhancedPresentation) -> None:
        """
        Process all files for a presentation.
        
        This is a convenience method that handles all file operations for a single presentation.
        
        Args:
            presentation: Processed presentation
        """
        self._process_enhanced_presentation_media(presentation)
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
        
    def process_all_presentations(self, presentations: List[EnhancedPresentation]) -> None:
        """
        Process files for all presentations.
        
        Args:
            presentations: List of processed presentations
        """
        # Set up output directories
        self.setup_output_directories()
        
        # Process each presentation
        for presentation in presentations:
            self.process_presentation_files(presentation)
        
        # Clean up unused files
        self.cleanup_output_directory(presentations)