"""
Deckset markdown parser for processing Deckset-specific syntax.

This module provides parsing capabilities for Deckset markdown features including
global commands, slide commands, speaker notes, footnotes, and other Deckset-specific syntax.
"""

import re
from typing import List, Dict, Tuple, Optional
from enhanced_models import (
    DecksetConfig, SlideConfig, DecksetParsingError, DecksetParserInterface
)


class DecksetParser(DecksetParserInterface):
    """Parser for Deckset markdown syntax and commands."""
    
    def __init__(self):
        """Initialize the parser with regex patterns."""
        # Global command patterns
        self.global_patterns = {
            'theme': re.compile(r'^theme:\s*(.+)$', re.MULTILINE),
            'autoscale': re.compile(r'^autoscale:\s*(true|false)$', re.MULTILINE),
            'slide_numbers': re.compile(r'^slidenumbers:\s*(true|false)$', re.MULTILINE),
            'slide_count': re.compile(r'^slidecount:\s*(true|false)$', re.MULTILINE),
            'footer': re.compile(r'^footer:\s*(.+)$', re.MULTILINE),
            'background_image': re.compile(r'^background-image:\s*(.+)$', re.MULTILINE),
            'build_lists': re.compile(r'^build-lists:\s*(true|false)$', re.MULTILINE),
            'slide_transition': re.compile(r'^slide-transition:\s*(.+)$', re.MULTILINE),
            'code_language': re.compile(r'^code-language:\s*(.+)$', re.MULTILINE),
            'fit_headers': re.compile(r'^fit-headers:\s*(.+)$', re.MULTILINE),
            'slide_dividers': re.compile(r'^slide-dividers:\s*(.+)$', re.MULTILINE),
        }
        
        # Slide command patterns
        self.slide_patterns = {
            'background_image': re.compile(r'^\[\.background-image:\s*([^\]]+)\]', re.MULTILINE),
            'hide_footer': re.compile(r'^\[\.hide-footer\]', re.MULTILINE),
            'hide_slide_numbers': re.compile(r'^\[\.hide-slidenumbers\]', re.MULTILINE),
            'autoscale': re.compile(r'^\[\.autoscale:\s*(true|false)\]', re.MULTILINE),
            'slide_transition': re.compile(r'^\[\.slide-transition:\s*([^\]]+)\]', re.MULTILINE),
            'column': re.compile(r'^\[\.column\]', re.MULTILINE),
        }
        
        # Other patterns
        self.slide_separator = re.compile(r'^---\s*$', re.MULTILINE)
        self.speaker_notes = re.compile(r'^(\^.*)$', re.MULTILINE)
        self.footnote_ref = re.compile(r'\[\^([^\]]+)\]')
        self.footnote_def = re.compile(r'^\[\^([^\]]+)\]:\s*(.+)$', re.MULTILINE)
        self.fit_header = re.compile(r'^(#+)\s*\[fit\]\s*(.+)$', re.MULTILINE)
        self.emoji_shortcode = re.compile(r':([a-zA-Z0-9_+-]+):')
    
    def parse_global_commands(self, content: str) -> DecksetConfig:
        """Parse global Deckset commands from markdown content."""
        config = DecksetConfig()
        
        try:
            # Parse each global setting
            for setting, pattern in self.global_patterns.items():
                match = pattern.search(content)
                if match:
                    value = match.group(1).strip()
                    
                    if setting in ['autoscale', 'slide_numbers', 'slide_count', 'build_lists']:
                        setattr(config, setting, value.lower() == 'true')
                    elif setting in ['fit_headers', 'slide_dividers']:
                        # Parse comma-separated lists
                        values = [v.strip() for v in value.split(',')]
                        setattr(config, setting, values)
                    else:
                        setattr(config, setting, value)
            
            return config
            
        except Exception as e:
            raise DecksetParsingError(f"Error parsing global commands: {str(e)}")
    
    def parse_slide_commands(self, slide_content: str) -> SlideConfig:
        """Parse slide-specific commands from slide content."""
        config = SlideConfig()
        
        try:
            # Check for background image
            bg_match = self.slide_patterns['background_image'].search(slide_content)
            if bg_match:
                config.background_image = bg_match.group(1).strip()
            
            # Check for hide footer
            if self.slide_patterns['hide_footer'].search(slide_content):
                config.hide_footer = True
            
            # Check for hide slide numbers
            if self.slide_patterns['hide_slide_numbers'].search(slide_content):
                config.hide_slide_numbers = True
            
            # Check for autoscale override
            autoscale_match = self.slide_patterns['autoscale'].search(slide_content)
            if autoscale_match:
                config.autoscale = autoscale_match.group(1).lower() == 'true'
            
            # Check for slide transition
            transition_match = self.slide_patterns['slide_transition'].search(slide_content)
            if transition_match:
                config.slide_transition = transition_match.group(1).strip()
            
            # Check for columns
            if self.slide_patterns['column'].search(slide_content):
                config.columns = True
            
            return config
            
        except Exception as e:
            raise DecksetParsingError(f"Error parsing slide commands: {str(e)}")
    
    def extract_slide_separators(self, content: str) -> List[str]:
        """Extract individual slides from markdown content."""
        try:
            # Split by slide separators
            slides = self.slide_separator.split(content)
            
            # Remove empty slides and strip whitespace
            slides = [slide.strip() for slide in slides if slide.strip()]
            
            return slides
            
        except Exception as e:
            raise DecksetParsingError(f"Error extracting slide separators: {str(e)}")
    
    def process_fit_headers(self, content: str, config: DecksetConfig) -> str:
        """Process [fit] modifiers on headers."""
        try:
            def replace_fit_header(match):
                level = match.group(1)  # Header level (# ## ###)
                text = match.group(2)   # Header text
                return f'{level} <span class="fit-text">{text}</span>'
            
            return self.fit_header.sub(replace_fit_header, content)
            
        except Exception as e:
            raise DecksetParsingError(f"Error processing fit headers: {str(e)}")
    
    def process_speaker_notes(self, content: str) -> Tuple[str, str]:
        """Separate speaker notes from slide content."""
        try:
            notes = []
            
            # Find all speaker notes
            for match in self.speaker_notes.finditer(content):
                note = match.group(1)[1:].strip()  # Remove ^ prefix
                notes.append(note)
            
            # Remove speaker notes from content
            clean_content = self.speaker_notes.sub('', content)
            
            # Join notes with newlines
            notes_text = '\n'.join(notes)
            
            return clean_content.strip(), notes_text
            
        except Exception as e:
            raise DecksetParsingError(f"Error processing speaker notes: {str(e)}")
    
    def process_footnotes(self, content: str) -> Tuple[str, Dict[str, str]]:
        """Process footnote references and definitions."""
        try:
            footnotes = {}
            
            # Find footnote definitions
            for match in self.footnote_def.finditer(content):
                key = match.group(1)
                definition = match.group(2).strip()
                footnotes[key] = definition
            
            # Remove footnote definitions from content
            clean_content = self.footnote_def.sub('', content)
            
            return clean_content.strip(), footnotes
            
        except Exception as e:
            raise DecksetParsingError(f"Error processing footnotes: {str(e)}")
    
    def process_emoji_shortcodes(self, content: str) -> str:
        """Convert emoji shortcodes to Unicode."""
        # Basic emoji mapping - can be extended
        emoji_map = {
            'smile': '😊',
            'heart': '❤️',
            'thumbsup': '👍',
            'thumbsdown': '👎',
            'fire': '🔥',
            'rocket': '🚀',
            'star': '⭐',
            'warning': '⚠️',
            'check': '✅',
            'x': '❌',
            'arrow_right': '→',
            'arrow_left': '←',
            'arrow_up': '↑',
            'arrow_down': '↓',
        }
        
        try:
            def replace_emoji(match):
                shortcode = match.group(1)
                return emoji_map.get(shortcode, f':{shortcode}:')
            
            return self.emoji_shortcode.sub(replace_emoji, content)
            
        except Exception as e:
            raise DecksetParsingError(f"Error processing emoji shortcodes: {str(e)}")
    
    def detect_auto_slide_breaks(self, content: str, config: DecksetConfig) -> List[str]:
        """Detect automatic slide breaks at heading levels."""
        if not config.slide_dividers:
            return self.extract_slide_separators(content)
        
        try:
            slides = []
            current_slide = []
            lines = content.split('\n')
            
            for line in lines:
                # Check if line matches any slide divider pattern
                is_divider = False
                for divider in config.slide_dividers:
                    if line.strip().startswith(divider + ' '):
                        is_divider = True
                        break
                
                if is_divider and current_slide:
                    # Start new slide
                    slides.append('\n'.join(current_slide).strip())
                    current_slide = [line]
                else:
                    current_slide.append(line)
            
            # Add final slide
            if current_slide:
                slides.append('\n'.join(current_slide).strip())
            
            return [slide for slide in slides if slide.strip()]
            
        except Exception as e:
            raise DecksetParsingError(f"Error detecting auto slide breaks: {str(e)}")