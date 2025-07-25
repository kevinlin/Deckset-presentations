"""
Enhanced template engine for rendering Deckset presentations with full feature support.

This module provides comprehensive template rendering capabilities for all Deckset features
including multi-column layouts, background images, media embedding, code highlighting,
mathematical formulas, and responsive design.
"""

import os
import re
from typing import List, Dict, Optional
from jinja2 import Environment, FileSystemLoader, Template
from models import (
    ProcessedSlide, ColumnContent, ProcessedImage, ProcessedVideo, ProcessedAudio,
    ProcessedCodeBlock, MathFormula, DecksetConfig, SlideConfig, ImageGrid
)


class EnhancedTemplateEngine:
    """Enhanced template engine with full Deckset feature support."""

    def __init__(self, template_dir: str = "templates"):
        """Initialize the enhanced template engine."""
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False  # We handle HTML escaping manually
        )

        # Load base templates first
        self._load_templates()

        # Register custom filters and functions
        self._register_template_functions()

    def _register_template_functions(self):
        """Register custom Jinja2 functions and filters."""
        self.env.globals.update({
            'render_columns': self.render_columns,
            'render_background_image': self.render_background_image,
            'render_inline_images': self.render_inline_images,
            'render_image_grid': self.render_image_grid,
            'render_video_player': self.render_video_player,
            'render_audio_player': self.render_audio_player,
            'render_code_block': self.render_code_block,
            'render_math_formula': self.render_math_formula,
            'render_footnotes': self.render_footnotes,
            'render_slide_footer': self.render_slide_footer,
            'render_slide_number': self.render_slide_number,
        })

        # Custom filters
        self.env.filters['markdown_to_html'] = self._markdown_to_html
        self.env.filters['escape_html'] = self._escape_html

    def _load_templates(self):
        """Load templates from files."""
        # Templates are now loaded automatically by Jinja2 FileSystemLoader
        # No need to preload them as strings anymore
        pass

    def render_slide(self, slide: ProcessedSlide, config: DecksetConfig, total_slides: int = 1) -> str:
        """Render a complete slide with full Deckset feature support."""
        template = self.env.get_template('slide.html')
        return template.render(
            slide=slide,
            config=config,
            total_slides=total_slides
        )

    def render_columns(self, columns: List[ColumnContent]) -> str:
        """Render multi-column layout."""
        if not columns:
            return ""

        html_parts = []

        for column in columns:
            width_style = f"width: {column.width_percentage:.1f}%;"
            html_parts.append(f"""
                <div class="column" style="{width_style}">
                    {self._markdown_to_html(column.content)}
                </div>
            """)

        return f'<div class="columns-container">{"".join(html_parts)}</div>'

    def render_background_image(self, image: ProcessedImage) -> str:
        """Render background image with proper positioning and filters."""
        if not image:
            return ""

        css_classes = ["background-image"]
        styles = []

        # Add the background image URL first
        styles.append(f"background-image: url('{image.web_path}')")

        # Add placement classes
        if image.modifiers.placement in ["left", "right"]:
            css_classes.append(image.modifiers.placement)

        # Add filter classes
        if image.modifiers.filter == "filtered":
            css_classes.append("filtered")

        # Add scaling styles
        if image.modifiers.scaling == "fit":
            styles.append("background-size: contain")
        elif image.modifiers.scaling == "cover":
            styles.append("background-size: cover")
        elif image.modifiers.scaling.endswith("%"):
            percentage = image.modifiers.scaling
            styles.append(f"background-size: {percentage}")

        # Add corner radius if specified
        if image.modifiers.corner_radius:
            styles.append(f"border-radius: {image.modifiers.corner_radius}px")

        # Combine all styles into a single style attribute
        style_attr = f'style="{"; ".join(styles)}"'
        class_attr = f'class="{" ".join(css_classes)}"'

        return f"""
            <div {class_attr} {style_attr}
                 aria-label="{self._escape_html(image.alt_text)}">
            </div>
        """

    def render_inline_images(self, images: List[ProcessedImage]) -> str:
        """Render inline images with proper layout."""
        if not images:
            return ""

        # Check if images should be in a grid
        inline_images = [img for img in images if img.modifiers.placement == "inline"]

        if len(inline_images) > 1:
            # Create image grid for multiple consecutive inline images
            from media_processor import MediaProcessor
            processor = MediaProcessor()
            grid = processor.create_image_grid(inline_images)
            return self.render_image_grid(grid)

        # Render single inline images
        html_parts = []
        for image in images:
            html_parts.append(self._render_single_inline_image(image))

        return "".join(html_parts)

    def render_image_grid(self, grid: ImageGrid) -> str:
        """Render image grid layout."""
        if not grid or not grid.images:
            return ""

        css_classes = ["image-grid"]

        # Add column class based on grid columns
        if grid.columns == 2:
            css_classes.append("two-columns")
        elif grid.columns == 3:
            css_classes.append("three-columns")
        elif grid.columns > 3:
            css_classes.append("multi-columns")

        grid_style = f"grid-template-columns: repeat({grid.columns}, 1fr); gap: {grid.gap};"

        html_parts = [f'<div class="{" ".join(css_classes)}" style="{grid_style}">']

        for image in grid.images:
            html_parts.append(self._render_grid_image(image))

        html_parts.append("</div>")

        return "".join(html_parts)

    def _render_single_inline_image(self, image: ProcessedImage) -> str:
        """Render a single inline image."""
        css_classes = ["inline-image"]
        styles = []

        # Add scaling classes and styles
        if image.modifiers.scaling == "fill":
            css_classes.append("fill")
        elif image.modifiers.scaling.endswith("%"):
            percentage = image.modifiers.scaling
            styles.append(f"width: {percentage}")

        # Add corner radius if specified
        if image.modifiers.corner_radius:
            styles.append(f"border-radius: {image.modifiers.corner_radius}px")

        style_attr = f'style="{"; ".join(styles)}"' if styles else ""
        class_attr = f'class="{" ".join(css_classes)}"'

        return f"""
            <img {class_attr} {style_attr}
                 src="{image.web_path}"
                 alt="{self._escape_html(image.alt_text)}"
                 loading="lazy">
        """

    def _render_grid_image(self, image: ProcessedImage) -> str:
        """Render an image within a grid layout."""
        styles = []

        # Add corner radius if specified
        if image.modifiers.corner_radius:
            styles.append(f"border-radius: {image.modifiers.corner_radius}px")

        style_attr = f'style="{"; ".join(styles)}"' if styles else ""

        return f"""
            <div class="grid-image-container">
                <img class="grid-image" {style_attr}
                     src="{image.web_path}"
                     alt="{self._escape_html(image.alt_text)}"
                     loading="lazy">
            </div>
        """

    def _markdown_to_html(self, content: str) -> str:
        """Convert markdown content to HTML with support for headers, lists, emphasis, and inline code."""
        if not content:
            return ""

        # Start with the original content
        html = content

        # Convert headers first (before line-by-line processing)
        # Handle fit headers with {.fit} markers
        html = re.sub(r'^# (.+?) \{\.fit\}$', r'<h1 class="fit">\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+?) \{\.fit\}$', r'<h2 class="fit">\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+?) \{\.fit\}$', r'<h3 class="fit">\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^#### (.+?) \{\.fit\}$', r'<h4 class="fit">\1</h4>', html, flags=re.MULTILINE)

        # Convert regular headers (without fit)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)

        # Convert emphasis
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        html = re.sub(r'_(.+?)_', r'<em>\1</em>', html)
        html = re.sub(r'__(.+?)__', r'<strong>\1</strong>', html)

        # Convert inline code
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)

        # Process lines to handle lists and paragraphs
        lines = html.split('\n')
        result_lines = []
        current_paragraph = []
        current_list = None  # Track current list state: None, 'ul', or 'ol'
        current_list_items = []

        def _finish_current_list():
            """Helper to close the current list and add it to results."""
            nonlocal current_list, current_list_items
            if current_list and current_list_items:
                list_html = f'<{current_list}>\n'
                for item in current_list_items:
                    list_html += f'    <li>{item}</li>\n'
                list_html += f'</{current_list}>'
                result_lines.append(list_html)
                current_list = None
                current_list_items = []

        def _finish_current_paragraph():
            """Helper to close the current paragraph and add it to results."""
            nonlocal current_paragraph
            if current_paragraph:
                result_lines.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []

        for line in lines:
            line = line.strip()
            
            if not line:
                # Empty line - finish current list or paragraph
                _finish_current_list()
                _finish_current_paragraph()
                
            elif line.startswith('<h') or line.startswith('<pre>'):
                # Block element - finish current items and add block element
                _finish_current_list()
                _finish_current_paragraph()
                result_lines.append(line)
                
            elif line.startswith('- ') or line == '-':
                # Unordered list item (including empty ones like just "-")
                _finish_current_paragraph()  # Finish paragraph if we were in one
                
                # Extract list item content
                if line == '-':
                    item_content = ''
                else:
                    item_content = line[2:].strip()
                
                if current_list != 'ul':
                    # Starting a new unordered list or switching from ordered list
                    _finish_current_list()
                    current_list = 'ul'
                    current_list_items = []
                
                current_list_items.append(item_content)
                
            elif re.match(r'^\d+\.\s*$', line) or re.match(r'^\d+\.\s+', line):
                # Ordered list item (starts with number followed by period and optional space/content)
                _finish_current_paragraph()  # Finish paragraph if we were in one
                
                # Extract list item content (everything after "number. ")
                if re.match(r'^\d+\.\s*$', line):
                    # Empty list item like "1." or "1. "
                    item_content = ''
                else:
                    item_content = re.sub(r'^\d+\.\s+', '', line)
                
                if current_list != 'ol':
                    # Starting a new ordered list or switching from unordered list
                    _finish_current_list()
                    current_list = 'ol'
                    current_list_items = []
                
                current_list_items.append(item_content)
                
            else:
                # Regular text line
                _finish_current_list()  # Finish list if we were in one
                current_paragraph.append(line)

        # Handle any remaining items at the end
        _finish_current_list()
        _finish_current_paragraph()

        # Join all lines
        html = '\n'.join(result_lines)

        # Clean up empty paragraphs
        html = re.sub(r'<p></p>', '', html)
        html = re.sub(r'<p>\s*</p>', '', html)

        return html

    def _escape_html(self, text: str) -> str:
        """Escape HTML characters in text."""
        if not text:
            return ""

        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))

    # Placeholder methods for subtasks 7.2 and 7.3 - will be implemented in those tasks
    def render_video_player(self, video: ProcessedVideo) -> str:
        """Render video player with HTML5 video element or iframe for external videos."""
        if not video:
            return ""

        css_classes = ["video-player"]
        attributes = []

        # Add placement classes
        if video.modifiers.placement in ["left", "right"]:
            css_classes.append(video.modifiers.placement)

        # Add scaling styles
        styles = []
        if video.modifiers.scaling.endswith("%"):
            styles.append(f"width: {video.modifiers.scaling}")
        elif video.modifiers.scaling == "fill":
            styles.append("width: 100%")

        # Add playback attributes
        if video.modifiers.autoplay:
            attributes.append('autoplay')
            attributes.append('data-autoplay="true"')
        if video.modifiers.loop:
            attributes.append('loop')
        if video.modifiers.mute:
            attributes.append('muted')
        if video.modifiers.hide:
            styles.append("display: none")

        # Add controls by default unless hidden
        if not video.modifiers.hide:
            attributes.append('controls')

        style_attr = f'style="{"; ".join(styles)}"' if styles else ""
        class_attr = f'class="{" ".join(css_classes)}"'
        attrs_str = " ".join(attributes)

        if video.embed_type == "youtube":
            # YouTube iframe embed
            iframe_attrs = []
            if video.modifiers.autoplay:
                iframe_attrs.append("autoplay=1")
            if video.modifiers.loop:
                iframe_attrs.append("loop=1")
            if video.modifiers.mute:
                iframe_attrs.append("mute=1")

            query_params = "&".join(iframe_attrs)
            embed_url = f"{video.embed_url}?{query_params}" if query_params else video.embed_url

            return f"""
                <div {class_attr} {style_attr}>
                    <iframe src="{embed_url}"
                            frameborder="0"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowfullscreen>
                    </iframe>
                </div>
            """
        else:
            # Local HTML5 video
            return f"""
                <video {class_attr} {style_attr} {attrs_str}>
                    <source src="{video.web_path}" type="video/mp4">
                    <p>Your browser doesn't support HTML5 video. 
                       <a href="{video.web_path}">Download the video</a> instead.</p>
                </video>
            """

    def render_audio_player(self, audio: ProcessedAudio) -> str:
        """Render audio player with HTML5 audio element."""
        if not audio:
            return ""

        css_classes = ["audio-player"]
        attributes = []

        # Add placement classes
        if audio.modifiers.placement in ["left", "right"]:
            css_classes.append(audio.modifiers.placement)

        # Add scaling styles
        styles = []
        if audio.modifiers.scaling.endswith("%"):
            styles.append(f"width: {audio.modifiers.scaling}")
        elif audio.modifiers.scaling == "fill":
            styles.append("width: 100%")

        # Add playback attributes
        if audio.modifiers.autoplay:
            attributes.append('autoplay')
        if audio.modifiers.loop:
            attributes.append('loop')
        if audio.modifiers.mute:
            attributes.append('muted')
        if audio.modifiers.hide:
            styles.append("display: none")

        # Add controls by default unless hidden
        if not audio.modifiers.hide:
            attributes.append('controls')

        style_attr = f'style="{"; ".join(styles)}"' if styles else ""
        class_attr = f'class="{" ".join(css_classes)}"'
        attrs_str = " ".join(attributes)

        return f"""
            <audio {class_attr} {style_attr} {attrs_str}>
                <source src="{audio.web_path}" type="audio/mpeg">
                <source src="{audio.web_path}" type="audio/ogg">
                <p>Your browser doesn't support HTML5 audio. 
                   <a href="{audio.web_path}">Download the audio</a> instead.</p>
            </audio>
        """

    def render_code_block(self, code_block: ProcessedCodeBlock) -> str:
        """Render code block with syntax highlighting and line emphasis."""
        if not code_block:
            return ""

        # Check if content is already processed HTML (contains <pre> tags)
        if '<pre' in code_block.content and '</pre>' in code_block.content:
            # Content is already processed, just wrap it
            return f"""
            <div class="code-container">
                {code_block.content}
            </div>
        """

        # Content is raw code, need to process it
        from code_processor import CodeProcessor
        processor = CodeProcessor()

        # Determine highlight configuration
        if code_block.highlighted_lines:
            highlight_config = ",".join(str(line) for line in sorted(code_block.highlighted_lines))
        else:
            highlight_config = ""

        # Process the code block
        processed = processor.process_code_block(
            code_block.content, 
            code_block.language, 
            highlight_config
        )

        return f"""
            <div class="code-container">
                {processed.content}
            </div>
        """

    def render_math_formula(self, formula: MathFormula) -> str:
        """Render mathematical formula with MathJax integration."""
        if not formula:
            return ""

        # Escape the formula content for safe HTML rendering
        escaped_content = self._escape_html(formula.content)

        if formula.formula_type == "display":
            # Display math (block-level, centered)
            return f"""
                <div class="math-display" data-formula-type="display">
                    \\[{escaped_content}\\]
                </div>
            """
        elif formula.formula_type == "inline":
            # Inline math (within text flow)
            return f"""
                <span class="math-inline" data-formula-type="inline">
                    \\({escaped_content}\\)
                </span>
            """
        else:
            # Fallback for unknown formula types
            return f"""
                <span class="math-unknown" data-formula-type="{formula.formula_type}">
                    {escaped_content}
                </span>
            """

    def render_footnotes(self, footnotes: Dict[str, str]) -> str:
        """Render slide footnotes with proper formatting."""
        if not footnotes:
            return ""

        footnote_items = []

        # Sort footnotes by key for consistent ordering
        sorted_footnotes = sorted(footnotes.items())

        for key, content in sorted_footnotes:
            # Convert markdown content to HTML
            html_content = self._markdown_to_html(content)

            footnote_items.append(f"""
                <div class="footnote-item" id="footnote-{key}">
                    <span class="footnote-marker">{key}</span>
                    <span class="footnote-content">{html_content}</span>
                </div>
            """)

        return f"""
            <div class="footnotes">
                <div class="footnotes-separator"></div>
                <div class="footnotes-list">
                    {"".join(footnote_items)}
                </div>
            </div>
        """

    def render_slide_footer(self, config: DecksetConfig, slide_config: SlideConfig) -> str:
        """Render slide footer with proper formatting and markdown support."""
        if not config.footer or slide_config.hide_footer:
            return ""

        # Convert markdown footer content to HTML
        footer_html = self._markdown_to_html(config.footer)

        return f"""
            <div class="footer-content">
                {footer_html}
            </div>
        """

    def render_slide_number(self, slide_index: int, total_slides: int, config: DecksetConfig) -> str:
        """Render slide number with optional slide count."""
        if not config.slide_numbers:
            return ""

        if config.slide_count:
            # Show both current slide and total count
            return f"""
                <span class="slide-number-current">{slide_index}</span>
                <span class="slide-number-separator"> / </span>
                <span class="slide-number-total">{total_slides}</span>
            """
        else:
            # Show only current slide number
            return f"""
                <span class="slide-number-current">{slide_index}</span>
            """

    def render_homepage(self, presentations, context=None):
        """
        Render homepage with presentation listings using existing template structure.
        
        Args:
            presentations: List of presentation info objects
            context: Optional context (for compatibility)
            
        Returns:
            Rendered HTML content for homepage
        """
        try:
            template = self.env.get_template('homepage.html')
            return template.render(presentations=presentations)

        except Exception as e:
            # Fallback to minimal homepage
            return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Presentations</title>
</head>
<body>
    <h1>Presentations</h1>
    <p>Error rendering enhanced homepage: {self._escape_html(str(e))}</p>
    <ul>
        {"".join(f'<li><a href="presentations/{p.folder_name}.html">{self._escape_html(p.title)}</a></li>' for p in presentations)}
    </ul>
</body>
</html>
            """

    def render_presentation_page(self, presentation, context: dict) -> str:
        """
        Render a complete presentation page using the presentation template.
        
        Args:
            presentation: Enhanced presentation object with all processed data
            context: Template context dictionary with variables for rendering
            
        Returns:
            Complete HTML string for the presentation page
        """
        try:
            template = self.env.get_template('presentation.html')
            return template.render(**context)

        except Exception as e:
            # Fallback to minimal presentation page
            return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._escape_html(presentation.info.title if hasattr(presentation, 'info') else 'Error')}</title>
</head>
<body>
    <h1>Presentation Rendering Error</h1>
    <p>Error: {self._escape_html(str(e))}</p>
    <p>Presentation: {self._escape_html(presentation.info.title if hasattr(presentation, 'info') else 'Unknown')}</p>
</body>
</html>
            """

    def _calculate_asset_path_prefix(self, folder_name: str) -> str:
        """
        Calculate the correct relative path prefix for assets based on presentation nesting.
        
        Args:
            folder_name: The folder name/path for the presentation (e.g., "single-pres" or "Examples/10 Deckset basics")
            
        Returns:
            Relative path prefix (e.g., "../" or "../../")
        """
        # Count the number of path separators to determine nesting depth
        # Examples:
        # "single-presentation" -> 0 separators -> "../" (presentations/single.html -> ../assets)
        # "Examples/10 Deckset basics" -> 1 separator -> "../../" (presentations/Examples/file.html -> ../../assets)
        path_parts = folder_name.split('/')
        depth = len(path_parts)

        # We need depth "../" segments to go back to the root from the presentation file
        # Single presentations: presentations/file.html -> ../
        # Nested presentations: presentations/subfolder/file.html -> ../../
        return "../" * depth
