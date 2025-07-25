"""
Unit tests for the CodeProcessor class.

Tests code block processing, syntax highlighting, and line highlighting features.
"""

import pytest
from code_processor import CodeProcessor
from enhanced_models import HighlightConfig, ProcessedCodeBlock, DecksetParsingError


class TestCodeProcessor:
    """Test cases for CodeProcessor functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = CodeProcessor()
    
    def test_init(self):
        """Test CodeProcessor initialization."""
        assert self.processor is not None
        assert len(self.processor.supported_languages) > 0
        assert 'python' in self.processor.supported_languages
        assert 'javascript' in self.processor.supported_languages
    
    def test_process_code_block_basic(self):
        """Test basic code block processing."""
        code = "print('Hello, World!')"
        language = "python"
        
        result = self.processor.process_code_block(code, language)
        
        assert isinstance(result, ProcessedCodeBlock)
        assert result.language == "python"
        assert result.highlighted_lines == set()
        assert result.line_numbers is False
        assert '<code class="language-python">' in result.content
    
    def test_process_code_block_with_highlighting(self):
        """Test code block processing with line highlighting."""
        code = "def hello():\n    print('Hello')\n    return True"
        language = "python"
        highlight_config = "1,3"
        
        result = self.processor.process_code_block(code, language, highlight_config)
        
        assert result.language == "python"
        assert result.highlighted_lines == {1, 3}
        assert result.line_numbers is True
        assert 'class="code-line code-line-highlighted"' in result.content
    
    def test_process_code_block_invalid_highlight(self):
        """Test code block processing with invalid highlight configuration."""
        code = "print('test')"
        language = "python"
        highlight_config = "invalid"
        
        with pytest.raises(DecksetParsingError):
            self.processor.process_code_block(code, language, highlight_config)
    
    def test_parse_highlight_directive_none(self):
        """Test parsing empty or 'none' highlight directive."""
        result = self.processor.parse_highlight_directive("")
        assert result.highlight_type == "none"
        assert result.highlighted_lines == set()
        
        result = self.processor.parse_highlight_directive("none")
        assert result.highlight_type == "none"
        assert result.highlighted_lines == set()
    
    def test_parse_highlight_directive_all(self):
        """Test parsing 'all' highlight directive."""
        result = self.processor.parse_highlight_directive("all")
        assert result.highlight_type == "all"
        assert result.highlighted_lines == set()
    
    def test_parse_highlight_directive_single_line(self):
        """Test parsing single line highlight directive."""
        result = self.processor.parse_highlight_directive("5")
        assert result.highlight_type == "lines"
        assert result.highlighted_lines == {5}
    
    def test_parse_highlight_directive_range(self):
        """Test parsing range highlight directive."""
        result = self.processor.parse_highlight_directive("2-5")
        assert result.highlight_type == "lines"
        assert result.highlighted_lines == {2, 3, 4, 5}
    
    def test_parse_highlight_directive_multiple_lines(self):
        """Test parsing multiple lines highlight directive."""
        result = self.processor.parse_highlight_directive("1,3,5")
        assert result.highlight_type == "lines"
        assert result.highlighted_lines == {1, 3, 5}
    
    def test_parse_highlight_directive_mixed(self):
        """Test parsing mixed highlight directive."""
        result = self.processor.parse_highlight_directive("1,3-5,8")
        assert result.highlight_type == "lines"
        assert result.highlighted_lines == {1, 3, 4, 5, 8}
    
    def test_parse_highlight_directive_invalid_range(self):
        """Test parsing invalid range highlight directive."""
        with pytest.raises(DecksetParsingError):
            self.processor.parse_highlight_directive("5-2")
    
    def test_parse_highlight_directive_invalid_format(self):
        """Test parsing invalid format highlight directive."""
        with pytest.raises(DecksetParsingError):
            self.processor.parse_highlight_directive("abc")
    
    def test_parse_highlight_directive_zero_line(self):
        """Test parsing zero line number."""
        with pytest.raises(DecksetParsingError):
            self.processor.parse_highlight_directive("0")
    
    def test_parse_highlight_directive_negative_line(self):
        """Test parsing negative line number."""
        with pytest.raises(DecksetParsingError):
            self.processor.parse_highlight_directive("-1")
    
    def test_apply_syntax_highlighting_python(self):
        """Test syntax highlighting for Python code."""
        code = "def hello():\n    print('Hello')"
        result = self.processor.apply_syntax_highlighting(code, "python")
        
        assert '<pre><code class="language-python">' in result
        assert '</code></pre>' in result
        assert 'def hello():' in result
        assert 'print(&#x27;Hello&#x27;)' in result  # HTML escaped
    
    def test_apply_syntax_highlighting_javascript(self):
        """Test syntax highlighting for JavaScript code."""
        code = "function hello() {\n    console.log('Hello');\n}"
        result = self.processor.apply_syntax_highlighting(code, "javascript")
        
        assert '<pre><code class="language-javascript">' in result
        assert 'function hello()' in result
        assert 'console.log(&#x27;Hello&#x27;);' in result
    
    def test_apply_syntax_highlighting_html_escape(self):
        """Test HTML escaping in syntax highlighting."""
        code = "if x < 5 && y > 3:\n    print('<tag>')"
        result = self.processor.apply_syntax_highlighting(code, "python")
        
        assert '&lt;' in result
        assert '&gt;' in result
        assert '&amp;&amp;' in result
        assert '&lt;tag&gt;' in result
    
    def test_apply_line_highlighting_none(self):
        """Test line highlighting with no highlighting."""
        code = '<pre><code class="language-python">line1\nline2\nline3</code></pre>'
        config = HighlightConfig(highlighted_lines=set(), highlight_type="none")
        
        result = self.processor.apply_line_highlighting(code, config)
        # Should wrap lines but not add highlighting classes
        assert 'class="code-line" data-line="1"' in result
        assert 'class="code-line" data-line="2"' in result
        assert 'class="code-line" data-line="3"' in result
        assert 'code-line-highlighted' not in result
        assert 'code-block-with-highlighting' not in result
    
    def test_apply_line_highlighting_specific_lines(self):
        """Test line highlighting with specific lines."""
        code = '<pre><code class="language-python">line1\nline2\nline3</code></pre>'
        config = HighlightConfig(highlighted_lines={1, 3}, highlight_type="lines")
        
        result = self.processor.apply_line_highlighting(code, config)
        
        assert 'class="code-line code-line-highlighted" data-line="1"' in result
        assert 'class="code-line" data-line="2"' in result
        assert 'class="code-line code-line-highlighted" data-line="3"' in result
        assert 'data-highlight="true"' in result
        assert 'data-highlight="false"' in result
        assert 'class="code-block-with-highlighting"' in result
    
    def test_apply_line_highlighting_all_lines(self):
        """Test line highlighting with all lines highlighted."""
        code = '<pre><code class="language-python">line1\nline2</code></pre>'
        config = HighlightConfig(highlighted_lines=set(), highlight_type="all")
        
        result = self.processor.apply_line_highlighting(code, config)
        
        assert 'class="code-line code-line-highlighted" data-line="1"' in result
        assert 'class="code-line code-line-highlighted" data-line="2"' in result
        assert result.count('data-highlight="true"') == 2
        assert 'class="code-block-with-highlighting"' in result
    
    def test_normalize_language_basic(self):
        """Test basic language normalization."""
        assert self.processor._normalize_language("Python") == "python"
        assert self.processor._normalize_language("JAVASCRIPT") == "javascript"
        assert self.processor._normalize_language("  TypeScript  ") == "typescript"
    
    def test_normalize_language_aliases(self):
        """Test language alias normalization."""
        assert self.processor._normalize_language("js") == "javascript"
        assert self.processor._normalize_language("ts") == "typescript"
        assert self.processor._normalize_language("py") == "python"
        assert self.processor._normalize_language("rb") == "ruby"
        assert self.processor._normalize_language("cs") == "csharp"
        assert self.processor._normalize_language("c++") == "cpp"
        assert self.processor._normalize_language("c#") == "csharp"
        assert self.processor._normalize_language("sh") == "bash"
        assert self.processor._normalize_language("yml") == "yaml"
        assert self.processor._normalize_language("md") == "markdown"
    
    def test_normalize_language_unsupported(self):
        """Test normalization of unsupported languages."""
        assert self.processor._normalize_language("unknown") == "text"
        assert self.processor._normalize_language("") == "text"
        assert self.processor._normalize_language(None) == "text"
    
    def test_get_hljs_language_class(self):
        """Test highlight.js language class mapping."""
        assert self.processor._get_hljs_language_class("python") == "python"
        assert self.processor._get_hljs_language_class("javascript") == "javascript"
        assert self.processor._get_hljs_language_class("csharp") == "cs"
        assert self.processor._get_hljs_language_class("cpp") == "cpp"
        assert self.processor._get_hljs_language_class("dockerfile") == "docker"
    
    def test_escape_html(self):
        """Test HTML escaping functionality."""
        text = "if x < 5 && y > 3 && z == \"test\" && w == 'value':"
        result = self.processor._escape_html(text)
        
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&amp;&amp;" in result
        assert "&quot;" in result
        assert "&#x27;" in result
        assert result == "if x &lt; 5 &amp;&amp; y &gt; 3 &amp;&amp; z == &quot;test&quot; &amp;&amp; w == &#x27;value&#x27;:"
    
    def test_supported_languages_coverage(self):
        """Test that all major languages are supported."""
        expected_languages = {
            'python', 'javascript', 'typescript', 'java', 'cpp', 'c', 'csharp',
            'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'html', 'css',
            'json', 'xml', 'yaml', 'markdown', 'bash', 'sql'
        }
        
        for lang in expected_languages:
            assert lang in self.processor.supported_languages
    
    def test_parse_deckset_highlight_directive_basic(self):
        """Test parsing basic Deckset highlight directive."""
        content = "[.code-highlight: 1,3]\n```python\nprint('hello')\n```"
        
        cleaned_content, config = self.processor.parse_deckset_highlight_directive(content)
        
        assert "[.code-highlight:" not in cleaned_content
        assert config.highlight_type == "lines"
        assert config.highlighted_lines == {1, 3}
    
    def test_parse_deckset_highlight_directive_all(self):
        """Test parsing 'all' Deckset highlight directive."""
        content = "[.code-highlight: all]\n```python\ncode here\n```"
        
        cleaned_content, config = self.processor.parse_deckset_highlight_directive(content)
        
        assert config.highlight_type == "all"
        assert config.highlighted_lines == set()
    
    def test_parse_deckset_highlight_directive_none(self):
        """Test parsing 'none' Deckset highlight directive."""
        content = "[.code-highlight: none]\n```python\ncode here\n```"
        
        cleaned_content, config = self.processor.parse_deckset_highlight_directive(content)
        
        assert config.highlight_type == "none"
    
    def test_parse_deckset_highlight_directive_no_directive(self):
        """Test content without highlight directive."""
        content = "```python\nprint('hello')\n```"
        
        cleaned_content, config = self.processor.parse_deckset_highlight_directive(content)
        
        assert cleaned_content == content
        assert config.highlight_type == "none"
    
    def test_parse_deckset_highlight_directive_multiple(self):
        """Test content with multiple highlight directives (uses last one)."""
        content = "[.code-highlight: 1]\n[.code-highlight: 2,3]\n```python\ncode\n```"
        
        cleaned_content, config = self.processor.parse_deckset_highlight_directive(content)
        
        assert "[.code-highlight:" not in cleaned_content
        assert config.highlighted_lines == {2, 3}
    
    def test_process_code_block_with_deckset_directive(self):
        """Test processing code blocks with Deckset directives."""
        content = "[.code-highlight: 1,3]\n```python\ndef hello():\n    print('hi')\n    return True\n```"
        
        processed_content, blocks = self.processor.process_code_block_with_deckset_directive(content)
        
        assert len(blocks) == 1
        assert blocks[0].language == "python"
        assert blocks[0].highlighted_lines == {1, 3}
        assert 'class="code-line code-line-highlighted"' in processed_content
    
    def test_apply_line_highlighting_enhanced_classes(self):
        """Test enhanced line highlighting with better CSS classes."""
        code = '<pre><code class="language-python">line1\nline2\nline3</code></pre>'
        config = HighlightConfig(highlighted_lines={1, 3}, highlight_type="lines")
        
        result = self.processor.apply_line_highlighting(code, config)
        
        assert 'class="code-line code-line-highlighted"' in result
        assert 'data-highlight="true"' in result
        assert 'data-highlight="false"' in result
        assert 'class="code-block-with-highlighting"' in result
        assert 'data-highlight-type="lines"' in result
    
    def test_apply_line_highlighting_all_enhanced(self):
        """Test enhanced line highlighting with all lines."""
        code = '<pre><code class="language-python">line1\nline2</code></pre>'
        config = HighlightConfig(highlighted_lines=set(), highlight_type="all")
        
        result = self.processor.apply_line_highlighting(code, config)
        
        assert result.count('class="code-line code-line-highlighted"') == 2
        assert result.count('data-highlight="true"') == 2
        assert 'data-highlight-type="all"' in result
    
    def test_wrap_lines_for_styling(self):
        """Test wrapping lines for consistent styling."""
        code = '<pre><code class="language-python">line1\nline2\nline3</code></pre>'
        
        result = self.processor._wrap_lines_for_styling(code)
        
        assert 'class="code-line" data-line="1"' in result
        assert 'class="code-line" data-line="2"' in result
        assert 'class="code-line" data-line="3"' in result
        assert result.count('class="code-line"') == 3
    
    def test_highlight_config_to_string(self):
        """Test converting HighlightConfig back to string format."""
        # Test single lines
        config = HighlightConfig(highlighted_lines={1, 3, 5}, highlight_type="lines")
        result = self.processor._highlight_config_to_string(config)
        assert result == "1,3,5"
        
        # Test ranges
        config = HighlightConfig(highlighted_lines={1, 2, 3, 5, 6, 8}, highlight_type="lines")
        result = self.processor._highlight_config_to_string(config)
        assert result == "1-3,5-6,8"
        
        # Test all
        config = HighlightConfig(highlighted_lines=set(), highlight_type="all")
        result = self.processor._highlight_config_to_string(config)
        assert result == "all"
        
        # Test none
        config = HighlightConfig(highlighted_lines=set(), highlight_type="none")
        result = self.processor._highlight_config_to_string(config)
        assert result == ""
    
    def test_integration_full_processing(self):
        """Test full integration of code processing features."""
        code = """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))"""
        
        result = self.processor.process_code_block(code, "python", "1,3-4")
        
        # Check basic properties
        assert result.language == "python"
        assert result.highlighted_lines == {1, 3, 4}
        assert result.line_numbers is True
        
        # Check enhanced content structure
        assert '<pre class="code-block-with-highlighting"' in result.content
        assert 'data-highlight-type="lines"' in result.content
        assert 'class="code-line code-line-highlighted"' in result.content
        assert 'data-highlight="true"' in result.content
        assert 'data-highlight="false"' in result.content
        
        # Check HTML escaping
        assert '&lt;=' in result.content
    
    def test_integration_deckset_directive_processing(self):
        """Test full integration with Deckset directive processing."""
        slide_content = """# My Slide

[.code-highlight: 1,3-4]

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
```

Some text after code."""
        
        processed_content, blocks = self.processor.process_code_block_with_deckset_directive(slide_content, "text")
        
        # Check that directive was removed
        assert "[.code-highlight:" not in processed_content
        
        # Check that code block was processed
        assert len(blocks) == 1
        assert blocks[0].language == "python"
        assert blocks[0].highlighted_lines == {1, 3, 4}
        
        # Check that processed content contains enhanced highlighting
        assert 'class="code-line code-line-highlighted"' in processed_content
        assert 'data-highlight="true"' in processed_content