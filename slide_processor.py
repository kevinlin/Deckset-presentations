"""
Slide processor for handling individual slide processing with advanced layout features.

This module provides processing capabilities for slides including multi-column layouts,
background images, code blocks, math formulas, and autoscaling.
"""

import re
from typing import List, Optional
from enhanced_models import (
    ProcessedSlide, ColumnContent, ProcessedImage, ProcessedCodeBlock, MathFormula,
    DecksetConfig, SlideConfig, SlideContext, SlideProcessingError, SlideProcessorInterface
)


class SlideProcessor(SlideProcessorInterface):
    """Processor for individual slides with advanced layout features."""
    
    def __init__(self):
        """Initialize the slide processor with regex patterns."""
        # Column separator pattern
        self.column_pattern = re.compile(r'^\[\.column\]', re.MULTILINE)
        
        # Code block patterns
        self.code_block_pattern = re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL)
        self.code_highlight_pattern = re.compile(r'^\[\.code-highlight:\s*([^\]]+)\]', re.MULTILINE)
        
        # Math formula patterns
        self.display_math_pattern = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)
        self.inline_math_pattern = re.compile(r'\$([^$]+)\$')
        
        # Background image pattern
        self.background_image_pattern = re.compile(r'^\[\.background-image:\s*([^\]]+)\]', re.MULTILINE)
        
        # Autoscale content detection
        self.content_length_threshold = 1000  # Characters
    
    def process_slide(self, slide_content: str, slide_index: int, config: DecksetConfig) -> ProcessedSlide:
        """Process individual slide with all features."""
        try:
            slide = ProcessedSlide(index=slide_index, content=slide_content)
            
            # Parse slide-specific configuration
            from deckset_parser import DecksetParser
            parser = DecksetParser()
            slide.slide_config = parser.parse_slide_commands(slide_content)
            
            # Process speaker notes and footnotes
            content_without_notes, notes = parser.process_speaker_notes(slide_content)
            content_without_footnotes, footnotes = parser.process_footnotes(content_without_notes)
            
            slide.notes = notes
            slide.footnotes = footnotes
            slide.content = content_without_footnotes
            
            # Process columns if present
            if slide.slide_config.columns:
                slide.columns = self.process_columns(slide.content)
            
            # Process background image
            slide.background_image = self.process_background_image(slide.content)
            
            # Process code blocks
            slide.content = self.process_code_blocks(slide.content)
            
            # Process math formulas
            slide.content = self.process_math_formulas(slide.content)
            
            # Apply autoscale if needed
            if config.autoscale or slide.slide_config.autoscale:
                slide.content = self.apply_autoscale(slide.content, config)
            
            # Process fit headers
            slide.content = parser.process_fit_headers(slide.content, config)
            
            # Process emoji shortcodes
            slide.content = parser.process_emoji_shortcodes(slide.content)
            
            return slide
            
        except Exception as e:
            raise SlideProcessingError(f"Error processing slide {slide_index}: {str(e)}", slide_index)
    
    def process_columns(self, slide_content: str) -> List[ColumnContent]:
        """Process multi-column layout."""
        try:
            # Split content by column markers
            column_parts = self.column_pattern.split(slide_content)
            
            # Remove empty parts and clean up
            column_parts = [part.strip() for part in column_parts if part.strip()]
            
            if not column_parts:
                return []
            
            columns = []
            num_columns = len(column_parts)
            width_percentage = 100.0 / num_columns if num_columns > 0 else 100.0
            
            for i, content in enumerate(column_parts):
                # Remove column directive from content if it's at the beginning
                content = re.sub(r'^\[\.column\]\s*', '', content, flags=re.MULTILINE)
                
                columns.append(ColumnContent(
                    index=i,
                    content=content.strip(),
                    width_percentage=width_percentage
                ))
            
            return columns
            
        except Exception as e:
            raise SlideProcessingError(f"Error processing columns: {str(e)}")
    
    def process_background_image(self, slide_content: str) -> Optional[ProcessedImage]:
        """Process slide background image."""
        try:
            match = self.background_image_pattern.search(slide_content)
            if not match:
                return None
            
            image_path = match.group(1).strip()
            
            # Create a basic ProcessedImage for background
            # Note: In a full implementation, this would use MediaProcessor
            from enhanced_models import ImageModifiers
            
            modifiers = ImageModifiers(
                placement="background",
                scaling="cover",
                filter="original"
            )
            
            return ProcessedImage(
                src_path=image_path,
                web_path=image_path,  # Will be processed by MediaProcessor
                modifiers=modifiers,
                alt_text="Background image"
            )
            
        except Exception as e:
            raise SlideProcessingError(f"Error processing background image: {str(e)}")
    
    def process_code_blocks(self, slide_content: str) -> str:
        """Process code blocks with highlighting."""
        try:
            # Find code highlight directives
            highlight_configs = {}
            for match in self.code_highlight_pattern.finditer(slide_content):
                directive = match.group(1).strip()
                # Store position and directive for later use
                highlight_configs[match.start()] = directive
            
            # Remove highlight directives from content
            content = self.code_highlight_pattern.sub('', slide_content)
            
            # Process code blocks
            def replace_code_block(match):
                language = match.group(1) or 'text'
                code = match.group(2)
                
                # Find applicable highlight directive
                highlight_directive = None
                for pos, directive in highlight_configs.items():
                    if pos < match.start():
                        highlight_directive = directive
                
                # Create enhanced code block HTML
                css_class = f"code-block language-{language}"
                if highlight_directive:
                    css_class += f" highlight-{highlight_directive.replace(' ', '-')}"
                
                return f'<pre class="{css_class}"><code>{code}</code></pre>'
            
            return self.code_block_pattern.sub(replace_code_block, content)
            
        except Exception as e:
            raise SlideProcessingError(f"Error processing code blocks: {str(e)}")
    
    def process_math_formulas(self, slide_content: str) -> str:
        """Process mathematical formulas."""
        try:
            # Process display math ($$...$$)
            def replace_display_math(match):
                formula = match.group(1).strip()
                return f'<div class="math-display">\\[{formula}\\]</div>'
            
            content = self.display_math_pattern.sub(replace_display_math, slide_content)
            
            # Process inline math ($...$)
            def replace_inline_math(match):
                formula = match.group(1).strip()
                return f'<span class="math-inline">\\({formula}\\)</span>'
            
            content = self.inline_math_pattern.sub(replace_inline_math, content)
            
            return content
            
        except Exception as e:
            raise SlideProcessingError(f"Error processing math formulas: {str(e)}")
    
    def apply_autoscale(self, slide_content: str, config: DecksetConfig) -> str:
        """Apply autoscale to slide content."""
        try:
            # Simple autoscale implementation based on content length
            content_length = len(slide_content)
            
            if content_length > self.content_length_threshold:
                # Add autoscale class to trigger CSS scaling
                return f'<div class="autoscale-content">{slide_content}</div>'
            
            return slide_content
            
        except Exception as e:
            raise SlideProcessingError(f"Error applying autoscale: {str(e)}")
    
    def _parse_highlight_lines(self, directive: str) -> List[int]:
        """Parse line numbers from highlight directive."""
        lines = []
        
        if directive.lower() == 'all':
            return [-1]  # Special value for all lines
        elif directive.lower() == 'none':
            return []
        
        # Parse individual lines and ranges
        parts = directive.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                # Range like "1-5"
                start, end = part.split('-')
                lines.extend(range(int(start), int(end) + 1))
            else:
                # Single line
                lines.append(int(part))
        
        return lines
    
    def _estimate_content_overflow(self, content: str) -> bool:
        """Estimate if content might overflow the slide."""
        # Simple heuristic based on content characteristics
        lines = content.split('\n')
        
        # Check for long lines
        long_lines = sum(1 for line in lines if len(line) > 80)
        
        # Check total line count
        total_lines = len(lines)
        
        # Check for large code blocks
        code_blocks = len(self.code_block_pattern.findall(content))
        
        # Estimate overflow risk
        overflow_score = (
            (long_lines * 2) +
            (total_lines * 0.5) +
            (code_blocks * 10)
        )
        
        return overflow_score > 50  # Threshold for autoscale trigger