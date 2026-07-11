"""Thin template engine for rendering Deckset presentations.

All HTML generation now lives in Jinja2 macros under ``templates/macros/``.
This module wires up the Jinja2 environment, registers custom filters, and
exposes page-level rendering entry points.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Set

from jinja2 import Environment, FileSystemLoader
from markdown_renderer import MarkdownRenderer
from models import (
    ProcessedSlide, DecksetConfig, SlideConfig,
)

logger = logging.getLogger(__name__)


class EnhancedTemplateEngine:
    """Jinja2 engine with custom filters for Deckset presentations."""

    def __init__(self, template_dir: str = "templates"):
        self.template_dir = template_dir
        self._renderer = MarkdownRenderer()
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False,
        )
        self.env.filters["markdown_to_html"] = self._markdown_to_html
        self.env.filters["escape_html"] = self._escape_html

    # ------------------------------------------------------------------
    # Page-level rendering
    # ------------------------------------------------------------------

    def render_slide(self, slide: ProcessedSlide, config: DecksetConfig, total_slides: int = 1) -> str:
        template = self.env.get_template("slide.html")
        return template.render(slide=slide, config=config, total_slides=total_slides)

    def render_homepage(self, presentations, context=None):
        try:
            template = self.env.get_template("homepage.html")
            context = context or {}
            return template.render(presentations=presentations, **context)
        except Exception as e:
            items = "".join(
                f'<li><a href="presentations/{p.folder_name}.html">'
                f"{self._escape_html(p.title)}</a></li>"
                for p in presentations
            )
            return (
                "<!DOCTYPE html><html><head><title>Presentations</title></head>"
                f"<body><h1>Presentations</h1><p>Error: {self._escape_html(str(e))}</p>"
                f"<ul>{items}</ul></body></html>"
            )

    def render_presentation_page(self, presentation, context: dict) -> str:
        try:
            template = self.env.get_template("presentation.html")
            return template.render(**context)
        except Exception as e:
            title = self._escape_html(
                presentation.info.title if hasattr(presentation, "info") else "Error"
            )
            return (
                f"<!DOCTYPE html><html><head><title>{title}</title></head>"
                f"<body><h1>Rendering Error</h1><p>{self._escape_html(str(e))}</p></body></html>"
            )

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------

    def _markdown_to_html(self, content: str) -> str:
        """Render a markdown snippet to HTML via ``MarkdownRenderer``."""
        if not content:
            return ""
        return self._renderer.render(content, "snippet")

    @staticmethod
    def _escape_html(text: str) -> str:
        if not text:
            return ""
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def set_theme_registry(self, slugs: Set[str], default_theme: str) -> None:
        """Configure the known theme slugs and site default.

        Called after the theme compiler runs so that ``resolve_theme``
        validates against the full pool (built-ins + compiled designs).
        """
        self._theme_slugs: Set[str] = slugs
        self._default_theme: str = default_theme

    def resolve_theme(self, theme_name: Optional[str]) -> str:
        """Return a known theme slug, falling back to the site default.

        Warns if *theme_name* is not recognised.
        """
        default = getattr(self, "_default_theme", "light")
        slugs: Set[str] = getattr(self, "_theme_slugs", {"light", "dark", "minimal"})

        if not theme_name:
            return default
        name = theme_name.strip().lower()
        if name in slugs:
            return name
        logger.warning(
            f"Unknown theme '{theme_name}', falling back to {default}"
        )
        return default

    def theme_stylesheets(self, config: DecksetConfig, asset_prefix: str) -> List[str]:
        """Return ``<link>`` tags for the resolved theme (and custom CSS if present)."""
        theme = self.resolve_theme(config.theme)
        href = f"{asset_prefix}assets/css/themes/{theme}.css"
        links = [
            f'<link id="theme-css" rel="stylesheet" href="{href}" data-default-href="{href}">'
        ]
        return links

    def _calculate_asset_path_prefix(self, folder_name: str) -> str:
        """Return relative path prefix (e.g. ``../`` or ``../../``) for assets."""
        depth = len(folder_name.split("/"))
        return "../" * depth
