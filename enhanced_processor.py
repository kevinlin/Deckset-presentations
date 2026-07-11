"""
Enhanced presentation processor that integrates all Deckset features.

This module provides a comprehensive processor that uses the DecksetParser,
MediaProcessor, and other enhanced components to process presentations with
full Deckset compatibility.
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Any

from models import PresentationInfo, PresentationProcessingError, ProcessedImage, ImageModifiers
from models import (
    ProcessedSlide, EnhancedPresentation, DecksetConfig, SlideConfig,
    SlideContext, DecksetParsingError, MediaProcessingError, SlideProcessingError
)
from deckset_parser import DecksetParser
from markdown_renderer import MarkdownRenderer
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
        self.markdown_renderer = MarkdownRenderer()
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

            # Step 4: Apply global background to slides without their own
            if config.background_image:
                self._apply_global_background(processed_slides, config, presentation_info)

            # Step 5: Cross-slide footnote resolution (single consolidated pass)
            global_footnotes = self._resolve_footnotes(processed_slides)

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

                # Determine per-slide readability filter flag (boolean) based on content:
                # - True if there's an unmodified image used as a background (no placement modifiers)
                #   AND there is other text content on the slide
                # - False in all other cases (e.g., left/right/inline/fit modifiers or image-only slides)
                has_bg = bool(processed_slide.background_images)
                visible_text = bool((processed_slide.content or '').strip())

                unmodified_background = False
                if has_bg:
                    try:
                        mods = processed_slide.background_images[0].modifiers
                        # Unmodified means default placement 'background' and no explicit left/right/inline
                        # and no explicit scaling like 'fit' or percentage
                        is_background = mods.placement == 'background'
                        has_explicit_scaling = (mods.scaling in ['fit'] or str(mods.scaling).endswith('%'))
                        unmodified_background = is_background and not has_explicit_scaling
                    except Exception:
                        unmodified_background = True

                processed_slide.slide_config.readability_filter_mode = bool(unmodified_background and visible_text)

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
            default_lang = context.config.code_language or ""
            original_content_cleaned, code_blocks = (
                self.code_processor.process_code_block_with_deckset_directive(
                    original_content,
                    default_language=default_lang,
                )
            )
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

            slide = self._detect_inline_figures(slide, original_content, context)

            # Render slide content to HTML (single pass via MarkdownRenderer).
            # Protect MathJax delimiters from being mangled by markdown.
            render_text, math_map = self._protect_math(slide.content)
            slide_id = f"slide-{slide.index}"
            rendered = self.markdown_renderer.render(render_text, slide_id)
            slide.body_html = self._restore_math(rendered, math_map)

            return slide

        except Exception as e:
            logger.warning(f"Failed to enhance slide {slide.index}: {e}")
            return slide

    def _process_slide_media(
        self, 
        slide: ProcessedSlide, 
        original_content: str, 
        context: SlideContext
    ) -> ProcessedSlide:
        """Process media elements (images, videos, audio) in the slide."""
        try:
            # Extract media references from original content (with inline-in-text detection)
            media_references = self._extract_media_references(original_content)
            processed_media_refs = []

            # Process each media reference
            for media in media_references:
                media_ref = media['ref']
                try:
                    if self._is_image_reference(media_ref):
                        processed_image = self.media_processor.process_image(media_ref, context)

                        # If this is an inline-in-text image, replace in content in place and do not add to side collections
                        if media.get('inline_in_text', False) and processed_image.modifiers.placement == 'inline':
                            # Replace markdown token with inline <img> tag preserving flow
                            replacement = (
                                f'<img class="inline-image inline-text" '
                                f'src="{processed_image.web_path}" '
                                f'alt="{processed_image.alt_text}" loading="lazy">'
                            )
                            slide.content = self._replace_one(slide.content, media_ref, replacement)
                        else:
                            # Categorize image based on modifiers
                            if processed_image.modifiers.placement == "background":
                                slide.background_image = processed_image
                                slide.background_images.append(processed_image)
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

    def _replace_one(self, text: str, target: str, replacement: str) -> str:
        """Replace a single occurrence of target string in text with replacement.
        Uses split once to avoid regex pitfalls.
        """
        try:
            parts = text.split(target, 1)
            if len(parts) == 2:
                return parts[0] + replacement + parts[1]
            return text
        except Exception:
            return text

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

    def _detect_inline_figures(
        self,
        slide: ProcessedSlide,
        original_content: str,
        context: SlideContext,
    ) -> ProcessedSlide:
        """Identify inline image lines that are immediately followed by a caption line.

        Supported pattern (no blank line between image and text):
            ![inline](image.jpg)
            Caption text here
        or
            ![](image.jpg)
            Caption text here
        """
        try:
            lines = original_content.split('\n')
            import re
            img_re = re.compile(r'^\s*!\[[^\]]*\]\([^\)]+\)\s*$')

            # Quick lookup from filename to processed images
            images_by_name = {}
            for img in slide.inline_images:
                images_by_name.setdefault(img.web_path.split('/')[-1], []).append(img)
            for bg in slide.background_images:
                images_by_name.setdefault(bg.web_path.split('/')[-1], []).append(bg)

            i = 0
            while i < len(lines) - 1:
                line = lines[i]
                next_line = lines[i + 1]
                if img_re.match(line) and next_line.strip() and not img_re.match(next_line):
                    m = re.search(r'\(([^\)]+)\)', line)
                    img_path = m.group(1).strip() if m else None
                    if img_path:
                        key = img_path.split('/')[-1]
                        candidates = images_by_name.get(key, [])
                        chosen = None
                        for cand in candidates:
                            try:
                                if cand.modifiers.placement == 'inline':
                                    chosen = cand
                                    break
                            except Exception:
                                pass
                        if not chosen and candidates:
                            chosen = candidates[0]
                        if chosen:
                            from models import InlineFigure
                            slide.inline_figures.append(InlineFigure(image=chosen, caption=next_line.strip()))
                            if chosen in slide.inline_images:
                                slide.inline_images.remove(chosen)
                            # Remove the raw lines from HTML/markdown content best-effort
                            slide.content = re.sub(re.escape(line), '', slide.content)
                            slide.content = re.sub(re.escape(next_line), '', slide.content)
                            i += 2
                            continue
                i += 1

            # Normalize extra blank lines
            slide.content = re.sub(r'\n\s*\n\s*\n+', '\n\n', slide.content)
            return slide
        except Exception:
            return slide

    def _extract_media_references(self, content: str) -> List[Dict[str, Any]]:
        """Extract all media references from slide content with inline-in-text context.

        Returns a list of dicts: { 'ref': full_markdown, 'inline_in_text': bool }
        """
        import re

        # Pattern to match ![...](...) with support for spaces/Unicode in paths and adjacent tokens
        media_pattern = re.compile(r'!\[[^\]]*\]\([^\)]+?\)')
        results: List[Dict[str, Any]] = []
        for m in media_pattern.finditer(content):
            ref = m.group(0)
            # Determine if inline inside a non-empty line (not alone on its line)
            line_start = content.rfind('\n', 0, m.start()) + 1
            line_end = content.find('\n', m.end())
            if line_end == -1:
                line_end = len(content)
            line_text = content[line_start:line_end]
            stripped = line_text.strip()
            inline_in_text = not (stripped == ref)
            results.append({'ref': ref, 'inline_in_text': inline_in_text})

        return results

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

    def _apply_global_background(
        self,
        slides: List[ProcessedSlide],
        config: DecksetConfig,
        presentation_info: PresentationInfo,
    ) -> None:
        """Apply ``DecksetConfig.background_image`` to slides lacking their own."""
        for slide in slides:
            if not slide.background_images:
                mods = ImageModifiers(placement="background", scaling="cover", filter="original")
                global_bg = ProcessedImage(
                    src_path=config.background_image,
                    web_path=config.background_image,
                    modifiers=mods,
                    alt_text="",
                )
                slide.background_image = global_bg
                slide.background_images.append(global_bg)

    _MATH_DELIM_RE = re.compile(r'(\\\([^)]+?\\\)|\\\[[\s\S]+?\\\])')

    @staticmethod
    def _protect_math(text: str) -> tuple[str, dict[str, str]]:
        """Replace MathJax delimiters with unique placeholders."""
        mapping: dict[str, str] = {}
        counter = 0

        def _repl(m: re.Match) -> str:
            nonlocal counter
            token = f"\x00MATH{counter}\x00"
            mapping[token] = m.group(0)
            counter += 1
            return token

        protected = EnhancedPresentationProcessor._MATH_DELIM_RE.sub(_repl, text)
        return protected, mapping

    @staticmethod
    def _restore_math(html: str, mapping: dict[str, str]) -> str:
        """Restore MathJax delimiters from placeholders."""
        for token, original in mapping.items():
            html = html.replace(token, original)
        return html

    _FOOTNOTE_REF_RE = re.compile(r'\[\^([^\]]+)\](?!:)')

    def _resolve_footnotes(self, slides: List[ProcessedSlide]) -> Dict[str, str]:
        """Consolidate footnotes across all slides.

        1. Collect every definition from every slide into a single pool.
           Duplicates are logged as warnings and first-definition-wins.
        2. For each slide, find which footnote IDs are *referenced* in its
           content and assign only those definitions.
        3. Namespace footnote keys per slide (``fn-slideN-ID``).
        4. Transform ``[^ID]`` references in content to superscript anchor links.

        Returns the global definition pool (unnamespaced) for ``EnhancedPresentation.global_footnotes``.
        """
        global_pool: Dict[str, str] = {}

        for slide in slides:
            for fn_id, fn_text in slide.footnotes.items():
                if fn_id in global_pool:
                    logger.warning(
                        "Duplicate footnote [^%s] on slide %d; keeping first definition",
                        fn_id,
                        slide.index,
                    )
                else:
                    global_pool[fn_id] = fn_text

        for slide in slides:
            refs = set(self._FOOTNOTE_REF_RE.findall(slide.content))
            resolved: Dict[str, str] = {}
            for ref_id in refs:
                if ref_id in global_pool:
                    ns_key = f"fn-slide{slide.index}-{ref_id}"
                    resolved[ns_key] = global_pool[ref_id]
                else:
                    logger.warning(
                        "Footnote [^%s] on slide %d has no definition", ref_id, slide.index
                    )

            def _ref_to_sup(m: re.Match) -> str:
                fid = m.group(1)
                ns = f"fn-slide{slide.index}-{fid}"
                return f'<sup><a href="#{ns}">{fid}</a></sup>'

            slide.content = self._FOOTNOTE_REF_RE.sub(_ref_to_sup, slide.content)
            slide.footnotes = resolved

        return global_pool
