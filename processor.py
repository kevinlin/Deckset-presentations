"""
Presentation processor for parsing Deckset markdown files.

This module handles the parsing of markdown content, extracting slides,
speaker notes, and metadata from Deckset presentation files.
"""

import re
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
        Extract slides from markdown content by splitting on slide separators.
        
        Args:
            content: Raw markdown content
            
        Returns:
            List of Slide objects
        """
        # Split content by slide separators (---)
        slide_contents = re.split(r'^---\s*$', content, flags=re.MULTILINE)
        
        slides = []
        for i, slide_content in enumerate(slide_contents):
            slide_content = slide_content.strip()
            if not slide_content:
                continue
            
            notes = self.extract_notes(slide_content)
            
            # Remove notes from slide content
            clean_content = self._remove_notes_from_content(slide_content)
            
            slide = Slide(
                index=i + 1,
                content=clean_content,
                notes=notes
            )
            slides.append(slide)
        
        return slides
    
    def extract_notes(self, slide_content: str) -> str:
        """
        Extract speaker notes from slide content (lines starting with ^).
        
        Args:
            slide_content: Content of a single slide
            
        Returns:
            Extracted notes as a string
        """
        lines = slide_content.split('\n')
        note_lines = []
        
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith('^'):
                # Remove the ^ prefix and add to notes
                note_text = stripped_line[1:].strip()
                if note_text:
                    note_lines.append(note_text)
        
        return '\n'.join(note_lines)
    
    def extract_metadata(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata from markdown frontmatter or content.
        
        Args:
            content: Raw markdown content
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        # Try to extract YAML frontmatter
        if content.startswith('---'):
            try:
                # Find the end of frontmatter
                end_match = re.search(r'\n---\s*\n', content)
                if end_match:
                    frontmatter = content[3:end_match.start()]
                    # Simple key-value extraction (not full YAML parsing)
                    for line in frontmatter.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()
            except Exception:
                # If frontmatter parsing fails, continue without metadata
                pass
        
        return metadata
    
    def _remove_notes_from_content(self, content: str) -> str:
        """Remove speaker notes from slide content."""
        lines = content.split('\n')
        clean_lines = []
        
        for line in lines:
            if not line.strip().startswith('^'):
                clean_lines.append(line)
        
        return '\n'.join(clean_lines).strip()