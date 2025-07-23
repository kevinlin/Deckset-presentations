"""
Template management system for HTML rendering.

This module provides template loading and rendering capabilities using Jinja2
for generating consistent HTML output across all pages.
"""

from pathlib import Path
from typing import Dict, Any
try:
    from jinja2 import Environment, FileSystemLoader, Template
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

from models import GeneratorConfig, TemplateRenderingError


class TemplateManager:
    """Manages HTML templates and provides rendering utilities."""
    
    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.template_dir = Path(config.template_dir)
        
        if JINJA2_AVAILABLE:
            self.env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=True
            )
        else:
            self.env = None
    
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
        if not JINJA2_AVAILABLE:
            raise TemplateRenderingError(
                "Jinja2 is not available. Please install it to use templates."
            )
        
        try:
            return self.env.get_template(template_name)
        except Exception as e:
            raise TemplateRenderingError(f"Failed to load template {template_name}: {e}")
    
    def render_presentation(self, template: Template, data: Dict[str, Any]) -> str:
        """
        Render a presentation template with data.
        
        Args:
            template: Jinja2 template object
            data: Data to render in the template
            
        Returns:
            Rendered HTML string
            
        Raises:
            TemplateRenderingError: If rendering fails
        """
        try:
            return template.render(**data)
        except Exception as e:
            raise TemplateRenderingError(f"Failed to render presentation template: {e}")
    
    def render_homepage(self, template: Template, data: Dict[str, Any]) -> str:
        """
        Render a homepage template with data.
        
        Args:
            template: Jinja2 template object
            data: Data to render in the template
            
        Returns:
            Rendered HTML string
            
        Raises:
            TemplateRenderingError: If rendering fails
        """
        try:
            return template.render(**data)
        except Exception as e:
            raise TemplateRenderingError(f"Failed to render homepage template: {e}")
    
    def template_exists(self, template_name: str) -> bool:
        """Check if a template file exists."""
        template_path = self.template_dir / template_name
        return template_path.exists()
    
    def ensure_template_dir(self) -> None:
        """Ensure the template directory exists."""
        self.template_dir.mkdir(parents=True, exist_ok=True)