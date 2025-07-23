"""
Web page generator for creating HTML output from processed presentations.

This module handles the generation of HTML pages for individual presentations
and the homepage with presentation listings.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from models import (
    ProcessedPresentation, 
    PresentationInfo, 
    GeneratorConfig,
    TemplateRenderingError
)
from templates import TemplateManager


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
            
            # Render the homepage using the template manager
            html_content = self.template_manager.render_homepage(presentations, None)
            
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
            
            # Copy the image file (this will be implemented in the file management task)
            # For now, just log that we would copy the file
            self.logger.debug(f"Would copy {image_path} to {dest_path}")
    
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
            
        output_dir_path = Path(output_dir)
        presentations_dir = output_dir_path / "presentations"
        presentations_dir.mkdir(parents=True, exist_ok=True)
        
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
        
        return stats