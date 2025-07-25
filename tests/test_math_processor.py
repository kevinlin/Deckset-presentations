"""
Unit tests for the MathProcessor class.

Tests mathematical formula processing, LaTeX validation, and MathJax integration.
"""

import pytest
from math_processor import MathProcessor
from models import MathFormula


class TestMathProcessor:
    """Test cases for MathProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = MathProcessor()
    
    def test_extract_display_math_single_formula(self):
        """Test extraction of single display math formula."""
        content = "Here is a formula: $$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$ and some text."
        formulas = self.processor.extract_display_math(content)
        
        assert len(formulas) == 1
        assert formulas[0].content == "x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}"
        assert formulas[0].formula_type == "display"
        assert formulas[0].valid is True
    
    def test_extract_display_math_multiple_formulas(self):
        """Test extraction of multiple display math formulas."""
        content = """
        First formula: $$E = mc^2$$
        
        Second formula: $$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$
        """
        formulas = self.processor.extract_display_math(content)
        
        assert len(formulas) == 2
        assert formulas[0].content == "E = mc^2"
        assert formulas[1].content == "\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}"
        assert all(f.formula_type == "display" for f in formulas)
    
    def test_extract_inline_math_single_formula(self):
        """Test extraction of single inline math formula."""
        content = "The value of $\\pi$ is approximately 3.14159."
        formulas = self.processor.extract_inline_math(content)
        
        assert len(formulas) == 1
        assert formulas[0].content == "\\pi"
        assert formulas[0].formula_type == "inline"
        assert formulas[0].valid is True
    
    def test_extract_inline_math_multiple_formulas(self):
        """Test extraction of multiple inline math formulas."""
        content = "We have $x = 5$ and $y = 3$, so $x + y = 8$."
        formulas = self.processor.extract_inline_math(content)
        
        assert len(formulas) == 3
        assert formulas[0].content == "x = 5"
        assert formulas[1].content == "y = 3"
        assert formulas[2].content == "x + y = 8"
        assert all(f.formula_type == "inline" for f in formulas)
    
    def test_extract_inline_math_ignores_display_math(self):
        """Test that inline math extraction doesn't match display math."""
        content = "Display: $$x^2 + y^2 = z^2$$ and inline: $a = b$"
        formulas = self.processor.extract_inline_math(content)
        
        assert len(formulas) == 1
        assert formulas[0].content == "a = b"
    
    def test_process_math_formulas_mixed_content(self):
        """Test processing content with both display and inline math."""
        content = """
        # Mathematical Examples
        
        The quadratic formula is: $$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$
        
        For a simple case where $a = 1$, $b = -5$, and $c = 6$, we get solutions.
        """
        
        processed_content, formulas = self.processor.process_math_formulas(content)
        
        # Should have 1 display and 3 inline formulas
        display_formulas = [f for f in formulas if f.formula_type == "display"]
        inline_formulas = [f for f in formulas if f.formula_type == "inline"]
        
        assert len(display_formulas) == 1
        assert len(inline_formulas) == 3
        
        # Check that content was properly converted to MathJax syntax
        assert "\\[x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}\\]" in processed_content
        assert "\\(a = 1\\)" in processed_content
        assert "\\(b = -5\\)" in processed_content
        assert "\\(c = 6\\)" in processed_content
    
    def test_validate_latex_syntax_valid_formulas(self):
        """Test validation of valid LaTeX formulas."""
        valid_formulas = [
            "x^2 + y^2 = z^2",
            "\\frac{a}{b} + \\frac{c}{d}",
            "\\int_{0}^{1} x^2 dx",
            "\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}",
            "\\begin{matrix} a & b \\\\ c & d \\end{matrix}",
            "\\alpha + \\beta = \\gamma",
            "\\mathbb{R}^n",
            "\\left( \\frac{1}{2} \\right)^n"
        ]
        
        for formula in valid_formulas:
            assert self.processor.validate_latex_syntax(formula), f"Formula should be valid: {formula}"
    
    def test_validate_latex_syntax_invalid_formulas(self):
        """Test validation of invalid LaTeX formulas."""
        invalid_formulas = [
            "",  # Empty
            "   ",  # Whitespace only
            "x^2 + {y^2 = z^2",  # Unbalanced braces
            "x^2 + y^2} = z^2",  # Unbalanced braces
            "\\begin{matrix} a & b \\end{array}",  # Mismatched environments
            "\\begin{matrix} a & b",  # Missing end
            "a & b \\end{matrix}",  # Missing begin
            "\\\\\\x",  # Triple backslash
            "$$nested$$",  # Nested dollar signs
        ]
        
        for formula in invalid_formulas:
            assert not self.processor.validate_latex_syntax(formula), f"Formula should be invalid: {formula}"
    
    def test_balanced_braces_check(self):
        """Test balanced braces checking."""
        # Valid cases
        assert self.processor._check_balanced_braces("x^{2}")
        assert self.processor._check_balanced_braces("\\frac{a}{b}")
        assert self.processor._check_balanced_braces("\\left\\{ x \\right\\}")
        assert self.processor._check_balanced_braces("")
        
        # Invalid cases
        assert not self.processor._check_balanced_braces("x^{2")
        assert not self.processor._check_balanced_braces("x^2}")
        assert not self.processor._check_balanced_braces("\\frac{a}{b")
        assert not self.processor._check_balanced_braces("\\frac{a}b}")
    
    def test_balanced_environments_check(self):
        """Test balanced environments checking."""
        # Valid cases
        assert self.processor._check_balanced_environments("\\begin{matrix} a \\end{matrix}")
        assert self.processor._check_balanced_environments("\\begin{align} x = 1 \\end{align}")
        assert self.processor._check_balanced_environments("no environments here")
        assert self.processor._check_balanced_environments("")
        
        # Invalid cases
        assert not self.processor._check_balanced_environments("\\begin{matrix} a \\end{array}")
        assert not self.processor._check_balanced_environments("\\begin{matrix} a")
        assert not self.processor._check_balanced_environments("a \\end{matrix}")
    
    def test_common_syntax_errors_check(self):
        """Test common syntax errors detection."""
        # Valid cases (no errors)
        assert not self.processor._has_common_syntax_errors("x^2 + y^2")
        assert not self.processor._has_common_syntax_errors("\\frac{a}{b}")
        assert not self.processor._has_common_syntax_errors("\\text{some text}")
        
        # Invalid cases (has errors)
        assert self.processor._has_common_syntax_errors("a & b")  # Unescaped &
        assert self.processor._has_common_syntax_errors("50% of x")  # Unescaped %
        assert self.processor._has_common_syntax_errors("\\\\\\x")  # Triple backslash
        assert self.processor._has_common_syntax_errors("$$nested$$")  # Nested $$
    
    def test_generate_mathjax_config(self):
        """Test MathJax configuration generation."""
        config = self.processor.generate_mathjax_config()
        
        # Check that config contains expected elements
        assert "window.MathJax" in config
        assert "inlineMath" in config
        assert "displayMath" in config
        assert "processEscapes: true" in config
        assert "fontCache: 'global'" in config
        assert "enableMenu: false" in config
        assert "responsive" in config
        
        # Check that it's valid JavaScript (basic syntax check)
        assert config.count("{") == config.count("}")
        assert config.count("[") == config.count("]")
    
    def test_process_math_formulas_empty_content(self):
        """Test processing empty or no-math content."""
        # Empty content
        processed, formulas = self.processor.process_math_formulas("")
        assert processed == ""
        assert formulas == []
        
        # Content without math
        content = "This is just regular text with no formulas."
        processed, formulas = self.processor.process_math_formulas(content)
        assert processed == content
        assert formulas == []
    
    def test_process_math_formulas_preserves_non_math_content(self):
        """Test that non-math content is preserved during processing."""
        content = """
        # Title
        
        Some text before math: $x = 5$
        
        More text and a display formula:
        $$y = mx + b$$
        
        Final paragraph with inline $z = x + y$ math.
        """
        
        processed, formulas = self.processor.process_math_formulas(content)
        
        # Check that non-math content is preserved
        assert "# Title" in processed
        assert "Some text before math:" in processed
        assert "More text and a display formula:" in processed
        assert "Final paragraph with inline" in processed
        assert "math." in processed
        
        # Check that math was converted
        assert "\\(x = 5\\)" in processed
        assert "\\[y = mx + b\\]" in processed
        assert "\\(z = x + y\\)" in processed
    
    def test_formula_position_tracking(self):
        """Test that formula positions are correctly tracked."""
        content = "Start $x = 1$ middle $$y = 2$$ end $z = 3$"
        processed, formulas = self.processor.process_math_formulas(content)
        
        # Positions should be in order
        positions = [f.position for f in formulas]
        assert positions == sorted(positions)
        
        # First formula should be after "Start "
        assert formulas[0].position > 5
        
        # Display formula should be after inline formula
        display_formula = next(f for f in formulas if f.formula_type == "display")
        inline_formulas = [f for f in formulas if f.formula_type == "inline"]
        assert display_formula.position > inline_formulas[0].position
    
    def test_invalid_latex_handling(self):
        """Test handling of invalid LaTeX syntax."""
        content = "Valid: $x = 1$ Invalid: $x^{2$ More: $y = 3$"
        processed, formulas = self.processor.process_math_formulas(content)
        
        # Should still extract all formulas
        assert len(formulas) == 3
        
        # Check validity flags
        valid_formulas = [f for f in formulas if f.valid]
        invalid_formulas = [f for f in formulas if not f.valid]
        
        assert len(valid_formulas) == 2  # x = 1 and y = 3
        assert len(invalid_formulas) == 1  # x^{2
        
        # Invalid formula should still be processed
        assert invalid_formulas[0].content == "x^{2"
    
    def test_multiline_display_math(self):
        """Test processing of multiline display math."""
        content = """
        $$
        \\begin{align}
        x &= a + b \\\\
        y &= c + d
        \\end{align}
        $$
        """
        
        formulas = self.processor.extract_display_math(content)
        assert len(formulas) == 1
        
        formula_content = formulas[0].content
        assert "\\begin{align}" in formula_content
        assert "\\end{align}" in formula_content
        assert "x &= a + b" in formula_content
        assert "y &= c + d" in formula_content
    
    def test_generate_mathjax_config_with_responsive(self):
        """Test MathJax configuration generation with responsive features."""
        config = self.processor.generate_mathjax_config(responsive=True, error_handling=True)
        
        # Check responsive features
        assert "responsive" in config
        assert "scale" in config
        assert "overflowX" in config
        assert "transform" in config
        
        # Check error handling features
        assert "errorHandling" in config
        assert "formatError" in config
        assert "merror" in config
        
        # Check basic configuration
        assert "window.MathJax" in config
        assert "inlineMath" in config
        assert "displayMath" in config
    
    def test_generate_mathjax_config_minimal(self):
        """Test MathJax configuration generation without responsive features."""
        config = self.processor.generate_mathjax_config(responsive=False, error_handling=False)
        
        # Should not contain responsive or error handling code
        assert "responsive" not in config
        assert "errorHandling" not in config
        
        # Should still contain basic configuration
        assert "window.MathJax" in config
        assert "inlineMath" in config
        assert "displayMath" in config
    
    def test_generate_responsive_css(self):
        """Test responsive CSS generation."""
        css = self.processor.generate_responsive_css()
        
        # Check for responsive classes
        assert ".math-display" in css
        assert ".math-inline" in css
        assert ".MathJax[display=\"true\"]" in css
        assert ".MathJax[display=\"false\"]" in css
        
        # Check for error styling
        assert ".merror" in css
        assert "background-color" in css
        
        # Check for media queries
        assert "@media (max-width: 768px)" in css
        assert "@media (max-width: 480px)" in css
        assert "@media print" in css
        
        # Check for responsive properties
        assert "overflow-x: auto" in css
        assert "max-width: 100%" in css
    
    def test_handle_math_error(self):
        """Test math error handling."""
        error_message = "Undefined control sequence"
        latex_content = "\\undefined{command}"
        position = 100
        
        fallback = self.processor.handle_math_error(error_message, latex_content, position)
        
        # Check fallback content
        assert "math-error" in fallback
        assert "latex-fallback" in fallback
        assert "error-indicator" in fallback
        assert "Math Error" in fallback
        assert latex_content.replace('<', '&lt;').replace('>', '&gt;') in fallback
    
    def test_process_math_with_error_handling_valid_content(self):
        """Test math processing with error handling for valid content."""
        content = "Valid math: $x = 1$ and $$y = 2$$"
        
        processed, formulas, errors = self.processor.process_math_with_error_handling(content)
        
        # Should process normally with no errors
        assert len(errors) == 0
        assert len(formulas) == 2
        assert "\\(x = 1\\)" in processed
        assert "\\[y = 2\\]" in processed
    
    def test_process_math_with_error_handling_invalid_content(self):
        """Test math processing with error handling for invalid content."""
        content = "Invalid math: $x^{2$ and valid: $y = 3$"
        
        processed, formulas, errors = self.processor.process_math_with_error_handling(content)
        
        # Should have errors for invalid formula
        assert len(errors) > 0
        assert any("Invalid LaTeX syntax" in error for error in errors)
        
        # Should still process valid formulas
        valid_formulas = [f for f in formulas if f.valid]
        assert len(valid_formulas) >= 1
        
        # Should contain fallback for invalid formula
        assert "math-error" in processed or "latex-fallback" in processed
    
    def test_process_math_with_error_handling_critical_error(self):
        """Test math processing with critical error handling."""
        # Mock a critical error by temporarily breaking the processor
        original_method = self.processor.process_math_formulas
        
        def failing_method(content):
            raise Exception("Critical processing error")
        
        self.processor.process_math_formulas = failing_method
        
        content = "Some math: $x = 1$"
        processed, formulas, errors = self.processor.process_math_with_error_handling(content)
        
        # Should handle critical error gracefully
        assert len(errors) > 0
        assert any("Critical error" in error for error in errors)
        assert processed == content  # Should return original content
        assert len(formulas) == 0
        
        # Restore original method
        self.processor.process_math_formulas = original_method
    
    def test_responsive_math_scaling_logic(self):
        """Test the logic for responsive math scaling."""
        config = self.processor.generate_mathjax_config(responsive=True)
        
        # Check that scaling logic is present
        assert "scale" in config
        assert "Math.min" in config
        assert "scrollWidth" in config
        assert "clientWidth" in config
        assert "transform" in config
        assert "transformOrigin" in config
    
    def test_error_handling_features_in_config(self):
        """Test error handling features in MathJax config."""
        config = self.processor.generate_mathjax_config(error_handling=True)
        
        # Check error handling features
        assert "formatError" in config
        assert "merror" in config
        assert "console.warn" in config
        assert "backgroundColor" in config
        assert "border" in config
    
    def test_macros_in_config(self):
        """Test that common macros are included in config."""
        config = self.processor.generate_mathjax_config()
        
        # Check for common mathematical macros
        assert "RR" in config  # Real numbers
        assert "NN" in config  # Natural numbers
        assert "ZZ" in config  # Integers
        assert "QQ" in config  # Rationals
        assert "CC" in config  # Complex numbers
        assert "eps" in config  # Epsilon
        assert "implies" in config  # Implication
        assert "iff" in config  # If and only if