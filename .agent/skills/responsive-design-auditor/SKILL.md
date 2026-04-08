---
name: responsive-design-auditor
description: Analyzes and optimizes website responsiveness based on mobile-first and accessibility principles. Focuses on fluid grids, media queries, performance, reflow (WCAG 1.4.10), and CLS optimization.
---

# Responsive Design Auditor

This skill analyzes and provides actionable recommendations to optimize website responsiveness and accessibility, adhering to modern mobile-first architecture and WCAG standards.

## Core Philosophy: Mobile-First Architecture

We strictly follow a **Mobile-First** approach (Progressive Enhancement).
- **Start Small**: Design for the most constrained environment first (mobile viewports).
- **Scale Up**: Use `min-width` media queries to add complexity for larger screens.
- **Prioritize Content**: Focus on vital information for small screens; remove non-essential "eye-candy".

## Capabilities

### 1. WCAG 2.1 Reflow Compliance (Success Criterion 1.4.10)
- **Goal**: Support users with low vision who use screen magnification.
- **Requirement**:
    - **Vertical Scrolling**: Content must reflow at **320px** width without horizontal scrolling.
    - **Horizontal Scrolling**: Content must reflow at **256px** height without vertical scrolling.
- **Testing**: Verify layout at 1280px width zoomed to 400%.
- **Exceptions**: Maps, diagrams, complex data tables, video interfaces, and toolbars.

### 2. Modern CSS Architecture
- **Utility-First**: Use utility classes (e.g., Tailwind) or single-purpose classes for speed and consistency.
- **Fluid Grids**: Use percentage-based widths or `fr` units (CSS Grid) instead of fixed pixels.
- **Media Queries**: Use `min-width` breakpoints:
    - **Phones**: Up to 480px
    - **Tablets (Portrait)**: 481px - 768px
    - **Tablets (Landscape)**: 769px - 1024px
    - **Desktops**: 1025px+

### 3. Performance & Situational Design
- **Mobile Latency**: Optimize for volatile networks.
- **Image Optimization**:
    - **Resolution Switching**: Use `srcset` and `sizes` for different resolutions.
    - **Art Direction**: Use `<picture>` and `<source media="...">` for different crops/compositions.
    - **Attributes**: Aways specify `width` and `height` to prevent layout shifts.
- **Lazy Loading**: Use `loading="lazy"` for off-screen images.
- **Minification**: Ensure HTML, CSS, and JS are minified.

### 4. Layout Stability (CLS)
- **Target**: CLS score of **0.1 or less**.
- **Common Issues**: Undefined image dimensions, late-loading ads/embeds, web font loading (FOUT/FOIT).
- **Fixes**: Reserve space using `aspect-ratio` or `min-height`. Optimize font loading.

### 5. Foldable & Modern Form Factors
- **Postures**: Account for "Tent", "Book", "Tabletop", and "Flat" states.
- **Hinge Avoidance**: Ensure UI elements do not span across the hinge (gap).
- **Testing**: Use browser DevTools and real-device labs (BrowserStack, etc.).

## Audit Checklist

When analyzing a page, verify the following:

- [ ] **Viewport Meta Tag**: Is `<meta name="viewport" content="width=device-width, initial-scale=1">` present?
- [ ] **Mobile-First CSS**: Are media queries using `min-width`?
- [ ] **Reflow**: Does the site work at 320px width without horizontal scroll (except allowed exceptions)?
- [ ] **Images**: Do responsive images use `srcset`/`sizes` or `<picture>`? Do they have `width`/`height`?
- [ ] **Touch Targets**: Are interactive elements at least 44x44 CSS pixels?
- [ ] **Typography**: Is text size readable on mobile (min 16px recommended for body)?
- [ ] **CLS**: Are there unexpected layout shifts during loading?

## Usage

Use this skill when the user asks to:
- "Check if my site is responsive."
- "Optimize my mobile view."
- "Fix horizontal scrolling issues."
- "Make my site accessible for low vision."
- "Review my CSS for best practices."
