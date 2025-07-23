"""
Template management for the Deckset Website Generator.

This module handles HTML template loading, rendering, and management
using Jinja2 templating engine.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
import markdown as md

from models import (
    ProcessedPresentation, 
    PresentationInfo,
    GeneratorConfig,
    TemplateRenderingError
)

# Set up logging
logger = logging.getLogger(__name__)


class TemplateManager:
    """Manages HTML templates and provides rendering utilities."""
    
    def __init__(self, config: GeneratorConfig):
        """
        Initialize the template manager with configuration.
        
        Args:
            config: Generator configuration object
            
        Raises:
            TemplateRenderingError: If Jinja2 is not available or templates cannot be loaded
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Set up Jinja2 environment
        template_dir = Path(config.template_dir)
        if not template_dir.exists():
            raise TemplateRenderingError(
                f"Template directory does not exist: {template_dir}",
                context={"template_dir": str(template_dir)}
            )
        
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        # Add custom filters
        self.env.filters['markdown'] = self._markdown_filter
    
    def _markdown_filter(self, text: str) -> str:
        """
        Custom Jinja2 filter to convert markdown text to HTML.
        
        Args:
            text: Markdown text to convert
            
        Returns:
            HTML string
        """
        if not text:
            return ""
        try:
            return md.markdown(text)
        except Exception as e:
            self.logger.error(f"Failed to convert markdown: {e}")
            return text
    
    def load_template(self, template_name: str) -> Template:
        """
        Load a template by name.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            Jinja2 Template object
            
        Raises:
            TemplateRenderingError: If template loading fails
        """
        try:
            template = self.env.get_template(template_name)
            logger.debug(f"Successfully loaded template: {template_name}")
            return template
        except Exception as e:
            logger.error(
                f"Failed to load template {template_name}: {e}",
                extra={
                    "template_name": template_name,
                    "template_dir": str(self.config.template_dir),
                    "error_type": type(e).__name__
                }
            )
            raise TemplateRenderingError(
                f"Failed to load template {template_name}: {e}",
                context={
                    "template_name": template_name,
                    "template_dir": str(self.config.template_dir),
                    "error_type": type(e).__name__
                }
            )
    
    def render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """
        Load and render a template with data.
        
        Args:
            template_name: Name of the template file
            data: Data to render in the template
            
        Returns:
            Rendered HTML string
            
        Raises:
            TemplateRenderingError: If loading or rendering fails
        """
        template = self.load_template(template_name)
        try:
            rendered_content = template.render(**data)
            logger.debug(f"Successfully rendered template {template_name} ({len(rendered_content)} chars)")
            return rendered_content
        except Exception as e:
            logger.error(
                f"Failed to render template {template_name}: {e}",
                extra={
                    "template_name": template_name,
                    "data_keys": list(data.keys()) if data else [],
                    "error_type": type(e).__name__
                }
            )
            raise TemplateRenderingError(
                f"Failed to render template {template_name}: {e}",
                context={
                    "template_name": template_name,
                    "data_keys": list(data.keys()) if data else [],
                    "error_type": type(e).__name__
                }
            )
    
    def render_presentation(self, presentation: ProcessedPresentation, 
                           output_path: Optional[str] = None) -> str:
        """
        Render a presentation using the presentation template.
        
        Args:
            presentation: Processed presentation data
            output_path: Optional path to write the rendered HTML
            
        Returns:
            Rendered HTML string
            
        Raises:
            TemplateRenderingError: If rendering fails
        """
        try:
            # Prepare data for template
            data = {
                'presentation': presentation,
                'config': self.config
            }
            
            # Render the template
            html = self.render_template('presentation.html', data)
            
            # Write to file if output path is provided
            if output_path:
                output_dir = os.path.dirname(output_path)
                os.makedirs(output_dir, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html)
            
            return html
        except Exception as e:
            raise TemplateRenderingError(f"Failed to render presentation template: {e}")
    
    def render_homepage(self, presentations: List[PresentationInfo], 
                       output_path: Optional[str] = None) -> str:
        """
        Render the homepage with presentation listings.
        
        Args:
            presentations: List of presentation info objects
            output_path: Optional path to write the rendered HTML
            
        Returns:
            Rendered HTML string
            
        Raises:
            TemplateRenderingError: If rendering fails
        """
        try:
            # Prepare data for template
            data = {
                'presentations': presentations,
                'config': self.config
            }
            
            # Render the template
            html = self.render_template('homepage.html', data)
            
            # Write to file if output path is provided
            if output_path:
                output_dir = os.path.dirname(output_path)
                os.makedirs(output_dir, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html)
            
            return html
        except Exception as e:
            raise TemplateRenderingError(f"Failed to render homepage template: {e}")
    
    def template_exists(self, template_name: str) -> bool:
        """
        Check if a template file exists.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            True if the template exists, False otherwise
        """
        template_path = Path(self.config.template_dir) / template_name
        return template_path.exists()
    
    def ensure_template_dir(self) -> None:
        """
        Ensure the template directory exists.
        
        Creates the template directory if it doesn't exist.
        """
        self.config.template_dir.mkdir(parents=True, exist_ok=True)
        
    def get_all_templates(self) -> List[str]:
        """
        Get a list of all available templates.
        
        Returns:
            List of template names
        """
        if not self.config.template_dir.exists():
            return []
            
        templates = []
        for file in self.config.template_dir.glob('*.html'):
            templates.append(file.name)
        return templates