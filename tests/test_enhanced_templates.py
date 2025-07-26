"""
Unit tests for the enhanced template engine.

Tests cover slide rendering, column layouts, background image handling,
and template functionality with Deckset features.
"""

import unittest
from unittest.mock import Mock, patch
from enhanced_templates import EnhancedTemplateEngine
from models import (
    ProcessedSlide, ColumnContent, ProcessedImage, ImageModifiers,
    DecksetConfig, SlideConfig
)


class TestEnhancedTemplateEngine(unittest.TestCase):
    """Test cases for EnhancedTemplateEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = EnhancedTemplateEngine()
        
        # Create test slide
        self.test_slide = ProcessedSlide(
            index=1,
            content="# Test Slide\n\nThis is test content.",
            notes="These are speaker notes.",
            slide_config=SlideConfig()
        )
        
        # Create test config
        self.test_config = DecksetConfig(
            slide_numbers=True,
            footer="Test Footer"
        )
    
    def test_render_slide_basic(self):
        """Test basic slide rendering."""
        result = self.engine.render_slide(self.test_slide, self.test_config)
        
        self.assertIn('class="slide"', result)
        self.assertIn('id="slide-1"', result)
        self.assertIn('Test Slide', result)
        self.assertIn('test content', result)
        self.assertIn('speaker-notes', result)
    
    def test_render_slide_with_background_image(self):
        """Test slide rendering with background image."""
        # Create background image
        modifiers = ImageModifiers(
            placement="background",
            scaling="cover",
            filter="filtered"
        )
        
        background_image = ProcessedImage(
            src_path="test.jpg",
            web_path="slides/test/test.jpg",
            modifiers=modifiers,
            alt_text="Background"
        )
        
        self.test_slide.background_image = background_image
        
        result = self.engine.render_slide(self.test_slide, self.test_config)
        
        self.assertIn('background-image', result)
        self.assertIn('slides/test/test.jpg', result)
        self.assertIn('filtered', result)
    
    def test_render_slide_with_columns(self):
        """Test slide rendering with multi-column layout."""
        # Create columns
        columns = [
            ColumnContent(index=0, content="Column 1 content", width_percentage=50.0),
            ColumnContent(index=1, content="Column 2 content", width_percentage=50.0)
        ]
        
        self.test_slide.columns = columns
        
        result = self.engine.render_slide(self.test_slide, self.test_config)
        
        self.assertIn('columns-container', result)
        self.assertIn('Column 1 content', result)
        self.assertIn('Column 2 content', result)
        self.assertIn('width: 50.0%', result)
    
    def test_render_slide_with_footer_and_numbers(self):
        """Test slide rendering with footer and slide numbers."""
        result = self.engine.render_slide(self.test_slide, self.test_config, total_slides=10)
        
        self.assertIn('slide-footer', result)
        self.assertIn('slide-number', result)
        self.assertIn('Test Footer', result)
    
    def test_render_slide_hidden_footer_and_numbers(self):
        """Test slide rendering with hidden footer and numbers."""
        self.test_slide.slide_config.hide_footer = True
        self.test_slide.slide_config.hide_slide_numbers = True
        
        result = self.engine.render_slide(self.test_slide, self.test_config)
        
        self.assertNotIn('slide-footer', result)
        self.assertNotIn('slide-number', result)
    
    def test_render_columns_empty(self):
        """Test rendering empty columns."""
        result = self.engine.render_columns([])
        self.assertEqual(result, "")
    
    def test_render_columns_multiple(self):
        """Test rendering multiple columns."""
        columns = [
            ColumnContent(index=0, content="# First Column", width_percentage=33.3),
            ColumnContent(index=1, content="## Second Column", width_percentage=33.3),
            ColumnContent(index=2, content="### Third Column", width_percentage=33.4)
        ]
        
        result = self.engine.render_columns(columns)
        
        self.assertIn('columns-container', result)
        self.assertIn('width: 33.3%', result)
        self.assertIn('width: 33.4%', result)
        self.assertIn('First Column', result)
        self.assertIn('Second Column', result)
        self.assertIn('Third Column', result)
    
    def test_render_background_image_basic(self):
        """Test basic background image rendering."""
        modifiers = ImageModifiers(
            placement="background",
            scaling="cover",
            filter="original"
        )
        
        image = ProcessedImage(
            src_path="test.jpg",
            web_path="slides/test/test.jpg",
            modifiers=modifiers,
            alt_text="Test background"
        )
        
        result = self.engine.render_background_image(image)
        
        self.assertIn('background-image', result)
        self.assertIn('slides/test/test.jpg', result)
        self.assertIn('background-size: cover', result)
        self.assertIn('Test background', result)
    
    def test_render_background_image_with_positioning(self):
        """Test background image rendering with left/right positioning."""
        modifiers = ImageModifiers(
            placement="left",
            scaling="fit",
            filter="filtered"
        )
        
        image = ProcessedImage(
            src_path="test.jpg",
            web_path="slides/test/test.jpg",
            modifiers=modifiers,
            alt_text="Left background"
        )
        
        result = self.engine.render_background_image(image)
        
        self.assertIn('background-image left', result)
        self.assertIn('filtered', result)
        self.assertIn('background-size: contain', result)
    
    def test_render_background_image_with_corner_radius(self):
        """Test background image rendering with corner radius."""
        modifiers = ImageModifiers(
            placement="background",
            scaling="cover",
            filter="original",
            corner_radius=10
        )
        
        image = ProcessedImage(
            src_path="test.jpg",
            web_path="slides/test/test.jpg",
            modifiers=modifiers,
            alt_text="Rounded background"
        )
        
        result = self.engine.render_background_image(image)
        
        self.assertIn('border-radius: 10px', result)
    
    def test_render_background_image_with_percentage_scaling(self):
        """Test background image rendering with percentage scaling."""
        modifiers = ImageModifiers(
            placement="background",
            scaling="75%",
            filter="original"
        )
        
        image = ProcessedImage(
            src_path="test.jpg",
            web_path="slides/test/test.jpg",
            modifiers=modifiers,
            alt_text="Scaled background"
        )
        
        result = self.engine.render_background_image(image)
        
        self.assertIn('background-size: 75%', result)
    
    def test_render_background_image_none(self):
        """Test rendering with no background image."""
        result = self.engine.render_background_image(None)
        self.assertEqual(result, "")
    
    def test_markdown_to_html_conversion(self):
        """Test markdown to HTML conversion."""
        markdown = "# Header\n\n**Bold** and *italic* text."
        result = self.engine._markdown_to_html(markdown)
        
        self.assertIn('<h1>Header</h1>', result)
        self.assertIn('<strong>Bold</strong>', result)
        self.assertIn('<em>italic</em>', result)
    
    def test_markdown_to_html_fit_headers(self):
        """Test markdown to HTML conversion with fit headers."""
        markdown = "# Title {.fit}\n\n## Subtitle {.fit}\n\n### Normal Header"
        result = self.engine._markdown_to_html(markdown)
        
        self.assertIn('<h1 class="fit">Title</h1>', result)
        self.assertIn('<h2 class="fit">Subtitle</h2>', result)
        self.assertIn('<h3>Normal Header</h3>', result)
    
    def test_html_escaping(self):
        """Test HTML character escaping."""
        text = '<script>alert("xss")</script>'
        result = self.engine._escape_html(text)
        
        self.assertIn('&lt;script&gt;', result)
        self.assertIn('&quot;xss&quot;', result)
        self.assertNotIn('<script>', result)
    
    def test_render_slide_with_autoscale(self):
        """Test slide rendering with autoscale enabled."""
        self.test_config.autoscale = True
        
        result = self.engine.render_slide(self.test_slide, self.test_config)
        
        self.assertIn('data-autoscale="true"', result)
    
    def test_render_slide_with_transition(self):
        """Test slide rendering with transition effect."""
        self.test_slide.slide_config.slide_transition = "fade"
        
        result = self.engine.render_slide(self.test_slide, self.test_config)
        
        self.assertIn('data-transition="fade"', result)
    
    def test_render_slide_fallback_on_error(self):
        """Test fallback rendering when template fails."""
        # Mock template to raise an exception
        with patch.object(self.engine, 'slide_template', 'invalid {{ template'):
            result = self.engine.render_slide(self.test_slide, self.test_config)
            
            self.assertIn('slide-error', result)
            self.assertIn('Template rendering error', result)
            self.assertIn('Test Slide', result)


if __name__ == '__main__':
    unittest.main()

class TestEnhancedTemplateEngineMedia(unittest.TestCase):
    """Test cases for media and content rendering (Task 7.2)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = EnhancedTemplateEngine()
    
    def test_render_video_player_local(self):
        """Test rendering local video player."""
        from models import ProcessedVideo, MediaModifiers
        
        modifiers = MediaModifiers(
            placement="inline",
            autoplay=True,
            loop=False,
            mute=True
        )
        
        video = ProcessedVideo(
            src_path="test.mp4",
            web_path="slides/test/test.mp4",
            modifiers=modifiers,
            embed_type="local"
        )
        
        result = self.engine.render_video_player(video)
        
        self.assertIn('<video', result)
        self.assertIn('class="video-player"', result)
        self.assertIn('slides/test/test.mp4', result)
        self.assertIn('autoplay', result)
        self.assertIn('muted', result)
        self.assertIn('controls', result)
        self.assertNotIn('loop', result)
    
    def test_render_video_player_youtube(self):
        """Test rendering YouTube video player."""
        from models import ProcessedVideo, MediaModifiers
        
        modifiers = MediaModifiers(
            placement="inline",
            autoplay=True,
            loop=True
        )
        
        video = ProcessedVideo(
            src_path="https://youtube.com/watch?v=test123",
            web_path="https://youtube.com/watch?v=test123",
            modifiers=modifiers,
            embed_type="youtube",
            embed_url="https://www.youtube.com/embed/test123"
        )
        
        result = self.engine.render_video_player(video)
        
        self.assertIn('<iframe', result)
        self.assertIn('youtube.com/embed/test123', result)
        self.assertIn('autoplay=1', result)
        self.assertIn('loop=1', result)
        self.assertIn('allowfullscreen', result)
    
    def test_render_video_player_with_positioning(self):
        """Test rendering video player with left/right positioning."""
        from models import ProcessedVideo, MediaModifiers
        
        modifiers = MediaModifiers(
            placement="left",
            scaling="50%"
        )
        
        video = ProcessedVideo(
            src_path="test.mp4",
            web_path="slides/test/test.mp4",
            modifiers=modifiers,
            embed_type="local"
        )
        
        result = self.engine.render_video_player(video)
        
        self.assertIn('class="video-player left"', result)
        self.assertIn('width: 50%', result)
    
    def test_render_video_player_hidden(self):
        """Test rendering hidden video player."""
        from models import ProcessedVideo, MediaModifiers
        
        modifiers = MediaModifiers(
            placement="inline",
            hide=True,
            autoplay=True
        )
        
        video = ProcessedVideo(
            src_path="test.mp4",
            web_path="slides/test/test.mp4",
            modifiers=modifiers,
            embed_type="local"
        )
        
        result = self.engine.render_video_player(video)
        
        self.assertIn('display: none', result)
        self.assertNotIn('controls', result)
        self.assertIn('autoplay', result)
    
    def test_render_audio_player_basic(self):
        """Test basic audio player rendering."""
        from models import ProcessedAudio, MediaModifiers
        
        modifiers = MediaModifiers(
            placement="inline",
            autoplay=False,
            loop=True
        )
        
        audio = ProcessedAudio(
            src_path="test.mp3",
            web_path="slides/test/test.mp3",
            modifiers=modifiers
        )
        
        result = self.engine.render_audio_player(audio)
        
        self.assertIn('<audio', result)
        self.assertIn('class="audio-player"', result)
        self.assertIn('slides/test/test.mp3', result)
        self.assertIn('loop', result)
        self.assertIn('controls', result)
        self.assertNotIn('autoplay', result)
    
    def test_render_audio_player_with_positioning(self):
        """Test audio player rendering with positioning."""
        from models import ProcessedAudio, MediaModifiers
        
        modifiers = MediaModifiers(
            placement="right",
            scaling="75%",
            mute=True
        )
        
        audio = ProcessedAudio(
            src_path="test.mp3",
            web_path="slides/test/test.mp3",
            modifiers=modifiers
        )
        
        result = self.engine.render_audio_player(audio)
        
        self.assertIn('class="audio-player right"', result)
        self.assertIn('width: 75%', result)
        self.assertIn('muted', result)
    
    def test_render_code_block_basic(self):
        """Test basic code block rendering."""
        from models import ProcessedCodeBlock
        
        code_block = ProcessedCodeBlock(
            content="def hello():\n    print('Hello, World!')",
            language="python",
            highlighted_lines={2},
            line_numbers=True
        )
        
        result = self.engine.render_code_block(code_block)
        
        self.assertIn('class="language-python"', result)
        self.assertIn('class="code-block-with-highlighting"', result)
        self.assertIn('def hello():', result)
        self.assertIn('print(&#x27;Hello, World!&#x27;)', result)
        self.assertIn('data-line=', result)
        self.assertIn('code-line-highlighted', result)
    
    def test_render_code_block_no_highlighting(self):
        """Test code block rendering without line highlighting."""
        from models import ProcessedCodeBlock
        
        code_block = ProcessedCodeBlock(
            content="console.log('test');",
            language="javascript",
            highlighted_lines=set(),
            line_numbers=False
        )
        
        result = self.engine.render_code_block(code_block)
        
        self.assertIn('class="language-javascript"', result)
        self.assertIn('console.log(&#x27;test&#x27;);', result)
        self.assertIn('data-line=', result)
        self.assertNotIn('code-line-highlighted', result)
    
    def test_render_code_block_multiple_highlighted_lines(self):
        """Test code block rendering with multiple highlighted lines."""
        from models import ProcessedCodeBlock
        
        code_block = ProcessedCodeBlock(
            content="line 1\nline 2\nline 3\nline 4",
            language="text",
            highlighted_lines={1, 3, 4}
        )
        
        result = self.engine.render_code_block(code_block)
        
        # Count highlighted lines
        highlighted_count = result.count('code-line-highlighted')
        self.assertEqual(highlighted_count, 3)
        self.assertIn('line 1', result)
        self.assertIn('line 4', result)
    
    def test_render_inline_images_single(self):
        """Test rendering single inline image."""
        from models import ProcessedImage, ImageModifiers
        
        modifiers = ImageModifiers(
            placement="inline",
            scaling="fit",
            filter="original"
        )
        
        image = ProcessedImage(
            src_path="test.jpg",
            web_path="slides/test/test.jpg",
            modifiers=modifiers,
            alt_text="Test image"
        )
        
        result = self.engine.render_inline_images([image])
        
        self.assertIn('<img', result)
        self.assertIn('class="inline-image"', result)
        self.assertIn('slides/test/test.jpg', result)
        self.assertIn('alt="Test image"', result)
        self.assertIn('loading="lazy"', result)
    
    def test_render_inline_images_with_fill_scaling(self):
        """Test rendering inline image with fill scaling."""
        from models import ProcessedImage, ImageModifiers
        
        modifiers = ImageModifiers(
            placement="inline",
            scaling="fill",
            filter="original"
        )
        
        image = ProcessedImage(
            src_path="test.jpg",
            web_path="slides/test/test.jpg",
            modifiers=modifiers,
            alt_text="Fill image"
        )
        
        result = self.engine.render_inline_images([image])
        
        self.assertIn('class="inline-image fill"', result)
    
    def test_render_inline_images_with_percentage_scaling(self):
        """Test rendering inline image with percentage scaling."""
        from models import ProcessedImage, ImageModifiers
        
        modifiers = ImageModifiers(
            placement="inline",
            scaling="80%",
            filter="original"
        )
        
        image = ProcessedImage(
            src_path="test.jpg",
            web_path="slides/test/test.jpg",
            modifiers=modifiers,
            alt_text="Scaled image"
        )
        
        result = self.engine.render_inline_images([image])
        
        self.assertIn('width: 80%', result)
    
    def test_render_inline_images_with_corner_radius(self):
        """Test rendering inline image with corner radius."""
        from models import ProcessedImage, ImageModifiers
        
        modifiers = ImageModifiers(
            placement="inline",
            scaling="fit",
            filter="original",
            corner_radius=15
        )
        
        image = ProcessedImage(
            src_path="test.jpg",
            web_path="slides/test/test.jpg",
            modifiers=modifiers,
            alt_text="Rounded image"
        )
        
        result = self.engine.render_inline_images([image])
        
        self.assertIn('border-radius: 15px', result)
    
    def test_render_image_grid_two_columns(self):
        """Test rendering image grid with two columns."""
        from models import ProcessedImage, ImageModifiers, ImageGrid
        
        modifiers = ImageModifiers(
            placement="inline",
            scaling="fit",
            filter="original"
        )
        
        images = [
            ProcessedImage(
                src_path="test1.jpg",
                web_path="slides/test/test1.jpg",
                modifiers=modifiers,
                alt_text="Image 1"
            ),
            ProcessedImage(
                src_path="test2.jpg",
                web_path="slides/test/test2.jpg",
                modifiers=modifiers,
                alt_text="Image 2"
            )
        ]
        
        grid = ImageGrid(images=images, columns=2)
        result = self.engine.render_image_grid(grid)
        
        self.assertIn('class="image-grid two-columns"', result)
        self.assertIn('grid-template-columns: repeat(2, 1fr)', result)
        self.assertIn('test1.jpg', result)
        self.assertIn('test2.jpg', result)
        self.assertIn('grid-image', result)
    
    def test_render_image_grid_three_columns(self):
        """Test rendering image grid with three columns."""
        from models import ProcessedImage, ImageModifiers, ImageGrid
        
        modifiers = ImageModifiers(
            placement="inline",
            scaling="fit",
            filter="original"
        )
        
        images = [
            ProcessedImage(
                src_path=f"test{i}.jpg",
                web_path=f"slides/test/test{i}.jpg",
                modifiers=modifiers,
                alt_text=f"Image {i}"
            ) for i in range(1, 4)
        ]
        
        grid = ImageGrid(images=images, columns=3)
        result = self.engine.render_image_grid(grid)
        
        self.assertIn('class="image-grid three-columns"', result)
        self.assertIn('grid-template-columns: repeat(3, 1fr)', result)
    
    def test_render_image_grid_empty(self):
        """Test rendering empty image grid."""
        from models import ImageGrid
        
        grid = ImageGrid(images=[], columns=1)
        result = self.engine.render_image_grid(grid)
        
        self.assertEqual(result, "")
    
    def test_render_video_player_none(self):
        """Test rendering with no video."""
        result = self.engine.render_video_player(None)
        self.assertEqual(result, "")
    
    def test_render_audio_player_none(self):
        """Test rendering with no audio."""
        result = self.engine.render_audio_player(None)
        self.assertEqual(result, "")
    
    def test_render_code_block_none(self):
        """Test rendering with no code block."""
        result = self.engine.render_code_block(None)
        self.assertEqual(result, "")

class TestEnhancedTemplateEngineFormulasAndMetadata(unittest.TestCase):
    """Test cases for formula and metadata rendering (Task 7.3)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = EnhancedTemplateEngine()
    
    def test_render_math_formula_display(self):
        """Test rendering display math formula."""
        from models import MathFormula
        
        formula = MathFormula(
            content="E = mc^2",
            formula_type="display",
            position=0,
            valid=True
        )
        
        result = self.engine.render_math_formula(formula)
        
        self.assertIn('class="math-display"', result)
        self.assertIn('data-formula-type="display"', result)
        self.assertIn('\\[E = mc^2\\]', result)
    
    def test_render_math_formula_inline(self):
        """Test rendering inline math formula."""
        from models import MathFormula
        
        formula = MathFormula(
            content="x^2 + y^2 = z^2",
            formula_type="inline",
            position=10,
            valid=True
        )
        
        result = self.engine.render_math_formula(formula)
        
        self.assertIn('class="math-inline"', result)
        self.assertIn('data-formula-type="inline"', result)
        self.assertIn('\\(x^2 + y^2 = z^2\\)', result)
    
    def test_render_math_formula_with_special_characters(self):
        """Test rendering math formula with special characters."""
        from models import MathFormula
        
        formula = MathFormula(
            content="\\sum_{i=1}^{n} x_i < \\infty",
            formula_type="display",
            position=0,
            valid=True
        )
        
        result = self.engine.render_math_formula(formula)
        
        self.assertIn('\\sum_{i=1}^{n} x_i &lt; \\infty', result)
    
    def test_render_math_formula_unknown_type(self):
        """Test rendering math formula with unknown type."""
        from models import MathFormula
        
        formula = MathFormula(
            content="a + b = c",
            formula_type="unknown",
            position=0,
            valid=True
        )
        
        result = self.engine.render_math_formula(formula)
        
        self.assertIn('class="math-unknown"', result)
        self.assertIn('data-formula-type="unknown"', result)
        self.assertIn('a + b = c', result)
    
    def test_render_math_formula_none(self):
        """Test rendering with no math formula."""
        result = self.engine.render_math_formula(None)
        self.assertEqual(result, "")
    
    def test_render_footnotes_basic(self):
        """Test basic footnotes rendering."""
        footnotes = {
            "1": "This is the first footnote.",
            "2": "This is the **second** footnote with *emphasis*."
        }
        
        result = self.engine.render_footnotes(footnotes)
        
        self.assertIn('class="footnotes"', result)
        self.assertIn('footnotes-separator', result)
        self.assertIn('footnotes-list', result)
        self.assertIn('footnote-item', result)
        self.assertIn('id="footnote-1"', result)
        self.assertIn('id="footnote-2"', result)
        self.assertIn('first footnote', result)
        self.assertIn('<strong>second</strong>', result)
        self.assertIn('<em>emphasis</em>', result)
    
    def test_render_footnotes_sorted_order(self):
        """Test footnotes are rendered in sorted order."""
        footnotes = {
            "3": "Third footnote",
            "1": "First footnote", 
            "2": "Second footnote"
        }
        
        result = self.engine.render_footnotes(footnotes)
        
        # Check that footnotes appear in sorted order
        pos_1 = result.find('id="footnote-1"')
        pos_2 = result.find('id="footnote-2"')
        pos_3 = result.find('id="footnote-3"')
        
        self.assertTrue(pos_1 < pos_2 < pos_3)
    
    def test_render_footnotes_empty(self):
        """Test rendering empty footnotes."""
        result = self.engine.render_footnotes({})
        self.assertEqual(result, "")
    
    def test_render_footnotes_none(self):
        """Test rendering with None footnotes."""
        result = self.engine.render_footnotes(None)
        self.assertEqual(result, "")
    
    def test_render_slide_footer_basic(self):
        """Test basic slide footer rendering."""
        from models import DecksetConfig, SlideConfig
        
        config = DecksetConfig(footer="**Footer Text** with *emphasis*")
        slide_config = SlideConfig()
        
        result = self.engine.render_slide_footer(config, slide_config)
        
        self.assertIn('class="footer-content"', result)
        self.assertIn('<strong>Footer Text</strong>', result)
        self.assertIn('<em>emphasis</em>', result)
    
    def test_render_slide_footer_hidden(self):
        """Test slide footer rendering when hidden."""
        from models import DecksetConfig, SlideConfig
        
        config = DecksetConfig(footer="Footer Text")
        slide_config = SlideConfig(hide_footer=True)
        
        result = self.engine.render_slide_footer(config, slide_config)
        
        self.assertEqual(result, "")
    
    def test_render_slide_footer_no_footer(self):
        """Test slide footer rendering with no footer configured."""
        from models import DecksetConfig, SlideConfig
        
        config = DecksetConfig(footer=None)
        slide_config = SlideConfig()
        
        result = self.engine.render_slide_footer(config, slide_config)
        
        self.assertEqual(result, "")
    
    def test_render_slide_footer_empty_footer(self):
        """Test slide footer rendering with empty footer."""
        from models import DecksetConfig, SlideConfig
        
        config = DecksetConfig(footer="")
        slide_config = SlideConfig()
        
        result = self.engine.render_slide_footer(config, slide_config)
        
        self.assertEqual(result, "")
    
    def test_render_slide_number_basic(self):
        """Test basic slide number rendering."""
        from models import DecksetConfig
        
        config = DecksetConfig(slide_numbers=True, slide_count=False)
        
        result = self.engine.render_slide_number(5, 10, config)
        
        self.assertIn('class="slide-number-current"', result)
        self.assertIn('>5<', result)
        self.assertNotIn('slide-number-total', result)
        self.assertNotIn('slide-number-separator', result)
    
    def test_render_slide_number_with_count(self):
        """Test slide number rendering with total count."""
        from models import DecksetConfig
        
        config = DecksetConfig(slide_numbers=True, slide_count=True)
        
        result = self.engine.render_slide_number(3, 15, config)
        
        self.assertIn('class="slide-number-current"', result)
        self.assertIn('class="slide-number-total"', result)
        self.assertIn('class="slide-number-separator"', result)
        self.assertIn('>3<', result)
        self.assertIn('>15<', result)
        self.assertIn('> / <', result)
    
    def test_render_slide_number_disabled(self):
        """Test slide number rendering when disabled."""
        from models import DecksetConfig
        
        config = DecksetConfig(slide_numbers=False)
        
        result = self.engine.render_slide_number(5, 10, config)
        
        self.assertEqual(result, "")
    
    def test_render_slide_number_first_slide(self):
        """Test slide number rendering for first slide."""
        from models import DecksetConfig
        
        config = DecksetConfig(slide_numbers=True, slide_count=True)
        
        result = self.engine.render_slide_number(1, 20, config)
        
        self.assertIn('>1<', result)
        self.assertIn('>20<', result)
    
    def test_render_slide_number_last_slide(self):
        """Test slide number rendering for last slide."""
        from models import DecksetConfig
        
        config = DecksetConfig(slide_numbers=True, slide_count=True)
        
        result = self.engine.render_slide_number(20, 20, config)
        
        self.assertIn('>20<', result)
        self.assertIn('>20<', result)  # Both current and total should be 20