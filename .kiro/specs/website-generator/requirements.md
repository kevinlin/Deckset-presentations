# Requirements Document

## Introduction

This feature will create a dynamic website generator that converts Deckset presentations stored in folders into a comprehensive web-based presentation viewer. The system will automatically discover presentation folders, convert markdown slides to web pages, generate preview images, create a homepage with navigation, and automate the entire process through GitHub Actions.

## Requirements

### Requirement 1

**User Story:** As a presentation author, I want the system to automatically discover all Deckset presentations in my repository, so that I don't have to manually configure each presentation.

#### Acceptance Criteria

1. WHEN the system runs THEN it SHALL scan all folders in the repository root directory
2. WHEN a folder contains a markdown file THEN the system SHALL identify it as a presentation folder
3. WHEN multiple markdown files exist in a folder THEN the system SHALL use the file with the same name as the folder or the first markdown file found
4. IF no markdown file matches the folder name THEN the system SHALL use the first markdown file alphabetically
5. WHEN a folder contains multiple independent presentations (e.g., "Examples", "Demos", "Samples", "Tutorials") THEN the system SHALL treat each markdown file as a separate presentation
6. WHEN extracting titles for multiple presentations in a single folder THEN the system SHALL use markdown filename as fallback instead of folder name, removing numeric prefixes (e.g., "10 Deckset basics" → "Deckset basics")
7. WHEN processing any presentation (single or multiple) THEN the system SHALL use the same EnhancedPresentationProcessor and processing pipeline to ensure consistency
8. WHEN extracting presentation titles THEN the system SHALL use the markdown filename instead of content extraction, applying formatting rules: remove numeric prefixes (e.g., "30 Big text" → "Big Text"), convert dashes/underscores to spaces, and apply title case formatting

### Requirement 2

**User Story:** As a presentation author, I want each presentation converted to a web page with slide images and speaker notes, so that viewers can see both the visual slides and accompanying content.

#### Acceptance Criteria

1. WHEN processing a presentation markdown file THEN the system SHALL split content by slide separators ("---")
2. WHEN extracting slide images THEN the system SHALL parse markdown image syntax (e.g., `![alt](filename.ext)`) from each slide's content to discover referenced images
3. WHEN multiple images exist in a slide THEN the system SHALL use the first image found as the primary slide image
4. WHEN generating the web page THEN the system SHALL create HTML with slide images and corresponding notes
5. WHEN a slide image is missing or no images are referenced THEN the system SHALL display a fallback "redacted.png" image
6. WHEN rendering notes THEN the system SHALL convert markdown formatting to HTML
7. WHEN extracting presentation titles THEN the system SHALL use the markdown filename with formatting rules applied (remove numeric prefixes, convert dashes/underscores to spaces, apply title case)
8. WHEN generating presentation HTML THEN the system SHALL use correct relative asset paths based on presentation nesting depth (e.g., "../assets/file.css" for single presentations, "../../assets/file.css" for presentations in subdirectories like Examples)

### Requirement 3

**User Story:** As a presentation author, I want the generated website to have consistent styling and responsive design, so that presentations look professional on all devices.

#### Acceptance Criteria

1. WHEN generating web pages THEN the system SHALL apply consistent CSS styling using Tailwind CSS
2. WHEN viewing on mobile devices THEN the layout SHALL adapt responsively
3. WHEN displaying slide images THEN they SHALL be properly sized and bordered
4. WHEN rendering text content THEN it SHALL use readable typography and spacing
5. WHEN navigating between pages THEN the styling SHALL remain consistent

### Requirement 4

**User Story:** As a website visitor, I want a homepage that shows all available presentations with preview images, so that I can easily browse and select presentations to view.

#### Acceptance Criteria

1. WHEN generating the homepage THEN the system SHALL list all discovered presentations (including multiple presentations from folders like Examples)
2. WHEN displaying each presentation THEN the system SHALL show a preview image from the first slide
3. WHEN a preview image is unavailable THEN the system SHALL display a placeholder image
4. WHEN clicking on a presentation THEN the system SHALL navigate to the presentation's web page
5. WHEN displaying presentation titles THEN the system SHALL use the extracted title (with proper filename-based fallback for multiple presentations in one folder)
6. WHEN organizing presentations from multiple-presentation folders THEN the system SHALL create appropriate subdirectories (e.g., presentations/Examples/10 Deckset basics.html)
7. WHEN listing presentations on the homepage THEN the system SHALL sort them alphabetically by title (case-insensitive, ignoring Deckset formatting markup)
8. WHEN viewing any presentation page THEN it SHALL include navigation links back to the homepage with correct relative paths based on presentation nesting depth

### Requirement 5

**User Story:** As a system administrator, I want the website generator to handle errors gracefully, so that partial failures don't prevent the entire website from being generated.

#### Acceptance Criteria

1. WHEN a presentation folder cannot be processed THEN the system SHALL log the error and continue with other presentations
2. WHEN slide images are missing THEN the system SHALL use fallback images without failing
3. WHEN markdown parsing fails THEN the system SHALL display raw content or skip the problematic slide
4. WHEN the homepage generation encounters errors THEN it SHALL still generate a basic homepage with available presentations
5. WHEN file operations fail THEN the system SHALL provide clear error messages for debugging

### Requirement 6

**User Story:** As a repository maintainer, I want the website generation to be automated through GitHub Actions, so that the website updates automatically when presentations are added or modified.

#### Acceptance Criteria

1. WHEN changes are pushed to the main branch THEN the GitHub Action SHALL trigger automatically
2. WHEN the action runs THEN it SHALL generate all presentation web pages
3. WHEN the action runs THEN it SHALL generate the homepage with current presentations
4. WHEN generation is complete THEN the action SHALL deploy the website to GitHub Pages or specified hosting
5. IF generation fails THEN the action SHALL report clear error messages

### Requirement 7

**User Story:** As a presentation viewer, I want functional slide navigation with an accurate slide counter and notes toggle, so that I can navigate presentations effectively and view speaker notes when needed.

#### Acceptance Criteria

1. WHEN viewing a presentation THEN the slide counter SHALL display the current slide number and total slide count in the format "X / Y"
2. WHEN navigating between slides using Previous/Next buttons OR keyboard arrows THEN the slide counter SHALL update in real-time to reflect the current slide
3. WHEN clicking the Notes button THEN all speaker notes SHALL toggle between visible and hidden states
4. WHEN notes are shown THEN the Notes button text SHALL change to "Hide Notes" and when hidden SHALL show "Notes"
5. WHEN using keyboard navigation (N key) THEN the notes SHALL toggle visibility the same as clicking the Notes button
6. WHEN navigating slides THEN only one slide SHALL be visible at a time, with all other slides hidden
7. WHEN JavaScript is enabled THEN the presentation container SHALL be marked with 'js-enabled' class for proper CSS styling
8. WHEN on the first slide THEN the Previous button SHALL be disabled
9. WHEN on the last slide THEN the Next button SHALL be disabled
10. WHEN on middle slides THEN both Previous and Next buttons SHALL be enabled
11. WHEN toggling notes THEN the aria-pressed attribute SHALL be properly set for screen reader accessibility