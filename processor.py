"""
Presentation processor for parsing Deckset markdown files.

This module handles the parsing of markdown content, extracting slides,
speaker notes, and metadata from Deckset presentation files.
"""

import re
import markdown
from pathlib import Path
from typing import List, Dict, Any

from models import (
    ProcessedPresentation, 
    PresentationInfo, 
    Slide, 
    PresentationProcessingError
)
import logging

# Set up logging
logger = logging.getLogger(__name__)


class PresentationProcessor:
    """Processes Deckset markdown files into structured presentation data."""
    
    def __init__(self):
        """Initialize the presentation processor."""
        # Compile regex patterns for better performance
        self._slide_separators = [
            re.compile(r'^---\s*$', re.MULTILINE),  # Standard --- separator
            re.compile(r'^\n---\n', re.MULTILINE),  # --- with newlines
            re.compile(r'^-{3,}\s*$', re.MULTILINE),  # Multiple dashes
        ]
        self._frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
        self._note_patterns = [
            re.compile(r'^\^(.*)$', re.MULTILINE),  # Standard ^ notes
            re.compile(r'^\^\s+(.*)$', re.MULTILINE),  # ^ with spaces
            re.compile(r'^\s*\^\s*(.*)$', re.MULTILINE),  # ^ with leading spaces
        ]
    
    def process_presentation(self, presentation_info: PresentationInfo) -> ProcessedPresentation:
        """
        Process a presentation markdown file into structured data.
        
        Args:
            presentation_info: Information about the presentation to process
            
        Returns:
            ProcessedPresentation with slides and metadata
            
        Raises:
            PresentationProcessingError: If processing fails
        """
        logger.info(f"Processing presentation: {presentation_info.title}")
        
        try:
            with open(presentation_info.markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (IOError, OSError) as e:
            raise PresentationProcessingError(
                f"Failed to read markdown file {presentation_info.markdown_path}: {e}",
                context={
                    "presentation_title": presentation_info.title,
                    "markdown_path": presentation_info.markdown_path,
                    "error_type": type(e).__name__
                }
            )
        except UnicodeDecodeError as e:
            raise PresentationProcessingError(
                f"Failed to decode markdown file {presentation_info.markdown_path}: {e}",
                context={
                    "presentation_title": presentation_info.title,
                    "markdown_path": presentation_info.markdown_path,
                    "encoding_error": str(e)
                }
            )
        
        try:
            metadata = self.extract_metadata(content)
            logger.debug(f"Extracted metadata: {list(metadata.keys())}")
            
            slides = self.extract_slides(content)
            logger.debug(f"Extracted {len(slides)} slides")
            
            # Update presentation info with slide count
            presentation_info.slide_count = len(slides)
            
            return ProcessedPresentation(
                info=presentation_info,
                slides=slides,
                metadata=metadata
            )
        except Exception as e:
            raise PresentationProcessingError(
                f"Failed to process presentation {presentation_info.title}: {e}",
                context={
                    "presentation_title": presentation_info.title,
                    "markdown_path": presentation_info.markdown_path,
                    "processing_stage": "content_parsing",
                    "error_type": type(e).__name__
                }
            )
    
    def extract_slides(self, content: str) -> List[Slide]:
        """
        Extract slides from markdown content by splitting on various separator formats.
        
        Args:
            content: Raw markdown content
            
        Returns:
            List of Slide objects
        """
        try:
            # Remove frontmatter from content before processing slides
            content_without_frontmatter = self._remove_frontmatter(content)
            
            # Try different separator patterns until one works
            slide_contents = None
            separator_used = None
            for i, pattern in enumerate(self._slide_separators):
                try:
                    potential_slides = pattern.split(content_without_frontmatter)
                    if len(potential_slides) > 1:
                        slide_contents = potential_slides
                        separator_used = i
                        break
                except Exception as e:
                    logger.warning(f"Failed to apply separator pattern {i}: {e}")
                    continue
            
            # If no separators found, treat entire content as one slide
            if slide_contents is None:
                slide_contents = [content_without_frontmatter]
                logger.debug("No slide separators found, treating as single slide")
            else:
                logger.debug(f"Split content into {len(slide_contents)} slides using separator pattern {separator_used}")
            
            slides = []
            for i, slide_content in enumerate(slide_contents):
                slide_content = slide_content.strip()
                if not slide_content:
                    logger.debug(f"Skipping empty slide at index {i}")
                    continue
                
                try:
                    notes = self.extract_notes(slide_content)
                    
                    # Remove notes from slide content
                    clean_content = self._remove_notes_from_content(slide_content)
                    
                    # Set image path based on slide index (for future use)
                    image_path = f"slides/{i + 1}.png" if i > 0 or len(slide_contents) > 1 else None
                    
                    slide = Slide(
                        index=i + 1,
                        content=clean_content,
                        notes=notes,
                        image_path=image_path
                    )
                    slides.append(slide)
                    
                except Exception as e:
                    # Log error but continue with other slides (graceful degradation)
                    logger.error(
                        f"Failed to process slide {i + 1}: {e}",
                        extra={
                            "slide_index": i + 1,
                            "slide_content_length": len(slide_content),
                            "error_type": type(e).__name__
                        }
                    )
                    # Create a minimal slide with raw content
                    slide = Slide(
                        index=i + 1,
                        content=slide_content,
                        notes="",
                        image_path=None
                    )
                    slides.append(slide)
            
            return slides
            
        except Exception as e:
            logger.error(f"Critical error in slide extraction: {e}")
            # Return a single slide with the raw content as fallback
            return [Slide(
                index=1,
                content=content,
                notes="",
                image_path=None
            )]
    
    def extract_notes(self, slide_content: str) -> str:
        """
        Extract speaker notes from slide content using various note formats.
        
        Args:
            slide_content: Content of a single slide
            
        Returns:
            Extracted notes as markdown-formatted HTML string
        """
        note_lines = []
        
        try:
            # Try different note patterns
            for i, pattern in enumerate(self._note_patterns):
                try:
                    matches = pattern.findall(slide_content)
                    for match in matches:
                        note_text = match.strip()
                        if note_text:
                            note_lines.append(note_text)
                except Exception as e:
                    logger.warning(f"Failed to apply note pattern {i}: {e}")
                    continue
            
            # Also handle the legacy format from main.py (multiline notes after \n^)
            try:
                if '\n^' in slide_content:
                    notes_idx = slide_content.index('\n^')
                    legacy_notes = slide_content[notes_idx:].replace('^ ', '').replace('^', '').strip()
                    if legacy_notes:
                        note_lines.append(legacy_notes)
            except Exception as e:
                logger.warning(f"Failed to extract legacy notes: {e}")
            
            # Convert notes to HTML using markdown
            if note_lines:
                try:
                    notes_text = '\n'.join(note_lines)
                    return markdown.markdown(notes_text)
                except Exception as e:
                    logger.error(f"Failed to convert notes to markdown: {e}")
                    # Return raw notes as fallback
                    return '\n'.join(note_lines)
            
            return ""
            
        except Exception as e:
            logger.error(f"Critical error in note extraction: {e}")
            return ""
    
    def extract_metadata(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata from markdown frontmatter or Deckset-style configuration.
        
        Args:
            content: Raw markdown content
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        # Try to extract YAML-style frontmatter
        frontmatter_match = self._frontmatter_pattern.match(content)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            metadata.update(self._parse_frontmatter(frontmatter))
        else:
            # Try Deckset-style configuration (key: value at the beginning)
            lines = content.split('\n')
            for line in lines[:20]:  # Only check first 20 lines
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' in line and not line.startswith('http'):
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    if key and value:
                        metadata[key] = self._parse_metadata_value(value)
                elif line.startswith('---') or line.startswith('!['):
                    # Stop parsing when we hit slide separators or images
                    break
        
        return metadata
    
    def _parse_frontmatter(self, frontmatter: str) -> Dict[str, Any]:
        """Parse YAML-style frontmatter."""
        metadata = {}
        for line in frontmatter.split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                if key and value:
                    metadata[key] = self._parse_metadata_value(value)
        return metadata
    
    def _parse_metadata_value(self, value: str) -> Any:
        """Parse metadata values, converting to appropriate types."""
        value = value.strip()
        
        # Remove quotes
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        
        # Convert boolean values
        if value.lower() in ('true', 'yes', 'on'):
            return True
        elif value.lower() in ('false', 'no', 'off'):
            return False
        
        # Try to convert to number
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        return value
    
    def _remove_frontmatter(self, content: str) -> str:
        """Remove frontmatter from content."""
        match = self._frontmatter_pattern.match(content)
        if match:
            return content[match.end():]
        
        # Handle Deckset-style configuration
        lines = content.split('\n')
        content_start = 0
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            if line.startswith('#') or line.startswith('![') or line.startswith('---'):
                content_start = i
                break
            if ':' in line and not line.startswith('http'):
                continue
            else:
                content_start = i
                break
        
        return '\n'.join(lines[content_start:])
    
    def _remove_notes_from_content(self, content: str) -> str:
        """Remove speaker notes from slide content."""
        # Remove lines that start with ^ (various formats)
        for pattern in self._note_patterns:
            content = pattern.sub('', content)
        
        # Handle legacy format
        if '\n^' in content:
            notes_idx = content.index('\n^')
            content = content[:notes_idx]
        
        return content.strip()