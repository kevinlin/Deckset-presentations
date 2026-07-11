---
name: Deckset Presentations
description: A talk archive that stages Markdown decks as a projected, switchable-theme website
colors:
  cue-blue: "#3b82f6"
  cue-blue-deep: "#2563eb"
  canvas: "#ffffff"
  booth-gray: "#f8fafc"
  ink: "#1f2937"
  ink-muted: "#4b5563"
  ink-subtle: "#6b7280"
  hairline: "#e5e7eb"
  code-slate: "#1f2937"
  on-accent: "#ffffff"
typography:
  display:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "3.5rem"
    fontWeight: 700
    lineHeight: 1.1
  headline:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "2.75rem"
    fontWeight: 600
    lineHeight: 1.2
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "2.125rem"
    fontWeight: 600
    lineHeight: 1.3
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.4
  mono:
    fontFamily: "Monaco, Menlo, 'Ubuntu Mono', monospace"
    fontSize: "1.125rem"
    fontWeight: 400
rounded:
  sm: "0.375rem"
  md: "0.5rem"
  lg: "0.75rem"
  pill: "2rem"
spacing:
  sm: "0.5rem"
  md: "1rem"
  lg: "2rem"
components:
  button-primary:
    backgroundColor: "{colors.cue-blue}"
    textColor: "{colors.on-accent}"
    rounded: "1.5rem"
    padding: "0.5rem 1rem"
  button-primary-hover:
    backgroundColor: "{colors.cue-blue-deep}"
  card:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
  input-search:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "0.5rem 1rem 0.5rem 2.5rem"
---

# Design System: Deckset Presentations

## 1. Overview

**Creative North Star: "The Projection Booth"**

This site is the booth, and the decks are the show. Every visible surface belongs to one of two worlds: the stage (slides, rendered at a strict 16:9, lifted off the page on soft shadow) or the machinery (nav, cards, chrome), which stays engineered, quiet, and exact so the light falls on the work. The system serves a portfolio whose claim is "the archive itself is the evidence": chrome precision is itself part of the pitch.

The whole visual layer runs through a token contract. Theme stylesheets define only `:root` custom properties (16 color roles, 3 font stacks, heading scale, radii); base CSS consumes `var(--…)` and nothing else. Sixteen themes (light, dark, minimal, plus 13 compiled from `design-md/`) swap through a single stylesheet link at runtime. The values below document the default light theme; the roles are the real system.

It explicitly rejects corporate slideware, the generic SaaS landing, and the bare docs site.

**Key Characteristics:**
- Two-world discipline: luminous stage, quiet machinery
- Strict 16:9 slide geometry at every viewport
- One accent color, spent on interaction only
- Theme-proof: every surface styleable through the token contract
- Motion as stagecraft: slide transitions, not decoration

## 2. Colors

A near-monochrome booth with a single blue cue light.

### Primary
- **Cue Blue** (#3b82f6): the only voice of interactivity. Nav buttons, links, focus rings, footnote markers, code-line highlights. If it is Cue Blue, you can act on it.
- **Cue Blue Deep** (#2563eb): hover and pressed states of Cue Blue; also the browser theme-color.

### Neutral
- **Canvas White** (#ffffff): the slide surface and card faces; the projection screen itself.
- **Booth Gray** (#f8fafc): the page background behind slides; the dim room around the screen.
- **Ink** (#1f2937): headings and primary text; also the block-code background (**Code Slate**), where it inverts to house light-on-dark code.
- **Ink Muted** (#4b5563): secondary headings, blockquotes, body text in supporting roles.
- **Ink Subtle** (#6b7280): captions, line numbers, footers, metadata.
- **Hairline** (#e5e7eb): borders, column rules, footnote separators.

### Named Rules
**The Token Contract Rule.** Base CSS never hardcodes a color. Every color is `var(--color-…, fallback)`, so all 16 themes restyle the site without touching a selector. A hex value outside a theme file is a defect.

**The Cue Rule.** Cue Blue is reserved for things a visitor can do. Never use it as decoration, background wash, or emphasis on static text.

## 3. Typography

**Display Font:** System sans stack (-apple-system, Segoe UI, Roboto)
**Body Font:** Same system stack
**Label/Mono Font:** Monaco (with Menlo, Ubuntu Mono)

**Character:** Deliberately fontless: the site ships zero font downloads and works fully offline, so voice comes from scale and weight, and themes re-voice the type via `--font-display` / `--font-body` / `--font-mono` (minimal, for instance, swaps headings to Georgia at weight 400).

### Hierarchy
Presentation pages run on an 18px base (16px tablet, 14px mobile) so slides read like slides.

- **Display** (700, 3.5rem via `--h1-size`, 1.1): slide h1; the projected headline.
- **Headline** (600, 2.75rem, 1.2): slide h2 and section leads.
- **Title** (600, 2.125rem, 1.3): slide h3; drops to Ink Muted.
- **Body** (400, 1.25rem, 1.6): slide paragraphs and lists.
- **Label** (500, 0.875rem): footers, slide counters, card metadata.
- **Fit** (700, `clamp(3rem, 15vw, 12rem)`, centered): the `[fit]` Deckset header, JS-assisted to fill the slide width.

### Named Rules
**The Fit Ceiling Rule.** `[fit]` headers may scale to 12rem inside a slide, because a slide is a stage. Chrome typography never exceeds Display scale.

## 4. Elevation

Lifted stage. Depth is structural, never decorative: the slide and the floating nav pill sit *above* Booth Gray on soft, wide shadows, exactly like a lit screen in a dim room. Chrome elements between those layers (header, footer) stay flat with hairline borders.

### Shadow Vocabulary
- **Stage lift** (`box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1)`): slides and presentation cards at rest.
- **Card hover** (`box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)`): a card responding to attention; transition 0.2s ease.
- **Nav float** (`box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1)`): the fixed navigation pill, the highest resting surface.

### Named Rules
**The Two Layers Rule.** Only the stage (slides, cards) and the nav pill cast shadows. Everything else is flat. A third shadow tier means something is on the wrong layer.

## 5. Components

Tactile and confident: components respond instantly and visibly (hover fills, shadow lifts, 0.2s transitions), with pill geometry on controls and precise hairlines everywhere else.

### Buttons
- **Shape:** Full pill (1.5rem radius) on nav controls.
- **Primary:** Cue Blue fill, white text, 0.5rem 1rem padding, weight 500.
- **Hover / Focus:** Fill deepens to Cue Blue Deep (0.2s); focus draws a 2px Cue Blue outline offset 2px.
- **Disabled:** Neutral gray (#9ca3af) fill, not-allowed cursor.

### Cards / Containers
- **Corner Style:** Rounded (0.5rem).
- **Background:** Canvas White with a 16:9 preview image (or a Booth Gray placeholder) above a 1.5rem body.
- **Shadow Strategy:** Stage lift at rest, Card hover on attention (see Elevation).
- **Internal Padding:** 1.5rem.

### Inputs / Fields
- **Style:** Canvas White, hairline border, 0.375rem radius, leading search icon in Ink Subtle.
- **Focus:** 2px Cue Blue ring replaces the border shadow.

### Navigation
- **Site header:** sticky, flat, hairline-bottomed; theme selector and text links in Label type.
- **Slide navigation:** fixed bottom-center floating pill (Canvas White, Nav float shadow) holding Previous / counter / Next; collapses to full-width edge-pinned bar under 768px.

### The Slide (signature component)
A strict `aspect-ratio: 16 / 9` Canvas White surface, 0.5rem radius, Stage lift shadow, 2rem content padding. Backgrounds layer under a readability overlay (`rgba(0,0,0,0.35)` gradient, JS-tunable) at z-index 2, content at 3. Transitions are Deckset-faithful: 300ms fade or push keyframes, fully disabled under `prefers-reduced-motion`.

## 6. Do's and Don'ts

### Do:
- **Do** route every color, font, and radius through the token contract (`--color-…`, `--font-…`, `--radius-…`); test changes in at least light, dark, and one compiled `design-md` theme.
- **Do** keep slides at exact 16:9 at every breakpoint; content adapts inside the frame, never the frame.
- **Do** keep body contrast at or above 4.5:1 in every theme (WCAG 2.1 AA), including text over background images via the readability overlay.
- **Do** give every animation a `prefers-reduced-motion: reduce` fallback, as the slide transitions already do.
- **Do** keep the site self-contained: vendored assets, system fonts, zero CDN calls at view time.

### Don't:
- **Don't** ship corporate slideware: no PowerPoint-export chrome, no SharePoint-era archive tables.
- **Don't** drift into the generic SaaS landing (hero, three feature cards, testimonial strip) on the homepage; it is an archive shelf, not a pitch page.
- **Don't** leave surfaces at bare-docs plainness: unstyled lists that undersell the work are the named failure mode.
- **Don't** spend Cue Blue on decoration; it marks interaction only (The Cue Rule).
- **Don't** add gradient chrome or badges; the existing `enhanced-indicator` gradient is legacy, not license.
- **Don't** hardcode a hex outside a theme file, ever (The Token Contract Rule).
