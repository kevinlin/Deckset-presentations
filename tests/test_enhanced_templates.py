"""Tests for EnhancedTemplateEngine and Jinja macro rendering.

Since render methods now live in Jinja macros (templates/macros/), tests exercise
the full render_slide() path rather than testing internal Python methods.
"""

import unittest
from pathlib import Path
from models import (
    ProcessedSlide, ColumnContent, ProcessedImage, ProcessedVideo, ProcessedAudio,
    ProcessedCodeBlock, MathFormula, DecksetConfig, SlideConfig, ImageGrid,
    MediaModifiers, ImageModifiers, InlineFigure,
)
from enhanced_templates import EnhancedTemplateEngine

TEMPLATES_DIR = str(Path(__file__).resolve().parent.parent / "templates")


def _engine():
    return EnhancedTemplateEngine(TEMPLATES_DIR)


def _slide(**kwargs):
    defaults = dict(index=1, content="", body_html="", slide_config=SlideConfig())
    defaults.update(kwargs)
    return ProcessedSlide(**defaults)


def _config(**kwargs):
    return DecksetConfig(**kwargs)


# ---------------------------------------------------------------------------
# Core slide rendering
# ---------------------------------------------------------------------------
class TestSlideRendering(unittest.TestCase):
    def setUp(self):
        self.engine = _engine()

    def test_basic_slide(self):
        slide = _slide(body_html="<h1>Title</h1><p>Content</p>")
        html = self.engine.render_slide(slide, _config())
        self.assertIn('class="slide', html)
        self.assertIn('id="slide-1"', html)
        self.assertIn("<h1>Title</h1>", html)

    def test_autoscale_attribute(self):
        slide = _slide()
        html = self.engine.render_slide(slide, _config(autoscale=True))
        self.assertIn('data-autoscale="true"', html)

    def test_transition_attribute(self):
        sc = SlideConfig(slide_transition="fade")
        slide = _slide(slide_config=sc)
        html = self.engine.render_slide(slide, _config())
        self.assertIn('data-transition="fade"', html)

    def test_speaker_notes_hidden(self):
        slide = _slide(notes="Secret notes")
        html = self.engine.render_slide(slide, _config())
        self.assertIn("speaker-notes", html)
        self.assertIn("Secret notes", html)
        self.assertIn('style="display: none;"', html)


# ---------------------------------------------------------------------------
# Background image macro
# ---------------------------------------------------------------------------
class TestBackgroundImage(unittest.TestCase):
    def setUp(self):
        self.engine = _engine()

    def _bg_slide(self, **mod_kw):
        defaults = dict(placement="background", scaling="cover", filter="original")
        defaults.update(mod_kw)
        mods = ImageModifiers(**defaults)
        img = ProcessedImage(src_path="bg.jpg", web_path="slides/bg.jpg", modifiers=mods, alt_text="BG")
        return _slide(background_image=img, background_images=[img])

    def test_background_renders(self):
        html = self.engine.render_slide(self._bg_slide(), _config())
        self.assertIn("background-image", html)
        self.assertIn("slides/bg.jpg", html)

    def test_background_filter(self):
        html = self.engine.render_slide(self._bg_slide(filter="filtered"), _config())
        self.assertIn("filtered", html)


# ---------------------------------------------------------------------------
# Inline images / grid macros
# ---------------------------------------------------------------------------
class TestInlineImages(unittest.TestCase):
    def setUp(self):
        self.engine = _engine()

    def test_single_inline_image(self):
        mods = ImageModifiers(placement="inline", scaling="fit", filter="original")
        img = ProcessedImage(src_path="pic.png", web_path="slides/pic.png", modifiers=mods, alt_text="Pic")
        slide = _slide(inline_images=[img])
        html = self.engine.render_slide(slide, _config())
        self.assertIn("slides/pic.png", html)
        self.assertIn("inline-image", html)

    def test_multiple_creates_grid(self):
        imgs = []
        for i in range(3):
            mods = ImageModifiers(placement="inline", scaling="fit", filter="original")
            imgs.append(ProcessedImage(src_path=f"{i}.png", web_path=f"slides/{i}.png", modifiers=mods, alt_text=f"img{i}"))
        slide = _slide(inline_images=imgs)
        html = self.engine.render_slide(slide, _config())
        self.assertIn("image-grid", html)


# ---------------------------------------------------------------------------
# Inline figures
# ---------------------------------------------------------------------------
class TestInlineFigures(unittest.TestCase):
    def setUp(self):
        self.engine = _engine()

    def test_figure_with_caption(self):
        mods = ImageModifiers(placement="inline", scaling="fit", filter="original")
        img = ProcessedImage(src_path="fig.jpg", web_path="slides/fig.jpg", modifiers=mods, alt_text="Fig")
        fig = InlineFigure(image=img, caption="My caption")
        slide = _slide(inline_figures=[fig])
        html = self.engine.render_slide(slide, _config())
        self.assertIn("<figure", html)
        self.assertIn("My caption", html)


# ---------------------------------------------------------------------------
# Video macro
# ---------------------------------------------------------------------------
class TestVideo(unittest.TestCase):
    def setUp(self):
        self.engine = _engine()

    def _video_slide(self, embed_type="local", embed_url="", **mod_kw):
        mods = MediaModifiers(placement="inline", **mod_kw)
        vid = ProcessedVideo(src_path="v.mp4", web_path="slides/v.mp4", modifiers=mods, embed_type=embed_type, embed_url=embed_url)
        return _slide(videos=[vid])

    def test_local_video(self):
        html = self.engine.render_slide(self._video_slide(), _config())
        self.assertIn("<video", html)
        self.assertIn("slides/v.mp4", html)
        self.assertIn("controls", html)

    def test_youtube_iframe(self):
        html = self.engine.render_slide(self._video_slide(embed_type="youtube", embed_url="https://youtube.com/embed/abc", autoplay=True), _config())
        self.assertIn("<iframe", html)
        self.assertIn("youtube.com/embed/abc", html)
        self.assertIn("autoplay=1", html)

    def test_hidden_video(self):
        html = self.engine.render_slide(self._video_slide(hide=True, autoplay=True), _config())
        self.assertIn("display: none", html)
        self.assertNotIn("controls", html)


# ---------------------------------------------------------------------------
# Audio macro
# ---------------------------------------------------------------------------
class TestAudio(unittest.TestCase):
    def setUp(self):
        self.engine = _engine()

    def test_audio_with_loop(self):
        mods = MediaModifiers(placement="inline", loop=True)
        aud = ProcessedAudio(src_path="a.mp3", web_path="slides/a.mp3", modifiers=mods)
        slide = _slide(audio=[aud])
        html = self.engine.render_slide(slide, _config())
        self.assertIn("<audio", html)
        self.assertIn("loop", html)
        self.assertIn("controls", html)


# ---------------------------------------------------------------------------
# Code block macro
# ---------------------------------------------------------------------------
class TestCodeBlock(unittest.TestCase):
    def setUp(self):
        self.engine = _engine()

    def test_code_renders(self):
        cb = ProcessedCodeBlock(content="<pre><code>x = 1</code></pre>", language="python")
        slide = _slide(code_blocks=[cb])
        html = self.engine.render_slide(slide, _config())
        self.assertIn("code-container", html)
        self.assertIn("x = 1", html)


# ---------------------------------------------------------------------------
# Math formula macro
# ---------------------------------------------------------------------------
class TestMathFormula(unittest.TestCase):
    def setUp(self):
        self.engine = _engine()

    def test_display_math(self):
        fm = MathFormula(content="E=mc^2", formula_type="display", position=0)
        slide = _slide(math_formulas=[fm])
        html = self.engine.render_slide(slide, _config())
        self.assertIn("math-display", html)
        self.assertIn("E=mc^2", html)

    def test_inline_math(self):
        fm = MathFormula(content="x^2", formula_type="inline", position=0)
        slide = _slide(math_formulas=[fm])
        html = self.engine.render_slide(slide, _config())
        self.assertIn("math-inline", html)
        self.assertIn("x^2", html)

    def test_no_formula(self):
        slide = _slide()
        html = self.engine.render_slide(slide, _config())
        self.assertNotIn("math-display", html)

    def test_special_chars_escaped(self):
        fm = MathFormula(content="a<b", formula_type="inline", position=0)
        slide = _slide(math_formulas=[fm])
        html = self.engine.render_slide(slide, _config())
        self.assertIn("a&lt;b", html)


# ---------------------------------------------------------------------------
# Footnotes macro
# ---------------------------------------------------------------------------
class TestFootnotes(unittest.TestCase):
    def setUp(self):
        self.engine = _engine()

    def test_namespaced_footnotes(self):
        fns = {"fn-slide1-1": "First", "fn-slide1-2": "Second"}
        slide = _slide(footnotes=fns)
        html = self.engine.render_slide(slide, _config())
        self.assertIn('id="fn-slide1-1"', html)
        self.assertIn('id="fn-slide1-2"', html)
        self.assertIn("First", html)

    def test_sorted_order(self):
        fns = {"fn-slide1-3": "Third", "fn-slide1-1": "First"}
        slide = _slide(footnotes=fns)
        html = self.engine.render_slide(slide, _config())
        pos1 = html.find('id="fn-slide1-1"')
        pos3 = html.find('id="fn-slide1-3"')
        self.assertTrue(pos1 < pos3)

    def test_empty_footnotes(self):
        slide = _slide(footnotes={})
        html = self.engine.render_slide(slide, _config())
        self.assertNotIn("footnote-item", html)


# ---------------------------------------------------------------------------
# Chrome macros (footer, slide number)
# ---------------------------------------------------------------------------
class TestChrome(unittest.TestCase):
    def setUp(self):
        self.engine = _engine()

    def test_footer_renders(self):
        slide = _slide()
        html = self.engine.render_slide(slide, _config(footer="**My Footer**"))
        self.assertIn("footer-content", html)
        self.assertIn("My Footer", html)

    def test_footer_hidden(self):
        sc = SlideConfig(hide_footer=True)
        slide = _slide(slide_config=sc)
        html = self.engine.render_slide(slide, _config(footer="Footer"))
        self.assertNotIn("footer-content", html)

    def test_no_footer_config(self):
        slide = _slide()
        html = self.engine.render_slide(slide, _config())
        self.assertNotIn("footer-content", html)

    def test_slide_number(self):
        slide = _slide()
        html = self.engine.render_slide(slide, _config(slide_numbers=True), total_slides=10)
        self.assertIn("slide-number-current", html)

    def test_slide_number_with_count(self):
        slide = _slide()
        html = self.engine.render_slide(slide, _config(slide_numbers=True, slide_count=True), total_slides=10)
        self.assertIn("slide-number-current", html)
        self.assertIn("slide-number-total", html)
        self.assertIn("10", html)

    def test_slide_number_disabled(self):
        slide = _slide()
        html = self.engine.render_slide(slide, _config(slide_numbers=False))
        self.assertNotIn("slide-number-current", html)

    def test_per_slide_footer_override(self):
        sc = SlideConfig(footer="**Per-slide** footer")
        slide = _slide(slide_config=sc)
        html = self.engine.render_slide(slide, _config(footer="Global footer"))
        self.assertIn("footer-content", html)
        self.assertIn("Per-slide", html)
        self.assertNotIn("Global footer", html)

    def test_per_slide_footer_empty_string_hides(self):
        sc = SlideConfig(footer="")
        slide = _slide(slide_config=sc)
        html = self.engine.render_slide(slide, _config(footer="Global"))
        self.assertNotIn("footer-content", html)

    def test_per_slide_hide_slide_numbers(self):
        sc = SlideConfig(hide_slide_numbers=True)
        slide = _slide(slide_config=sc)
        html = self.engine.render_slide(slide, _config(slide_numbers=True), total_slides=5)
        self.assertNotIn("slide-number-current", html)

    def test_slidecount_shows_real_total(self):
        slide = _slide(index=2)
        html = self.engine.render_slide(
            slide, _config(slide_numbers=True, slide_count=True), total_slides=5
        )
        self.assertIn("2", html)
        self.assertIn("5", html)
        self.assertIn("slide-number-total", html)


# ---------------------------------------------------------------------------
# Columns macro
# ---------------------------------------------------------------------------
class TestColumns(unittest.TestCase):
    def setUp(self):
        self.engine = _engine()

    def test_columns_render(self):
        cols = [
            ColumnContent(index=0, content="**Left**", width_percentage=50.0),
            ColumnContent(index=1, content="*Right*", width_percentage=50.0),
        ]
        sc = SlideConfig(columns=True)
        slide = _slide(columns=cols, slide_config=sc)
        html = self.engine.render_slide(slide, _config())
        self.assertIn("columns-container", html)
        self.assertIn("Left", html)
        self.assertIn("Right", html)


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
class TestFilters(unittest.TestCase):
    def setUp(self):
        self.engine = _engine()

    def test_markdown_to_html(self):
        html = self.engine._markdown_to_html("**bold**")
        self.assertIn("<strong>bold</strong>", html)

    def test_markdown_to_html_empty(self):
        self.assertEqual(self.engine._markdown_to_html(""), "")

    def test_escape_html(self):
        self.assertIn("&lt;script&gt;", self.engine._escape_html("<script>"))


# ---------------------------------------------------------------------------
# Homepage
# ---------------------------------------------------------------------------
class TestHomepage(unittest.TestCase):
    def setUp(self):
        self.engine = _engine()

    def test_renders_presentations(self):
        from unittest.mock import Mock
        p = Mock()
        p.title = "My Talk"
        p.folder_name = "my-talk"
        p.slide_count = 5
        p.folder_path = "/tmp/my-talk"
        html = self.engine.render_homepage([p])
        self.assertIn("My Talk", html)


if __name__ == "__main__":
    unittest.main()
