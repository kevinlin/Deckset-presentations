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
    TemplateRenderingError,
    FileOperationError
)
from enhanced_templates import EnhancedTemplateEngine
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
        self.template_manager = EnhancedTemplateEngine(config.template_dir)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Using enhanced template engine")
        self.file_manager = FileManager(config)

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
        self.logger.info(f"Generating presentation page for '{presentation.info.title}'")

        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_path)
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as e:
                raise FileOperationError(
                    f"Failed to create output directory {output_path.parent}: {e}",
                    context={
                        "presentation_title": presentation.info.title,
                        "output_path": str(output_path),
                        "directory": str(output_path.parent)
                    }
                )

            # Note: Image processing is handled by FileManager.process_presentation_files()
            # which is called in generate_all_pages() before this method

            # Render the presentation using the template manager
            try:
                if hasattr(presentation, 'config'):
                    # Enhanced presentation with Deckset features
                    html_content = self._render_enhanced_presentation(presentation)
                else:
                    # Basic presentation rendering using EnhancedTemplateEngine
                    html_content = self._render_enhanced_presentation(presentation)
            except Exception as e:
                raise TemplateRenderingError(
                    f"Failed to render template for presentation '{presentation.info.title}': {e}",
                    context={
                        "presentation_title": presentation.info.title,
                        "slide_count": len(presentation.slides),
                        "template_error": str(e)
                    }
                )

            # Write the HTML file
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
            except (OSError, PermissionError, UnicodeEncodeError) as e:
                raise FileOperationError(
                    f"Failed to write presentation page to {output_path}: {e}",
                    context={
                        "presentation_title": presentation.info.title,
                        "output_path": str(output_path),
                        "content_length": len(html_content)
                    }
                )

            self.logger.info(f"Generated presentation page for '{presentation.info.title}' at {output_path}")

        except (TemplateRenderingError, FileOperationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            error_msg = f"Unexpected error generating presentation page for {presentation.info.title}: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "presentation_title": presentation.info.title,
                    "output_path": str(output_path),
                    "error_type": type(e).__name__
                }
            )
            raise TemplateRenderingError(
                error_msg,
                context={
                    "presentation_title": presentation.info.title,
                    "output_path": str(output_path),
                    "unexpected_error": str(e)
                }
            ) from e

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
        self.logger.info(f"Generating homepage with {len(presentations)} presentations")

        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_path)
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as e:
                raise FileOperationError(
                    f"Failed to create output directory {output_path.parent}: {e}",
                    context={
                        "output_path": str(output_path),
                        "directory": str(output_path.parent),
                        "presentation_count": len(presentations)
                    }
                )

            # Process preview images for each presentation
            try:
                self._process_preview_images(presentations)
            except Exception as e:
                self.logger.warning(
                    f"Failed to process preview images: {e}",
                    extra={
                        "presentation_count": len(presentations),
                        "error_type": type(e).__name__
                    }
                )
                # Continue with generation even if preview processing fails

            # Sort presentations by title alphabetically
            try:
                sorted_presentations = sorted(
                    presentations,
                    key=lambda p: (p.last_modified if p.last_modified else p.title.lower()),
                    reverse=True
                )
            except Exception as e:
                self.logger.warning(f"Failed to sort presentations, using original order: {e}")
                sorted_presentations = presentations

            # Render the homepage using the template manager
            try:
                html_content = self.template_manager.render_homepage(sorted_presentations, None)
            except Exception as e:
                raise TemplateRenderingError(
                    f"Failed to render homepage template: {e}",
                    context={
                        "presentation_count": len(presentations),
                        "template_error": str(e)
                    }
                )

            # Write the HTML file
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
            except (OSError, PermissionError, UnicodeEncodeError) as e:
                raise FileOperationError(
                    f"Failed to write homepage to {output_path}: {e}",
                    context={
                        "output_path": str(output_path),
                        "content_length": len(html_content),
                        "presentation_count": len(presentations)
                    }
                )

            self.logger.info(f"Generated homepage with {len(presentations)} presentations at {output_path}")

        except (TemplateRenderingError, FileOperationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            error_msg = f"Unexpected error generating homepage: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "output_path": str(output_path),
                    "presentation_count": len(presentations),
                    "error_type": type(e).__name__
                }
            )
            raise TemplateRenderingError(
                error_msg,
                context={
                    "output_path": str(output_path),
                    "presentation_count": len(presentations),
                    "unexpected_error": str(e)
                }
            ) from e

    def _process_slide_images(self, presentation: ProcessedPresentation) -> None:
        """
        Process slide images and ensure they have proper paths.
        
        This method validates image paths and clears invalid ones.
        The actual copying is handled by FileManager.copy_slide_images().
        
        Args:
            presentation: The presentation to process
        """
        for slide in presentation.slides:
            # If the slide has no image path, leave it as None
            if not slide.image_path:
                continue

            # Check if the image exists (resolve relative to presentation folder)
            image_path = Path(slide.image_path)
            if not image_path.is_absolute() and not str(image_path).startswith('/'):
                # Resolve relative to presentation folder
                resolved_image_path = Path(presentation.info.folder_path) / image_path
            else:
                resolved_image_path = image_path

            if not resolved_image_path.exists():
                self.logger.warning(f"Image not found for slide {slide.index} in '{presentation.info.title}': {resolved_image_path}")
                slide.image_path = None
                continue

            # Leave the image_path as-is for now - FileManager will handle the copying
            # and update the path to the web-accessible location

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
            # Skip if preview image has already been processed by FileManager
            # (indicated by web-accessible path starting with "../")
            if presentation.preview_image and presentation.preview_image.startswith("../"):
                continue
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
                # Convert relative path to absolute path for validation
                if presentation.preview_image.startswith("../"):
                    # This is a web-accessible path like "../images/filename"
                    # Convert to actual file path: docs/images/filename
                    actual_path = Path(self.config.output_dir) / presentation.preview_image.replace("../", "")
                elif presentation.preview_image.startswith("images/"):
                    # This is a homepage-adjusted path like "images/filename"
                    # Convert to actual file path: docs/images/filename
                    actual_path = Path(self.config.output_dir) / presentation.preview_image
                else:
                    actual_path = Path(presentation.preview_image)

                if not actual_path.exists():
                    self.logger.warning(f"Preview image not found for '{presentation.title}': {presentation.preview_image}")
                    presentation.preview_image = None
                    continue

                # Create a standardized preview image name
                preview_filename = f"{presentation.folder_name}-preview{actual_path.suffix}"
                dest_path = preview_dir / preview_filename

                # Update the preview image path to use the web-accessible path
                presentation.preview_image = f"../images/{preview_filename}"
            # If no preview image is available, leave it as None (template will handle placeholder)

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

        # Set up output directories
        self.file_manager.setup_output_directories()

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

                # Process files for this presentation (this handles image copying and path updates)
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

                # Generate homepage - adjust preview image paths for root level
        try:
            # Create a copy of presentation_infos with adjusted paths for homepage
            homepage_presentation_infos = []
            for presentation_info in presentation_infos:
                # Create a copy to avoid modifying the original
                from copy import copy
                homepage_info = copy(presentation_info)

                # Adjust preview image paths for homepage (remove ../ prefix)
                if homepage_info.preview_image and homepage_info.preview_image.startswith("../"):
                    homepage_info.preview_image = homepage_info.preview_image[3:]  # Remove "../"

                homepage_presentation_infos.append(homepage_info)

            homepage_path = output_dir_path / "index.html"
            self.generate_homepage(homepage_presentation_infos, homepage_path)
        except Exception as e:
            stats["errors"].append({
                "presentation": "homepage",
                "error": str(e)
            })
            self.logger.error(f"Failed to generate homepage: {e}")

        # Clean up unused files
        self.file_manager.cleanup_output_directory(presentations)

        return stats

    def _render_enhanced_presentation(self, presentation) -> str:
        """
        Render an enhanced presentation with all features enabled.
        
        Args:
            presentation: Enhanced presentation object with all processed data
            
        Returns:
            Complete HTML string for the presentation
        """
        try:
            # Render all slides
            slides_html = []
            for slide in presentation.slides:
                slide_html = self.template_manager.render_slide(slide, presentation.config)
                slides_html.append(slide_html)

            # Calculate asset path depth based on folder structure
            asset_path_prefix = self._calculate_asset_path_prefix(presentation.info.folder_name)

            # Create presentation HTML with dynamic asset paths
            presentation_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{presentation.info.title}</title>
    <link rel="stylesheet" href="{asset_path_prefix}enhanced_slide_styles.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/default.min.css">
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <!-- Navigation Header -->
    <header class="bg-white shadow-sm border-b sticky top-0 z-50">
        <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" aria-label="Main navigation">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <a href="{asset_path_prefix}index.html" class="text-xl font-semibold text-gray-900 flex items-center">
                        <svg class="h-8 w-8 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                        <span>Deckset Presentations</span>
                    </a>
                </div>
                <div class="flex items-center space-x-4">
                    <a href="{asset_path_prefix}index.html" 
                       class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                        ← Back to Home
                    </a>
                </div>
            </div>
        </nav>
    </header>
    
    <div class="presentation-container" data-presentation-title="{presentation.info.title}">
        <div class="slides-container">
            {"".join(slides_html)}
        </div>
        
        <!-- Navigation -->
        <div class="navigation">
            <button id="prev-slide" class="nav-button">Previous</button>
            <span id="slide-counter">1 / {len(presentation.slides)}</span>
            <button id="next-slide" class="nav-button">Next</button>
            <button id="toggle-notes" class="nav-button">Notes</button>
        </div>
    </div>
    
    <!-- Enhanced JavaScript -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <script src="{asset_path_prefix}assets/js/enhanced-slide-viewer.js"></script>
    
    <!-- MathJax Configuration -->
    <script>
        {self._get_mathjax_config()}
    </script>
</body>
</html>
            """

            return presentation_html

        except Exception as e:
            self.logger.error(f"Failed to render enhanced presentation: {e}")
            # Return a minimal error page instead of fallback
            return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Presentation Error</title>
</head>
<body>
    <h1>Presentation Rendering Error</h1>
    <p>Error: {e}</p>
    <p>Presentation: {presentation.info.title if hasattr(presentation, 'info') else 'Unknown'}</p>
</body>
</html>
            """

    def _calculate_asset_path_prefix(self, folder_name: str) -> str:
        """
        Calculate the correct relative path prefix for assets based on presentation nesting.
        
        Args:
            folder_name: The folder name/path for the presentation (e.g., "single-pres" or "Examples/10 Deckset basics")
            
        Returns:
            Relative path prefix (e.g., "../" or "../../")
        """
        # Count the number of path separators to determine nesting depth
        # Examples:
        # "single-presentation" -> 0 separators -> "../" (presentations/single.html -> ../assets)
        # "Examples/10 Deckset basics" -> 1 separator -> "../../" (presentations/Examples/file.html -> ../../assets)
        path_parts = folder_name.split('/')
        depth = len(path_parts)

        # We need depth "../" segments to go back to the root from the presentation file
        # Single presentations: presentations/file.html -> ../
        # Nested presentations: presentations/subfolder/file.html -> ../../
        return "../" * depth

    def _get_mathjax_config(self) -> str:
        """Get MathJax configuration for enhanced presentations."""
        try:
            from math_processor import MathProcessor
            processor = MathProcessor()
            return processor.generate_mathjax_config(responsive=True, error_handling=True)
        except ImportError:
            # Fallback MathJax config
            return """
            window.MathJax = {
                tex: {
                    inlineMath: [['\\\\(', '\\\\)']],
                    displayMath: [['\\\\[', '\\\\]']],
                    processEscapes: true
                },
                svg: {
                    fontCache: 'global'
                }
            };
            """
