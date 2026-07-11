"""Tests for the MarkdownRenderer module.

Each test targets one rendering feature from requirements R2/R3.
"""

import pytest
from markdown_renderer import MarkdownRenderer


@pytest.fixture(scope="module")
def renderer():
    return MarkdownRenderer()


# ---------------------------------------------------------------------------
# R2 — Text rendering
# ---------------------------------------------------------------------------
class TestHeadings:
    def test_h1(self, renderer):
        html = renderer.render("# Hello", "s1")
        assert "<h1>" in html or "<h1 " in html

    def test_h5(self, renderer):
        html = renderer.render("##### Level 5", "s1")
        assert "<h5>" in html or "<h5 " in html

    def test_h6(self, renderer):
        html = renderer.render("###### Level 6", "s1")
        assert "<h6>" in html or "<h6 " in html


class TestInlineFormatting:
    def test_bold(self, renderer):
        html = renderer.render("**bold**", "s1")
        assert "<strong>" in html

    def test_italic(self, renderer):
        html = renderer.render("*italic*", "s1")
        assert "<em>" in html

    def test_bold_italic(self, renderer):
        html = renderer.render("***both***", "s1")
        assert "<strong>" in html and "<em>" in html

    def test_strikethrough(self, renderer):
        html = renderer.render("~~struck~~", "s1")
        assert "<del>" in html

    def test_inline_code(self, renderer):
        html = renderer.render("`code`", "s1")
        assert "<code>" in html

    def test_link(self, renderer):
        html = renderer.render("[text](https://example.com)", "s1")
        assert 'href="https://example.com"' in html
        assert "text" in html


class TestHTMLPassthrough:
    def test_sub(self, renderer):
        html = renderer.render("H<sub>2</sub>O", "s1")
        assert "<sub>" in html

    def test_sup(self, renderer):
        html = renderer.render("x<sup>2</sup>", "s1")
        assert "<sup>" in html

    def test_br(self, renderer):
        html = renderer.render("line1<br>line2", "s1")
        assert "<br" in html


class TestLineBreaks:
    def test_manual_newline_becomes_br(self, renderer):
        """Single newline inside a paragraph should produce <br>."""
        html = renderer.render("line one\nline two", "s1")
        assert "<br" in html


# ---------------------------------------------------------------------------
# R3 — Block elements
# ---------------------------------------------------------------------------
class TestLists:
    def test_unordered_list(self, renderer):
        html = renderer.render("- item 1\n- item 2", "s1")
        assert "<ul>" in html
        assert "<li>" in html

    def test_ordered_list(self, renderer):
        html = renderer.render("1. first\n2. second", "s1")
        assert "<ol>" in html


class TestBlockquotes:
    def test_blockquote(self, renderer):
        html = renderer.render("> A wise quote", "s1")
        assert "<blockquote>" in html

    def test_blockquote_with_attribution(self, renderer):
        md = "> The best way to predict the future is to invent it.\n\n-- Alan Kay"
        html = renderer.render(md, "s1")
        assert "<blockquote>" in html
        assert "<cite>" in html
        assert "Alan Kay" in html

    def test_blockquote_without_attribution(self, renderer):
        md = "> Just a regular quote.\n\nSome other text."
        html = renderer.render(md, "s1")
        assert "<blockquote>" in html
        assert "<cite>" not in html

    def test_blockquote_cite_inside_blockquote(self, renderer):
        """The <cite> element must be a child of the <blockquote>."""
        md = "> Simplicity is prerequisite for reliability.\n\n-- Edsger Dijkstra"
        html = renderer.render(md, "s1")
        import re
        bq = re.search(r"<blockquote>(.*?)</blockquote>", html, re.DOTALL)
        assert bq is not None
        assert "<cite>" in bq.group(1)


class TestTables:
    def test_pipe_table(self, renderer):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        html = renderer.render(md, "s1")
        assert "<table>" in html
        assert "<td>" in html

    def test_table_alignment(self, renderer):
        md = "| Left | Center | Right |\n|:-----|:------:|------:|\n| a | b | c |"
        html = renderer.render(md, "s1")
        assert 'text-align: right' in html or 'style="text-align: right' in html


# ---------------------------------------------------------------------------
# Sanitizer allowlist
# ---------------------------------------------------------------------------
class TestSanitizer:
    def test_safe_tags_preserved(self, renderer):
        for tag in ("sub", "sup", "br"):
            html = renderer.render(f"<{tag}>", "s1")
            assert f"<{tag}" in html, f"<{tag}> should not be stripped"

    def test_script_stripped(self, renderer):
        """Dangerous tags must be stripped."""
        html = renderer.render("<script>alert(1)</script>", "s1")
        assert "<script>" not in html
