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
        try:
            with open(presentation_info.markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            raise PresentationProcessingError(
                f"Failed to read markdown file {presentation_info.markdown_path}: {e}"
            )
        
        try:
            metadata = self.extract_metadata(content)
            slides = self.extract_slides(content)
            
            # Update presentation info with slide count
            presentation_info.slide_count = len(slides)
            
            return ProcessedPresentation(
                info=presentation_info,
                slides=slides,
                metadata=metadata
            )
        except Exception as e:
            raise PresentationProcessingError(
                f"Failed to process presentation {presentation_info.title}: {e}"
            )
    
    def extract_slides(self, content: str) -> List[Slide]:
        """
        Extract slides from markdown content by splitting on various separator formats.
        
        Args:
            content: Raw markdown content
            
        Returns:
            List of Slide objects
        """
        # Remove frontmatter from content before processing slides
        content_without_frontmatter = self._remove_frontmatter(content)
        
        # Try different separator patterns until one works
        slide_contents = None
        for pattern in self._slide_separators:
            potential_slides = pattern.split(content_without_frontmatter)
            if len(potential_slides) > 1:
                slide_contents = potential_slides
                break
        
        # If no separators found, treat entire content as one slide
        if slide_contents is None:
            slide_contents = [content_without_frontmatter]
        
        slides = []
        for i, slide_content in enumerate(slide_contents):
            slide_content = slide_content.strip()
            if not slide_content:
                continue
            
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
        
        return slides
    
    def extract_notes(self, slide_content: str) -> str:
        """
        Extract speaker notes from slide content using various note formats.
        
        Args:
            slide_content: Content of a single slide
            
        Returns:
            Extracted notes as markdown-formatted HTML string
        """
        note_lines = []
        
        # Try different note patterns
        for pattern in self._note_patterns:
            matches = pattern.findall(slide_content)
            for match in matches:
                note_text = match.strip()
                if note_text:
                    note_lines.append(note_text)
        
        # Also handle the legacy format from main.py (multiline notes after \n^)
        if '\n^' in slide_content:
            notes_idx = slide_content.index('\n^')
            legacy_notes = slide_content[notes_idx:].replace('^ ', '').replace('^', '').strip()
            if legacy_notes:
                note_lines.append(legacy_notes)
        
        # Convert notes to HTML using markdown
        if note_lines:
            notes_text = '\n'.join(note_lines)
            return markdown.markdown(notes_text)
        
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