# Deckset Markdown to HTML Slide Generator Specification

## Overview

The Markdown-to-webpage generator is a tool that **converts a Deckset-compatible Markdown file into a responsive static HTML website**. The output preserves Deckset’s slide-based layout logic, allowing users to author presentations in Markdown and view them in any web browser. Each section of the Markdown becomes an HTML “slide” with content formatted according to Deckset’s syntax and extended features. A clean, default theme is applied for readability (e.g. simple fonts, high-contrast text on a plain background), and the generated site is responsive for various screen sizes.

This specification outlines the supported Markdown features, how they are translated to HTML/CSS, and the behavior of extended Deckset syntax (layout directives, image modifiers, speaker notes, etc.). **All Deckset Markdown conventions** – such as slide separators, image placement options, speaker notes, code highlighting, and special formatting – are honored to maximize compatibility.

## Input: Deckset Markdown Features

The generator accepts a single Markdown file written with Deckset conventions. It supports the following **Deckset Markdown features** (as described in Deckset’s documentation):

* **Slide delimiters:** Use three dashes `---` on a blank line (with a blank line above and below) to start a new slide. (This is Deckset’s primary method for separating slides.)

* **Automatic slide breaks by headings:** Optionally, the user can enable automatic slide breaks at certain heading levels using Deckset’s `slide-dividers` command. For example, a global command `slide-dividers: #, ##, ###, ####` at the top of the file will treat each H1, H2, H3, or H4 heading as the start of a new slide. The generator will support this by splitting slides whenever a heading of the specified levels is encountered (if this setting is present).

* **Headings and text styles:** Markdown `#` through `####` headings are supported, corresponding to decreasing text sizes (Deckset defines “Large”, “Regular”, “Small”, “Tiny” headings). Standard **bold**, *italic*, ~~strikethrough~~, and `inline code` syntax is supported within slide text. Combination styles (like `_**bold+italic**_`) are also supported. Subscript and superscript can be included using HTML tags (e.g. `H<sub>2</sub>O`). Links can be included with `[Link text](URL)` syntax, and Deckset-style emoji shortcodes (e.g. `:smile:`) will be converted to actual Unicode emojis.

* **Paragraphs and line breaks:** A blank line in the Markdown separates paragraphs. In regular paragraphs, Deckset respects manual line breaks – if you break a line in the source, the output will start a new line. The generator will reproduce this behavior by inserting `<br>` tags or preserving line breaks in paragraph text. For elements that cannot directly contain newline characters (like headings or footer text), the HTML `<br>` tag can be used in Markdown to force a line break.

* **Lists:** Unordered lists (`-` or `*`) and numbered lists (`1.`, `2.`) are supported, including nested lists by indenting with spaces. The generator outputs these as HTML `<ul>`/`<ol>` lists with `<li>` items. If Deckset’s **build steps** feature is enabled (via `build-lists: true` at the top of the file), list items will appear one by one in Deckset. In the static HTML output, this could be simulated by adding a CSS class (e.g. `build-list`) to each list and a data-attribute to each list item indicating its index, allowing optional JavaScript to reveal items sequentially. However, by default the static site will show all list items (ensuring all content is accessible without scripts, since build steps affect only presenter mode). The `build-lists` setting is noted and could be used for progressive disclosure if an interactive mode is added.

* **Blockquotes:** A `>` at the start of a line indicates a block quote. The generator will wrap such text in `<blockquote>` tags. If the quote is followed by a line prefixed with `--` (two hyphens), Deckset treats that as the author attribution. For example:

  ```markdown
  > "The best way to predict the future is to invent it"  
  -- Alan Kay
  ```

  will be rendered as a quoted text with an author caption. The HTML output may enclose the author in a `<cite>` or a span with class for styling (e.g. smaller italics).

* **Tables:** Pipe-separated tables are supported. The syntax uses `|` to separate cells and a header separator of `---`. For example:

  ```markdown
  | Header 1 | Header 2 | Header 3 |
  |----------|:--------:|---------:|
  | Cell 1   | Cell 2   | Cell 3   |
  | Cell 4   | Cell 5   | Cell 6   |
  ```

  will produce a table with a header row and two body rows. Alignment markers (`:`) in the separator line control text alignment (left, center, right), which the generator will translate to corresponding CSS text-align on the `<td>` or `<th>` elements.

* **Footnotes:** Deckset supports Markdown footnotes. Footnote references like `[^1]` in text and definitions like `[^1]: footnote text` can be placed anywhere in the Markdown. The generator will gather footnote definitions and ensure that any footnote referenced on a slide is displayed at the bottom of that slide (in smaller text). Each footnote reference in HTML will be a clickable superscript link that scrolls to or toggles the corresponding footnote text. Footnote IDs must be unique across the document; the generator will enforce this by warning on duplicates or auto-uniquing if necessary. If a footnote is defined on one slide but referenced on another, the generator will still find the definition (since all footnotes are parsed globally) and include the footnote text on every slide where the reference appears (so each slide is self-contained for its citations). Named footnote labels (non-numeric, e.g. `[^Wiles, 1995]`) are also supported.

* **Mathematical formulas:** Deckset uses MathJax to render TeX math notation written between `$$…$$` delimiters. The generator will likewise support LaTeX math. Any content between `$$` markers will be treated as a display math formula and rendered via MathJax (included in the output). Inline math can be written with double-dollar or single-dollar (the Deckset docs use `$$a$$` for inline, but we will accept the common `$...$` as inline math as well). The MathJax library (or an alternative like KaTeX) will be loaded in the HTML so that formulas display properly. We will also configure MathJax for responsiveness – Deckset automatically scales down large equations to fit the slide, and similarly, our CSS/MathJax settings will shrink the font-size of math if it overflows its container (or allow horizontal scrolling for extremely wide equations as a fallback).

* **Emoji shortcodes:** The generator recognizes Slack/GitHub-style emoji codes and replaces them with the corresponding Unicode emoji characters. For example, `:sunflower:` becomes 🌻. We will use a predefined mapping (as in Deckset’s supported emoji list) to translate codes. (If an emoji code isn’t recognized, it will be left as-is or removed, similar to Deckset’s behavior of only supporting certain codes.)

## Output: HTML Slide Structure

The output will consist of standard static HTML, CSS, and optional JavaScript, structured as follows:

* **One HTML file per presentation** (by default). All slides can be contained in a single HTML file, each in its own container (e.g. a `<section>` or `<div>` with class `"slide"`). This allows easy navigation (possibly by scrolling or via JS for slide-by-slide controls) and enables intra-document links to work (anchors linking to slides). Optionally, the generator could offer a mode to output each slide as a separate HTML page, but the primary approach is a single-page presentation for simplicity.

* **Slide containers:** Each slide is wrapped in an element with a distinct ID and a common class. For example:

  ```html
  <section class="slide" id="slide-1">
      ... content ...
  </section>
  ```

  The ID can be auto-generated (like `slide-1`, `slide-2`, etc., or derived from the slide’s title text) to facilitate direct linking to slides and internal navigation. If the author manually inserted anchor tags in the Markdown (e.g. `<a name="intro-slide"/>`), the generator will preserve them in the corresponding slide, so links like `[see Intro](#intro-slide)` will function within the page to jump to that slide.

* **Slide content layout:** Inside each slide container, the content from the Markdown appears in HTML in a structure mimicking Deckset’s layout logic:

  * The first heading in a slide (e.g. an `# H1` at the top) is typically the slide title. We will allow it to be rendered as an `<h1>` (or `<h2>` etc., depending on the level used) inside the slide. We will apply CSS to make the top-level slide heading visually stand out (larger font, maybe centered). Subsequent headings (H2, H3, etc.) on the same slide will be smaller per their levels.
  * Paragraphs remain as `<p>` elements. Consecutive text lines in the Markdown without blank separation will be joined in one paragraph (with explicit `<br>` if a manual break was in the source).
  * Lists become `<ul>` or `<ol>` as appropriate, with nested `<ul>` for sublists.
  * Blockquotes become `<blockquote>` containing the quote text. If an attribution line (`-- Author`) was provided, it could be included in the `<blockquote>` (perhaps in a `<footer>` tag or a `<cite>` element inside the blockquote for semantic HTML5).
  * Horizontal separators (`---`) that indicate new slides will not appear in output (they are consumed by the slide splitting logic). If the user wants a visible horizontal rule within a slide, they can use `<hr>` in Markdown; the generator will pass that through to HTML.

* **Columns:** The generator supports Deckset’s multi-column layout command. In Markdown, a line containing `[.column]` indicates that subsequent content should start a new column on the same slide. We will implement this by splitting the slide’s content into multiple column containers:

  * When parsing a slide, if `[.column]` is encountered, the generator closes the current column’s `<div>` and starts a new one. For example, the slide:

    ```markdown
    [.column]
    ## Column One Title
    Some text in first column.

    [.column]
    ## Column Two Title
    More text in second column.
    ```

    would produce HTML roughly as:

    ```html
    <section class="slide">
      <div class="column"> 
        <h2>Column One Title</h2>
        <p>Some text in first column.</p>
      </div>
      <div class="column">
        <h2>Column Two Title</h2>
        <p>More text in second column.</p>
      </div>
    </section>
    ```

    The CSS will use a flexbox or grid layout for `.slide` to position `.column` divs side by side. By default, column widths are evenly divided based on the number of columns. If three columns are present, each gets \~33% width, etc., with some gap between. On very narrow screens, the CSS can stack columns vertically for readability (responsive behavior).
  * Content continues in the same column until another `[.column]` or the slide ends. You can have any number of columns, but note that more columns result in less width for each. The generator will ensure each column’s content is wrapped and will apply Deckset’s auto-scaling logic (if enabled) to shrink text if it overflows the column.

* **Global background:** If the Markdown begins with a `background-image: filename.jpg` command, the generator will apply that image as a background to **all** slides (unless overridden per slide). This could be implemented via a CSS `body { background: url(...); }` or by adding a class to each slide that sets that background. If only a single global background is used, we might set it on a parent container. The user can override or hide it on individual slides by using per-slide commands (Deckset allows `[.background-image: other.jpg]` for a specific slide or possibly `[.hide-background]` – the latter is not explicitly documented, but we could support a slide-level command to remove background). If not implementing override, at least global background will cover all slides uniformly.

* **Default theme styling:** The provided HTML will link to a default CSS file that defines a clean theme. This theme will ensure:

  * Slides have a consistent background (e.g. white or very light color by default, since we’re not matching Deckset’s dark themes unless specified).
  * Text is a legible web font (e.g. a sans-serif for headings and body).
  * Heading styles: The CSS will size headings relative to the slide (e.g. an H1 might be 2em or larger, H2 1.5em, etc.) to mimic Deckset’s hierarchy (Deckset’s “Large” vs “Regular” headings). If a heading uses the `[fit]` tag (see **Fit text** below), special styling or script will adjust its size.
  * Positioning: By default, content will be top-left aligned within a slide container with some padding. We may center content vertically/horizontally if desired for a more presentation-like look, but since it’s a webpage, a top alignment with scrolling is acceptable. A simple approach is to center horizontally (for title slides, etc.) but allow vertical scrolling if content exceeds one screen.
  * Slide spacing: If slides are stacked vertically (for scroll navigation), we add adequate margin between slide sections (or use a full-page height styling). If using a JavaScript to navigate slides (see below), slides might be absolutely positioned and hidden except the current one.
  * Print/PDF support: The CSS should also allow the page to be printed or saved as PDF, with each slide starting on a new page (e.g. use page-breaks at slide boundaries).

* **Responsive behavior:** The site is responsive:

  * On large screens (desktop), each slide’s content will typically fit within a 16:9 or 4:3 viewport. We may use a max-width on slides (e.g. 1024px) for readability. Text will wrap as needed and images/media will scale down if the browser window is smaller.
  * On small screens (mobile), the slide container will naturally shrink to device width. Text will reflow vertically. Multi-column layouts will stack columns vertically if the screen is too narrow (handled via a CSS media query).
  * Images and videos will have max-width: 100% to scale down to container width. If an image is meant to fill the background, it will use CSS `background-size: cover` or `contain` depending on the fit setting.
  * Navigation on small screens might simply be scroll (since all slides in one page can be scrolled). On larger screens or in “slideshow mode”, we might add JS to allow arrow-key navigation (but the specification focuses on static output, so JS is optional).

* **Navigation and scripting (optional):** While the output is static, we can enhance it with a bit of JavaScript for slide navigation and transitions:

  * For example, include a script that detects arrow key presses or swipes to move between slides (by scrolling or toggling which slide is visible). If transitions are enabled (see **Slide Transitions** below), this script would add a CSS class or use animations when showing/hiding slides.
  * A navigation UI (like “Prev/Next” buttons or a slide index) could be added. But by default, a user can scroll or use browser find, and internal links in the content (if any) will work.
  * All essential content is accessible without scripts; JS is for convenience/animation only.

## Slide Content Features and Rendering Rules

This section details how specific Deckset Markdown features are interpreted and rendered by the generator.

### Slide Titles and Fit Text

If a heading line in Markdown is prefixed with `[fit]`, Deckset will scale that heading to fit the slide. Our generator will treat `[fit]` as an inline instruction for large text:

* We will remove the `[fit]` marker from the text and add a CSS class or attribute to the resulting `<h1>`/`<h2>` element (e.g. `<h1 class="fit">`…).
* The default CSS will detect `.fit` on a heading and dynamically adjust its font-size to fill the available width (while maintaining line breaks). A simple approach is to use a large font-size or use the `fit-text` technique (possibly via a small JS that measures the parent container and scales the font). This achieves Deckset’s “fit header to slide” functionality. If the global `fit-header: #, ##` command is used in the Markdown (to auto-fit all H1 and H2, for example), the generator will behave as if each specified heading level had `[fit]` applied. (This can be done by automatically adding the `fit` class to all those headings in output.)
* Example: Markdown `# [fit] Big Announcement` will produce `<h1 class="fit">Big Announcement</h1>` in HTML, which via CSS/JS is sized to span the slide width.

### Presenter Notes

Deckset allows speaker notes by starting a paragraph with `^`. The generator will parse any lines beginning with `^` as **presenter notes**:

* These notes are **not displayed on the slide** content visible to viewers. Instead, they will be included as hidden elements in the HTML. We will wrap them in an `<aside class="speaker-notes">` tag (or similar) and use CSS to hide it by default.
* For example, `^ This is a presenter note.` in Markdown might become `<aside class="speaker-notes">This is a presenter note.</aside>` in the HTML for that slide, styled with `display: none` by default.
* Because this is a static site (no separate presenter console), we could provide an optional way to reveal these notes. For instance, a small script or a checkbox can toggle visibility of all notes (so a presenter using the page can see their cues). By default, the notes remain hidden, mimicking Deckset’s behavior of not showing them on the slides.
* The content of notes is preserved (it can include Markdown formatting which we will render as needed within the aside). If Deckset’s `presenter-notes: ...` style command is present (to change text size or alignment of notes), the generator can map that to a CSS style for `.speaker-notes` (e.g. `text-scale(2)` might double the font size in the aside, `alignment(left)` might left-align the note text). This is a nice-to-have; at minimum, we support the existence of notes.

### Hidden Slides and Content

If any part of the Markdown is enclosed in an HTML comment (`<!-- ... -->`), Deckset will skip rendering that content (useful for “hiding” slides without deleting them). Our generator will simply omit any content that is inside HTML comments from the output. We will treat `<!--` on its own line as the start of hidden content and `-->` as the end. Content in between is neither rendered nor kept in the HTML (or we could keep it as an HTML comment in the output if the user specifically wants it present but not visible – by default, we’ll strip it out entirely to avoid bloating the HTML). This way, “Hidden” slides in the source are not visible on the webpage, matching Deckset’s behavior.

### Images

Deckset distinguishes between **background images** (images that cover the slide background) and **inline images** (images that appear as part of the slide content flow). The generator will support both, using Deckset’s alt-text keywords to determine placement and styling:

* **Background Images:** An image syntax on its own line with no special `alt` text (or with certain keywords) is treated as a slide background. For example, in Markdown:

  ```markdown
  ![](photo.jpg)
  ```

  If this appears as the first element of a slide (and especially if followed by no other content or just a heading), Deckset will use `photo.jpg` as a full-slide background. We implement this by setting the slide’s background via CSS or an absolutely positioned `<img>`:

  * The generator will detect an image syntax that is not marked `inline` and which is placed at the top of a slide or between paragraphs. By default, we interpret `![](file.jpg)` as a **full-cover background**. The output HTML might not include an `<img>` tag at that location; instead, it could add a style to the slide container like `style="background-image:url('file.jpg')"` with `background-size: cover`. This ensures the image covers the slide area.
  * If the author uses the `![fit](file.jpg)` syntax, Deckset does not crop the image but fits it entirely on the slide (likely letterboxing it). We can implement `fit` by using `background-size: contain` instead of cover, so the entire image is visible (with possible blank margins if aspect ratio differs).
  * Multiple background images: Deckset supports multiple background images on one slide by listing multiple `![]()` lines. In such cases, the generator will overlay the images in the order given. Practically, we can insert multiple absolutely positioned `<img>` tags inside the slide container (each perhaps with `position:absolute; top:0; left:0; width:100%; height:100%`) so they all stack. The first image will be the bottom layer and subsequent ones on top. Alternatively, we can stack multiple backgrounds via CSS (noting that multiple backgrounds via CSS is possible with comma-separated URLs). However, layering images might require handling transparency or z-index if the intention is to composite them. Since Deckset documentation doesn’t detail exactly how multiple backgrounds appear, we will assume they are overlaid or tiled. We will choose a reasonable approach (e.g., overlay and let later images potentially cover earlier ones unless transparency is used).
  * **Positioning and split-screen:** If the alt text includes `left` or `right` (e.g. `![left](image.jpg)`), Deckset places that image on the left or right half of the slide. We implement this by wrapping the image in a container that occupies 50% width of the slide aligned to left or right, or by using CSS classes like `.bg-left` or `.bg-right` on the slide container which apply the image as background only on that half. Simpler: the generator can create a two-column layout for the slide with the image in one column as a background and the content in the other column. In practice, we can also absolutely position the image to cover left 50% of the slide (`left:0; width:50%; height:100%`) if it’s purely background. For a `![right](image.jpg)`, position it on the right half (`right:0; width:50%`). Deckset uses this for “split slides” where an image occupies one side and text on the other.

    * We will add corresponding classes or structures in HTML. For example, add `<div class="bg-image left"><img src="..."/></div>` that is styled to cover the left half. Or simply set the slide’s background with a gradient: left half image, right half solid – but using an actual `<img>` may give more control. The text content should be restricted to the opposite half (we can achieve that by wrapping text in a `<div class="half right">` that is 50% width).
    * If `left`/`right` is combined with `fit` or a percentage (see below), we adjust image sizing accordingly.
  * **Filters:** Deckset automatically applies a darkening filter to background images when there is slide text over them, to maintain readability. By default, our theme will mimic this by adding an overlay or using CSS filter. For example, if an image is set as a background and there is text on the slide, we can add `background-color: rgba(0,0,0,0.4)` overlay on that slide (or CSS `filter: brightness(50%)` on the image) to dim it. If the user wants to disable that, they can use the `original` keyword.

    * `![original](image.jpg)`: The `original` keyword tells Deckset **not** to apply any darkening filter. We will interpret this as no overlay: the image is shown as-is at full brightness.
    * Conversely, Deckset has a `filtered` keyword to force apply the filter even if it normally wouldn’t (e.g. if an image is on one half but you still want it dimmed). The generator will support `filtered` by always adding the dimming overlay for that image.
  * **Scaling (zoom):** If the alt text contains a percentage (e.g. `![original 250%](image.jpg)`), Deckset scales the background image by that factor. We will apply this by setting the background-size to that percentage of the slide or using a CSS transform scale on the `<img>`. For example, `250%` means the image is 2.5× its original size, effectively zooming in (so the image likely crops because it still covers the slide). The generator can set a CSS rule to scale the image element accordingly (and then use overflow hidden or just let it overflow off slide edges).
  * **Global background image command:** As noted, `background-image: file.jpg` at the top of the Markdown applies a background to every slide. The generator will implement this by adding a default background style to all slide containers unless a slide has its own specific background image (in which case that slide’s background overrides the global one). If a slide should have no background despite the global setting, Deckset might have a way to disable (possibly an `[.no-background]` command, though not documented – if not, users could set a transparent 1x1 PNG as a background to simulate none). We can provide a custom syntax like `[.background-image: none]` or `[.hide-background]` for a slide to override, if needed, or simply instruct users to comment out the global line for certain slides (which is not straightforward). This is an edge case – we will assume either all slides share the background or the user overrides by setting a different background on specific slides as needed.

* **Inline Images:** To include an image as part of the slide content (not as a background), Deckset uses the `![inline]` keyword in the alt text. The generator will treat any image with `inline` in its alt tag as a normal HTML `<img>` element placed in the content flow:

  * Syntax: `![inline](picture.png)` will produce `<img src="picture.png" class="inline-img" alt=""/>` in the HTML inside the slide. By default, we will style `.inline-img` to be centered or left-aligned within the text block, with margin around it. It will not be full-screen; it will display at its natural size or scaled as specified.
  * `![inline fill](picture.png)`: The `fill` keyword on an inline image tells Deckset to **fill the slide with that image** (similar to a background, but considered inline). In practice, Deckset likely enlarges the image to cover most of the slide while still being an object on the slide. Our implementation will set that image to width: 100% (or height: 100% if needed) so that it fills the slide’s width (and perhaps height). Essentially, `inline fill` means treat it like a full-bleed image but still an `<img>` tag (perhaps to allow it to mix with text above/below). We will likely just use `width: 100%` for `inline fill` images, which makes it as wide as the slide container.
  * Custom scaling: `![inline 50%](picture.png)` scales the image to 50% of the slide’s width. The generator will parse the percentage and output an `<img style="width:50%">` (or assign a class that applies the width via CSS). We interpret the percentage as relative to slide width (since Deckset does).
  * **Image grids:** If multiple inline images are placed consecutively (with no intervening text or line break separating them), Deckset arranges them as a grid. For example:

    ```markdown
    ![inline fill](img1.jpg) ![inline fill](img2.jpg)  
    ![inline fill](img3.jpg)
    ```

    might produce two images side-by-side on the first “row” and one centered on the second row. To mimic this, the generator will detect when multiple images are in the same paragraph or sequence. We can group them into a container (e.g. `<div class="image-grid">`) and use CSS grid or flex-wrap to arrange them. The rule could be: if two images are on one line in Markdown, put them in a row with equal widths. If a line break then another image, that becomes the next row. Essentially, images separated by only space/newline with each marked `inline` will tile. We will apply a straightforward approach: each inline image by default is inline-block; if they fit in one line, they’ll sit as columns. Or explicitly structure rows in HTML if needed for consistent layout.

    * We’ll also ensure spacing between images is even. The images in a grid can all use the `fill` modifier if the author wants them each to take maximum size in their grid cell.
  * **Corner radius:** Deckset allows rounding of image corners via a `corner-radius(x)` alt tag syntax. The generator will parse `corner-radius(n)` and apply a CSS `border-radius: npx` to that image. For example, `![inline corner-radius(16)](photo.png)` will result in an `<img>` with `style="border-radius:16px;"` or a class that applies that. (We will support this for inline images, and possibly for background images if it ever appears, though backgrounds typically cover full slide so corner radius isn’t common there.)

In summary, the generator covers all Deckset image options: **full backgrounds, fitted or original backgrounds, split left/right images, filtered/unfiltered overlays, zoomed backgrounds, inline images with fill or percentage scaling, image grids, and rounded corners** – as documented in Deckset. All images will have appropriate responsive behavior (max-width: 100% for inline images so they shrink on small screens, etc.).

### Video and Audio Support

Deckset supports embedding videos and audio with similar syntax to images. Our generator will provide equivalent support:

* **Videos:** To embed a video file (e.g. MP4, MOV) or a YouTube link:

  * Syntax: `![](video.mp4)` on a slide by itself will be treated by Deckset as a video player embedded in the slide. We will output an HTML `<video>` tag for local video files. For example, `![](clip.mp4)` becomes:

    ```html
    <video src="clip.mp4" controls></video>
    ```

    with `controls` enabled so the user can play/pause. We will also add attributes based on modifiers (see below).
  * `![inline](video.mp4)`: If the `inline` keyword is present, we treat the video similar to an inline image – i.e. not full-slide background. This essentially means we’ll include the `<video>` element in the content flow (perhaps centered by default) as opposed to making it a background video. Without `inline`, if a video is the first element on a slide, Deckset might treat it as a full background or full-width element. Our approach: if `inline` is not specified, we will still embed the video as a `<video>` tag, but we might style it differently (possibly full width).

    * We likely won’t implement video as actual CSS background, because unlike images, videos need HTML tags to play. So even a “background video” will be an HTML `<video>` covering the slide with appropriate positioning.
    * If a video is meant to be background (no inline keyword and perhaps with no other content), we will position the `<video>` absolutely to fill the slide (100% width/height, with object-fit: cover to crop appropriately). If `![fit]` is used on a video, we use object-fit: contain to show the whole frame.
  * **YouTube and online videos:** If the URL in the image syntax is a YouTube link (or Vimeo etc.), Deckset will embed that video via an iframe. The generator will detect common video URL patterns:

    * For YouTube, a link like `https://www.youtube.com/watch?v=XXXXX` or short form `youtu.be/XXXXX` will be replaced with an `<iframe width="560" height="315" src="https://www.youtube.com/embed/XXXXX?start=30&autoplay=0" frameborder="0" allowfullscreen></iframe>`. (We’ll include `?start=Ns` if a `?t=` parameter was provided in the link for start time.) We ensure `autoplay` is off by default to comply with browser policies (unless user specifically includes `autoplay` keyword, see below).
    * For Vimeo or others, similar embed handling can be added if needed.
    * If the generator is offline and cannot fetch oEmbed info, we rely on known patterns or simply embed the provided URL in a generic way (YouTube being the main case explicitly documented).
  * **Video layout modifiers:** Deckset uses the same keywords for video positioning and sizing as for images:

    * `left` or `right`: places the video on the left or right half of the slide. We will wrap the `<video>` in a container or apply a class to float it to one side at 50% width, with the other side available for text. (Analogous to the image split logic: a `.video-left` class could give the video container 50% width and float it left).
    * `fit` vs `fill`: We interpret `fit` for video as *contain* (show entire frame) and `fill` as *cover* (zoom to fill frame). We can achieve this with the CSS property `object-fit` on the video element. For `fit`, use `object-fit: contain` so no portion of video is cut (letterboxing might occur); for `fill` or default, use `object-fit: cover` so it fills the container cropping if necessary.
    * Percentage (e.g. `50%`): scale the video player to 50% width of the slide. This is straightforward by setting the video element’s width via CSS or attribute.
    * `hide`: If `hide` is present, the video’s visual element is hidden but if it has audio, the audio will still play. We implement this by setting the video element’s CSS to `display:none` or perhaps use the `<audio>` element instead. However, to play audio from a video while hidden might be tricky because many browsers will pause media if not visible. As a simpler approach, if `hide` is used and the source is a video file, we will output an `<audio>` element with the audio track (if the file is audio-only or if we extract the audio?). This might be beyond scope – instead, we can still include the `<video>` hidden and add the `muted` attribute’s opposite (actually, if hidden and not muted, some browsers might still allow play with user interaction). Alternatively, we interpret `hide` on a local video as “do not show any controls or visuals” – so we could output the `<video>` with `height="0" width="0"` but with audio. Given complexity, a simpler interpretation: `hide` for video we treat similarly to `hide` for audio (below) – no visual icon. Possibly we could indicate to user that auto-play of hidden video/audio may not work without user gesture (due to browser policies).
  * **Video playback controls:** Deckset supports `autoplay`, `loop`, and `mute` directives in the alt text:

    * If `autoplay` is present, we add the `autoplay` attribute to the video tag, so it starts playing automatically when the slide loads. *Note:* On the web, autoplay with sound is often blocked; Deckset likely expects videos to be used in presentations where it might be allowed. We will include `autoplay` if requested, but also recommend using `mute` to allow autoplay (most browsers allow muted autoplay). Perhaps we even automatically mute if autoplay is on to satisfy browser policy.
    * `loop` results in the `loop` attribute on `<video>` (video will restart when ended).
    * `mute` results in `muted` attribute (video plays with no sound). If both autoplay and mute are present, most browsers will then autoplay fine.
    * We will also add `controls` attribute by default unless `autoplay` and `hide controls` is intended. Deckset likely hides controls during a live presentation, but for a static webpage it’s user-friendly to keep controls. We can decide to always show controls unless `autoplay` is used (and maybe add controls after a user interacts).
    * Example: `![right autoplay mute](clip.mp4)` would generate `<video src="clip.mp4" class="video-right" autoplay muted loop>` (with loop only if specified).
  * **Auto-advance:** Deckset has a feature where if a video finishes and has the `autoadvance` tag, it will automatically move to the next slide. In a static HTML site, this would require JavaScript to detect video end and then scroll or navigate to the next slide. We can implement this as an enhancement: if `autoadvance` is in the alt, we add a small script on that page listening for the video’s `ended` event to trigger a slide change (scroll to next slide or call a next-slide function). If build-lists are on that slide, Deckset doesn’t allow autoadvance, but in our case, that’s not a conflict because we aren’t doing step-by-step building in static. We will note this feature and implement if time permits.

* **Audio:** An audio file can be embedded similarly:

  * Syntax: `![](audio.mp3)` in Deckset creates an audio player icon on the slide. The generator will output an `<audio>` element:

    ```html
    <audio src="track.mp3" controls></audio>
    ```

    By default, we’ll show the browser’s audio controls (so user can play/pause).
  * We do not have a visual waveform or anything (Deckset just shows an OS icon). If we wanted to mimic Deckset’s style, we could show an icon image (like a speaker symbol) linking to the audio, but a simpler approach is to use the `<audio>` element’s controls which provides play/pause UI. However, Deckset’s docs imply they show the OS file icon unless `hide` is used. To keep it simple, we will rely on standard controls. If a more Deckset-like appearance is desired, we could hide controls and show a custom icon with a click handler to play/pause the audio.
  * **Audio layout:** The same modifiers `left`, `right`, `fit`, `fill`, `%`, `hide` apply to audio icons as well:

    * If `left` or `right` is specified, we will float or position the audio’s icon or element to that side (similar to images, likely in a 50% column or just float left).
    * `fit` or `fill` might not be very applicable to audio (since there’s no visual beyond the icon), but if they were provided, we could size the icon bigger (`fill` could mean enlarge the icon perhaps). Given that we’ll likely use the native controls, `fill` doesn’t have meaning. We might ignore `fill` for audio or interpret it as make the controls 100% width which is probably not needed. Deckset likely only applies left/right/hide to audio.
    * `hide`: If present, Deckset hides the icon entirely but still plays the audio. We can implement `hide` for audio by not rendering the `<audio>` controls (or giving it `display:none` but still autoplay if that’s intended). More practically, if `autoplay` is also set, a hidden audio will start playing without the user seeing any player. We should still include the `<audio>` element (so the sound can play) but with controls hidden.
  * **Audio playback options:** `autoplay`, `loop`, `mute` apply to audio too:

    * `autoplay` on audio element (again, may be blocked unless muted, but audio muted is pointless – typically Deckset might not autoplay audio without user action. We’ll allow it though.)
    * `loop` on audio (repeat track).
    * `mute` on audio (which would start muted – not very useful unless user is meant to unmute? Possibly included for consistency; we’ll implement it but muted audio with no UI means no sound).
  * If a user wants background music across slides, Deckset doesn’t explicitly support that, but one could imagine placing an autoplay loop audio on the first slide and leaving it hidden, though navigating in a single-page app wouldn’t stop it. Our static site could have persistent audio if needed, but that’s beyond scope.

**Note:** The generator ensures that video/audio files are referenced properly (if the Markdown references local files, the output will assume those files are present in a media directory or alongside the HTML, with correct relative paths). We will not re-encode or embed the media, just link to them.

### Code Blocks and Syntax Highlighting

The generator will handle Markdown fenced code blocks and Deckset’s code-specific features:

* **Fenced code blocks:** Use triple backticks `to denote code blocks. An optional language identifier after the opening backticks (e.g.`javascript) indicates the language for syntax highlighting. The generator will produce a `<pre><code class="language-javascript">...</code></pre>` block in HTML. We will integrate a syntax highlighter (such as Highlight.js or Prism.js) by including its JS/CSS, or we can pre-process the code to add `<span>` tags for tokens. For simplicity, we might include a Highlight.js script in the HTML and call `hljs.highlightAll()` so that all `<code class="language-*">` sections get highlighted on page load. This way, any language specified will receive appropriate coloring. If no language is specified and the user provided a `code-language: X` default at top of Markdown, we will treat the code as language X for highlighting. (Implementation: if a fenced block has no class and a global default exists, we add `class="language-X"` to that code block.)
* **Inline code:** Backticks within a sentence produce `<code>` elements. These will be rendered with a monospaced font and a subtle background per the theme. (Deckset supports inline code as well.)
* **Code block styling:** The HTML/CSS will ensure code blocks are scrollable if they overflow. Deckset auto-scales code to fit the slide width – we have two options: either allow horizontal scrolling for overflow (which is standard on web and preferable to preserve code formatting), or attempt to scale down the font-size if a code block is slightly too wide. The specification will lean toward scrollable code by default. However, we might implement a simple auto-scale: e.g., if a `<code>` block’s length exceeds a certain number of characters per line, we could apply a smaller font class. Since this is complex to do statically, we probably stick to horizontal scroll for wide code, vertical scroll for long code, and an explicit mention that auto-scaling of code is limited (highlighting Deckset’s behavior but not fully mimicking it). We will document that extremely long code lines might not auto-shrink, but users can scroll or manually break lines.
* **Highlighted lines:** Deckset allows highlighting specific lines in a code block by preceding the block with a `[.code-highlight: ...]` directive. The generator will parse such directives:

  * If a code block is immediately preceded (within the same slide) by a line of the form `[.code-highlight: N]` or `[.code-highlight: X-Y]` or even multiple ranges like `[.code-highlight: 2, 6-8]`, we will use that information to mark those lines in the HTML output. The approach:

    * We will number the lines in the `<code>` block (either literally output line numbers or just count newlines in the text).
    * Then wrap the specified lines in a span with a highlight class or apply a background style via CSS. For example, `<span class="highlight-line">...</span>`.
    * Alternatively, output the code with each line in a separate `<div>` or `<span>` with line number data, then add a class to the lines to highlight. Simpler: we can post-process the text: split by newline, and for each line number that needs highlight, wrap that line in a `<mark>` tag or `<span class="line-highlight">`.
    * The highlighted lines will appear with a distinct background color (e.g. yellow or light highlight) to draw attention.
  * If the directive specifies multiple lines or ranges, all those will be highlighted.
  * **Stepped highlights:** Deckset’s advanced feature allows multiple `[.code-highlight]` directives in sequence (like none, then some lines, then more) to step through in presentation. In a static page, we cannot automatically step through highlights without user interaction. We have a few choices:

    * Simplest: if multiple highlight directives are present for one code block, we ignore all but the last one (so the final state is shown, effectively highlighting all lines that would be highlighted at the end of the sequence). For instance, if the Markdown has:

      ```
      [.code-highlight: none]  
      [.code-highlight: 2]  
      [.code-highlight: 6-8]  
      [.code-highlight: all]  
      ```

      above a code block, Deckset in a live talk would highlight none, then line 2, then lines 6-8, then all. We could choose to just highlight *all lines* in the static output (since the last state was `all`). But that’s not very useful.
    * Better: we could create an interactive component. For example, render a single code block, but include buttons or a slider to cycle through the highlight steps. That is complex for a static spec, though we could do it with a small script (the code steps are known).
    * Or output multiple versions of the code block for each state, and use CSS to only show one at a time. That would bloat the output.
    * Since the question emphasis is not on interactive parity but on layout and format, we will **not implement stepped reveal for code in the static HTML** by default. Instead, we will either take the last highlight or perhaps highlight the union of all lines that ever get highlighted. We will, however, mention in documentation that multiple `.code-highlight` directives are primarily for live presentations and are not fully represented in the static output (unless user uses the interactive features).
  * Thus, the generator will support a single `.code-highlight` directive (with possibly multiple line numbers in one) per code block for static highlighting. It will parse it and apply a highlight style to those lines. If `.code-highlight: none` is specified, that means explicitly no lines highlighted (we can ignore it since by default none are highlighted). If `.code-highlight: all` is specified, we highlight the entire block (maybe by giving the whole block a highlight background).
* **Example:** Given the Markdown:

  ````markdown
  [.code-highlight: 2, 6-8]
  ```js
  const data = fetchData();
  console.log("Step 1");
  if (data) {
    process(data);
  }
  console.log("Done");
  ````

  The generator might produce HTML like:

  ```html
  <pre><code class="language-js">const data = fetchData();
  <mark>console.log("Step 1");</mark>
  if (data) {
    <mark>process(data);</mark>
  }
  <mark>console.log("Done");</mark></code></pre>
  ```

  Here lines 2, 6, 7, 8 are highlighted per the directive (note: since we counted blank lines differently, the example lines highlight the concept; actual line numbers would be calculated precisely). The `<mark>` or a styled `<span>` will visually emphasize those lines (e.g. yellow background).
* The generator will ensure to escape HTML characters in code blocks and not process Markdown inside them (standard behavior).
* Finally, if Deckset’s global `autoscale: true` is set, code blocks might also be scaled down when too large. As mentioned, we handle text autoscaling separately, but we note that our default is scroll for code overflow.

### Slide Numbers, Footers, and Other Global Settings

Deckset provides configuration commands that affect the entire deck or individual slides. Our generator will support the most relevant ones:

* **Slide numbers:** If the Markdown contains `slidenumbers: true` at the top, the generator will number each slide and display the number in the output. We will add a small element (e.g. `<div class="slide-number">X</div>`) to each slide’s HTML, probably in a bottom corner. If `slidecount: true` is also set, we will display the number as “X / N” where N is the total count of slides. This could appear as text within that slide-number element (for example, slide 3 of 10 would show “3/10”). The styling will be subdued (smaller font, semi-transparent) so as not to distract. If the user doesn’t want the number on a specific slide, Deckset allows `[.slidenumbers: false]` on that slide; we will support that by not rendering the number on slides with that override (or by adding a class like `no-number` to suppress it via CSS).

  * We’ll calculate total slides N during generation. If `slidecount: true` is not set, we just show the current slide number or perhaps just omit the total part. If `slidenumbers: false` (global or not present), we simply don’t add slide numbers at all.
  * The numbering will exclude any hidden slides (since they won’t be in output).

* **Footer text:** A global `footer: Your footer text` command can define a line of text to appear on every slide’s bottom. The generator will capture this and output the footer on each slide, typically in a `<div class="footer">Your footer text</div>` at the bottom (below content, above slide number). The footer text can include Markdown styling (Deckset allows emphasis, etc. in footers), so we will parse that string as Markdown as well (inline styles, links, etc. inside the footer). If a slide has a specific override like `[.footer: Different text]`, we use that on that slide instead of the global one. If a slide has `[.hide-footer]`, we will simply not output any footer for that slide.

  * The footer element will be styled consistently (perhaps smaller font, italics or a different color) and typically aligned to bottom-left or bottom-center of the slide. Deckset likely puts it bottom-center, but we can choose bottom-center for a balanced look, or bottom-left if slide numbers are bottom-right, to avoid collision.
  * Footers will naturally repeat on each slide via the HTML generation, no client-side logic needed.

* **Autoscale text:** The `autoscale: true` global command triggers Deckset to automatically shrink text to fit slides when necessary. For our HTML output, we will implement a simplified version:

  * By default, our CSS will define responsive text sizes that adapt to screen width, so text will wrap and reflow rather than overflow. Therefore, autoscaling might not be needed in most cases (browser will handle smaller screens).
  * However, if extremely long text without breaks is placed (like a continuous string or a huge header), it might overflow horizontally. We can include a small script or CSS trick: e.g., for each slide, if the content height exceeds the slide container, we could scale down the container via a transform, or reduce font-size via a calculated factor. This is complex to do perfectly with pure CSS, but maybe not critical for static reading.
  * As a baseline, we will honor `autoscale: true` by adding a class to the `<body>` or `<div class="slide">` elements (like `.autoscale-on`). If this is present, we might apply a slightly smaller base font or allow a scaling. If `autoscale: false` is specified per slide with `[.autoscale: false]`, we skip scaling on that slide.
  * We will document that autoscaling is supported in a basic way: it helps avoid overflow by slight font reduction, but it won’t shrink text to an extreme degree.
  * Practically, given the responsive nature of web, we might not implement dynamic scaling at all; instead, trust the scroll or user resizing. But to align with spec, we’ll note that content is sized flexibly and that `autoscale` is mainly relevant to Deckset’s fixed-size slides, whereas our output can scroll. So this command might be a no-op in our generator, or perhaps toggles a minor CSS change (like enabling word-wrap and slightly reducing margins on slides to accommodate more text).

* **Build lists:** (Discussed earlier in Lists) – global `build-lists: true` is noted. Since static output shows all content, we do not hide list items by default. But if we want to incorporate this feature, we might add a data-attribute to each list and list item. For example, `<ul class="build-list">` and each `<li data-step="n">`. Then with a bit of JS/CSS, we could initially hide all but the first items and reveal more on clicks or keypress. This is an optional enhancement. The specification will state that by default, lists are fully visible (so information is not lost), and that the `build-lists` command can be utilized for an interactive mode if needed. We ensure that `[.build-lists: false]` on a slide (to disable incremental build on that slide) would simply result in no special behavior for that list.

* **Transitions:** Deckset’s `slide-transition: true` global command enables animated transitions between slides in presenter mode. It also allows specifying transition style and duration (e.g. `slide-transition: fade(0.5)` or `push(horizontal)` etc.). In a static HTML site, transitions are not inherent (since it’s not a controlled slideshow unless we add JS). We will:

  * Interpret `slide-transition: X` (and per-slide `[.slide-transition: X]`) and store the preference. If we provide a JS slideshow script, we can use these preferences: for example, include a CSS class on the `<body>` like `transition-fade` or data attributes on slides indicating the transition style to next slide. Then the JS can pick up and animate accordingly. If the style is `fade`, we cross-fade slides; if `push(right)`, we scroll horizontally, etc. This is advanced, but possible.
  * For the scope of static output, we might not implement actual animations, but we’ll preserve the info. For instance, if `slide-transition: fade` is set, we could add `data-transition="fade"` on each slide or on the container.
  * If we decide to implement, the simplest is a fade: using CSS, we can fade out one slide and fade in the next on navigation. Others like push or move would require more complex CSS transforms.
  * The specification will note that common transition styles (`fade`, `push`, `move`, `reveal`) are recognized, and if an interactive mode is enabled, those animations will be applied. If no interactive mode, the presence of a transition setting doesn’t affect the static view (other than maybe including a link or style that doesn’t get triggered).
  * Slide-specific `transition: false` will override to no animation for that slide transition (we might ignore in static).

* **Theme selection:** Deckset uses `theme: Name` and possibly color variant index to choose one of its built-in themes. Our generator does not have multiple themes by default – it has one default HTML/CSS theme. If the Markdown specifies a theme name, we will simply ignore it or output a comment saying “Theme X requested”. Optionally, if we predefine a couple of CSS themes (like a light and dark mode), we could map some Deckset theme names to ours. But since the user explicitly said we don’t need to match Deckset’s visual styles, we will not attempt to clone specific themes. We will just ensure the default is clean. (We could allow a command like `theme: dark` to switch to a dark color scheme CSS if we supply one, but that’s an extension.)

  * We will store the theme command in metadata (maybe as a meta tag) if needed for reference, but largely it won’t affect the output unless we support custom theming down the line.

* **Default code language:** As noted, `code-language: X` at top sets a default highlight language. We will implement this by remembering X, and any fenced code blocks without an explicit language will get `class="language-X"`. This ensures syntax highlighting is applied using that default (if using highlight.js, it might not auto-detect well without a class, so this helps).

* **Fit header (global):** Already handled above with `[fit]`. The `fit-header: #, ##, ...` global command just tells us to auto-add the fit behavior to those heading levels. We will implement it by adding the `.fit` class to all such headings in the HTML generation phase, as discussed.

* **Custom CSS (theming):** Deckset allows custom theme modifications via the app or a limited CSS injection. Our generator can allow an optional custom CSS file to be linked. For example, if the user places a `custom.css` file and a command `theme: custom.css`, we might link that. However, since not required, we simply mention that the output’s CSS can be edited or replaced by the user to achieve custom styling. The HTML will be structured with classes (like `slide`, `column`, `inline-img`, `speaker-notes`, etc.) to facilitate easy theming.

* **Keyboard shortcuts:** Deckset docs mention keys for presentation, but in a static site context, we might allow using arrow keys to navigate if we include JS. Not a core spec item, but we can note that if JS navigation is present, Left/Right arrows or swipe can move slides, Esc could show an overview, etc., but this is beyond the markdown conversion scope.

## Sample Workflow and Example

To illustrate, consider a small example Deckset Markdown input and how the generator processes it:

````markdown
theme: Simple, 1
autoscale: true
footer: Demo Presentation
slidenumbers: true

# Welcome to Deckset [fit]
This is an introduction slide.

^ Speaker notes for intro slide.

---

![left](city.jpg)
# About Our City
Our city has **great** views and many opportunities.
- Population: 1,000,000
- Founded: *1900*

![inline 50%](chart.png)

---

```yaml
# Data Example
name: Deckset Project
features:
  - Markdown
  - Images
  - Code
````

````

After running the generator, the output might include:

- A single HTML file with three `<section class="slide">` elements (for the three slides).
- The first slide’s HTML:
  ```html
  <section class="slide" id="slide-1">
    <h1 class="fit">Welcome to Deckset</h1>
    <p>This is an introduction slide.</p>
    <aside class="speaker-notes">Speaker notes for intro slide.</aside>
    <div class="footer">Demo Presentation</div>
    <div class="slide-number">1/3</div>
  </section>
````

The first slide has a centered fitted title, the intro text, hidden notes, a footer, and slide number “1/3”.

* The second slide:

  ```html
  <section class="slide" id="slide-2" style="background-image:url('city.jpg')" class="bg-left">
    <div class="content right-half">
      <h1>About Our City</h1>
      <p>Our city has <strong>great</strong> views and many opportunities.</p>
      <ul>
        <li>Population: 1,000,000</li>
        <li>Founded: <em>1900</em></li>
      </ul>
      <p><img src="chart.png" alt="" class="inline-img" style="width:50%"></p>
    </div>
    <div class="footer">Demo Presentation</div>
    <div class="slide-number">2/3</div>
  </section>
  ```

  Here we used the city.jpg as a **left-half background** (with possibly `bg-left` class or inline style to only show on left side), and we wrapped the text in a `content right-half` container so it sits on the right side. The list is fully displayed (we ignored build-lists because it wasn’t set here). The image `chart.png` is an inline image at 50% width inside a paragraph – it will appear alongside the text content. The footer and slide number are shown. (In CSS, the `.content.right-half` might be `width:50%; float:right;` and `.slide` with `bg-left` might have the left half covered by the background image via an absolutely positioned element.)
* The third slide:

  ```html
  <section class="slide" id="slide-3">
    <pre><code class="language-yaml"><span class="hl-line"># Data Example</span>
  name: Deckset Project
  features:
    - Markdown
    - Images
    - Code</code></pre>
    <div class="footer">Demo Presentation</div>
    <div class="slide-number">3/3</div>
  </section>
  ```

  This slide shows a YAML code block. Suppose we had a highlight directive to highlight the comment line. The output code shows `<span class="hl-line"># Data Example</span>` wrapped for highlighting. The rest is normal code. Syntax highlighting (via JS library) would apply color to YAML keywords etc. The footer and number are present.

All these slides are wrapped in appropriate containers, and a linked CSS file styles them for a clean look. The site can be opened in a browser, where the user can scroll through or, if we added a script, use arrow keys to navigate with optional transitions.

## Conclusion

This Markdown-to-HTML generator will **faithfully reproduce Deckset’s Markdown semantics in a web environment**, covering slide separation, text formatting, lists, tables, images (with placement and scaling options), videos, audio, code blocks with syntax highlighting and line emphasis, mathematical formulas, footnotes, and more. The output is a static, responsive HTML presentation with a default theme, which users can further customize. By adhering closely to Deckset’s documented features – from `---` slide breaks to `^` speaker notes to `![inline](image.jpg)` figures – the tool allows content creators to leverage their Deckset knowledge and content for the web. All citations and references in this specification correspond to Deckset’s official documentation, ensuring that the implemented behavior aligns with Deckset’s intended functionality.
