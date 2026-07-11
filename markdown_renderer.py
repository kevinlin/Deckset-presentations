"""MarkdownRenderer — one configured python-markdown instance for slide bodies.

Provides ``render(text, slide_id)`` and ``render_with_footnotes(text, slide_id)``
which return body HTML (and optionally footnotes HTML).  The instance is reset
per call so extension state never leaks between slides.

Extensions enabled:
  tables, footnotes, nl2br, pymdownx.tilde (~~del~~), pymdownx.caret (^sup^).

A lightweight sanitizer strips dangerous tags while preserving safe HTML
that Deckset authors expect (sub, sup, br, cite, mark, a).
"""

import logging
import re
from typing import Tuple

import markdown
from markdown.extensions.footnotes import FootnoteExtension

logger = logging.getLogger(__name__)

# Tags that are safe for slide content
_SAFE_TAGS = frozenset({
    "a", "abbr", "b", "blockquote", "br", "cite", "code", "dd", "del",
    "div", "dl", "dt", "em", "h1", "h2", "h3", "h4", "h5", "h6", "hr",
    "i", "img", "ins", "kbd", "li", "mark", "ol", "p", "pre", "q", "s",
    "small", "span", "strong", "sub", "sup", "table", "tbody", "td",
    "tfoot", "th", "thead", "tr", "u", "ul",
})

_SAFE_ATTRS = frozenset({
    "href", "src", "alt", "title", "class", "id", "style", "target",
    "rel", "colspan", "rowspan", "scope", "align", "name",
})

_STRIP_RE = re.compile(
    r"<(?P<closing>/?)(?P<tag>[a-zA-Z][a-zA-Z0-9]*)"
    r"(?P<attrs>[^>]*)>",
)


def _sanitize(html: str) -> str:
    """Strip tags not on the safe-list; keep their inner content."""

    def _repl(m: re.Match) -> str:
        tag = m.group("tag").lower()
        if tag not in _SAFE_TAGS:
            return ""
        closing = m.group("closing")
        if closing:
            return f"</{tag}>"
        attrs_str = m.group("attrs").strip()
        if not attrs_str:
            return f"<{tag}>"
        safe_parts: list[str] = []
        for attr_m in re.finditer(
            r'([a-zA-Z\-]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|(\S+))', attrs_str
        ):
            name = attr_m.group(1).lower()
            val = attr_m.group(2) or attr_m.group(3) or attr_m.group(4) or ""
            if name in _SAFE_ATTRS:
                safe_parts.append(f'{name}="{val}"')
        attr_out = (" " + " ".join(safe_parts)) if safe_parts else ""
        # Self-closing tags
        if attrs_str.rstrip().endswith("/"):
            return f"<{tag}{attr_out} />"
        return f"<{tag}{attr_out}>"

    return _STRIP_RE.sub(_repl, html)


class MarkdownRenderer:
    """Render slide body markdown to HTML via python-markdown."""

    def __init__(self) -> None:
        self._build_md()

    def _build_md(self) -> markdown.Markdown:
        self._md = markdown.Markdown(
            extensions=[
                "tables",
                "footnotes",
                "nl2br",
                "pymdownx.tilde",
                "pymdownx.caret",
            ],
            extension_configs={
                "footnotes": {
                    "UNIQUE_IDS": True,
                    "BACKLINK_TEXT": "&#8617;",
                },
            },
        )
        return self._md

    def render(self, text: str, slide_id: str) -> str:
        """Render markdown *text* to sanitized HTML for the given slide."""
        self._md.reset()
        raw_html = self._md.convert(text)
        return _sanitize(raw_html)

    def render_with_footnotes(
        self, text: str, slide_id: str
    ) -> Tuple[str, str]:
        """Render and return ``(body_html, footnotes_html)``."""
        self._md.reset()
        raw_html = self._md.convert(text)
        body = _sanitize(raw_html)

        fn_html = ""
        if hasattr(self._md, "footnotes"):
            # The footnotes extension stores definitions internally
            fn_div_match = re.search(
                r'<div class="footnote">.*</div>',
                raw_html,
                re.DOTALL,
            )
            if fn_div_match:
                fn_html = _sanitize(fn_div_match.group(0))
                body = body.replace(fn_div_match.group(0), "")

        return body, fn_html
