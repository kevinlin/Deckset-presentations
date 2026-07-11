"""
Code highlighting processor for the Deckset Website Generator.

This module handles advanced code highlighting with line emphasis features,
supporting Deckset-specific code block directives and syntax highlighting.
"""

import re
from typing import Set, List, Optional, Tuple
from dataclasses import dataclass
from models import HighlightConfig, ProcessedCodeBlock, DecksetParsingError


class CodeProcessor:
    """Processor for code blocks with syntax highlighting and line emphasis."""
    
    def __init__(self):
        """Initialize the code processor."""
        self.supported_languages = {
            'python', 'javascript', 'typescript', 'java', 'cpp', 'c', 'csharp',
            'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'scala', 'html',
            'css', 'scss', 'sass', 'json', 'xml', 'yaml', 'yml', 'markdown',
            'md', 'bash', 'shell', 'sh', 'sql', 'dockerfile', 'makefile'
        }
        
        # Regex pattern for Deckset code highlight directive
        self.highlight_directive_pattern = re.compile(
            r'\[\.code-highlight:\s*([^\]]+)\]',
            re.IGNORECASE
        )
    
    def process_code_block(self, code_content: str, language: str, highlight_config: str = "") -> ProcessedCodeBlock:
        """
        Process a code block with language-specific highlighting.
        
        Args:
            code_content: The raw code content
            language: Programming language for syntax highlighting
            highlight_config: Highlight configuration string (e.g., "1-3,5")
            
        Returns:
            ProcessedCodeBlock with highlighting information
            
        Raises:
            DecksetParsingError: If highlight configuration is invalid
        """
        # Normalize language identifier
        normalized_language = self._normalize_language(language)
        
        # Parse highlight configuration
        highlight_cfg = self.parse_highlight_directive(highlight_config)
        
        # Apply syntax highlighting
        highlighted_content = self.apply_syntax_highlighting(code_content, normalized_language)
        
        # Apply line highlighting
        final_content = self.apply_line_highlighting(highlighted_content, highlight_cfg)
        
        return ProcessedCodeBlock(
            content=final_content,
            language=normalized_language,
            highlighted_lines=highlight_cfg.highlighted_lines,
            line_numbers=len(highlight_cfg.highlighted_lines) > 0
        )
    
    def parse_deckset_highlight_directive(self, slide_content: str) -> Tuple[str, HighlightConfig]:
        """
        Parse Deckset-style code highlight directive from slide content.
        
        Looks for patterns like [.code-highlight: 1,3-5] before code blocks
        and removes them from the content while returning the configuration.
        
        Args:
            slide_content: Full slide content that may contain highlight directives
            
        Returns:
            Tuple of (cleaned_content, highlight_config)
        """
        # Find all highlight directives
        matches = list(self.highlight_directive_pattern.finditer(slide_content))
        
        if not matches:
            return slide_content, HighlightConfig(highlighted_lines=set(), highlight_type="none")
        
        # Use the last directive found (in case there are multiple)
        last_match = matches[-1]
        directive_text = last_match.group(1).strip()
        
        # Remove all highlight directives from content
        cleaned_content = self.highlight_directive_pattern.sub('', slide_content).strip()
        
        # Parse the directive
        highlight_config = self.parse_highlight_directive(directive_text)
        
        return cleaned_content, highlight_config
    
    def parse_highlight_directive(self, directive: str) -> HighlightConfig:
        """
        Parse highlight directive from Deckset syntax.
        
        Supports formats:
        - "N" (single line)
        - "X-Y" (range)
        - "X,Y,Z" (multiple lines)
        - "X-Y,Z" (mixed)
        - "all" (all lines)
        - "none" or "" (no highlighting)
        
        Args:
            directive: Highlight directive string
            
        Returns:
            HighlightConfig with parsed settings
            
        Raises:
            DecksetParsingError: If directive format is invalid
        """
        if not directive or directive.strip().lower() == "none":
            return HighlightConfig(highlighted_lines=set(), highlight_type="none")
        
        directive = directive.strip().lower()
        
        if directive == "all":
            return HighlightConfig(highlighted_lines=set(), highlight_type="all")
        
        highlighted_lines = set()
        
        try:
            # Split by commas for multiple specifications
            parts = [part.strip() for part in directive.split(',')]
            
            for part in parts:
                if '-' in part:
                    # Handle range (e.g., "1-5")
                    start_str, end_str = part.split('-', 1)
                    start = int(start_str.strip())
                    end = int(end_str.strip())
                    
                    if start > end:
                        raise ValueError(f"Invalid range: {part} (start > end)")
                    
                    highlighted_lines.update(range(start, end + 1))
                else:
                    # Handle single line number
                    line_num = int(part)
                    if line_num <= 0:
                        raise ValueError(f"Line numbers must be positive: {line_num}")
                    highlighted_lines.add(line_num)
        
        except ValueError as e:
            raise DecksetParsingError(
                f"Invalid highlight directive '{directive}': {str(e)}",
                context={"directive": directive},
            )
        
        return HighlightConfig(
            highlighted_lines=highlighted_lines,
            highlight_type="lines" if highlighted_lines else "none"
        )
    
    def apply_syntax_highlighting(self, code: str, language: str) -> str:
        """
        Apply syntax highlighting to code content.
        
        This method prepares the code for highlight.js integration by wrapping
        it in appropriate HTML structure with language classes.
        
        Args:
            code: Raw code content
            language: Programming language identifier
            
        Returns:
            HTML-wrapped code ready for highlight.js
        """
        # Escape HTML entities in code
        escaped_code = self._escape_html(code)
        
        # Determine highlight.js language class
        hljs_language = self._get_hljs_language_class(language)
        
        # Wrap in pre/code structure for highlight.js
        return f'<pre><code class="language-{hljs_language}">{escaped_code}</code></pre>'
    
    # Matches a [.code-highlight:] line optionally followed by blank lines and
    # then a fenced code block.  The directive is consumed and its config is
    # applied only to the immediately following block.
    _DIRECTIVE_THEN_FENCE_RE = re.compile(
        r'\[\.code-highlight:\s*([^\]]+)\]\s*\n'   # directive line
        r'(```(\w*)\n(.*?)\n```)',                  # fenced block
        re.DOTALL | re.IGNORECASE,
    )
    _BARE_FENCE_RE = re.compile(r'```(\w*)\n(.*?)\n```', re.DOTALL)

    def process_code_block_with_deckset_directive(
        self, slide_content: str, default_language: str = ""
    ) -> Tuple[str, List[ProcessedCodeBlock]]:
        """Process code blocks in slide content with Deckset highlight directives.

        Each ``[.code-highlight:]`` directive is associated with the fenced code
        block it immediately precedes.  If multiple directives appear before the
        same block the last one wins.  Code blocks without a preceding directive
        receive no line highlighting.
        """
        processed_blocks: List[ProcessedCodeBlock] = []
        placeholders: dict = {}
        counter = [0]

        def _placeholder() -> str:
            counter[0] += 1
            return f"\x00CODEBLOCK{counter[0]}\x00"

        # Pass 1 — directive+block pairs (placeholder replaces HTML output)
        def _replace_directive_block(match: re.Match) -> str:
            directive_text = match.group(1).strip()
            language = match.group(3) or default_language
            code_content = match.group(4)
            block = self.process_code_block(code_content, language, directive_text)
            processed_blocks.append(block)
            ph = _placeholder()
            placeholders[ph] = block.content
            return ph

        result = self._DIRECTIVE_THEN_FENCE_RE.sub(_replace_directive_block, slide_content)

        # Pass 2 — remaining bare fences (no directive)
        def _replace_bare_fence(match: re.Match) -> str:
            language = match.group(1) or default_language
            code_content = match.group(2)
            block = self.process_code_block(code_content, language, "")
            processed_blocks.append(block)
            ph = _placeholder()
            placeholders[ph] = block.content
            return ph

        result = self._BARE_FENCE_RE.sub(_replace_bare_fence, result)

        # Pass 3 — indented code blocks (safe now; placeholders contain no spaces)
        indented_pattern = re.compile(
            r'(?:(?<=\n)|^)((?:(?: {4}|\t).*(?:\n|$))+)', re.MULTILINE
        )

        def _strip_indent(line: str) -> str:
            if line.startswith('    '):
                return line[4:]
            if line.startswith('\t'):
                return line[1:]
            return line

        def _is_probably_list_item(line: str) -> bool:
            core = _strip_indent(line).lstrip()
            return (
                core.startswith('- ') or core.startswith('* ')
                or core.startswith('+ ') or bool(re.match(r'^\d+\.\s', core))
            )

        def _replace_indented(match: re.Match) -> str:
            block = match.group(1)
            lines = [ln for ln in block.split('\n') if ln.strip() != '']
            if not lines:
                return block
            if all(_is_probably_list_item(ln) for ln in lines):
                return block
            stripped = [_strip_indent(ln) for ln in block.split('\n')]
            code_content = '\n'.join(stripped).strip('\n')
            pb = self.process_code_block(code_content, default_language or "text", "")
            processed_blocks.append(pb)
            ph = _placeholder()
            placeholders[ph] = pb.content
            return ph + "\n"

        result = indented_pattern.sub(_replace_indented, result)

        # Restore placeholders and clean up orphaned directives
        for ph, html in placeholders.items():
            result = result.replace(ph, html)
        result = self.highlight_directive_pattern.sub('', result).strip()

        return result, processed_blocks
    
    def apply_line_highlighting(self, code: str, highlight_config: HighlightConfig) -> str:
        """Apply per-line highlighting spans.

        Emits ``<span class="line-highlight">`` only on highlighted lines.
        Non-highlighted lines are left as plain text (tokenization is
        client-side highlight.js only).
        """
        if highlight_config.highlight_type == "none":
            return code

        code_match = re.search(r'<code[^>]*>(.*?)</code>', code, re.DOTALL)
        if not code_match:
            return code

        code_content = code_match.group(1)
        code_lines = code_content.split('\n')
        out_lines: list = []

        for i, line in enumerate(code_lines, 1):
            if highlight_config.highlight_type == "all" or i in highlight_config.highlighted_lines:
                out_lines.append(f'<span class="line-highlight">{line}</span>')
            else:
                out_lines.append(line)

        enhanced = code.replace(code_content, '\n'.join(out_lines))
        enhanced = enhanced.replace(
            '<pre>',
            f'<pre data-highlight-type="{highlight_config.highlight_type}">',
            1,
        )
        return enhanced
    
    def _normalize_language(self, language: str) -> str:
        """
        Normalize language identifier to supported format.
        
        Args:
            language: Raw language identifier
            
        Returns:
            Normalized language identifier
        """
        if not language:
            return "text"
        
        # Convert to lowercase and handle common aliases
        lang = language.lower().strip()
        
        # Language aliases mapping
        aliases = {
            'js': 'javascript',
            'ts': 'typescript',
            'py': 'python',
            'rb': 'ruby',
            'cs': 'csharp',
            'c++': 'cpp',
            'c#': 'csharp',
            'sh': 'bash',
            'zsh': 'bash',
            'fish': 'bash',
            'yml': 'yaml',
            'md': 'markdown'
        }
        
        normalized = aliases.get(lang, lang)
        
        # Return normalized language if supported, otherwise 'text'
        return normalized if normalized in self.supported_languages else "text"
    
    def _get_hljs_language_class(self, language: str) -> str:
        """
        Get the appropriate highlight.js language class.
        
        Args:
            language: Normalized language identifier
            
        Returns:
            Highlight.js language class name
        """
        # Map internal language names to highlight.js classes
        hljs_mapping = {
            'csharp': 'cs',
            'cpp': 'cpp',
            'dockerfile': 'docker',
            'makefile': 'makefile'
        }
        
        return hljs_mapping.get(language, language)
    
    def _highlight_config_to_string(self, config: HighlightConfig) -> str:
        """
        Convert HighlightConfig back to string format for processing.
        
        Args:
            config: HighlightConfig object
            
        Returns:
            String representation of highlight configuration
        """
        if config.highlight_type == "none":
            return ""
        elif config.highlight_type == "all":
            return "all"
        else:
            # Convert set of lines back to string format
            if not config.highlighted_lines:
                return ""
            
            sorted_lines = sorted(config.highlighted_lines)
            ranges = []
            start = sorted_lines[0]
            end = start
            
            for line in sorted_lines[1:]:
                if line == end + 1:
                    end = line
                else:
                    if start == end:
                        ranges.append(str(start))
                    else:
                        ranges.append(f"{start}-{end}")
                    start = end = line
            
            # Add the last range
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            
            return ",".join(ranges)
    
    def _escape_html(self, text: str) -> str:
        """
        Escape HTML entities in text.
        
        Args:
            text: Raw text content
            
        Returns:
            HTML-escaped text
        """
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))