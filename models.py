"""
Data models for the Deckset Website Generator.

This module defines the core data structures used throughout the application
for representing presentations, slides, and configuration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class PresentationInfo:
    """Information about a discovered presentation."""
    folder_name: str
    folder_path: str
    markdown_path: str
    title: str
    preview_image: Optional[str] = None
    slide_count: int = 0
    last_modified: Optional[datetime] = None


@dataclass
class Slide:
    """Represents a single slide in a presentation."""
    index: int
    content: str
    notes: str = ""
    image_path: Optional[str] = None


@dataclass
class ProcessedPresentation:
    """A fully processed presentation with all slides and metadata."""
    info: PresentationInfo
    slides: List[Slide]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratorConfig:
    """Configuration settings for the website generator."""
    output_dir: str = "docs"
    template_dir: str = "templates"
    slides_dir: str = "slides"
    fallback_image: str = "slides/redacted.png"
    exclude_folders: List[str] = field(default_factory=lambda: [
        '.git', '.kiro', 'node_modules', 'Examples', '__pycache__', '.pytest_cache'
    ])


# Base exception classes for error handling
class GeneratorError(Exception):
    """Base exception for all generator-related errors."""
    pass


class PresentationProcessingError(GeneratorError):
    """Errors that occur during presentation processing."""
    pass


class TemplateRenderingError(GeneratorError):
    """Errors that occur during template rendering."""
    pass