"""
Data models for the Deckset Website Generator.

This module defines the core data structures used throughout the application
for representing presentations, slides, and configuration. It includes both
basic models for simple processing and enhanced models for comprehensive
Deckset markdown processing with advanced layout features, media processing,
and configuration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Set, Tuple
from abc import ABC, abstractmethod


# Basic Models (for backward compatibility)
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
    output_dir: str = "site"
    template_dir: str = "templates"
    slides_dir: str = "slides"
    exclude_folders: List[str] = field(default_factory=lambda: ["__pycache__", "node_modules"])


# Enhanced Configuration Models
@dataclass
class DecksetConfig:
    """Global Deckset configuration settings."""
    # Global settings
    theme: Optional[str] = None
    autoscale: bool = False
    slide_numbers: bool = False
    slide_count: bool = False
    footer: Optional[str] = None
    background_image: Optional[str] = None
    build_lists: bool = False
    slide_transition: Optional[str] = None
    code_language: Optional[str] = None
    fit_headers: List[str] = field(default_factory=list)
    slide_dividers: List[str] = field(default_factory=list)


@dataclass
class SlideConfig:
    """Slide-specific configuration overrides."""
    background_image: Optional[str] = None
    hide_footer: bool = False
    hide_slide_numbers: bool = False
    autoscale: Optional[bool] = None
    slide_transition: Optional[str] = None
    columns: bool = False
    # Computed flag: apply automatic readability filter overlay for this slide
    readability_filter_mode: bool = False


# Media Processing Models
@dataclass
class ImageModifiers:
    """Image placement and styling modifiers."""
    placement: str  # 'background', 'inline', 'left', 'right'
    scaling: str    # 'fit', 'fill', 'original', percentage
    filter: str     # 'filtered', 'original'
    corner_radius: Optional[int] = None
    # For inline images, optional alignment hint: 'left' or 'right'
    inline_alignment: Optional[str] = None


@dataclass
class ProcessedImage:
    """Processed image with web-optimized paths and modifiers."""
    src_path: str
    web_path: str
    modifiers: ImageModifiers
    grid_position: Optional[Tuple[int, int]] = None
    alt_text: str = ""


@dataclass
class MediaModifiers:
    """Video/audio placement and playback modifiers."""
    placement: str      # 'background', 'inline', 'left', 'right'
    autoplay: bool = False
    loop: bool = False
    mute: bool = False
    hide: bool = False
    scaling: str = "fit"  # 'fit', 'fill', percentage


@dataclass
class ProcessedVideo:
    """Processed video with web-optimized paths and modifiers."""
    src_path: str
    web_path: str
    modifiers: MediaModifiers
    embed_type: str     # 'local', 'youtube', 'vimeo'
    embed_url: Optional[str] = None


@dataclass
class ProcessedAudio:
    """Processed audio with web-optimized paths and modifiers."""
    src_path: str
    web_path: str
    modifiers: MediaModifiers


# Layout and Content Models
@dataclass
class ColumnContent:
    """Content for a single column in multi-column layout."""
    index: int
    content: str
    width_percentage: float


@dataclass
class ImageGrid:
    """Grid layout for multiple consecutive inline images."""
    images: List[ProcessedImage]
    columns: int
    gap: str = "1rem"


# Figure Models
@dataclass
class InlineFigure:
    """Inline image with an associated caption placed directly below the image."""
    image: ProcessedImage
    caption: str


# Code Processing Models
@dataclass
class HighlightConfig:
    """Configuration for code line highlighting."""
    highlighted_lines: Set[int] = field(default_factory=set)
    highlight_type: str = "none"  # 'lines', 'all', 'none'


@dataclass
class ProcessedCodeBlock:
    """Processed code block with syntax highlighting."""
    content: str
    language: str
    highlighted_lines: Set[int] = field(default_factory=set)
    line_numbers: bool = False


# Math Processing Models
@dataclass
class MathFormula:
    """Mathematical formula with LaTeX content."""
    content: str
    formula_type: str  # 'display', 'inline'
    position: int
    valid: bool = True


# Enhanced Slide Models
@dataclass
class ProcessedSlide:
    """Enhanced slide with full Deckset feature support."""
    index: int
    content: str
    notes: str = ""
    columns: List[ColumnContent] = field(default_factory=list)
    background_image: Optional[ProcessedImage] = None
    inline_images: List[ProcessedImage] = field(default_factory=list)
    inline_figures: List[InlineFigure] = field(default_factory=list)
    videos: List[ProcessedVideo] = field(default_factory=list)
    audio: List[ProcessedAudio] = field(default_factory=list)
    code_blocks: List[ProcessedCodeBlock] = field(default_factory=list)
    math_formulas: List[MathFormula] = field(default_factory=list)
    footnotes: Dict[str, str] = field(default_factory=dict)
    slide_config: SlideConfig = field(default_factory=SlideConfig)


@dataclass
class EnhancedPresentation:
    """Enhanced presentation with full Deckset feature support."""
    info: PresentationInfo
    slides: List[ProcessedSlide]
    config: DecksetConfig
    global_footnotes: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)  # For compatibility with basic processor


# Context Models for Processing
@dataclass
class SlideContext:
    """Context information for slide processing."""
    slide_index: int
    total_slides: int
    presentation_path: str
    config: DecksetConfig
    slide_config: SlideConfig


# Base exception classes for error handling
class GeneratorError(Exception):
    """Base exception for all generator-related errors."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize the error with message and optional context.
        
        Args:
            message: Error message
            context: Optional dictionary with additional context information
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
    
    def __str__(self) -> str:
        """Return string representation with context if available."""
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} (Context: {context_str})"
        return self.message


class PresentationProcessingError(GeneratorError):
    """Errors that occur during presentation processing."""
    pass


class TemplateRenderingError(GeneratorError):
    """Errors that occur during template rendering."""
    pass


class FileOperationError(GeneratorError):
    """Errors that occur during file operations."""
    pass


class ScanningError(GeneratorError):
    """Errors that occur during repository scanning."""
    pass


class ConfigurationError(GeneratorError):
    """Errors that occur due to invalid configuration."""
    pass


# Enhanced Error Classes
class DecksetParsingError(Exception):
    """Errors specific to Deckset syntax parsing."""
    
    def __init__(self, message: str, line_number: Optional[int] = None, context: Optional[str] = None):
        self.line_number = line_number
        self.context = context
        super().__init__(message)


class MediaProcessingError(Exception):
    """Errors in media file processing."""
    
    def __init__(self, message: str, media_path: Optional[str] = None, media_type: Optional[str] = None):
        self.media_path = media_path
        self.media_type = media_type
        super().__init__(message)


class SlideProcessingError(Exception):
    """Errors in slide processing."""
    
    def __init__(self, message: str, slide_index: Optional[int] = None):
        self.slide_index = slide_index
        super().__init__(message)


# Base Interfaces
class DecksetParserInterface(ABC):
    """Interface for Deckset markdown parsing."""
    
    @abstractmethod
    def parse_global_commands(self, content: str) -> DecksetConfig:
        """Parse global Deckset commands from markdown content."""
        pass
    
    @abstractmethod
    def parse_slide_commands(self, slide_content: str) -> SlideConfig:
        """Parse slide-specific commands from slide content."""
        pass
    
    @abstractmethod
    def extract_slide_separators(self, content: str) -> List[str]:
        """Extract individual slides from markdown content."""
        pass
    
    @abstractmethod
    def process_fit_headers(self, content: str, config: DecksetConfig) -> str:
        """Process [fit] modifiers on headers."""
        pass
    
    @abstractmethod
    def process_speaker_notes(self, content: str) -> Tuple[str, str]:
        """Separate speaker notes from slide content."""
        pass
    
    @abstractmethod
    def process_footnotes(self, content: str) -> Tuple[str, Dict[str, str]]:
        """Process footnote references and definitions."""
        pass
    
    @abstractmethod
    def process_emoji_shortcodes(self, content: str) -> str:
        """Convert emoji shortcodes to Unicode."""
        pass
    
    @abstractmethod
    def detect_auto_slide_breaks(self, content: str, config: DecksetConfig) -> List[str]:
        """Detect automatic slide breaks at heading levels."""
        pass


class MediaProcessorInterface(ABC):
    """Interface for media processing."""
    
    @abstractmethod
    def process_image(self, image_syntax: str, slide_context: SlideContext) -> ProcessedImage:
        """Process image with Deckset modifiers."""
        pass
    
    @abstractmethod
    def process_video(self, video_syntax: str, slide_context: SlideContext) -> ProcessedVideo:
        """Process video with Deckset modifiers."""
        pass
    
    @abstractmethod
    def process_audio(self, audio_syntax: str, slide_context: SlideContext) -> ProcessedAudio:
        """Process audio with Deckset modifiers."""
        pass
    
    @abstractmethod
    def parse_image_modifiers(self, alt_text: str) -> ImageModifiers:
        """Parse image modifiers from alt text."""
        pass
    
    @abstractmethod
    def parse_media_modifiers(self, alt_text: str) -> MediaModifiers:
        """Parse media modifiers from alt text."""
        pass
    
    @abstractmethod
    def optimize_image_for_web(self, image_path: str, output_path: str) -> str:
        """Optimize image for web delivery."""
        pass
    
    @abstractmethod
    def create_image_grid(self, images: List[ProcessedImage]) -> ImageGrid:
        """Create grid layout for consecutive inline images."""
        pass


class SlideProcessorInterface(ABC):
    """Interface for slide processing."""
    
    @abstractmethod
    def process_slide(self, slide_content: str, slide_index: int, config: DecksetConfig) -> ProcessedSlide:
        """Process individual slide with all features."""
        pass
    
    @abstractmethod
    def process_columns(self, slide_content: str) -> List[ColumnContent]:
        """Process multi-column layout."""
        pass
    
    @abstractmethod
    def process_background_image(self, slide_content: str) -> Optional[ProcessedImage]:
        """Process slide background image."""
        pass
    
    @abstractmethod
    def remove_code_blocks(self, slide_content: str) -> str:
        """Remove code blocks."""
        pass
    
    @abstractmethod
    def apply_autoscale(self, slide_content: str, config: DecksetConfig) -> str:
        """Apply autoscale to slide content."""
        pass
