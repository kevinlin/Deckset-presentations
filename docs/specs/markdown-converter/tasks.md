# Implementation Plan

- [x] 1. Set up enhanced project structure and core interfaces
  - Create directory structure for enhanced Deckset processing components
  - Define base interfaces for DecksetParser, MediaProcessor, and SlideProcessor
  - Set up enhanced data models for DecksetConfig, SlideConfig, and ProcessedSlide
  - _Requirements: 1.1, 1.4, 1.5_

- [x] 2. Implement core Deckset markdown parser
- [x] 2.1 Create DecksetParser class with global command processing
  - Implement parse_global_commands() to extract slidenumbers, footer, autoscale settings
  - Implement parse_slide_commands() for slide-specific directives like [.column], [.background-image]
  - Create unit tests for global and slide command parsing
  - _Requirements: 1.4, 1.5, 7.6, 7.7_

- [x] 2.2 Implement slide separation and auto-break functionality
  - Implement extract_slide_separators() to handle --- slide breaks
  - Implement detect_auto_slide_breaks() for slide-dividers configuration
  - Create unit tests for slide splitting logic
  - _Requirements: 1.1, 1.6_

- [x] 2.3 Implement speaker notes and footnote processing
  - Implement process_speaker_notes() to extract ^ prefixed notes
  - Implement process_footnotes() to handle [^1] references and definitions
  - Create unit tests for notes and footnotes extraction
  - _Requirements: 1.3, 7.2_

- [x] 2.4 Implement fit headers and emoji processing ✅ UPDATED
  - ✅ Implement process_fit_headers() to handle [fit] modifier on headings with proper HTML class output
  - ✅ Add support for global fit-headers configuration (e.g., fit-headers: #, ##)
  - ✅ Update CSS to use .fit class instead of .fit-text for proper Deckset compatibility
  - ✅ Update JavaScript to target .fit class for dynamic font scaling
  - ✅ Implement process_emoji_shortcodes() to convert :emoji: to Unicode
  - ✅ Create comprehensive unit tests for text processing features including global config
  - _Requirements: 1.2, 1.2.1, 7.3_

- [x] 3. Implement enhanced media processor
- [x] 3.1 Create MediaProcessor class with image processing
  - Implement process_image() with support for all Deckset image modifiers
  - Implement parse_image_modifiers() for background, inline, left, right, fit, fill, percentage scaling
  - Implement optimize_image_for_web() for web delivery optimization
  - Create unit tests for image processing and modifier parsing
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.8, 2.9, 2.10, 10.1_

- [x] 3.2 Implement image grid and advanced image features
  - Implement create_image_grid() for consecutive inline images
  - Add support for corner-radius modifier and filtered/original keywords
  - Create unit tests for image grid layout and advanced features
  - _Requirements: 2.7, 2.8, 2.9, 2.10_

- [x] 3.3 Implement video and audio processing
  - Implement process_video() with HTML5 video player generation
  - Implement process_audio() with HTML5 audio player generation
  - Add support for autoplay, loop, mute, hide modifiers
  - Implement YouTube URL detection and iframe embedding
  - Create unit tests for video/audio processing and modifiers
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

- [x] 4. Implement enhanced slide processor
- [x] 4.1 Create SlideProcessor class with column support
  - Implement process_slide() for individual slide processing
  - Implement process_columns() to handle [.column] directives
  - Create unit tests for slide processing and column layout
  - _Requirements: 6.1, 6.2, 6.3, 6.5_

- [x] 4.2 Implement background image and autoscale processing
  - Implement process_background_image() for slide backgrounds
  - Implement apply_autoscale() for text scaling when content overflows
  - Create unit tests for background processing and autoscaling
  - _Requirements: 2.1, 2.2, 7.5_

- [x] 5. Implement code highlighting processor
- [x] 5.1 Create CodeProcessor class with syntax highlighting
  - Implement process_code_block() with language-specific highlighting
  - Implement apply_syntax_highlighting() using highlight.js integration
  - Create unit tests for code block processing and syntax highlighting
  - _Requirements: 4.1, 4.6, 4.7_

- [x] 5.2 Implement line highlighting and emphasis features
  - Implement parse_highlight_directive() for [.code-highlight: N] parsing
  - Implement apply_line_highlighting() to highlight specific lines
  - Create unit tests for line highlighting functionality
  - _Requirements: 4.2, 4.3, 4.4, 4.5_

- [x] 6. Implement mathematical formula processor
- [x] 6.1 Create MathProcessor class with MathJax integration
  - Implement process_math_formulas() to handle $$...$$ and $...$ delimiters
  - Implement extract_display_math() and extract_inline_math() functions
  - Implement validate_latex_syntax() for error handling
  - Create unit tests for math formula processing
  - _Requirements: 5.1, 5.2, 5.4_

- [x] 6.2 Implement responsive math and error handling
  - Implement generate_mathjax_config() for responsive math rendering
  - Add support for math formula scaling and horizontal scrolling
  - Create unit tests for responsive math and error scenarios
  - _Requirements: 5.3, 5.4_

- [x] 7. Implement enhanced template engine
- [x] 7.1 Create EnhancedTemplateEngine class with slide rendering
  - Implement render_slide() with full Deckset feature support
  - Implement render_columns() for multi-column layout rendering
  - Implement render_background_image() for background image handling
  - Create unit tests for slide template rendering
  - _Requirements: 6.1, 6.2, 6.4_

- [x] 7.2 Implement media and content rendering
  - Implement render_inline_images() and render_image_grid() for image layouts
  - Implement render_video_player() and render_audio_player() for media
  - Implement render_code_block() with syntax highlighting support
  - Create unit tests for media and content rendering
  - _Requirements: 2.4, 2.7, 3.1, 3.2, 4.1_

- [x] 7.3 Implement formula and metadata rendering
  - Implement render_math_formula() for MathJax integration
  - Implement render_footnotes() for slide footnote display
  - Implement render_slide_footer() and render_slide_number() for metadata
  - Create unit tests for formula and metadata rendering
  - _Requirements: 5.1, 5.2, 7.2, 7.6_

- [x] 8. Create responsive CSS framework
- [x] 8.1 Implement base slide styling and responsive design
  - Create CSS for slide containers, content areas, and responsive breakpoints
  - Implement column layout styles with flexbox/grid
  - Add mobile-responsive column stacking behavior
  - Create CSS for fit text scaling and autoscale functionality
  - _Requirements: 6.4, 8.1, 8.2_

- [x] 8.2 Implement image and media styling
  - Create CSS for background images with left/right positioning
  - Implement inline image styles with grid layouts
  - Add video and audio player responsive styling
  - Create CSS for image filters and corner radius effects
  - _Requirements: 2.1, 2.2, 2.3, 2.8, 2.9, 2.10, 3.8_

- [x] 8.3 Implement code and math styling
  - Create CSS for code block syntax highlighting and line emphasis
  - Implement math formula responsive styling with overflow handling
  - Add footnote and speaker notes styling
  - Create print/PDF optimized styles with page breaks
  - _Requirements: 4.7, 5.3, 7.2, 8.6_

- [x] 9. Implement JavaScript enhancements
- [x] 9.1 Create EnhancedSlideViewer class with interactive features
  - Implement fit text scaling with dynamic font-size adjustment
  - Add MathJax initialization and error handling
  - Implement video autoplay with intersection observer
  - Create unit tests for JavaScript functionality
  - _Requirements: 1.2, 5.1, 5.4, 3.3_

- [x] 9.2 Implement navigation and accessibility features
  - Add keyboard navigation support for slide traversal
  - Implement speaker notes toggle functionality
  - Add accessibility attributes and keyboard support
  - Create unit tests for navigation and accessibility
  - _Requirements: 8.5_

- [x] 10. Integrate with existing website generator
- [x] 10.1 Update main generator to use enhanced processors
  - Modify existing PresentationProcessor to use DecksetParser
  - Update template rendering to use EnhancedTemplateEngine
  - Integrate MediaProcessor with existing file management
  - Create integration tests for enhanced processing pipeline
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [x] 10.2 Update website structure and navigation
  - Ensure enhanced presentations integrate with existing homepage
  - Update presentation listing to handle enhanced features
  - Maintain backward compatibility with existing presentations
  - Create end-to-end tests for complete website generation
  - _Requirements: 8.1, 8.2, 10.5_

- [ ] 11. Implement comprehensive error handling
- [ ] 11.1 Create enhanced error handling and validation
  - Implement DecksetParsingError and MediaProcessingError classes
  - Add line number tracking and context for error reporting
  - Implement graceful degradation for missing media files
  - Create unit tests for error handling scenarios
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 11.2 Add logging and debugging support
  - Implement comprehensive logging for parsing and processing steps
  - Add debug mode for detailed processing information
  - Create fallback rendering for unsupported features
  - Create unit tests for logging and fallback behavior
  - _Requirements: 9.1, 9.4, 9.5_

- [ ] 12. Performance optimization and testing
- [ ] 12.1 Implement performance optimizations
  - Add image optimization and progressive loading
  - Implement CSS and JavaScript minification
  - Add caching strategies for generated content
  - Create performance tests and benchmarks
  - _Requirements: 10.1, 10.2, 10.3_

- [ ] 12.2 Create comprehensive test suite
  - Write integration tests with real Deckset presentation files
  - Add performance tests for large presentations
  - Create accessibility validation tests
  - Implement cross-browser compatibility tests
  - _Requirements: 8.3, 8.4, 8.5, 10.4, 10.5_

- [x] 13. Documentation and deployment
- [x] 13.1 Create user documentation
  - ✅ Write comprehensive documentation for all Deckset features
  - ✅ Create migration guide from basic to enhanced generator
  - ✅ Add troubleshooting guide for common issues (documented in design.md)
  - ✅ Create examples demonstrating all supported features (Examples/10 Deckset basics.md working)
  - _Requirements: 9.1, 9.2, 9.3_

- [x] 13.2 Prepare for deployment
  - ✅ Update deployment scripts for enhanced dependencies
  - ✅ Add MathJax and syntax highlighting library integration
  - ✅ Create production build process with optimization
  - ✅ Perform final testing and validation (all 279 tests passing)
  - _Requirements: 5.1, 4.1, 10.2_

- [x] 14. Post-implementation fixes and improvements
- [x] 14.1 Fix background image visibility issue ✅ COMPLETED
  - ✅ Identified CSS stacking context issue with background images not being visible
  - ✅ Updated z-index values to create proper layering: background (z-index: 1), content (z-index: 2), UI elements (z-index: 3)
  - ✅ Updated both template and generated CSS files
  - ✅ Verified fix with regenerated presentations showing visible background images
  - _Requirements: 2.1, 8.2_

- [x] 15. Enhanced mode simplification ✅ COMPLETED
- [x] 15.1 Remove enhanced_mode configuration and always use enhanced features
  - ✅ Removed GeneratorConfig.enhanced_mode instance variable from WebPageGenerator and DecksetWebsiteGenerator
  - ✅ Removed EnhancedTemplateEngine.render_presentation() method (redundant with _render_enhanced_presentation)
  - ✅ Updated WebPageGenerator to always use _render_enhanced_presentation() method
  - ✅ Updated all tests to remove enhanced_mode references and patch the correct methods
  - ✅ Updated test_enhanced_features_usage to verify enhanced features are always enabled
  - ✅ All 287 tests passing with enhanced features always enabled
  - _Requirements: All enhanced requirements now apply by default_

- [x] 16. Template file refactoring ✅ COMPLETED
- [x] 16.1 Move hardcoded templates to separate template files
  - ✅ Created `templates/slide.html` with complete slide template
  - ✅ Created `templates/homepage.html` with homepage template
  - ✅ Updated `EnhancedTemplateEngine` to load templates from files using Jinja2 FileSystemLoader
  - ✅ Removed hardcoded template strings from `_load_templates()` method
  - ✅ Updated `render_slide()` to use `env.get_template('slide.html')`
  - ✅ Updated `render_homepage()` to use `env.get_template('homepage.html')`
  - ✅ All 287 tests passing with template file system
  - ✅ End-to-end verification: website generation works with template files
  - _Benefits: Better maintainability, version control friendly, designer-friendly editing_

- [x] 17. Typography enhancement for presentation formatting ✅ COMPLETED
- [x] 17.1 Implement presentation-appropriate typography hierarchy
  - ✅ Increased base font size to 18px for desktop presentations (from default 16px)
  - ✅ Implemented clear header hierarchy with appropriate font sizes and weights:
    - H1: 3.5rem (63px) with font-weight 700
    - H2: 2.75rem (49.5px) with font-weight 600
    - H3: 2.125rem (38.25px) with font-weight 600
    - H4: 1.625rem (29.25px) with font-weight 500
    - H5: 1.25rem (22.5px) with font-weight 500
    - H6: 1.125rem (20.25px) with font-weight 500
  - ✅ Enhanced paragraph and text styling with 1.25rem (22.5px) font size
  - ✅ Improved list items, blockquotes, and inline code typography
  - ✅ Updated `.fit` class to use larger scaling range: clamp(3rem, 15vw, 12rem)
  - ✅ Implemented responsive typography scaling:
    - Tablets (768px): 16px base with proportional scaling
    - Mobile (480px): 14px base with proportional scaling
  - ✅ Updated code blocks to use 1.125rem for better presentation readability
  - ✅ All 287 tests passing with enhanced typography
  - ✅ End-to-end verification: presentations display with improved typography
  - _Requirements: 10.1-10.9 (Typography and Presentation Formatting)_

- [x] 18. Enhanced markdown list support ✅ COMPLETED
- [x] 18.1 Implement comprehensive list processing in _markdown_to_html function
  - ✅ Enhanced `_markdown_to_html()` function with sophisticated list processing logic
  - ✅ Added support for unordered lists (lines starting with `- `) converting to HTML `<ul>` elements
  - ✅ Added support for ordered lists (lines starting with `1. `, `2. `, etc.) converting to HTML `<ol>` elements
  - ✅ Implemented proper list item content extraction preserving emphasis, code, and inline formatting
  - ✅ Added support for empty list items and malformed list syntax with graceful handling
  - ✅ Ensured proper separation between lists and surrounding paragraph content
  - ✅ Created comprehensive test suite covering all list scenarios including mixed content
  - ✅ All 22 enhanced template tests passing with list functionality
  - ✅ End-to-end verification: presentations display lists correctly with proper HTML structure
  - _Requirements: 1.7-1.10 (Core Deckset Markdown Compatibility - List Support)_

- [x] 19. Enforce 16:9 slide aspect ratio
  - Implement strict 16:9 slide container using CSS `aspect-ratio` with padding-top fallback
  - Update `EnhancedSlideViewer` to scale slides to viewport while preserving 16:9 and add neutral letterboxing/pillarboxing when needed
  - Update print styles to render each slide as 16:9 pages with consistent margins
  - Ensure media and layouts (backgrounds, left/right, inline, grids, columns) compute within 16:9 bounds without distortion
  - Create unit/integration tests to validate container ratio and scaling behavior (resize scenarios)
  - _Requirements: 13.1-13.6 (Slide Aspect Ratio - 16:9 Standard)_

- [x] 20. Implement Markdown link support
  - Extend `_markdown_to_html()` to convert `[text](url)` into anchors
  - Add URL sanitization (allow: `http`, `https`, `mailto`, `tel`, `#`) with safe fallbacks for unsupported schemes
  - Apply `target="_blank"` and `rel="noopener noreferrer"` to external links; keep internal anchors/relative paths in same tab
  - Support optional link titles `[text](url "title")`
  - Add unit tests for links in headings, paragraphs, lists, tables, blockquotes, and footnotes
  - Add end-to-end test to verify links remain present and clickable in generated HTML and printed PDF
  - _Requirements: 14.1-14.7 (Markdown Link Support)_

- [x] 21. Nested lists and mixed list types
  - Enhance list parser to support multi-level nesting via indentation (4 spaces/tab) and mixed ordered/unordered lists
  - Add tests covering deeply nested and mixed lists across slides
  - _Requirements: 1.11-1.12_

- [x] 22. Indented code blocks parity with fenced code
  - Detect indented code blocks and assign language from `code-language` fallback when no fence language is provided
  - Ensure highlighting, overflow scrolling, and line-number options remain consistent
  - Add unit tests for indented code inside lists and blockquotes
  - _Requirements: 4.8_

- [x] 23. Image path robustness and adjacent inline parsing
  - Support filenames with spaces/Unicode; ensure URLs are correctly encoded in output
  - Parse adjacent inline image tokens on the same line without requiring whitespace
  - Add tests for single-line galleries and captions below inline images
  - _Requirements: 2.11-2.12_

- [x] 24. Animated GIF support
  - Ensure `.gif` images render animated by default; document performance caveats
  - Add tests verifying animation presence and correct sizing within 16:9 container
  - _Requirements: 2.13_

- [x] 25. Math in footnotes and tables
  - Ensure inline/display math renders correctly inside footnotes and table cells
  - Add tests for overflow handling and scaling within these contexts
  - _Requirements: 5.5_

- [x] 26. Safe inline HTML and sanitization
  - Allow a minimal safe HTML subset (`br`, named anchor) with attribute sanitization
  - Add tests ensuring unsafe tags/attributes are stripped while preserving text
  - _Requirements: 7.8_

- [x] 27. Internal anchors and cross-slide navigation
  - Generate stable, unique IDs for headings and named anchors; build an index across slides
  - Update viewer to navigate across slides on internal anchor clicks and focus target elements
  - Warn on unresolved anchors; add tests for duplicate IDs and de-duplication
  - Add tests for internal anchors and cross-slide navigation and ensure all tests are passing
  - _Requirements: 15.1-15.4_

- [x] 28. Automatic readability filter for text over background images
  - Implement eligibility detection in the processing pipeline to flag slides that combine background images and overlaying text
  - Add global and slide-level config: `readability-filter: auto | on | off` (default `auto`), with slide precedence
  - Respect image modifiers: `![filtered]` forces filter; `![original]` disables it
  - Implement CSS baseline: overlay pseudo-element and optional background blur with themeable CSS variables
  - Implement JS adaptive enhancement in `EnhancedSlideViewer` to measure contrast and tune `--overlay-opacity`/`--bg-blur`, with a minimal backplate fallback when limits are reached
  - Ensure exclusions for inline/left/right images that do not sit behind text
  - Add accessibility tests that assert WCAG AA contrast for representative slides and verify fallbacks when canvas/image sampling is unavailable
  - Add unit and integration tests covering overrides, defaults, and no-regression for slides without background images
  - _Requirements: 2.15-2.15.6, 8.1, 8.2_

- [x] 29. Inline image captions
  - Extend parser to detect caption lines immediately following an inline image without a blank line
  - Add `InlineFigure` model with `caption` field and use semantic `<figure>/<figcaption>` in templates
  - Ensure autoscale and wrapping work with captions; maintain grouping in print/PDF
  - Add unit tests for detection, rendering, and accessibility (associating captions with images)
  - _Requirements: 2.16-2.16.1_

- [ ] 30. Inline-in-text image sizing and alignment
  - Constrain inline images to the current line height with baseline alignment; preserve aspect ratio
  - Add tests for lines with mixed text and inline images across different font sizes and in lists/quotes
  - _Requirements: 2.17_

- [ ] 31. Modifier composition and precedence
  - Implement deterministic application order (context → placement → sizing → filtering)
  - Validate conflicting combinations; log structured warnings without halting processing
  - Add tests for combinations such as `[inline, right]`, `[left, 30%]`, `[fit, filtered]`, and override interactions with the readability filter
  - _Requirements: 2.18_

- [ ] 32. Inline image grids across lines
  - Render consecutive `![inline]` tokens into grid containers with consistent gutters; support multi-line grids
  - Add responsiveness tests for wrapping and 16:9 safe-area containment
  - _Requirements: 2.19, 13.4-13.5_