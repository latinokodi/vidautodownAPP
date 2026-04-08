# UI/UX Design Intelligence - Complete Reference

**Version 2.0.0**  
Adapted for Google Antigravity  
February 2026

> This document provides comprehensive design guidelines optimized for AI agents and LLMs. Rules are prioritized by impact from critical (accessibility, touch targets) to incremental (chart types).

---

## Abstract

Comprehensive UI/UX design intelligence guide for developers and designers. Contains 50+ UI styles, 97 color palettes, 57 font pairings, 99 UX guidelines across 9 technology stacks. Each guideline includes incorrect vs correct examples, code samples, and specific implementation guidance for automated design generation and code review.

---

## Table of Contents

1. [Accessibility (CRITICAL)](#1-accessibility-critical)
2. [Touch & Interaction (CRITICAL)](#2-touch--interaction-critical)
3. [Performance (HIGH)](#3-performance-high)
4. [Layout & Responsive (HIGH)](#4-layout--responsive-high)
5. [Typography & Color (MEDIUM)](#5-typography--color-medium)
6. [Animation (MEDIUM)](#6-animation-medium)
7. [Style Selection (MEDIUM)](#7-style-selection-medium)
8. [Charts & Data (LOW)](#8-charts--data-low)

---

## 1. Accessibility (CRITICAL)

**Impact: CRITICAL**

WCAG compliance, screen reader support, keyboard navigation. Non-negotiable for inclusive design.

### 1.1 Color Contrast Requirements

**Impact: CRITICAL (Affects ~8% of male population with color vision deficiency)**

Minimum 4.5:1 contrast ratio for normal text, 3:1 for large text and UI components.

**Incorrect (fails WCAG AA):**
```css
/* 2.1:1 contrast - fails WCAG AA */
.text-gray-400 { color: #94A3B8; }
.bg-white { background-color: #FFFFFF; }
/* Gray text on white background fails */
```

**Correct (passes WCAG AA):**
```css
/* 7.5:1 contrast - passes WCAG AAA */
.text-slate-700 { color: #334155; }
.bg-white { background-color: #FFFFFF; }

/* Always test with tools */
/* Primary text: #0F172A on #FFFFFF = 12.6:1 ✓ */
/* Muted text: #475569 on #FFFFFF = 7.1:1 ✓ */
```

### 1.2 Focus States

**Impact: CRITICAL (Keyboard users cannot navigate without visible focus)**

All interactive elements must have visible focus indicators.

**Incorrect (invisible focus):**
```css
button:focus {
  outline: none; /* Screen reader users lost */
}
```

**Correct (visible focus ring):**
```css
button:focus-visible {
  outline: 2px solid #2563EB;
  outline-offset: 2px;
}

/* Modern approach with ring utility */
button:focus {
  outline: none;
  box-shadow: 0 0 0 2px #FFFFFF, 0 0 0 4px #2563EB;
}
```

### 1.3 Alternative Text

**Impact: HIGH (Screen readers announce images)**

Provide descriptive alt text for meaningful images, empty alt for decorative.

**Incorrect:**
```html
<img src="product.jpg"> <!-- Missing alt -->
<img src="chart.png" alt="image"> <!-- Non-descriptive -->
```

**Correct:**
```html
<img src="product.jpg" alt="Blue ceramic vase with geometric pattern">
<img src="chart.png" alt="Sales chart showing 25% growth in Q3">
<img src="divider.svg" alt="" role="presentation"> <!-- Decorative -->
```

### 1.4 Form Labels

**Impact: CRITICAL (Screen readers cannot identify unlabeled inputs)**

All form inputs must have associated labels.

**Incorrect:**
```html
<input type="email" placeholder="Enter email"> <!-- No label -->
```

**Correct:**
```html
<label for="email">Email Address</label>
<input type="email" id="email" name="email">

<!-- Hidden label for visual design -->
<label for="search" class="sr-only">Search</label>
<input type="search" id="search" placeholder="Search...">
```

### 1.5 Keyboard Navigation

**Impact: CRITICAL (Many users rely on keyboard)**

Ensure tab order matches visual order, all functionality available via keyboard.

**Incorrect:**
```jsx
// Only clickable, not focusable
<div onClick={handleClick}>Click me</div>
```

**Correct:**
```jsx
// Proper interactive element
<button onClick={handleClick}>Click me</button>

<!-- Or with proper ARIA -->
<div 
  role="button" 
  tabIndex={0}
  onClick={handleClick}
  onKeyDown={(e) => e.key === 'Enter' && handleClick()}
  aria-pressed={isPressed}
>
  Click me
</div>
```

---

## 2. Touch & Interaction (CRITICAL)

**Impact: CRITICAL**

Touch targets, cursor feedback, loading states. Essential for usable interfaces.

### 2.1 Minimum Touch Target Size

**Impact: CRITICAL (44×44px Apple HIG, 48×48dp Material Design)**

Touch targets must meet minimum size requirements.

**Incorrect:**
```css
.icon-button {
  width: 32px;
  height: 32px; /* Too small - missed taps */
}
```

**Correct:**
```css
.icon-button {
  min-width: 44px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Or increase hit area with padding */
.icon-button {
  padding: 10px; /* 48px area around 28px icon */
}
```

### 2.2 Cursor Pointer

**Impact: HIGH (Users need feedback on interactive elements)**

All clickable elements must show pointer cursor.

**Incorrect:**
```css
.card:hover {
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  /* Missing cursor: pointer */
}
```

**Correct:**
```css
.card {
  cursor: pointer;
}
.card:hover {
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
```

### 2.3 Loading States

**Impact: HIGH (Prevents double-submit, confirms action received)**

Show loading state during async operations.

**Incorrect:**
```jsx
<button onClick={submitForm}>Submit</button>
<!-- User can click multiple times -->
```

**Correct:**
```jsx
<button 
  onClick={submitForm} 
  disabled={isLoading}
  aria-busy={isLoading}
>
  {isLoading ? (
    <><Spinner /> Processing...</>
  ) : 'Submit'}
</button>
```

### 2.4 Error Feedback

**Impact: HIGH (Users need to know what went wrong)**

Display error messages near the problem field.

**Incorrect:**
```html
<div class="error-banner">Email is invalid</div>
<form>
  <input type="email">
</form>
```

**Correct:**
```html
<form>
  <label for="email">Email</label>
  <input 
    type="email" 
    id="email"
    aria-invalid="true"
    aria-describedby="email-error"
  >
  <p id="email-error" class="text-red-600">
    Please enter a valid email address
  </p>
</form>
```

---

## 3. Performance (HIGH)

**Impact: HIGH**

Image optimization, animation performance, content layout shifts.

### 3.1 Image Optimization

**Impact: HIGH (WebP 25-35% smaller than JPEG)**

Use modern formats, lazy loading, responsive images.

**Incorrect:**
```html
<img src="hero.png" width="1920"> <!-- Unoptimized, immediate load -->
```

**Correct:**
```html
<picture>
  <source srcset="hero.avif" type="image/avif">
  <source srcset="hero.webp" type="image/webp">
  <img 
    src="hero.jpg" 
    alt="Hero"
    loading="lazy"
    width="1920"
    height="1080"
    srcset="hero-480.jpg 480w, hero-768.jpg 768w"
    sizes="100vw"
  >
</picture>
```

### 3.2 Respect Reduced Motion

**Impact: MEDIUM (Vestibular disorders triggered by motion)**

Honor `prefers-reduced-motion`.

**Incorrect:**
```css
.modal {
  animation: slide-in 0.5s ease;
} /* Always animates */
```

**Correct:**
```css
.modal {
  animation: slide-in 0.3s ease;
}

@media (prefers-reduced-motion: reduce) {
  .modal {
    animation: none;
  }
}
```

### 3.3 Prevent Layout Shift

**Impact: HIGH (Affects CLS Core Web Vital)**

Reserve space for async content.

**Incorrect:**
```jsx
<img src={imageUrl} alt="Content"> <!-- Pushes content down when loads -->
```

**Correct:**
```jsx
<div className="aspect-video">
  <img src={imageUrl} alt="Content" className="w-full h-full object-cover">
</div>
```

---

## 4. Layout & Responsive (HIGH)

**Impact: HIGH**

Viewport configuration, responsive breakpoints, z-index management.

### 4.1 Viewport Meta Tag

**Impact: CRITICAL (Mobile displays incorrectly without)**

Always include proper viewport meta.

**Incorrect:**
```html
<head>
  <title>My App</title>
  <!-- Missing viewport -->
</head>
```

**Correct:**
```html
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>My App</title>
</head>
```

### 4.2 Z-Index Management

**Impact: MEDIUM (Prevents z-index wars)**

Define consistent z-index scale.

**Incorrect:**
```css
.dropdown { z-index: 9999; }
.modal { z-index: 10000; }
.tooltip { z-index: 99999; }
```

**Correct:**
```css
:root {
  --z-dropdown: 10;
  --z-sticky: 20;
  --z-drawer: 30;
  --z-modal: 40;
  --z-popover: 50;
  --z-tooltip: 60;
}
```

---

## 5. Typography & Color (MEDIUM)

**Impact: MEDIUM**

Font pairings, color palettes, type scale.

### 5.1 Font Pairings Database

| Mood | Heading | Body | CSS Import |
|------|---------|------|------------|
| Professional | Inter | Inter | `family=Inter:wght@400;600` |
| Editorial | Playfair Display | Source Sans Pro | `family=Playfair+Display\|Source+Sans+Pro` |
| Modern | Space Grotesk | Inter | `family=Space+Grotesk\|Inter` |
| Luxury | Cormorant Garamond | Montserrat | `family=Cormorant+Garamond\|Montserrat` |

### 5.2 Color Palettes by Industry

| Industry | Primary | Secondary | Background | Text |
|----------|---------|-----------|------------|------|
| SaaS | #2563EB | #3B82F6 | #F8FAFC | #0F172A |
| Healthcare | #0D9488 | #14B8A6 | #F0FDFA | #0F172A |
| Fintech | #059669 | #10B981 | #F0FDF4 | #0F172A |
| E-commerce | #1E1B4B | #4338CA | #FAFAF9 | #18181B |
| Gaming | #7C3AED | #8B5CF6 | #0F172A | #E2E8F0 |
| Beauty | #DB2777 | #EC4899 | #FDF2F8 | #1E1B4B |

---

## 6. Animation (MEDIUM)

**Impact: MEDIUM**

Duration, easing, performance.

### 6.1 Animation Guidelines

| Type | Duration | Easing |
|------|----------|--------|
| Micro-interaction | 150-200ms | ease-out |
| Button hover | 200ms | ease |
| Page transition | 300-500ms | ease-in-out |
| Modal open | 200-300ms | cubic-bezier(0.16, 1, 0.3, 1) |

### 6.2 GPU-Accelerated Properties

**Animate only:** `transform`, `opacity`

**Incorrect:**
```css
.element:hover {
  width: 200px; /* Triggers layout */
  height: 200px;
}
```

**Correct:**
```css
.element:hover {
  transform: scale(1.1); /* GPU accelerated */
}
```

---

## 7. Style Selection (MEDIUM)

**Impact: MEDIUM**

UI styles, design patterns, component selection.

### 7.1 Style Selection Matrix

| Product Type | Primary Style | Alternative | Key Effects |
|--------------|---------------|-------------|-------------|
| SaaS Dashboard | Minimalism | Bento Grid | Subtle shadows, clean borders |
| E-commerce | Minimalism | Dark Mode | Product shadows, hover lifts |
| Healthcare | Soft Minimalism | Neumorphism | Soft shadows, calming colors |
| Fintech | Professional | Dark Mode | Data visualizations, trust colors |
| Gaming | Dark/Cyberpunk | Brutalism | Neon accents, glow effects |
| Portfolio | Brutalism | Experimental | Bold typography, unusual layouts |

### 7.2 Style Definitions

**Minimalism:**
- Clean lines, whitespace, functional
- Colors: Monochrome with single accent
- Effects: Subtle shadows, clean borders

**Glassmorphism:**
- Translucency, blur effects
- Background blur: `backdrop-blur-md`
- Opacity: 0.7-0.9 for cards

**Neumorphism:**
- Soft shadows, extruded look
- Light: shadow + highlight
- `box-shadow: 5px 5px 10px #d1d1d1, -5px -5px 10px #ffffff`

**Brutalism:**
- Bold colors, raw aesthetics
- High contrast borders
- Unconventional layouts

---

## 8. Charts & Data (LOW)

**Impact: LOW**

Chart type selection, data visualization.

### 8.1 Chart Type Selection

| Data Type | Best Chart | Alternative | Library |
|-----------|------------|-------------|---------|
| Trends over time | Line | Area | Recharts, D3 |
| Comparisons | Bar | Column | Chart.js |
| Part-to-whole | Pie | Donut | Recharts |
| Correlations | Scatter | Bubble | D3 |
| Hierarchical | Tree | Treemap | D3 |
| Geographic | Choropleth | Bubble map | D3, Leaflet |

### 8.2 Chart Accessibility

- Always provide data table alternative
- Use patterns + color, not color alone
- Label data points directly or with legend

---

## Pre-Delivery Checklist

### Visual Quality
- [ ] No emojis as icons (SVG instead)
- [ ] Consistent icon set
- [ ] Correct brand logos
- [ ] Hover states without layout shift

### Interaction
- [ ] All clickable elements: `cursor-pointer`
- [ ] Clear hover feedback
- [ ] Smooth transitions (150-300ms)
- [ ] Visible focus states

### Light/Dark Mode
- [ ] Text contrast 4.5:1 minimum
- [ ] Glass elements visible in light mode
- [ ] Borders visible in both modes

### Layout
- [ ] Floating elements have edge spacing
- [ ] No content behind fixed navbars
- [ ] Responsive breakpoints tested
- [ ] No horizontal scroll on mobile

### Accessibility
- [ ] All images have alt text
- [ ] Form inputs have labels
- [ ] Color not only indicator
- [ ] `prefers-reduced-motion` respected

---

## Design System Generation Workflow

### Step 1: Analyze
Extract from request:
- Product type (SaaS, e-commerce, etc.)
- Industry (healthcare, fintech, etc.)
- Style keywords (minimal, playful, etc.)
- Target stack

### Step 2: Select Components
1. Choose landing pattern
2. Select UI style from matrix
3. Pick color palette for industry
4. Choose font pairing for mood
5. Define key effects

### Step 3: Implement
Apply stack-specific guidelines with proper code structure.

### Step 4: Verify
Run through pre-delivery checklist.

---

## References

- [WCAG 2.2](https://www.w3.org/WAI/WCAG22/quickref/)
- [Apple HIG](https://developer.apple.com/design/human-interface-guidelines/)
- [Material Design](https://m3.material.io/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Radix UI](https://www.radix-ui.com/)
