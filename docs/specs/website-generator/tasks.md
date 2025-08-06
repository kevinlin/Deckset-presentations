# Implementation Plan

- [x] 1. Basic presentation processing foundation
  - Basic markdown processing with slide splitting using "---" separators (already implemented)
  - Speaker notes extraction for "^" prefixed content (already implemented)
  - Jinja2 template rendering with Tailwind CSS styling (already implemented)
  - Placeholder UI for missing slides (already implemented in template)
  - _Requirements: 2.1, 2.2, 2.5, 3.1_

- [x] 2. Set up project structure and core data models
  - Create modular Python files (scanner.py, processor.py, generator.py, templates.py, models.py)
  - Define data classes for PresentationInfo, Slide, ProcessedPresentation, and GeneratorConfig
  - Create base exception classes for error handling (GeneratorError, PresentationProcessingError, TemplateRenderingError)
  - Create templates/ directory with base template structure
  - _Requirements: 1.1, 1.2, 5.1, 5.5_

- [x] 3. Implement repository scanner functionality
  - Create PresentationScanner class to discover presentation folders
  - Implement folder scanning logic that excludes system directories (.git, .kiro, etc.)
  - Add markdown file detection and selection logic (prefer folder-named files)
  - Write unit tests for scanner functionality with various folder structures in tests/test_scanner.py
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 4. Refactor existing code into presentation processor
  - Extract current markdown processing logic into PresentationProcessor class
  - Enhance slide splitting to handle various separator formats
  - Add frontmatter metadata parsing for presentation configuration
  - Improve notes extraction to handle different note formats
  - Write unit tests for markdown processing with various content formats in tests/test_processor.py
  - _Requirements: 2.1, 2.2, 2.5_

- [x] 5. Create template management system
  - Create TemplateManager class using Jinja2 for HTML rendering
  - Enhance existing presentation template with better responsive layout
  - Create homepage template with presentation grid layout
  - Add base template with common styling and navigation elements
  - Write unit tests for template rendering with mock data in tests/test_templates.py
  - _Requirements: 3.1, 3.2, 3.4, 3.5_

- [x] 6. Implement web page generator
  - Create WebPageGenerator class for HTML output generation
  - Refactor existing template rendering into the new generator
  - Implement individual presentation page generation with slide images and notes
  - Add proper image path handling with fallback for missing slides
  - Implement error handling for template rendering failures
  - Write unit tests for page generation with various presentation data in tests/test_generator.py
  - _Requirements: 2.3, 2.4, 3.3, 5.2, 5.3_

- [x] 7. Build homepage generator functionality
  - Implement homepage generation with presentation listings
  - Add preview image handling with placeholder fallbacks
  - Create presentation metadata display (title, slide count, last modified)
  - Implement responsive grid layout for presentation cards
  - Write unit tests for homepage generation with multiple presentations in tests/test_generator.py
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 8. Create file and asset management

  - Implement slide image copying from source folders to output directory
  - Create output directory structure management (site/, slides/, assets/)
  - Implement file cleanup and organization for generated website
  - Write integration tests for complete file management workflow in tests/test_integration.py
  - _Requirements: 2.4, 4.3, 5.2_

- [x] 9. Enhance main generator orchestration
  - Refactor existing main.py into DecksetWebsiteGenerator class
  - Implement complete website generation workflow for multiple presentations
  - Add configuration management for output directories and settings
  - Implement comprehensive error handling with graceful degradation
  - Add logging for debugging and monitoring generation process
  - _Requirements: 5.1, 5.4, 5.5_

- [x] 10. Build comprehensive error handling and logging
  - Implement specific exception classes for different error types
  - Add graceful error recovery that continues processing other presentations
  - Create detailed logging with context information for debugging
  - Implement error reporting that doesn't break the entire generation process
  - Write unit tests for error scenarios and recovery mechanisms in tests/test_error_handling.py
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 11. Create GitHub Actions workflow
  - Design workflow YAML file for automated website generation
  - Implement Python environment setup and dependency installation
  - Add website generation step that runs the main generator
  - Configure GitHub Pages deployment from generated site/ directory
  - Add error notification and reporting for failed builds
  - Write workflow that triggers on main branch pushes
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 12. Enhance title extraction for multiple presentations folders
  - Modify extract_presentation_title method to support filename fallback for multiple presentations in single folder
  - Add _format_filename_as_title method to remove numeric prefixes from filenames (e.g., "10 Deckset basics" → "Deckset basics")
  - Update _create_presentation_info_from_file to use filename fallback for title extraction
  - Create comprehensive unit tests covering Examples folder scenarios and filename fallback behavior
  - Update requirements.md and design.md to reflect new title extraction logic
  - _Requirements: 1.5, 1.6, 2.7, 4.5, 4.6_

- [x] 13. Verify processing consistency between single and multiple presentations
  - Add unit tests to verify that both single and multiple presentations use the same EnhancedPresentationProcessor
  - Create integration test to ensure both types produce identical enhanced features (MathJax, code highlighting, enhanced styles)
  - Verify that all presentations go through the same _process_presentations pipeline in main.py
  - Document processing consistency in requirements and design specifications
  - _Requirements: 1.7_

- [x] 14. Fix asset paths for presentations in subdirectories
  - Implement _calculate_asset_path_prefix method in WebPageGenerator and EnhancedTemplateEngine to calculate correct relative paths
  - Update asset path generation to use "../" for single presentations and "../../" for presentations in subdirectories like Examples
  - Fix CSS and JavaScript asset path references in enhanced rendering templates
  - Update FileManager to copy JavaScript assets to assets/js directory structure
  - Create comprehensive integration test to verify asset paths are correct for both single and multiple presentations
  - Update requirements.md and design.md to document asset path management requirements
  - _Requirements: 2.8_

- [x] 15. Fix homepage presentation sorting and navigation
  - Fix homepage to sort presentations alphabetically by title instead of by last modified date
  - Improve title extraction logic to handle Deckset-specific frontmatter format and locate first header in content
  - Add navigation header to all presentation pages with "Back to Home" links using correct relative paths
  - Update both _render_enhanced_presentation method and EnhancedTemplateEngine.render_presentation method to include navigation
  - Ensure navigation paths automatically adjust based on presentation nesting depth
  - Update requirements.md and design.md to reflect homepage sorting and navigation requirements
  - _Requirements: 4.7, 4.8_

- [x] 16. Implement filename-based presentation titles
  - Change title extraction from content-based to filename-based for all presentations
  - Enhance _format_filename_as_title method to remove numeric prefixes, convert dashes/underscores to spaces, and apply title case
  - Update extract_presentation_title method to always use filename formatting instead of content extraction
  - Update all tests to reflect new filename-based title behavior and alphabetical sorting
  - Run full test suite to ensure all 285 tests pass
  - Update requirements.md, design.md, and tasks.md to document filename-based title extraction
  - _Requirements: 1.8, 2.7_

- [x] 17. Fix and enhance presentation navigation functionality
  - Fix slide counter not updating when navigating between slides by ensuring updateSlideCounter() method works correctly
  - Fix Notes button not working by ensuring toggleNotes() method properly shows/hides speaker-notes elements
  - Implement CSS-based slide display management using .active class and fallback inline styles for better compatibility
  - Add proper initialization of notes toggle button with aria-pressed attribute for accessibility
  - Ensure presentation container gets js-enabled class for proper CSS styling when JavaScript is active
  - Create comprehensive test suite (test_navigation_functionality.js) covering slide counter, notes toggle, slide display, and button states
  - Update slide-viewer.js to handle all navigation functionality with proper error handling and logging
  - Update slide_styles.css to properly hide/show slides based on JavaScript state
  - Update requirements.md, design.md, and tasks.md to document navigation enhancement requirements
  - _Requirements: 7.1-7.11_

- [x] 18. Enhance homepage with Deckset branding and favicon
  - Download and integrate Deckset favicon from https://www.deckset.com/static/images/favicon.png for professional branding
  - Add Deckset app icon from https://www.deckset.com/static/images/deckset-icon.png as fallback or header logo
  - Update homepage template to include proper favicon links in HTML head section
  - Implement favicon copying to output directory during website generation
  - Add proper meta tags for favicon support across different browsers and devices
  - Update FileManager to handle favicon and icon asset copying
  - Test favicon display in generated website across different browsers
  - _Requirements: 4.9, 4.10_

- [x] 19. Implement folder name inclusion in presentation titles for multiple presentations
  - Modify _create_presentation_info_from_file to use _create_title_with_folder_name for multiple presentations
  - Implement _create_title_with_folder_name method to include singularized folder name as prefix in titles
  - Add _singularize_folder_name method to convert plural folder names to singular (e.g., "Examples" → "Example")
  - Update presentation titles for multiple presentations to include folder name: "Examples/10 Deckset basics.md" → "Example - Deckset Basics"
  - Ensure single presentations maintain filename-only titles without folder name prefix
  - Update scanner tests to expect folder names in multiple presentation titles
  - Update integration tests to expect folder names in multiple presentation titles
  - Verify all tests pass with manual testing and validation
  - Update requirements.md, design.md, and tasks.md to document folder name inclusion feature
  - _Requirements: 1.9, 2.8_

- [x] 20. Separate presentation HTML template into modular template file
  - Create templates/presentation.html template file with Jinja2 template syntax for main presentation layout
  - Add render_presentation_page method to EnhancedTemplateEngine for rendering presentation pages using the new template
  - Update WebPageGenerator._render_enhanced_presentation to use template engine instead of hardcoded HTML strings
  - Implement template context passing with presentation data, slides HTML, asset paths, and MathJax configuration
  - Add error handling and fallback HTML generation for template rendering failures
  - Update requirements.md to add Requirement 3.1 for template modularization and renumber subsequent requirements
  - Update design.md to document template files, Enhanced Template Engine interface changes, and file structure
  - Update tasks.md to document template separation implementation
  - _Requirements: 3.1.1, 3.1.2, 3.1.4, 3.1.5, 3.1.6_