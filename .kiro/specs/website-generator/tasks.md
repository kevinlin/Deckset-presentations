# Implementation Plan

- [x] 1. Basic presentation processing foundation
  - Basic markdown processing with slide splitting using "---" separators (already implemented)
  - Speaker notes extraction for "^" prefixed content (already implemented)
  - Jinja2 template rendering with Tailwind CSS styling (already implemented)
  - Fallback image handling for missing slides (already implemented in template)
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
  - Create slides/redacted.png fallback image (referenced in template but missing)
  - Implement slide image copying from source folders to output directory
  - Create output directory structure management (docs/, slides/, assets/)
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
  - Configure GitHub Pages deployment from generated docs/ directory
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