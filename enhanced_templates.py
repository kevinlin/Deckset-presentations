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
            # Use the existing base template structure but with enhanced features
            presentation_cards = []
            
            for presentation in presentations:
                # Create presentation card compatible with existing styles
                preview_image = presentation.preview_image or "images/fallback.png"
                last_modified_str = ""
                if hasattr(presentation, 'last_modified') and presentation.last_modified:
                    last_modified_str = f"<p>Updated: {presentation.last_modified.strftime('%Y-%m-%d')}</p>"
                
                presentation_cards.append(f"""
                    <div class="presentation-card bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 overflow-hidden">
                        <a href="presentations/{presentation.folder_name}.html" class="block">
                            <div class="aspect-w-16 aspect-h-9">
                                <img src="{preview_image}" 
                                     alt="Preview of {self._escape_html(presentation.title)}"
                                     class="w-full h-48 object-cover"
                                     loading="lazy">
                            </div>
                        </a>
                        
                        <div class="p-6">
                            <h3 class="text-xl font-semibold text-gray-900 mb-2 presentation-title">
                                <a href="presentations/{presentation.folder_name}.html" 
                                   class="hover:text-blue-600 transition-colors">
                                    {self._escape_html(presentation.title)}
                                </a>
                            </h3>
                            
                            <div class="text-sm text-gray-600 space-y-1">
                                <p>{presentation.slide_count} slide{'s' if presentation.slide_count != 1 else ''}</p>
                                {last_modified_str}
                            </div>
                            
                            <div class="mt-4 flex justify-end">
                                <a href="presentations/{presentation.folder_name}.html" 
                                   class="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                                    View Presentation
                                    <svg class="ml-1 -mr-0.5 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                                    </svg>
                                </a>
                            </div>
                        </div>
                    </div>
                """)
            
            # Create homepage HTML using existing base template structure
            homepage_html = f"""
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Browse a collection of Deckset presentations with {len(presentations)} available presentations">
    <title>Deckset Presentations</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Custom styles for presentation content */
        .slide-content {{
            @apply prose prose-lg max-w-none;
        }}

        .slide-notes {{
            @apply text-gray-600 bg-gray-50 p-4 rounded-lg mt-4;
        }}

        /* Responsive improvements */
        @media (max-width: 640px) {{
            .slide-content {{
                @apply prose-sm;
            }}
        }}

        /* Print styles */
        @media print {{
            .no-print {{
                display: none;
            }}

            .page-break {{
                page-break-after: always;
            }}
        }}

        /* Accessibility improvements */
        .sr-only {{
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border-width: 0;
        }}

        /* Enhanced presentation features indicator */
        .enhanced-indicator {{
            background: linear-gradient(45deg, #3b82f6, #8b5cf6);
            color: white;
            font-size: 0.75rem;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
        }}
    </style>
</head>

<body class="bg-gray-50 min-h-screen flex flex-col">
    <a href="#main-content"
        class="sr-only focus:not-sr-only focus:absolute focus:p-4 focus:bg-blue-500 focus:text-white focus:z-50">
        Skip to main content
    </a>

    <header class="bg-white shadow-sm border-b sticky top-0 z-10">
        <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" aria-label="Main navigation">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <a href="/" class="text-xl font-semibold text-gray-900 flex items-center">
                        <svg class="h-8 w-8 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                        <span>Deckset Presentations</span>
                        <span class="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">Enhanced</span>
                    </a>
                </div>

                <div class="hidden sm:flex sm:items-center sm:space-x-4">
                    <a href="/"
                        class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">Home</a>
                </div>
            </div>
        </nav>
    </header>

    <main id="main-content" class="flex-grow max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div class="mb-8">
            <div class="flex flex-col md:flex-row md:items-center md:justify-between">
                <div>
                    <h1 class="text-3xl font-bold text-gray-900 mb-2">Deckset Presentations</h1>
                    <p class="text-gray-600">
                        Found {len(presentations)} presentation{'s' if len(presentations) != 1 else ''} with enhanced Deckset features
                    </p>
                </div>
                
                <div class="mt-4 md:mt-0">
                    <div class="relative">
                        <input type="text" id="search-input" placeholder="Search presentations..." 
                               class="w-full md:w-64 pl-10 pr-4 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                        <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <svg class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div id="presentations-grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {"".join(presentation_cards)}
        </div>

        <div id="no-results" class="hidden text-center py-12">
            <div class="text-gray-500">
                <svg class="mx-auto h-12 w-12 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 class="text-lg font-medium text-gray-900 mb-2">No matching presentations</h3>
                <p class="text-gray-600">Try adjusting your search criteria.</p>
            </div>
        </div>
    </main>

    <footer class="bg-white border-t mt-12 no-print">
        <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
            <div class="flex flex-col sm:flex-row justify-between items-center">
                <p class="text-center text-gray-500 text-sm mb-2 sm:mb-0">
                    Generated by Enhanced Deckset Website Generator
                </p>
            </div>
        </div>
    </footer>

    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const searchInput = document.getElementById('search-input');
            const presentationCards = document.querySelectorAll('.presentation-card');
            const presentationsGrid = document.getElementById('presentations-grid');
            const noResults = document.getElementById('no-results');
            
            if (searchInput) {{
                searchInput.addEventListener('input', function() {{
                    const searchTerm = this.value.toLowerCase().trim();
                    let matchCount = 0;
                    
                    presentationCards.forEach(card => {{
                        const title = card.querySelector('.presentation-title').textContent.toLowerCase();
                        if (title.includes(searchTerm)) {{
                            card.classList.remove('hidden');
                            matchCount++;
                        }} else {{
                            card.classList.add('hidden');
                        }}
                    }});
                    
                    // Show/hide no results message
                    if (matchCount === 0 && searchTerm !== '') {{
                        presentationsGrid.classList.add('hidden');
                        noResults.classList.remove('hidden');
                    }} else {{
                        presentationsGrid.classList.remove('hidden');
                        noResults.classList.add('hidden');
                    }}
                }});
            }}
        }});
    </script>
</body>
</html>
            """
            
            return homepage_html
            
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

    def render_presentation(self, presentation, config=None, context=None):
        """
        Render a complete presentation with all slides.
        
        Args:
            presentation: ProcessedPresentation or EnhancedPresentation object
            config: Optional configuration overrides
            context: Optional additional context
            
        Returns:
            Complete HTML for the presentation
        """
        try:
            # Extract presentation info and slides
            if hasattr(presentation, 'info'):
                info = presentation.info
                slides = presentation.slides
                presentation_config = getattr(presentation, 'config', config)
            else:
                # Fallback for basic ProcessedPresentation
                info = presentation.info if hasattr(presentation, 'info') else presentation
                slides = presentation.slides if hasattr(presentation, 'slides') else []
                presentation_config = config
                
            if not presentation_config:
                from models import DecksetConfig
                presentation_config = DecksetConfig()
            
            # Render all slides
            rendered_slides = []
            for slide in slides:
                rendered_slide = self.render_slide(slide, presentation_config, len(slides))
                rendered_slides.append(rendered_slide)
            
            # Create the complete presentation HTML
            presentation_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._escape_html(info.title if hasattr(info, 'title') else 'Presentation')}</title>
    <link rel="stylesheet" href="../assets/enhanced_slide_styles.css">
    <link rel="stylesheet" href="../assets/code_highlighting_styles.css">
    <script src="../assets/js/enhanced-slide-viewer.js" defer></script>
</head>
<body>
    <div class="presentation-container">
        <div class="slides-container">
            {"".join(rendered_slides)}
        </div>
        
        <div class="presentation-controls">
            <button id="prev-slide">Previous</button>
            <span id="slide-counter">1 / {len(slides)}</span>
            <button id="next-slide">Next</button>
            <button id="fullscreen-toggle">Fullscreen</button>
        </div>
        
        <div class="presentation-navigation">
            <div class="slide-thumbnails">
                {self._render_slide_thumbnails(slides)}
            </div>
        </div>
    </div>
</body>
</html>
            """
            
            return presentation_html
            
        except Exception as e:
            # Fallback to minimal presentation
            return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Presentation Error</title>
</head>
<body>
    <h1>Presentation Rendering Error</h1>
    <p>Error: {self._escape_html(str(e))}</p>
    <p>Presentation: {self._escape_html(str(presentation))}</p>
</body>
</html>
            """
    
    def _render_slide_thumbnails(self, slides):
        """Render slide thumbnails for navigation."""
        thumbnails = []
        for i, slide in enumerate(slides, 1):
            # Create a simplified thumbnail view
            content_preview = slide.content[:100] + "..." if len(slide.content) > 100 else slide.content
            thumbnails.append(f"""
                <div class="slide-thumbnail" data-slide="{i}">
                    <div class="thumbnail-number">{i}</div>
                    <div class="thumbnail-content">{self._escape_html(content_preview)}</div>
                </div>
            """)
        return "".join(thumbnails)