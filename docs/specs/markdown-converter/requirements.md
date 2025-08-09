# Enhanced Requirements Document

## Introduction

This enhanced Deckset-compatible markdown-to-HTML converter provides comprehensive support for all Deckset markdown features including slide separators, image placement options, speaker notes, code highlighting, mathematical formulas, video/audio embedding, and advanced layout features like multi-column layouts and fit text. The system faithfully reproduces Deckset's markdown semantics in a responsive web environment, with all enhanced features enabled by default.

## Requirements

### Requirement 1: Core Deckset Markdown Compatibility

**User Story:** As a presentation author, I want to use all standard Deckset markdown features in my presentations, so that I can leverage my existing Deckset knowledge and content for the web.

#### Acceptance Criteria

1. WHEN the system encounters slide separators (`---`) THEN it SHALL split content into individual slides
2. WHEN the system processes headings with `[fit]` modifier THEN it SHALL scale the heading to fit the slide width and add `class="fit"` to the HTML element
2.1. WHEN global `fit-headers: #, ##` configuration is set THEN the system SHALL automatically apply fit scaling to all headers of the specified levels
3. WHEN the system encounters speaker notes (lines starting with `^`) THEN it SHALL hide them from slide content but make them accessible
4. WHEN the system processes global commands (e.g., `slidenumbers: true`, `footer: text`) THEN it SHALL apply them to all slides
5. WHEN the system encounters slide-specific commands (e.g., `[.column]`, `[.background-image: file.jpg]`) THEN it SHALL apply them only to that slide
6. WHEN automatic slide breaks are enabled (`slide-dividers: #, ##`) THEN the system SHALL create new slides at specified heading levels
7. WHEN the system encounters unordered list items (lines starting with `- `) THEN it SHALL convert them to HTML `<ul>` and `<li>` elements
8. WHEN the system encounters ordered list items (lines starting with `1. `, `2. `, etc.) THEN it SHALL convert them to HTML `<ol>` and `<li>` elements
9. WHEN list items contain emphasis, code, or other inline formatting THEN the formatting SHALL be preserved within the list items
10. WHEN lists are followed by other content THEN there SHALL be proper separation with paragraph elements
11. WHEN nested lists are created by indenting with four spaces (or one tab) per level THEN the system SHALL render properly nested `<ul>`/`<ol>` structures
12. WHEN nested lists mix ordered and unordered types THEN the system SHALL preserve the mixed structure and indentation levels

### Requirement 2: Advanced Image and Media Support

**User Story:** As a presentation author, I want full control over image placement and scaling options, so that I can create visually compelling presentations with proper image layouts.

#### Acceptance Criteria

1. WHEN an image uses `![](image.jpg)` syntax without modifiers THEN it SHALL be treated as a full-slide background with cover scaling
1.1. WHEN background images are displayed THEN they SHALL be visible above the slide background but below the content text and UI elements
2. WHEN an image uses `![fit](image.jpg)` syntax THEN it SHALL fit entirely on the slide with letterboxing if needed
3. WHEN an image uses `![left](image.jpg)` or `![right](image.jpg)` THEN it SHALL occupy the left or right half of the slide
4. WHEN an image uses `![inline](image.jpg)` THEN it SHALL appear as part of the content flow
5. WHEN an image uses `![inline fill](image.jpg)` THEN it SHALL fill the slide width while remaining inline
6. WHEN an image uses percentage scaling (e.g., `![inline 50%](image.jpg)`) THEN it SHALL scale to that percentage of slide width
7. WHEN multiple inline images are consecutive THEN they SHALL arrange in a grid layout
8. WHEN an image uses `![original](image.jpg)` THEN no darkening filter SHALL be applied
9. WHEN an image uses `![filtered](image.jpg)` THEN a darkening filter SHALL be applied for text readability
10. WHEN an image uses `corner-radius(n)` modifier THEN it SHALL apply border-radius styling
11. WHEN image file paths contain spaces or Unicode characters THEN they SHALL be parsed and rendered correctly
12. WHEN multiple inline image tokens appear back-to-back without whitespace THEN they SHALL be parsed as separate images
13. WHEN the system encounters animated GIFs (`.gif`) THEN they SHALL render as animated images without conversion to static frames
14. WHEN referencing web images via `http(s)` URLs THEN remote images SHALL be supported, subject to network/CORS constraints

### Requirement 3: Video and Audio Embedding

**User Story:** As a presentation author, I want to embed videos and audio files in my presentations, so that I can create multimedia-rich content.

#### Acceptance Criteria

1. WHEN the system encounters `![](video.mp4)` THEN it SHALL embed an HTML5 video player
2. WHEN the system encounters `![](audio.mp3)` THEN it SHALL embed an HTML5 audio player
3. WHEN video/audio uses `autoplay` modifier THEN it SHALL start playing automatically (with browser policy compliance)
4. WHEN video/audio uses `loop` modifier THEN it SHALL repeat when finished
5. WHEN video/audio uses `mute` modifier THEN it SHALL start muted
6. WHEN video/audio uses `hide` modifier THEN the visual element SHALL be hidden but audio SHALL still play
7. WHEN the system encounters YouTube URLs THEN it SHALL embed them as iframes
8. WHEN video uses positioning modifiers (`left`, `right`) THEN it SHALL position accordingly like images
9. WHEN the system encounters common video formats (`.mp4`, `.webm`, `.mov`) THEN it SHALL render them via HTML5 video with appropriate `type` attributes; if playback is unsupported by the browser, a clear fallback message SHALL be shown and processing SHALL continue

### Requirement 4: Code Block Enhancement

**User Story:** As a presentation author, I want advanced code highlighting and line emphasis features, so that I can effectively present code examples.

#### Acceptance Criteria

1. WHEN the system encounters fenced code blocks with language identifiers THEN it SHALL apply syntax highlighting
2. WHEN a code block is preceded by `[.code-highlight: N]` THEN it SHALL highlight line N
3. WHEN a code block is preceded by `[.code-highlight: X-Y]` THEN it SHALL highlight lines X through Y
4. WHEN a code block is preceded by `[.code-highlight: all]` THEN it SHALL highlight all lines
5. WHEN a code block is preceded by `[.code-highlight: none]` THEN no lines SHALL be highlighted
6. WHEN global `code-language: X` is set THEN unlabeled code blocks SHALL use language X for highlighting
7. WHEN code blocks overflow horizontally THEN they SHALL be scrollable while preserving formatting
8. WHEN the system encounters indented code blocks (four leading spaces or a single tab) THEN it SHALL render them as code blocks with syntax highlighting, equivalent to fenced code

### Requirement 5: Mathematical Formula Support

**User Story:** As a presentation author, I want to include mathematical formulas in my presentations, so that I can create technical and scientific content.

#### Acceptance Criteria

1. WHEN the system encounters `$$...$$` delimiters THEN it SHALL render the content as display math using MathJax
2. WHEN the system encounters `$...$` delimiters THEN it SHALL render the content as inline math
3. WHEN math formulas are too wide for the slide THEN they SHALL scale down or allow horizontal scrolling
4. WHEN MathJax fails to load THEN the system SHALL display the raw LaTeX as fallback
5. WHEN math appears inside footnotes or table cells THEN it SHALL be rendered using MathJax with the same rules as elsewhere on the slide

### Requirement 6: Multi-Column Layout Support

**User Story:** As a presentation author, I want to create multi-column layouts within slides, so that I can organize content more effectively.

#### Acceptance Criteria

1. WHEN the system encounters `[.column]` directive THEN it SHALL start a new column on the same slide
2. WHEN multiple `[.column]` directives exist THEN content SHALL be distributed across columns with equal width
3. WHEN columns contain different amounts of content THEN they SHALL align to the top
4. WHEN viewing on narrow screens THEN columns SHALL stack vertically for readability
5. WHEN three or more columns exist THEN each SHALL receive approximately equal width with appropriate gaps

### Requirement 7: Advanced Text and Layout Features

**User Story:** As a presentation author, I want advanced text formatting and layout options, so that I can create professional-looking presentations.

#### Acceptance Criteria

1. WHEN the system encounters blockquotes with `-- Author` attribution THEN it SHALL format them with proper citation styling
2. WHEN the system encounters footnotes (`[^1]` and `[^1]: text`) THEN it SHALL display them at the bottom of the slide
3. WHEN the system encounters emoji shortcodes (`:smile:`) THEN it SHALL convert them to Unicode emojis
4. WHEN the system encounters tables THEN it SHALL render them with proper alignment based on separator markers
5. WHEN global `autoscale: true` is set THEN text SHALL scale down when it overflows the slide
6. WHEN slide numbers are enabled (`slidenumbers: true`) THEN each slide SHALL display its number
7. WHEN footer text is set (`footer: text`) THEN it SHALL appear on every slide unless overridden
8. WHEN the system encounters safe inline HTML (e.g., `<br/>`, `<a name="id"></a>`) THEN it SHALL preserve and sanitize these elements, applying allowed attributes only
9. WHEN footnote references appear inside tables, headings, or captions THEN they SHALL render and function correctly; footnote definitions MAY appear anywhere in the document and SHALL be unique by label
10. WHEN multiple references point to the same footnote definition across slides THEN they SHALL all resolve correctly and display on the slide where the reference appears

### Requirement 8: Responsive Design and Accessibility

**User Story:** As a website visitor, I want presentations to work well on all devices and be accessible, so that I can view content regardless of my device or abilities.

#### Acceptance Criteria

1. WHEN viewing on mobile devices THEN slide content SHALL reflow and scale appropriately
2. WHEN viewing on large screens THEN slides SHALL maintain readable proportions with max-width constraints
3. WHEN images are displayed THEN they SHALL have appropriate alt text for screen readers
4. WHEN videos are embedded THEN they SHALL include proper controls and accessibility attributes
5. WHEN using keyboard navigation THEN all interactive elements SHALL be accessible via keyboard
6. WHEN printing or saving as PDF THEN each slide SHALL start on a new page

### Requirement 9: Enhanced Error Handling and Validation

**User Story:** As a presentation author, I want clear feedback when my markdown has issues, so that I can fix problems quickly.

#### Acceptance Criteria

1. WHEN invalid Deckset syntax is encountered THEN the system SHALL log specific warnings with line numbers
2. WHEN referenced images are missing THEN the system SHALL use fallback images and log warnings
3. WHEN video/audio files are missing THEN the system SHALL display placeholder content and continue processing
4. WHEN MathJax formulas have syntax errors THEN the system SHALL display the raw LaTeX and log warnings
5. WHEN code highlighting fails THEN the system SHALL display unstyled code and continue processing

### Requirement 10: Typography and Presentation Formatting

**User Story:** As a presentation author, I want text and headers to be sized appropriately for presentation slides, so that content is readable and visually appealing at various viewing distances and screen sizes.

#### Acceptance Criteria

1. WHEN rendering slide content THEN the system SHALL use an 18px base font size for desktop presentations
2. WHEN rendering headers THEN the system SHALL use a clear typographic hierarchy:
   - H1: 3.5rem (63px) with font-weight 700
   - H2: 2.75rem (49.5px) with font-weight 600  
   - H3: 2.125rem (38.25px) with font-weight 600
   - H4: 1.625rem (29.25px) with font-weight 500
   - H5: 1.25rem (22.5px) with font-weight 500
   - H6: 1.125rem (20.25px) with font-weight 500
3. WHEN rendering paragraph text THEN it SHALL use 1.25rem (22.5px) font size with 1.6 line height
4. WHEN rendering list items THEN they SHALL use 1.25rem (22.5px) font size with 1.6 line height
5. WHEN rendering blockquotes THEN they SHALL use 1.375rem (24.75px) font size with italic styling
6. WHEN rendering inline code THEN it SHALL use 1.125rem (20.25px) font size with monospace font
7. WHEN viewing on tablets (max-width: 768px) THEN font sizes SHALL scale down proportionally with 16px base
8. WHEN viewing on mobile (max-width: 480px) THEN font sizes SHALL scale down proportionally with 14px base
9. WHEN using fit text THEN the system SHALL scale text to clamp(3rem, 15vw, 12rem) for optimal presentation sizing

### Requirement 11: Performance and Optimization

**User Story:** As a website visitor, I want presentations to load quickly and perform well, so that I have a smooth viewing experience.

#### Acceptance Criteria

1. WHEN generating websites THEN the system SHALL optimize images for web delivery
2. WHEN loading presentations THEN CSS and JavaScript SHALL be minified and cached
3. WHEN viewing slides THEN images SHALL load progressively to improve perceived performance
4. WHEN navigating between slides THEN transitions SHALL be smooth and responsive
5. WHEN the website is accessed THEN it SHALL achieve good performance scores on web vitals metrics

### Requirement 12: Template Maintainability

**User Story:** As a developer or designer, I want templates to be organized in separate files, so that I can easily maintain and update the presentation layout and styling.

#### Acceptance Criteria

1. WHEN templates are needed THEN the system SHALL load them from separate Jinja2 template files
2. WHEN updating slide layouts THEN changes SHALL be made in `templates/slide.html` file
3. WHEN updating homepage layout THEN changes SHALL be made in `templates/homepage.html` file
4. WHEN template files are modified THEN changes SHALL be immediately available without code changes
5. WHEN templates are versioned THEN they SHALL be tracked in version control as separate files

### Requirement 13: Slide Aspect Ratio (16:9 Standard)

**User Story:** As a presenter, I want every slide to use a consistent 16:9 aspect ratio so that my presentations reliably fit modern displays and video platforms.

#### Acceptance Criteria

1. WHEN rendering slide containers THEN they SHALL preserve a strict 16:9 aspect ratio on all screen sizes
2. WHEN the viewport aspect ratio differs from 16:9 THEN slides SHALL scale to fit while maintaining 16:9, with neutral letterboxing or pillarboxing as needed, and without cropping slide content
3. WHEN printing or exporting to PDF THEN each slide page SHALL be rendered at a 16:9 ratio with consistent margins
4. WHEN background images or videos are displayed THEN they SHALL scale within the 16:9 container without distortion; positioning modifiers (e.g., `left`, `right`, `fit`, `fill`) SHALL respect the 16:9 bounds
5. WHEN multi-column layouts, inline images, or image grids are used THEN the layout SHALL compute within the 16:9 container so that elements do not overflow the slide
6. WHEN autoscale or `[fit]` text is applied THEN scaling SHALL occur within the 16:9 safe content area (no clipping)

### Requirement 14: Markdown Link Support

**User Story:** As a presentation author and viewer, I want standard Markdown links to be clickable, so that I can reference external and internal resources from my slides.

#### Acceptance Criteria

1. WHEN the system encounters Markdown links in the form `[link-text](link-url)` THEN it SHALL render an HTML `<a>` element with the correct `href`
2. WHEN links appear inside headings, paragraphs, list items, blockquotes, table cells, or footnotes THEN they SHALL render and function consistently
3. WHEN the link target uses `http://` or `https://` THEN the rendered link SHALL include `target="_blank"` and `rel="noopener noreferrer"`
4. WHEN the link target is an internal anchor (e.g., `#section`) or a relative path THEN the link SHALL open in the same tab without adding `rel` attributes
5. WHEN the Markdown link includes a title (e.g., `[text](url \"title\")`) THEN the rendered link SHALL include a `title` attribute
6. WHEN processing links THEN the system SHALL sanitize URLs and only allow safe schemes (`http`, `https`, `mailto`, `tel`, and `#` anchors); unsupported or unsafe schemes SHALL be rendered as plain text
7. WHEN printing or exporting to PDF THEN links SHALL remain present and clickable in the output

### Requirement 15: Internal Anchors and Cross-Slide Linking

**User Story:** As a viewer, I want to navigate to specific sections within or across slides using internal anchors, so that I can jump to relevant content quickly.

#### Acceptance Criteria

1. WHEN anchors are defined via `<a name="id"></a>` or generated from headings THEN the system SHALL assign stable, unique `id` attributes to target elements
2. WHEN a link with a fragment identifier (e.g., `[See more](#details)`) is clicked THEN the viewer SHALL navigate to the slide containing the target `id` and focus/scroll to it within the slide
3. WHEN multiple anchors share the same proposed `id` THEN the system SHALL de-duplicate by suffixing to ensure uniqueness and SHALL update internal links accordingly during generation
4. WHEN an internal anchor cannot be resolved THEN the system SHALL leave the link inert and log a warning without breaking slide navigation