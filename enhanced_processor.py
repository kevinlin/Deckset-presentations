"""
Enhanced presentation processor that integrates all Deckset features.

This module provides a comprehensive processor that uses the DecksetParser,
MediaProcessor, and other enhanced components to process presentations with
full Deckset compatibility.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any

from models import PresentationInfo, PresentationProcessingError
from models import (
    ProcessedSlide, EnhancedPresentation, DecksetConfig, SlideConfig,
    SlideContext, DecksetParsingError, MediaProcessingError, SlideProcessingError
)
from deckset_parser import DecksetParser
from media_processor import MediaProcessor
from slide_processor import SlideProcessor
from code_processor import CodeProcessor
from math_processor import MathProcessor

logger = logging.getLogger(__name__)


class EnhancedPresentationProcessor:
    """Enhanced processor for Deckset presentations with full feature support."""
    
    def __init__(self):
        """Initialize the enhanced presentation processor."""
        self.deckset_parser = DecksetParser()
        self.media_processor = MediaProcessor()
        self.slide_processor = SlideProcessor()
        self.code_processor = CodeProcessor()
        self.math_processor = MathProcessor()
    
    def process_presentation(self, presentation_info: PresentationInfo) -> EnhancedPresentation:
        """
        Process a presentation with full Deckset feature support.
        
        Args:
            presentation_info: Information about the presentation to process
            
        Returns:
            EnhancedPresentation with processed slides and configuration
            
        Raises:
            PresentationProcessingError: If processing fails
        """
        logger.info(f"Enhanced processor: Starting to process presentation {presentation_info.title}")
        
        # Read the markdown file
        try:
            with open(presentation_info.markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (FileNotFoundError, IOError, UnicodeDecodeError) as e:
            raise PresentationProcessingError(
                f"Failed to read markdown file {presentation_info.markdown_path}: {e}",
                context={
                    "presentation_title": presentation_info.title,
                    "markdown_path": presentation_info.markdown_path,
                    "processing_stage": "file_reading"
                }
            )
        
        try:
            # Step 1: Parse global Deckset configuration
            config = self._parse_global_config(content)
            logger.debug(f"Parsed global config: slide_numbers={config.slide_numbers}, autoscale={config.autoscale}")
            
            # Step 2: Extract slides using enhanced parsing
            slide_contents = self._extract_slides(content, config)
            logger.debug(f"Extracted {len(slide_contents)} slides")
            
            # Step 3: Process each slide with full feature support
            processed_slides = self._process_slides(slide_contents, config, presentation_info)
            logger.debug(f"Processed {len(processed_slides)} slides with enhanced features")
            
            # Step 4: Extract global footnotes
            global_footnotes = self._extract_global_footnotes(content)
            
            # Update presentation info with slide count
            presentation_info.slide_count = len(processed_slides)
            
            return EnhancedPresentation(
                info=presentation_info,
                slides=processed_slides,
                config=config,
                global_footnotes=global_footnotes
            )
            
        except (DecksetParsingError, MediaProcessingError, SlideProcessingError) as e:
            raise PresentationProcessingError(
                f"Failed to process enhanced presentation {presentation_info.title}: {e}",
                context={
                    "presentation_title": presentation_info.title,
                    "markdown_path": presentation_info.markdown_path,
                    "processing_stage": "enhanced_processing",
                    "error_type": type(e).__name__
                }
            )
        except Exception as e:
            raise PresentationProcessingError(
                f"Unexpected error processing enhanced presentation {presentation_info.title}: {e}",
                context={
                    "presentation_title": presentation_info.title,
                    "markdown_path": presentation_info.markdown_path,
                    "processing_stage": "enhanced_processing",
                    "error_type": type(e).__name__
                }
            )
    
    def _parse_global_config(self, content: str) -> DecksetConfig:
        """Parse global Deckset configuration from markdown content."""
        try:
            config = self.deckset_parser.parse_global_commands(content)
            logger.debug(f"Parsed global commands: {vars(config)}")
            return config
        except DecksetParsingError as e:
            logger.warning(f"Failed to parse global config: {e}")
            # Return default config on parsing failure
            return DecksetConfig()
    
    def _extract_slides(self, content: str, config: DecksetConfig) -> List[str]:
        """Extract slides using enhanced parsing with auto-breaks support."""
        try:
            # First try auto-break detection if configured
            if config.slide_dividers:
                slide_contents = self.deckset_parser.detect_auto_slide_breaks(content, config)
            else:
                # Use standard slide separator extraction
                slide_contents = self.deckset_parser.extract_slide_separators(content)
            
            logger.debug(f"Extracted {len(slide_contents)} slides")
            return slide_contents
            
        except DecksetParsingError as e:
            logger.error(f"Failed to extract slides: {e}")
            # Fallback to treating entire content as one slide
            return [content]
    
    def _process_slides(
        self, 
        slide_contents: List[str], 
        config: DecksetConfig, 
        presentation_info: PresentationInfo
    ) -> List[ProcessedSlide]:
        """Process each slide with full Deckset feature support."""
        processed_slides = []
        
        for i, slide_content in enumerate(slide_contents):
            try:
                slide_index = i + 1
                
                # Create slide context
                slide_context = SlideContext(
                    slide_index=slide_index,
                    total_slides=len(slide_contents),
                    presentation_path=str(Path(presentation_info.folder_path)),
                    config=config,
                    slide_config=SlideConfig()  # Will be updated during processing
                )
                
                # Process the slide using the slide processor
                processed_slide = self.slide_processor.process_slide(
                    slide_content, slide_index, config
                )
                
                # Additional processing for media, code, and math
                processed_slide = self._enhance_slide_processing(
                    processed_slide, slide_content, slide_context
                )
                
                processed_slides.append(processed_slide)
                
            except Exception as e:
                logger.error(f"Failed to process slide {i + 1}: {e}")
                # Create a minimal fallback slide
                fallback_slide = ProcessedSlide(
                    index=i + 1,
                    content=slide_content,
                    notes="",
                    slide_config=SlideConfig()
                )
                processed_slides.append(fallback_slide)
        
        return processed_slides
    
    def _enhance_slide_processing(
        self, 
        slide: ProcessedSlide, 
        original_content: str, 
        context: SlideContext
    ) -> ProcessedSlide:
        """Apply additional enhanced processing to a slide."""
        try:
            # Process code blocks from original content first, before SlideProcessor transforms them
            original_content_cleaned, code_blocks = self._process_slide_code_blocks(original_content, original_content)
            slide.code_blocks = code_blocks
            
            # Process emoji shortcodes in content
            slide.content = self.deckset_parser.process_emoji_shortcodes(slide.content)
            
            # Process fit headers
            slide.content = self.deckset_parser.process_fit_headers(slide.content, context.config)
            
            # Process footnotes for this slide
            slide.content, slide.footnotes = self.deckset_parser.process_footnotes(slide.content)
            
            # Process mathematical formulas
            slide.content, math_formulas = self.math_processor.process_math_formulas(slide.content)
            slide.math_formulas = math_formulas
            
            # Process media elements (use original content to find media references)
            slide = self._process_slide_media(slide, original_content, context)
            
            return slide
            
        except Exception as e:
            logger.warning(f"Failed to enhance slide {slide.index}: {e}")
            return slide
    
    def _process_slide_code_blocks(self, content: str, original_content: str) -> tuple:
        """Process code blocks with syntax highlighting and line emphasis."""
        try:
            # Process code blocks using the processed content, not the original
            # The original_content is only used if we need to extract code block directives
            # that might have been removed during earlier processing
            cleaned_content, code_blocks = self.code_processor.process_code_block_with_deckset_directive(
                content,  # Use the processed content, not original_content
                default_language=""
            )
            
            return cleaned_content, code_blocks
            
        except Exception as e:
            logger.warning(f"Failed to process code blocks: {e}")
            return content, []
    
    def _process_slide_media(
        self, 
        slide: ProcessedSlide, 
        original_content: str, 
        context: SlideContext
    ) -> ProcessedSlide:
        """Process media elements (images, videos, audio) in the slide."""
        try:
            # Extract media references from original content
            media_references = self._extract_media_references(original_content)
            processed_media_refs = []
            
            # Process each media reference
            for media_ref in media_references:
                try:
                    if self._is_image_reference(media_ref):
                        processed_image = self.media_processor.process_image(media_ref, context)
                        
                        # Categorize image based on modifiers
                        if processed_image.modifiers.placement == "background":
                            slide.background_image = processed_image
                        else:
                            slide.inline_images.append(processed_image)
                        
                        processed_media_refs.append(media_ref)
                            
                    elif self._is_video_reference(media_ref):
                        processed_video = self.media_processor.process_video(media_ref, context)
                        slide.videos.append(processed_video)
                        processed_media_refs.append(media_ref)
                        
                    elif self._is_audio_reference(media_ref):
                        processed_audio = self.media_processor.process_audio(media_ref, context)
                        slide.audio.append(processed_audio)
                        processed_media_refs.append(media_ref)
                        
                except MediaProcessingError as e:
                    logger.warning(f"Failed to process media reference '{media_ref}': {e}")
                    continue
            
            # Remove processed media references from slide content
            for media_ref in processed_media_refs:
                # Remove the media reference and any surrounding paragraph tags
                slide.content = self._remove_media_reference_from_content(slide.content, media_ref)
            
            return slide
            
        except Exception as e:
            logger.warning(f"Failed to process slide media: {e}")
            return slide
    
    def _remove_media_reference_from_content(self, content: str, media_ref: str) -> str:
        """Remove a processed media reference from slide content."""
        import re
        
        # Escape special regex characters in the media reference
        escaped_ref = re.escape(media_ref)
        
        # Pattern to match the media reference with optional surrounding whitespace and paragraph tags
        patterns = [
            # Media reference on its own line (most common for background images)
            rf'^\s*{escaped_ref}\s*$',
            # Media reference in a paragraph
            rf'<p>\s*{escaped_ref}\s*</p>',
            # Media reference with surrounding whitespace
            rf'\s*{escaped_ref}\s*',
            # Just the media reference itself
            escaped_ref
        ]
        
        # Try each pattern and remove the first match
        for pattern in patterns:
            if re.search(pattern, content, re.MULTILINE):
                content = re.sub(pattern, '', content, count=1, flags=re.MULTILINE)
                break
        
        # Clean up any empty lines or paragraphs left behind
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)  # Remove multiple blank lines
        content = re.sub(r'<p>\s*</p>', '', content)  # Remove empty paragraphs
        
        return content.strip()
    
    def _extract_media_references(self, content: str) -> List[str]:
        """Extract all media references from slide content."""
        import re
        
        # Pattern to match ![...](...)
        media_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
        matches = media_pattern.findall(content)
        
        # Reconstruct full media references
        media_references = []
        for alt_text, path in matches:
            media_references.append(f"![{alt_text}]({path})")
        
        return media_references
    
    def _is_image_reference(self, media_ref: str) -> bool:
        """Check if media reference is an image."""
        import re
        
        # Extract path from media reference
        path_match = re.search(r'\(([^)]+)\)', media_ref)
        if not path_match:
            return False
        
        path = path_match.group(1)
        
        # Check for image extensions
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'}
        path_lower = path.lower()
        
        return any(path_lower.endswith(ext) for ext in image_extensions)
    
    def _is_video_reference(self, media_ref: str) -> bool:
        """Check if media reference is a video."""
        import re
        
        # Extract path from media reference
        path_match = re.search(r'\(([^)]+)\)', media_ref)
        if not path_match:
            return False
        
        path = path_match.group(1)
        
        # Check for video extensions or YouTube URLs
        video_extensions = {'.mp4', '.mov', '.avi', '.webm', '.mkv', '.m4v'}
        path_lower = path.lower()
        
        is_video_file = any(path_lower.endswith(ext) for ext in video_extensions)
        is_youtube = 'youtube.com' in path_lower or 'youtu.be' in path_lower
        
        return is_video_file or is_youtube
    
    def _is_audio_reference(self, media_ref: str) -> bool:
        """Check if media reference is audio."""
        import re
        
        # Extract path from media reference
        path_match = re.search(r'\(([^)]+)\)', media_ref)
        if not path_match:
            return False
        
        path = path_match.group(1)
        
        # Check for audio extensions
        audio_extensions = {'.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac'}
        path_lower = path.lower()
        
        return any(path_lower.endswith(ext) for ext in audio_extensions)
    
    def _extract_global_footnotes(self, content: str) -> Dict[str, str]:
        """Extract global footnotes that apply to the entire presentation."""
        try:
            _, footnotes = self.deckset_parser.process_footnotes(content)
            return footnotes
        except Exception as e:
            logger.warning(f"Failed to extract global footnotes: {e}")
            return {}