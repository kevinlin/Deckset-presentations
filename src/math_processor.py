"""
Mathematical formula processor for Deckset Website Generator.

This module handles the processing of mathematical formulas in Deckset markdown,
including LaTeX syntax parsing, MathJax integration, and responsive rendering.
"""

import re
import logging
from typing import List, Tuple, Optional
from models import MathFormula, DecksetParsingError


class MathProcessor:
    """
    Processor for mathematical formulas with MathJax integration.
    
    Handles both display math ($$...$$) and inline math ($...$) delimiters,
    validates LaTeX syntax, and provides configuration for responsive rendering.
    """
    
    def __init__(self):
        """Initialize the MathProcessor."""
        self.logger = logging.getLogger(__name__)
        
        # Regex patterns for math detection
        self.display_math_pattern = re.compile(r'\$\$([^$]+?)\$\$', re.DOTALL)
        self.inline_math_pattern = re.compile(r'(?<!\$)\$([^$\n]+?)\$(?!\$)')
        
        # Common LaTeX commands for basic validation
        self.common_latex_commands = {
            'frac', 'sqrt', 'sum', 'int', 'lim', 'sin', 'cos', 'tan', 'log', 'ln',
            'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'theta', 'lambda', 'mu',
            'pi', 'sigma', 'phi', 'psi', 'omega', 'infty', 'partial', 'nabla',
            'cdot', 'times', 'div', 'pm', 'mp', 'leq', 'geq', 'neq', 'approx',
            'equiv', 'subset', 'supset', 'in', 'notin', 'cup', 'cap', 'emptyset',
            'mathbb', 'mathcal', 'mathfrak', 'mathrm', 'mathbf', 'mathit',
            'left', 'right', 'begin', 'end', 'text', 'textbf', 'textit'
        }
    
    def process_math_formulas(self, content: str) -> Tuple[str, List[MathFormula]]:
        """
        Process mathematical formulas in content and return modified content with formula list.
        
        Args:
            content: Markdown content containing math formulas
            
        Returns:
            Tuple of (processed_content, list_of_math_formulas)
        """
        formulas = []
        processed_content = content
        
        # Process display math first ($$...$$)
        display_formulas = self.extract_display_math(content)
        formulas.extend(display_formulas)
        
        # Replace display math with placeholders
        for i, formula in enumerate(display_formulas):
            placeholder = f"__DISPLAY_MATH_{i}__"
            processed_content = processed_content.replace(
                f"$${formula.content}$$", placeholder, 1
            )
        
        # Process inline math ($...$)
        inline_formulas = self.extract_inline_math(processed_content)
        formulas.extend(inline_formulas)
        
        # Replace inline math with placeholders
        for i, formula in enumerate(inline_formulas):
            placeholder = f"__INLINE_MATH_{i}__"
            processed_content = processed_content.replace(
                f"${formula.content}$", placeholder, 1
            )
        
        # Replace placeholders with proper MathJax syntax
        for i, formula in enumerate(display_formulas):
            placeholder = f"__DISPLAY_MATH_{i}__"
            mathjax_syntax = f"\\[{formula.content}\\]"
            processed_content = processed_content.replace(placeholder, mathjax_syntax)
        
        for i, formula in enumerate(inline_formulas):
            placeholder = f"__INLINE_MATH_{i}__"
            mathjax_syntax = f"\\({formula.content}\\)"
            processed_content = processed_content.replace(placeholder, mathjax_syntax)
        
        # Sort formulas by position for consistent ordering
        all_formulas = sorted(formulas, key=lambda f: f.position)
        
        return processed_content, all_formulas
    
    def extract_display_math(self, content: str) -> List[MathFormula]:
        """
        Extract display math formulas ($$...$$) from content.
        
        Args:
            content: Content to search for display math
            
        Returns:
            List of MathFormula objects for display math
        """
        formulas = []
        
        for match in self.display_math_pattern.finditer(content):
            latex_content = match.group(1).strip()
            position = match.start()
            
            # Validate LaTeX syntax
            is_valid = self.validate_latex_syntax(latex_content)
            
            if not is_valid:
                self.logger.warning(f"Invalid LaTeX syntax in display math at position {position}: {latex_content}")
            
            formula = MathFormula(
                content=latex_content,
                formula_type="display",
                position=position,
                valid=is_valid
            )
            formulas.append(formula)
        
        return formulas
    
    def extract_inline_math(self, content: str) -> List[MathFormula]:
        """
        Extract inline math formulas ($...$) from content.
        
        Args:
            content: Content to search for inline math
            
        Returns:
            List of MathFormula objects for inline math
        """
        formulas = []
        
        for match in self.inline_math_pattern.finditer(content):
            latex_content = match.group(1).strip()
            position = match.start()
            
            # Validate LaTeX syntax
            is_valid = self.validate_latex_syntax(latex_content)
            
            if not is_valid:
                self.logger.warning(f"Invalid LaTeX syntax in inline math at position {position}: {latex_content}")
            
            formula = MathFormula(
                content=latex_content,
                formula_type="inline",
                position=position,
                valid=is_valid
            )
            formulas.append(formula)
        
        return formulas
    
    def validate_latex_syntax(self, latex: str) -> bool:
        """
        Validate basic LaTeX syntax for mathematical formulas.
        
        Args:
            latex: LaTeX content to validate
            
        Returns:
            True if syntax appears valid, False otherwise
        """
        if not latex or not latex.strip():
            return False
        
        # Check for balanced braces
        if not self._check_balanced_braces(latex):
            return False
        
        # Check for balanced environments (begin/end)
        if not self._check_balanced_environments(latex):
            return False
        
        # Check for common syntax errors
        if self._has_common_syntax_errors(latex):
            return False
        
        return True
    
    def _check_balanced_braces(self, latex: str) -> bool:
        """Check if braces are balanced in LaTeX content."""
        brace_count = 0
        i = 0
        
        while i < len(latex):
            if latex[i] == '\\' and i + 1 < len(latex):
                # Skip escaped characters
                i += 2
                continue
            elif latex[i] == '{':
                brace_count += 1
            elif latex[i] == '}':
                brace_count -= 1
                if brace_count < 0:
                    return False
            i += 1
        
        return brace_count == 0
    
    def _check_balanced_environments(self, latex: str) -> bool:
        """Check if begin/end environments are balanced."""
        begin_pattern = re.compile(r'\\begin\{([^}]+)\}')
        end_pattern = re.compile(r'\\end\{([^}]+)\}')
        
        begins = [match.group(1) for match in begin_pattern.finditer(latex)]
        ends = [match.group(1) for match in end_pattern.finditer(latex)]
        
        # Simple check: same number and types of begins and ends
        return sorted(begins) == sorted(ends)
    
    def _has_common_syntax_errors(self, latex: str) -> bool:
        """Check for common LaTeX syntax errors."""
        # Check for unescaped special characters in wrong contexts
        error_patterns = [
            # Only check for & outside of matrix/align environments
            r'(?<!\\)&(?!&)(?![^{]*\\end\{(?:matrix|align|array|tabular)\})',
            r'(?<!\\)%(?![^{]*})',  # Unescaped % outside of commands
            r'\\\\\\',  # Triple backslash (likely error)
            r'\$\$',  # Double dollar signs inside math (nested math)
        ]
        
        # Skip & check if we're in a matrix-like environment
        if re.search(r'\\begin\{(?:matrix|align|array|tabular|cases)\}', latex):
            error_patterns = error_patterns[1:]  # Skip the & pattern
        
        for pattern in error_patterns:
            if re.search(pattern, latex):
                return True
        
        return False
    
    def generate_mathjax_config(self, responsive: bool = True, error_handling: bool = True) -> str:
        """
        Generate MathJax configuration for responsive math rendering.
        
        Args:
            responsive: Enable responsive math scaling and scrolling
            error_handling: Enable enhanced error handling and fallbacks
        
        Returns:
            JavaScript configuration string for MathJax
        """
        responsive_code = ""
        if responsive:
            responsive_code = """
                    // Add responsive behavior for math formulas
                    MathJax.startup.document.addRenderAction('responsive', function() {
                        // Handle display math responsiveness
                        const displays = document.querySelectorAll('.MathJax[display="true"]');
                        displays.forEach(function(display) {
                            const container = display.parentElement;
                            if (container && display.scrollWidth > container.clientWidth) {
                                // Scale down if too wide
                                const scale = Math.min(0.8, container.clientWidth / display.scrollWidth);
                                if (scale < 1) {
                                    display.style.transform = `scale(${scale})`;
                                    display.style.transformOrigin = 'center';
                                    display.style.margin = '0.5em 0';
                                }
                                
                                // Add horizontal scrolling as fallback
                                display.style.overflowX = 'auto';
                                display.style.overflowY = 'hidden';
                                display.style.maxWidth = '100%';
                            }
                        });
                        
                        // Handle inline math responsiveness
                        const inlines = document.querySelectorAll('.MathJax[display="false"]');
                        inlines.forEach(function(inline) {
                            const container = inline.parentElement;
                            if (container && inline.scrollWidth > container.clientWidth * 0.8) {
                                inline.style.fontSize = '0.9em';
                                inline.style.overflowX = 'auto';
                                inline.style.display = 'inline-block';
                                inline.style.maxWidth = '80%';
                            }
                        });
                    });"""
        
        error_handling_code = ""
        if error_handling:
            error_handling_code = """
                    // Enhanced error handling
                    MathJax.startup.document.addRenderAction('errorHandling', function() {
                        // Find and handle math errors
                        const errors = document.querySelectorAll('.MathJax .merror');
                        errors.forEach(function(error) {
                            const mathElement = error.closest('.MathJax');
                            if (mathElement) {
                                // Add error styling
                                mathElement.style.backgroundColor = '#ffebee';
                                mathElement.style.border = '1px solid #f44336';
                                mathElement.style.borderRadius = '3px';
                                mathElement.style.padding = '2px 4px';
                                
                                // Add tooltip with error information
                                mathElement.title = 'Math rendering error: ' + error.textContent;
                                
                                // Log error for debugging
                                console.warn('MathJax rendering error:', error.textContent, mathElement);
                            }
                        });
                    });"""
        
        config = f"""
        window.MathJax = {{
            tex: {{
                inlineMath: [['\\\\(', '\\\\)']],
                displayMath: [['\\\\[', '\\\\]']],
                processEscapes: true,
                processEnvironments: true,
                tags: 'none',
                formatError: function (jax, err) {{
                    // Custom error formatting
                    console.warn('MathJax LaTeX Error:', err.message);
                    return 'LaTeX Error: ' + err.message.replace(/\\n/g, ' ');
                }},
                macros: {{
                    // Common macros for better compatibility
                    RR: "\\\\mathbb{{R}}",
                    NN: "\\\\mathbb{{N}}",
                    ZZ: "\\\\mathbb{{Z}}",
                    QQ: "\\\\mathbb{{Q}}",
                    CC: "\\\\mathbb{{C}}",
                    // Additional useful macros
                    eps: "\\\\varepsilon",
                    phi: "\\\\varphi",
                    implies: "\\\\Rightarrow",
                    iff: "\\\\Leftrightarrow"
                }}
            }},
            svg: {{
                fontCache: 'global',
                displayAlign: 'center',
                displayIndent: '0em',
                scale: 1,
                minScale: 0.5,
                mtextInheritFont: false,
                merrorInheritFont: true
            }},
            options: {{
                enableMenu: false,
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
                ignoreHtmlClass: 'tex2jax_ignore',
                processHtmlClass: 'tex2jax_process',
                renderActions: {{
                    addMenu: [],  // Disable context menu
                    checkLoading: []  // Disable loading messages
                }}
            }},
            startup: {{
                ready: function () {{
                    MathJax.startup.defaultReady();{responsive_code}{error_handling_code}
                }},
                pageReady: function () {{
                    // Custom page ready handler
                    return MathJax.startup.defaultPageReady().then(function () {{
                        // Add global error handler
                        window.addEventListener('error', function(e) {{
                            if (e.message && e.message.includes('MathJax')) {{
                                console.error('MathJax Error:', e.message, e.filename, e.lineno);
                            }}
                        }});
                    }});
                }}
            }},
            loader: {{
                load: ['[tex]/ams', '[tex]/newcommand', '[tex]/configmacros']
            }}
        }};
        """
        return config.strip()
    
    def generate_responsive_css(self) -> str:
        """
        Generate CSS for responsive math formula display.
        
        Returns:
            CSS string for responsive math styling
        """
        css = """
        /* Responsive Math Formula Styles */
        .math-display {
            text-align: center;
            margin: 1rem 0;
            overflow-x: auto;
            overflow-y: hidden;
            max-width: 100%;
        }
        
        .math-inline {
            display: inline;
            max-width: 100%;
        }
        
        /* MathJax responsive containers */
        .MathJax[display="true"] {
            max-width: 100%;
            overflow-x: auto;
            overflow-y: hidden;
            margin: 0.5em 0;
        }
        
        .MathJax[display="false"] {
            max-width: 100%;
            overflow-x: auto;
            display: inline-block;
            vertical-align: middle;
        }
        
        /* Error styling for math formulas */
        .MathJax .merror {
            background-color: #ffebee !important;
            color: #c62828 !important;
            border: 1px solid #f44336 !important;
            border-radius: 3px !important;
            padding: 1px 3px !important;
            font-size: 0.9em !important;
        }
        
        /* Mobile responsive adjustments */
        @media (max-width: 768px) {
            .MathJax[display="true"] {
                font-size: 0.9em;
                margin: 0.3em 0;
            }
            
            .MathJax[display="false"] {
                font-size: 0.85em;
            }
            
            .math-display {
                margin: 0.5rem 0;
                padding: 0 0.5rem;
            }
        }
        
        @media (max-width: 480px) {
            .MathJax[display="true"] {
                font-size: 0.8em;
            }
            
            .MathJax[display="false"] {
                font-size: 0.8em;
            }
        }
        
        /* Print styles for math */
        @media print {
            .MathJax[display="true"] {
                break-inside: avoid;
                page-break-inside: avoid;
            }
            
            .math-display {
                break-inside: avoid;
                page-break-inside: avoid;
            }
        }
        """
        return css.strip()
    
    def handle_math_error(self, error_message: str, latex_content: str, position: int) -> str:
        """
        Handle math processing errors with graceful fallback.
        
        Args:
            error_message: The error message
            latex_content: The original LaTeX content
            position: Position in the document where error occurred
            
        Returns:
            Fallback HTML content for the error
        """
        self.logger.error(f"Math processing error at position {position}: {error_message}")
        self.logger.debug(f"Problematic LaTeX content: {latex_content}")
        
        # Create fallback HTML with error indication
        escaped_latex = latex_content.replace('<', '&lt;').replace('>', '&gt;')
        fallback_html = f"""
        <span class="math-error" title="Math Error: {error_message}">
            <code class="latex-fallback">{escaped_latex}</code>
            <small class="error-indicator" style="color: #f44336; font-size: 0.8em;">
                ⚠ Math Error
            </small>
        </span>
        """
        return fallback_html.strip()
    
    def process_math_with_error_handling(self, content: str) -> Tuple[str, List[MathFormula], List[str]]:
        """
        Process math formulas with comprehensive error handling.
        
        Args:
            content: Markdown content containing math formulas
            
        Returns:
            Tuple of (processed_content, list_of_formulas, list_of_errors)
        """
        errors = []
        
        try:
            # First, extract all formulas to identify invalid ones
            display_formulas = self.extract_display_math(content)
            temp_content = self.display_math_pattern.sub("__TEMP_DISPLAY__", content)
            inline_formulas = self.extract_inline_math(temp_content)
            
            all_formulas = display_formulas + inline_formulas
            processed_content = content
            
            # Process invalid formulas first (replace with fallbacks)
            invalid_formulas = [f for f in all_formulas if not f.valid]
            for formula in invalid_formulas:
                error_msg = f"Invalid LaTeX syntax in {formula.formula_type} math"
                errors.append(error_msg)
                
                # Create fallback and replace in original content
                fallback = self.handle_math_error(error_msg, formula.content, formula.position)
                
                if formula.formula_type == "display":
                    original_pattern = f"$${formula.content}$$"
                else:
                    original_pattern = f"${formula.content}$"
                
                # Replace first occurrence
                processed_content = processed_content.replace(original_pattern, fallback, 1)
            
            # Now process the remaining valid formulas normally
            if processed_content != content:  # If we made replacements
                # Re-process only valid formulas
                valid_processed, valid_formulas = self.process_math_formulas(processed_content)
                processed_content = valid_processed
                # Combine all formulas for return
                all_formulas = valid_formulas + invalid_formulas
            else:
                # No invalid formulas, process normally
                processed_content, all_formulas = self.process_math_formulas(content)
            
            return processed_content, all_formulas, errors
            
        except Exception as e:
            error_msg = f"Critical error in math processing: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg, exc_info=True)
            
            # Return original content if processing fails completely
            return content, [], errors