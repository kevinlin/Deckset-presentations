"""
Enhanced Deckset markdown parser for comprehensive Deckset compatibility.

This module provides parsing capabilities for all Deckset-specific markdown features
including global commands, slide commands, speaker notes, footnotes, and more.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple, Set
import logging

logger = logging.getLogger(__name__)


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


class DecksetParsingError(Exception):
    """Errors specific to Deckset syntax parsing."""
    def __init__(self, message: str, line_number: int = None, context: str = None):
        self.line_number = line_number
        self.context = context
        super().__init__(message)


class DecksetParser:
    """Enhanced parser for Deckset markdown syntax."""
    
    def __init__(self):
        """Initialize the Deckset parser with compiled regex patterns."""
        # Global command patterns
        self._global_patterns = {
            'theme': re.compile(r'^theme:\s*(.+)$', re.MULTILINE | re.IGNORECASE),
            'autoscale': re.compile(r'^autoscale:\s*(true|false|yes|no|on|off|1|0)$', re.MULTILINE | re.IGNORECASE),
            'slide_numbers': re.compile(r'^slidenumbers:\s*(true|false|yes|no|on|off|1|0)$', re.MULTILINE | re.IGNORECASE),
            'slide_count': re.compile(r'^slidecount:\s*(true|false|yes|no|on|off|1|0)$', re.MULTILINE | re.IGNORECASE),
            'footer': re.compile(r'^footer:\s*(.+)$', re.MULTILINE | re.IGNORECASE),
            'background_image': re.compile(r'^background-image:\s*(.+)$', re.MULTILINE | re.IGNORECASE),
            'build_lists': re.compile(r'^build-lists:\s*(true|false|yes|no|on|off|1|0)$', re.MULTILINE | re.IGNORECASE),
            'slide_transition': re.compile(r'^slide-transition:\s*(.+)$', re.MULTILINE | re.IGNORECASE),
            'code_language': re.compile(r'^code-language:\s*(.+)$', re.MULTILINE | re.IGNORECASE),
            'fit_headers': re.compile(r'^fit-headers:\s*(.+)$', re.MULTILINE | re.IGNORECASE),
            'slide_dividers': re.compile(r'^slide-dividers:\s*(.+)$', re.MULTILINE | re.IGNORECASE),
        }
        
        # Slide command patterns
        self._slide_command_patterns = {
            'column': re.compile(r'^\[\.column\]$', re.MULTILINE | re.IGNORECASE),
            'background_image': re.compile(r'^\[\.background-image:\s*([^\]]+)\]$', re.MULTILINE | re.IGNORECASE),
            'hide_footer': re.compile(r'^\[\.hide-footer\]$', re.MULTILINE | re.IGNORECASE),
            'hide_slide_numbers': re.compile(r'^\[\.hide-slide-numbers\]$', re.MULTILINE | re.IGNORECASE),
            'autoscale': re.compile(r'^\[\.autoscale:\s*(true|false|yes|no|on|off|1|0)\]$', re.MULTILINE | re.IGNORECASE),
            'slide_transition': re.compile(r'^\[\.slide-transition:\s*([^\]]+)\]$', re.MULTILINE | re.IGNORECASE),
        }
        
        # Slide separator patterns
        self._slide_separators = [
            re.compile(r'^---\s*$', re.MULTILINE),  # Standard --- separator
            re.compile(r'^\n---\n', re.MULTILINE),  # --- with newlines
            re.compile(r'^-{3,}\s*$', re.MULTILINE),  # Multiple dashes
        ]
        
        # Speaker notes patterns
        self._note_patterns = [
            re.compile(r'^\^(.*)$', re.MULTILINE),  # Standard ^ notes
            re.compile(r'^\^\s+(.*)$', re.MULTILINE),  # ^ with spaces
            re.compile(r'^\s*\^\s*(.*)$', re.MULTILINE),  # ^ with leading spaces
        ]
        
        # Footnote patterns
        self._footnote_ref_pattern = re.compile(r'\[\^([^\]]+)\]')
        self._footnote_def_pattern = re.compile(r'^\[\^([^\]]+)\]:\s*(.+)$', re.MULTILINE)
        
        # Fit header pattern
        self._fit_header_pattern = re.compile(r'^(#{1,6})\s*\[fit\]\s*(.+)$', re.MULTILINE)
        
        # Emoji shortcode pattern
        self._emoji_pattern = re.compile(r':([a-zA-Z0-9_+-]+):')
        
        # Common emoji mappings
        self._emoji_map = {
            'smile': '😊',
            'heart': '❤️',
            'thumbs_up': '👍',
            'thumbs_down': '👎',
            'fire': '🔥',
            'star': '⭐',
            'check': '✅',
            'x': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'question': '❓',
            'exclamation': '❗',
            'arrow_right': '➡️',
            'arrow_left': '⬅️',
            'arrow_up': '⬆️',
            'arrow_down': '⬇️',
        }
    
    def parse_global_commands(self, content: str) -> DecksetConfig:
        """
        Extract global Deckset commands from markdown content.
        
        Args:
            content: Raw markdown content
            
        Returns:
            DecksetConfig with parsed global settings
            
        Raises:
            DecksetParsingError: If parsing fails
        """
        try:
            config = DecksetConfig()
            
            # Parse each global command type
            for command, pattern in self._global_patterns.items():
                try:
                    match = pattern.search(content)
                    if match:
                        value = match.group(1).strip()
                        
                        if command in ['autoscale', 'slide_numbers', 'slide_count', 'build_lists']:
                            # Boolean values
                            parsed_value = self._parse_boolean(value)
                            setattr(config, command, parsed_value)
                        elif command in ['fit_headers', 'slide_dividers']:
                            # List values (comma-separated)
                            setattr(config, command, [item.strip() for item in value.split(',') if item.strip()])
                        else:
                            # String values
                            setattr(config, command, value)
                            
                        logger.debug(f"Parsed global command {command}: {getattr(config, command)}")
                        
                except Exception as e:
                    logger.warning(f"Failed to parse global command {command}: {e}")
                    continue
            
            return config
            
        except Exception as e:
            raise DecksetParsingError(f"Failed to parse global commands: {e}")
    
    def parse_slide_commands(self, slide_content: str) -> SlideConfig:
        """
        Parse slide-specific commands from slide content.
        
        Args:
            slide_content: Content of a single slide
            
        Returns:
            SlideConfig with parsed slide-specific settings
            
        Raises:
            DecksetParsingError: If parsing fails
        """
        try:
            config = SlideConfig()
            
            # Parse each slide command type
            for command, pattern in self._slide_command_patterns.items():
                try:
                    match = pattern.search(slide_content)
                    if match:
                        if command == 'column':
                            config.columns = True
                        elif command in ['hide_footer', 'hide_slide_numbers']:
                            setattr(config, command, True)
                        elif command == 'autoscale':
                            value = match.group(1).strip()
                            config.autoscale = self._parse_boolean(value)
                        elif command in ['background_image', 'slide_transition']:
                            value = match.group(1).strip()
                            setattr(config, command, value)
                            
                        logger.debug(f"Parsed slide command {command}: {getattr(config, command)}")
                        
                except Exception as e:
                    logger.warning(f"Failed to parse slide command {command}: {e}")
                    continue
            
            return config
            
        except Exception as e:
            raise DecksetParsingError(f"Failed to parse slide commands: {e}")
    
    def _parse_boolean(self, value: str) -> bool:
        """Parse boolean values from string."""
        return value.strip().lower() in ('true', 'yes', 'on', '1')
    
    def extract_slide_separators(self, content: str) -> List[str]:
        """
        Extract slides by splitting on various separator formats.
        
        Args:
            content: Raw markdown content
            
        Returns:
            List of slide content strings
            
        Raises:
            DecksetParsingError: If extraction fails
        """
        try:
            # Remove any frontmatter or global commands from the beginning
            content = self._remove_frontmatter_and_globals(content)
            
            # Try different separator patterns until one works
            slide_contents = None
            separator_used = None
            
            for i, pattern in enumerate(self._slide_separators):
                try:
                    potential_slides = pattern.split(content)
                    if len(potential_slides) > 1:
                        slide_contents = potential_slides
                        separator_used = i
                        break
                except Exception as e:
                    logger.warning(f"Failed to apply separator pattern {i}: {e}")
                    continue
            
            # If no separators found, treat entire content as one slide
            if slide_contents is None:
                slide_contents = [content]
                logger.debug("No slide separators found, treating as single slide")
            else:
                logger.debug(f"Split content into {len(slide_contents)} slides using separator pattern {separator_used}")
            
            # Clean up slide contents
            cleaned_slides = []
            for slide_content in slide_contents:
                slide_content = slide_content.strip()
                if slide_content:  # Skip empty slides
                    cleaned_slides.append(slide_content)
            
            return cleaned_slides
            
        except Exception as e:
            raise DecksetParsingError(f"Failed to extract slide separators: {e}")
    
    def detect_auto_slide_breaks(self, content: str, config: DecksetConfig) -> List[str]:
        """
        Detect automatic slide breaks based on slide-dividers configuration.
        
        Args:
            content: Raw markdown content
            config: DecksetConfig with slide_dividers setting
            
        Returns:
            List of slide content strings with auto-breaks applied
            
        Raises:
            DecksetParsingError: If detection fails
        """
        try:
            if not config.slide_dividers:
                # No auto-breaks configured, return original slide separation
                return self.extract_slide_separators(content)
            
            # Remove frontmatter and globals
            content = self._remove_frontmatter_and_globals(content)
            
            # Build pattern for auto-break headers
            header_patterns = []
            for divider in config.slide_dividers:
                if divider.startswith('#'):
                    # Header level divider (e.g., '#', '##')
                    level = len(divider)
                    pattern = re.compile(f'^#{{{level}}}\\s+(.+)$', re.MULTILINE)
                    header_patterns.append(pattern)
            
            if not header_patterns:
                # No valid header patterns, fall back to regular separation
                return self.extract_slide_separators(content)
            
            # Find all header positions
            break_positions = []
            for pattern in header_patterns:
                for match in pattern.finditer(content):
                    break_positions.append(match.start())
            
            # Sort break positions
            break_positions.sort()
            
            if not break_positions:
                # No auto-breaks found, return as single slide
                return [content]
            
            # Split content at break positions
            slides = []
            start = 0
            
            for pos in break_positions:
                if start < pos:
                    slide_content = content[start:pos].strip()
                    if slide_content:
                        slides.append(slide_content)
                start = pos
            
            # Add final slide
            if start < len(content):
                final_slide = content[start:].strip()
                if final_slide:
                    slides.append(final_slide)
            
            logger.debug(f"Auto-break created {len(slides)} slides from {len(config.slide_dividers)} divider patterns")
            return slides
            
        except Exception as e:
            raise DecksetParsingError(f"Failed to detect auto slide breaks: {e}")
    
    def process_speaker_notes(self, content: str) -> Tuple[str, str]:
        """
        Extract speaker notes from slide content.
        
        Args:
            content: Slide content with potential speaker notes
            
        Returns:
            Tuple of (cleaned_content, notes_html)
            
        Raises:
            DecksetParsingError: If processing fails
        """
        try:
            note_lines = []
            cleaned_lines = []
            
            # Process line by line to separate notes from content
            for line in content.split('\n'):
                is_note = False
                
                # Check each note pattern
                for pattern in self._note_patterns:
                    match = pattern.match(line)
                    if match:
                        note_text = match.group(1).strip()
                        if note_text:
                            note_lines.append(note_text)
                        is_note = True
                        break
                
                if not is_note:
                    cleaned_lines.append(line)
            
            # Join cleaned content
            cleaned_content = '\n'.join(cleaned_lines).strip()
            
            # Convert notes to markdown if any found
            notes_html = ""
            if note_lines:
                try:
                    import markdown
                    notes_text = '\n'.join(note_lines)
                    notes_html = markdown.markdown(notes_text)
                except ImportError:
                    # Fallback if markdown not available
                    notes_html = '<br>'.join(note_lines)
                except Exception as e:
                    logger.warning(f"Failed to convert notes to HTML: {e}")
                    notes_html = '\n'.join(note_lines)
            
            logger.debug(f"Extracted {len(note_lines)} note lines")
            return cleaned_content, notes_html
            
        except Exception as e:
            raise DecksetParsingError(f"Failed to process speaker notes: {e}")
    
    def process_footnotes(self, content: str) -> Tuple[str, Dict[str, str]]:
        """
        Process footnote references and definitions.
        
        Args:
            content: Content with potential footnotes
            
        Returns:
            Tuple of (content_with_refs, footnote_definitions)
            
        Raises:
            DecksetParsingError: If processing fails
        """
        try:
            footnote_definitions = {}
            
            # Extract footnote definitions
            for match in self._footnote_def_pattern.finditer(content):
                footnote_id = match.group(1)
                footnote_text = match.group(2).strip()
                footnote_definitions[footnote_id] = footnote_text
            
            # Remove footnote definitions from content
            content_without_defs = self._footnote_def_pattern.sub('', content)
            
            # Find all footnote references
            footnote_refs = set()
            for match in self._footnote_ref_pattern.finditer(content_without_defs):
                footnote_refs.add(match.group(1))
            
            # Validate that all references have definitions
            missing_refs = footnote_refs - set(footnote_definitions.keys())
            if missing_refs:
                logger.warning(f"Missing footnote definitions for: {missing_refs}")
            
            logger.debug(f"Processed {len(footnote_definitions)} footnote definitions and {len(footnote_refs)} references")
            return content_without_defs.strip(), footnote_definitions
            
        except Exception as e:
            raise DecksetParsingError(f"Failed to process footnotes: {e}")
    
    def process_fit_headers(self, content: str, config: DecksetConfig) -> str:
        """
        Process [fit] modifiers on headers.
        
        Args:
            content: Content with potential fit headers
            config: DecksetConfig for context
            
        Returns:
            Content with fit headers processed
            
        Raises:
            DecksetParsingError: If processing fails
        """
        try:
            def replace_fit_header(match):
                header_level = match.group(1)  # The # symbols
                header_text = match.group(2).strip()
                
                # Add CSS class for fit text styling
                return f'{header_level} <span class="fit-text">{header_text}</span>'
            
            processed_content = self._fit_header_pattern.sub(replace_fit_header, content)
            
            # Count how many fit headers were processed
            fit_count = len(self._fit_header_pattern.findall(content))
            if fit_count > 0:
                logger.debug(f"Processed {fit_count} fit headers")
            
            return processed_content
            
        except Exception as e:
            raise DecksetParsingError(f"Failed to process fit headers: {e}")
    
    def process_emoji_shortcodes(self, content: str) -> str:
        """
        Convert emoji shortcodes to Unicode emojis.
        
        Args:
            content: Content with potential emoji shortcodes
            
        Returns:
            Content with emojis converted
            
        Raises:
            DecksetParsingError: If processing fails
        """
        try:
            def replace_emoji(match):
                emoji_name = match.group(1)
                return self._emoji_map.get(emoji_name, match.group(0))  # Return original if not found
            
            processed_content = self._emoji_pattern.sub(replace_emoji, content)
            
            # Count how many emojis were converted
            emoji_matches = self._emoji_pattern.findall(content)
            converted_count = sum(1 for emoji in emoji_matches if emoji in self._emoji_map)
            
            if converted_count > 0:
                logger.debug(f"Converted {converted_count} emoji shortcodes")
            
            return processed_content
            
        except Exception as e:
            raise DecksetParsingError(f"Failed to process emoji shortcodes: {e}")
    
    def _remove_frontmatter_and_globals(self, content: str) -> str:
        """
        Remove frontmatter and global commands from content.
        
        Args:
            content: Raw markdown content
            
        Returns:
            Content with frontmatter and globals removed
        """
        try:
            # Remove YAML frontmatter
            frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
            content = frontmatter_pattern.sub('', content)
            
            # Remove global commands from the beginning
            lines = content.split('\n')
            content_start = 0
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Check if line is a global command
                is_global_command = False
                for pattern in self._global_patterns.values():
                    if pattern.match(line):
                        is_global_command = True
                        break
                
                if not is_global_command:
                    content_start = i
                    break
            
            return '\n'.join(lines[content_start:]).strip()
            
        except Exception as e:
            logger.warning(f"Failed to remove frontmatter and globals: {e}")
            return content