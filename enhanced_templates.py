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
from enhanced_models import (
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
        """Load and cache template strings."""
        self.slide_template = """
<section class="slide" id="slide-{{ slide.index }}" 
         data-transition="{{ slide.slide_config.slide_transition or config.slide_transition or 'none' }}"
         {% if slide.slide_config.autoscale or config.autoscale %}data-autoscale="true"{% endif %}>
    
    <!-- Background Image -->
    {% if slide.background_image %}
        {{ render_background_image(slide.background_image) }}
    {% endif %}
    
    <!-- Slide Content -->
    <div class="slide-content {{ 'columns' if slide.columns else 'single-column' }}">
        {% if slide.columns %}
            {{ render_columns(slide.columns) }}
        {% else %}
            <div class="content-area">
                {{ slide.content | markdown_to_html }}
                {% if slide.inline_images %}
                    {{ render_inline_images(slide.inline_images) }}
                {% endif %}
                {% if slide.videos %}
                    {% for video in slide.videos %}
                        {{ render_video_player(video) }}
                    {% endfor %}
                {% endif %}
                {% if slide.audio %}
                    {% for audio in slide.audio %}
                        {{ render_audio_player(audio) }}
                    {% endfor %}
                {% endif %}
                {% if slide.code_blocks %}
                    {% for code_block in slide.code_blocks %}
                        {{ render_code_block(code_block) }}
                    {% endfor %}
                {% endif %}
                {% if slide.math_formulas %}
                    {% for formula in slide.math_formulas %}
                        {{ render_math_formula(formula) }}
                    {% endfor %}
                {% endif %}
            </div>
        {% endif %}
    </div>
    
    <!-- Footnotes -->
    {% if slide.footnotes %}
        <div class="footnotes">
            {{ render_footnotes(slide.footnotes) }}
        </div>
    {% endif %}
    
    <!-- Footer -->
    {% if not slide.slide_config.hide_footer and config.footer %}
        <div class="slide-footer">
            {{ render_slide_footer(config, slide.slide_config) }}
        </div>
    {% endif %}
    
    <!-- Slide Number -->
    {% if not slide.slide_config.hide_slide_numbers and config.slide_numbers %}
        <div class="slide-number">
            {{ render_slide_number(slide.index, total_slides, config) }}
        </div>
    {% endif %}
    
    <!-- Speaker Notes (hidden by default) -->
    {% if slide.notes %}
        <aside class="speaker-notes" style="display: none;">
            {{ slide.notes | markdown_to_html }}
        </aside>
    {% endif %}
</section>
        """
    
    def render_slide(self, slide: ProcessedSlide, config: DecksetConfig, total_slides: int = 1) -> str:
        """Render a complete slide with full Deckset feature support."""
        try:
            template = self.env.from_string(self.slide_template)
            return template.render(
                slide=slide,
                config=config,
                total_slides=total_slides
            )
        except Exception as e:
            # Fallback to minimal slide rendering
            return self._render_fallback_slide(slide, config, str(e))
    
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
        
        style_attr = f'style="{"; ".join(styles)}"' if styles else ""
        class_attr = f'class="{" ".join(css_classes)}"'
        
        return f"""
            <div {class_attr} {style_attr}
                 style="background-image: url('{image.web_path}'); {'; '.join(styles)}"
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
    
    def _render_fallback_slide(self, slide: ProcessedSlide, config: DecksetConfig, error: str) -> str:
        """Render a minimal fallback slide when template rendering fails."""
        return f"""
            <section class="slide slide-error" id="slide-{slide.index}">
                <div class="slide-content">
                    <div class="content-area">
                        <h2>Slide {slide.index}</h2>
                        <div class="error-message">Template rendering error: {self._escape_html(error)}</div>
                        <div class="fallback-content">
                            {self._escape_html(slide.content[:500])}
                            {'...' if len(slide.content) > 500 else ''}
                        </div>
                    </div>
                </div>
            </section>
        """
    
    def _markdown_to_html(self, content: str) -> str:
        """Convert markdown content to HTML."""
        if not content:
            return ""
        
        # Basic markdown conversion (simplified)
        # In a full implementation, this would use a proper markdown library
        html = content
        
        # Convert headers
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        
        # Convert emphasis
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        
        # Convert line breaks
        html = html.replace('\n\n', '</p><p>')
        html = f'<p>{html}</p>'
        
        # Clean up empty paragraphs
        html = re.sub(r'<p></p>', '', html)
        
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
        
        css_classes = ["code-block"]
        
        # Add language class for syntax highlighting
        if code_block.language:
            css_classes.append(f"language-{code_block.language}")
        
        # Process code content with line highlighting
        lines = code_block.content.split('\n')
        processed_lines = []
        
        for i, line in enumerate(lines, 1):
            line_classes = ["code-line"]
            
            # Add highlight class if line is highlighted
            if i in code_block.highlighted_lines:
                line_classes.append("highlighted")
            
            # Add line number if enabled
            line_number = f'<span class="line-number">{i}</span>' if code_block.line_numbers else ''
            
            processed_lines.append(
                f'<span class="{" ".join(line_classes)}">{line_number}{self._escape_html(line)}</span>'
            )
        
        code_content = '\n'.join(processed_lines)
        class_attr = f'class="{" ".join(css_classes)}"'
        
        return f"""
            <div class="code-container">
                <pre {class_attr}><code>{code_content}</code></pre>
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