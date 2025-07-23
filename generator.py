"""
Web page generator for creating HTML output from processed presentations.

This module handles the generation of HTML pages for individual presentations
and the homepage with presentation listings.
"""

from pathlib import Path
from typing import List

from models import (
    ProcessedPresentation, 
    PresentationInfo, 
    GeneratorConfig,
    TemplateRenderingError
)


class WebPageGenerator:
    """Generates HTML pages for presentations and homepage."""
    
    def __init__(self, config: GeneratorConfig):
        self.config = config
    
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
            
            # For now, create a basic HTML structure
            # This will be enhanced when template system is implemented
            html_content = self._generate_basic_presentation_html(presentation)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
        except Exception as e:
            raise TemplateRenderingError(
                f"Failed to generate presentation page for {presentation.info.title}: {e}"
            )
    
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
            
            # For now, create a basic HTML structure
            # This will be enhanced when template system is implemented
            html_content = self._generate_basic_homepage_html(presentations)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
        except Exception as e:
            raise TemplateRenderingError(f"Failed to generate homepage: {e}")
    
    def _generate_basic_presentation_html(self, presentation: ProcessedPresentation) -> str:
        """Generate basic HTML for a presentation (placeholder implementation)."""
        slides_html = ""
        for slide in presentation.slides:
            notes_html = f"<div class='notes'>{slide.notes}</div>" if slide.notes else ""
            slides_html += f"""
            <div class="slide">
                <h3>Slide {slide.index}</h3>
                <div class="content">{slide.content}</div>
                {notes_html}
            </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{presentation.info.title}</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .slide {{ border: 1px solid #ccc; margin: 20px 0; padding: 20px; }}
                .notes {{ background: #f5f5f5; padding: 10px; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <h1>{presentation.info.title}</h1>
            <p>Slides: {len(presentation.slides)}</p>
            {slides_html}
        </body>
        </html>
        """
    
    def _generate_basic_homepage_html(self, presentations: List[PresentationInfo]) -> str:
        """Generate basic HTML for homepage (placeholder implementation)."""
        presentations_html = ""
        for presentation in presentations:
            presentations_html += f"""
            <div class="presentation-card">
                <h3><a href="presentations/{presentation.folder_name}.html">{presentation.title}</a></h3>
                <p>Slides: {presentation.slide_count}</p>
                <p>Folder: {presentation.folder_name}</p>
            </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Deckset Presentations</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .presentation-card {{ border: 1px solid #ccc; margin: 20px 0; padding: 20px; }}
                .presentation-card h3 {{ margin-top: 0; }}
                a {{ text-decoration: none; color: #0066cc; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h1>Deckset Presentations</h1>
            <p>Found {len(presentations)} presentations:</p>
            {presentations_html}
        </body>
        </html>
        """