"""
Web page generator for creating HTML output from processed presentations.

This module handles the generation of HTML pages for individual presentations
and the homepage with presentation listings.
"""

import os
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from models import (
    ProcessedPresentation, 
    PresentationInfo, 
    GeneratorConfig,
    TemplateRenderingError
)
from templates import TemplateManager
from file_manager import FileManager


class WebPageGenerator:
    """Generates HTML pages for presentations and homepage."""
    
    def __init__(self, config: GeneratorConfig):
        """
        Initialize the web page generator with configuration.
        
        Args:
            config: Generator configuration object
        """
        self.config = config
        self.template_manager = TemplateManager(config)
        self.file_manager = FileManager(config)
        self.logger = logging.getLogger(__name__)
    
    def generate_presentation_page(
        self, 
        presentation: ProcessedPresentation, 
        output_path: str
    ) -> None:
        """
        Generate HTML page for a single presentation.
        
        Args:
            presentation: Processed presentation data
            output_path: Path where HTML file should be written
            
        Raises:
            TemplateRenderingError: If page generation fails
        """
        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Process slide images and ensure they have proper paths
            self._process_slide_images(presentation)
            
            # Render the presentation using the template manager
            html_content = self.template_manager.render_presentation(presentation, None)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            self.logger.info(f"Generated presentation page for '{presentation.info.title}' at {output_path}")
                
        except Exception as e:
            error_msg = f"Failed to generate presentation page for {presentation.info.title}: {str(e)}"
            self.logger.error(error_msg)
            raise TemplateRenderingError(error_msg) from e
    
    def generate_homepage(
        self, 
        presentations: List[PresentationInfo], 
        output_path: str
    ) -> None:
        """
        Generate homepage with presentation listings.
        
        Args:
            presentations: List of discovered presentations
            output_path: Path where homepage HTML should be written
            
        Raises:
            TemplateRenderingError: If homepage generation fails
        """
        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Process preview images for each presentation
            self._process_preview_images(presentations)
            
            # Sort presentations by last modified date (newest first)
            sorted_presentations = sorted(
                presentations,
                key=lambda p: p.last_modified if p.last_modified else datetime.min,
                reverse=True
            )
            
            # Render the homepage using the template manager
            html_content = self.template_manager.render_homepage(sorted_presentations, None)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            self.logger.info(f"Generated homepage with {len(presentations)} presentations at {output_path}")
                
        except Exception as e:
            error_msg = f"Failed to generate homepage: {str(e)}"
            self.logger.error(error_msg)
            raise TemplateRenderingError(error_msg) from e
    
    def _process_slide_images(self, presentation: ProcessedPresentation) -> None:
        """
        Process slide images and ensure they have proper paths.
        
        This method updates the image_path for each slide, handling fallbacks for missing images.
        
        Args:
            presentation: The presentation to process
        """
        output_slides_dir = Path(self.config.output_dir) / self.config.slides_dir / presentation.info.folder_name
        
        # Create slides directory if it doesn't exist
        output_slides_dir.mkdir(parents=True, exist_ok=True)
        
        for slide in presentation.slides:
            # If the slide has no image path, set the fallback image
            if not slide.image_path:
                slide.image_path = f"/{self.config.fallback_image}"
                continue
                
            # Check if the image exists
            image_path = Path(slide.image_path)
            if not image_path.exists():
                self.logger.warning(f"Image not found for slide {slide.index} in '{presentation.info.title}': {slide.image_path}")
                slide.image_path = f"/{self.config.fallback_image}"
                continue
                
            # Determine the destination path for the image
            rel_path = f"{presentation.info.folder_name}/{image_path.name}"
            dest_path = Path(self.config.output_dir) / self.config.slides_dir / rel_path
            
            # Update the image path to use the web-accessible path
            slide.image_path = f"/{self.config.slides_dir}/{rel_path}"
            
    def _process_preview_images(self, presentations: List[PresentationInfo]) -> None:
        """
        Process preview images for presentations.
        
        This method updates the preview_image for each presentation, handling fallbacks
        for missing images and creating preview directories.
        
        Args:
            presentations: List of presentation info objects to process
        """
        # Create images directory for previews if it doesn't exist
        preview_dir = Path(self.config.output_dir) / "images"
        preview_dir.mkdir(parents=True, exist_ok=True)
        
        for presentation in presentations:
            # If no preview image is set, try to find the first slide image
            if not presentation.preview_image:
                # Look for potential first slide image in the presentation folder
                potential_images = list(Path(presentation.folder_path).glob("*.png")) + \
                                  list(Path(presentation.folder_path).glob("*.jpg")) + \
                                  list(Path(presentation.folder_path).glob("*.jpeg"))
                
                # Also check in a slides/ subdirectory if it exists
                slides_dir = Path(presentation.folder_path) / "slides"
                if slides_dir.exists():
                    potential_images.extend(list(slides_dir.glob("*.png")))
                    potential_images.extend(list(slides_dir.glob("*.jpg")))
                    potential_images.extend(list(slides_dir.glob("*.jpeg")))
                
                # Sort by name to try to get slide1.png or similar
                potential_images.sort(key=lambda p: p.name)
                
                if potential_images:
                    # Use the first image found as preview
                    presentation.preview_image = str(potential_images[0])
            
            # Process the preview image if it exists
            if presentation.preview_image:
                image_path = Path(presentation.preview_image)
                
                if not image_path.exists():
                    self.logger.warning(f"Preview image not found for '{presentation.title}': {presentation.preview_image}")
                    presentation.preview_image = f"/{self.config.fallback_image}"
                    continue
                
                # Create a standardized preview image name
                preview_filename = f"{presentation.folder_name}-preview{image_path.suffix}"
                dest_path = preview_dir / preview_filename
                
                # Update the preview image path to use the web-accessible path
                presentation.preview_image = f"/images/{preview_filename}"
            else:
                # Use fallback image if no preview is available
                presentation.preview_image = f"/{self.config.fallback_image}"
    
    def generate_all_pages(
        self, 
        presentations: List[ProcessedPresentation],
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate all pages for the website, including presentation pages and homepage.
        
        Args:
            presentations: List of processed presentations
            output_dir: Optional output directory (defaults to config.output_dir)
            
        Returns:
            Dictionary with generation statistics
            
        Raises:
            TemplateRenderingError: If page generation fails
        """
        if output_dir is None:
            output_dir = self.config.output_dir
            
        # Set up output directories and ensure fallback image exists
        self.file_manager.setup_output_directories()
        self.file_manager.ensure_fallback_image()
            
        output_dir_path = Path(output_dir)
        presentations_dir = output_dir_path / "presentations"
        
        stats = {
            "total": len(presentations),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        # Generate individual presentation pages
        presentation_infos = []
        for presentation in presentations:
            try:
                # Update presentation metadata
                if not presentation.info.last_modified:
                    # Set last modified time based on markdown file
                    md_path = Path(presentation.info.markdown_path)
                    if md_path.exists():
                        presentation.info.last_modified = datetime.fromtimestamp(md_path.stat().st_mtime)
                
                # Set slide count if not already set
                if presentation.info.slide_count == 0:
                    presentation.info.slide_count = len(presentation.slides)
                
                # Process files for this presentation
                self.file_manager.process_presentation_files(presentation)
                
                # Generate the presentation page
                output_path = presentations_dir / f"{presentation.info.folder_name}.html"
                self.generate_presentation_page(presentation, output_path)
                presentation_infos.append(presentation.info)
                stats["successful"] += 1
            except Exception as e:
                stats["failed"] += 1
                error_info = {
                    "presentation": presentation.info.title,
                    "error": str(e)
                }
                stats["errors"].append(error_info)
                self.logger.error(f"Failed to generate page for '{presentation.info.title}': {e}")
                # Continue with other presentations despite errors
        
        # Generate homepage
        try:
            homepage_path = output_dir_path / "index.html"
            self.generate_homepage(presentation_infos, homepage_path)
        except Exception as e:
            stats["errors"].append({
                "presentation": "homepage",
                "error": str(e)
            })
            self.logger.error(f"Failed to generate homepage: {e}")
        
        # Clean up unused files
        self.file_manager.cleanup_output_directory(presentations)
        
        return stats