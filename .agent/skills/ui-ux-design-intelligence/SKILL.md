---
name: ui-ux-design-intelligence
description: Comprehensive UI/UX design intelligence system with 50+ styles, 97 color palettes, 57 font pairings, and 99 UX guidelines. Use when designing interfaces, selecting color schemes, choosing typography, implementing responsive layouts, ensuring accessibility, or reviewing UI/UX code for web and mobile applications.
license: MIT
metadata:
  author: adapted-from-ui-ux-pro-max
  version: "2.0.0"
  styles_count: 50
  palettes_count: 97
  font_pairings_count: 57
  ux_guidelines_count: 99
---

# UI/UX Design Intelligence

Comprehensive design guide for web and mobile applications. Contains 50+ UI styles, 97 color palettes, 57 font pairings, 99 UX guidelines, and 25 chart types across 9 technology stacks.

## When to Apply

Reference these guidelines when:
- Designing new UI components or complete interfaces
- Choosing color palettes and typography combinations
- Reviewing code for UX issues or accessibility violations
- Building landing pages, dashboards, or mobile apps
- Implementing accessibility (a11y) requirements
- Selecting animation patterns and interaction designs
- Creating data visualizations and charts

## Rule Categories by Priority

| Priority | Category | Impact | Domain |
|----------|----------|--------|--------|
| 1 | Accessibility | CRITICAL | `ux` |
| 2 | Touch & Interaction | CRITICAL | `ux` |
| 3 | Performance | HIGH | `ux` |
| 4 | Layout & Responsive | HIGH | `ux` |
| 5 | Typography & Color | MEDIUM | `typography`, `color` |
| 6 | Animation | MEDIUM | `ux` |
| 7 | Style Selection | MEDIUM | `style` |
| 8 | Charts & Data | LOW | `chart` |

---

## 1. Accessibility Guidelines (CRITICAL)

### 1.1 Color Contrast Requirements

**Rule:** Minimum 4.5:1 contrast ratio for normal text, 3:1 for large text (18pt+) and UI components.

**Why:** Users with low vision or color blindness cannot read low-contrast text.

**Incorrect:**
```css
/* Fails WCAG AA - only 2.1:1 contrast */
.text-gray-400 { color: #94A3B8; }
.bg-white { background-color: #FFFFFF; }
```

**Correct:**
```css
/* Passes WCAG AA - 7.5:1 contrast */
.text-slate-700 { color: #334155; }
.bg-white { background-color: #FFFFFF; }

/* Use contrast checking tools */
/* Primary text: #0F172A on #FFFFFF = 12.6:1 ✓ */
```

### 1.2 Focus States

**Rule:** All interactive elements must have visible focus indicators.

**Incorrect:**
```css
/* Focus invisible - accessibility violation */
button:focus {
  outline: none;
}
```

**Correct:**
```css
/* Visible focus ring */
button:focus-visible {
  outline: 2px solid #2563EB;
  outline-offset: 2px;
}

/* Or custom focus state */
button:focus {
  outline: none;
  ring: 2px;
  ring-color: #2563EB;
  ring-offset: 2px;
}
```

### 1.3 Alternative Text for Images

**Rule:** Provide descriptive alt text for meaningful images, empty alt for decorative.

**Incorrect:**
```html
<!-- Missing alt text -->
<img src="product.jpg">

<!-- Non-descriptive alt -->
<img src="chart.png" alt="image">
```

**Correct:**
```html
<!-- Descriptive alt text -->
<img src="product.jpg" alt="Blue ceramic vase with geometric pattern">

<!-- Decorative image -->
<img src="divider.svg" alt="" role="presentation">

<!-- Complex image with extended description -->
<img src="chart.png" alt="Sales chart showing 25% growth in Q3" 
     aria-describedby="chart-desc">
<div id="chart-desc">Detailed description of chart data...</div>
```

### 1.4 Form Labels

**Rule:** All form inputs must have associated labels.

**Incorrect:**
```html
<!-- No label - screen readers can't identify purpose -->
<input type="email" placeholder="Enter email">
```

**Correct:**
```html
<!-- Explicit label association -->
<label for="email">Email Address</label>
<input type="email" id="email" name="email">

<!-- Or implicit association -->
<label>
  Email Address
  <input type="email" name="email">
</label>

<!-- Hidden label for visual design requirements -->
<label for="search" class="sr-only">Search</label>
<input type="search" id="search" placeholder="Search...">
```

---

## 2. Touch & Interaction Guidelines (CRITICAL)

### 2.1 Minimum Touch Target Size

**Rule:** Touch targets must be at least 44×44px (Apple HIG) or 48×48dp (Material Design).

**Incorrect:**
```css
/* Too small - 32px touch target */
.icon-button {
  width: 32px;
  height: 32px;
}
```

**Correct:**
```css
/* Minimum 44px touch target */
.icon-button {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Or use padding to increase hit area */
.icon-button {
  padding: 12px; /* Creates 48px area around 24px icon */
}
```

### 2.2 Cursor Feedback

**Rule:** All interactive elements must show pointer cursor on hover.

**Incorrect:**
```css
/* Missing cursor feedback */
.card {
  cursor: default;
}
.card:hover {
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
```

**Correct:**
```css
/* Clear interactive feedback */
.card {
  cursor: pointer;
}
.card:hover {
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

/* Also for custom interactive elements */
.clickable-area {
  cursor: pointer;
}
```

### 2.3 Loading States for Async Actions

**Rule:** Show loading state during async operations, disable button to prevent double-submit.

**Incorrect:**
```jsx
// No loading state - user can click multiple times
<button onClick={submitForm}>Submit</button>
```

**Correct:**
```jsx
// Loading state with disabled button
<button 
  onClick={submitForm} 
  disabled={isLoading}
  className={isLoading ? 'opacity-50 cursor-not-allowed' : ''}
>
  {isLoading ? (
    <><Spinner className="animate-spin" /> Processing...</>
  ) : 'Submit'}
</button>
```

### 2.4 Error Feedback Placement

**Rule:** Display error messages near the problem field, not just at the top of the form.

**Incorrect:**
```html
<!-- Error far from input -->
<div class="error-banner">Email is invalid</div>
<form>
  <input type="email">
</form>
```

**Correct:**
```html
<!-- Error adjacent to input -->
<form>
  <label for="email">Email</label>
  <input type="email" id="email" aria-invalid="true" aria-describedby="email-error">
  <p id="email-error" class="text-red-600">Please enter a valid email address</p>
</form>
```

---

## 3. Performance Guidelines (HIGH)

### 3.1 Image Optimization

**Rule:** Use WebP format, implement lazy loading, provide responsive srcset.

**Incorrect:**
```html
<!-- Large unoptimized image, loads immediately -->
<img src="hero.png" width="1920">
```

**Correct:**
```html
<!-- Optimized with multiple formats and lazy loading -->
<picture>
  <source srcset="hero.avif" type="image/avif">
  <source srcset="hero.webp" type="image/webp">
  <img 
    src="hero.jpg" 
    alt="Hero image"
    loading="lazy"
    decoding="async"
    width="1920"
    height="1080"
    srcset="hero-480.jpg 480w, hero-768.jpg 768w, hero-1200.jpg 1200w"
    sizes="100vw"
  >
</picture>
```

### 3.2 Respect Reduced Motion

**Rule:** Honor `prefers-reduced-motion` for users with vestibular disorders.

**Incorrect:**
```css
/* Always animating - can cause motion sickness */
.modal {
  animation: slide-in 0.3s ease-out;
}
```

**Correct:**
```css
/* Respects user preference */
.modal {
  animation: slide-in 0.3s ease-out;
}

@media (prefers-reduced-motion: reduce) {
  .modal {
    animation: none;
    opacity: 1;
    transform: none;
  }
}
```

### 3.3 Content Layout Shift Prevention

**Rule:** Reserve space for async content to prevent layout shifts (CLS).

**Incorrect:**
```jsx
// Image loads and pushes content down
<img src={imageUrl} alt="Dynamic content">
```

**Correct:**
```jsx
// Reserve space with aspect ratio
<div className="aspect-video bg-gray-100">
  <img 
    src={imageUrl} 
    alt="Dynamic content"
    className="w-full h-full object-cover"
  >
</div>

// Or fixed dimensions
<div style={{ width: 300, height: 200 }}>
  {content}
</div>
```

---

## 4. Layout & Responsive Guidelines (HIGH)

### 4.1 Viewport Meta Tag

**Rule:** Always include proper viewport meta tag for responsive behavior.

**Incorrect:**
```html
<!-- Missing viewport tag - mobile displays at desktop width -->
<head>
  <title>My App</title>
</head>
```

**Correct:**
```html
<!-- Proper viewport configuration -->
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>My App</title>
</head>
```

### 4.2 Minimum Font Size on Mobile

**Rule:** Body text should be minimum 16px on mobile to prevent iOS zoom on focus.

**Incorrect:**
```css
/* Too small - triggers zoom on iOS */
body {
  font-size: 14px;
}
```

**Correct:**
```css
/* Readable minimum size */
body {
  font-size: 16px;
}

@media (min-width: 768px) {
  body {
    font-size: 18px;
  }
}
```

### 4.3 Z-Index Management

**Rule:** Define a consistent z-index scale to prevent overlay issues.

**Incorrect:**
```css
/* Arbitrary values lead to z-index wars */
.dropdown { z-index: 9999; }
.modal { z-index: 10000; }
.tooltip { z-index: 99999; }
```

**Correct:**
```css
/* Consistent scale */
:root {
  --z-base: 0;
  --z-dropdown: 10;
  --z-sticky: 20;
  --z-drawer: 30;
  --z-modal: 40;
  --z-popover: 50;
  --z-tooltip: 60;
}

.modal { z-index: var(--z-modal); }
.modal-overlay { z-index: calc(var(--z-modal) - 1); }
```

---

## 5. Typography Guidelines (MEDIUM)

### 5.1 Line Height for Readability

**Rule:** Use 1.5-1.75 line height for body text, 1.2-1.4 for headings.

**Incorrect:**
```css
/* Too tight - hard to read */
body {
  line-height: 1.1;
}
```

**Correct:**
```css
/* Comfortable reading */
body {
  line-height: 1.6;
}

h1, h2, h3 {
  line-height: 1.2;
}
```

### 5.2 Optimal Line Length

**Rule:** Limit text width to 60-75 characters per line for optimal readability.

**Incorrect:**
```css
/* Too wide - eye strain */
.content {
  max-width: none;
}
```

**Correct:**
```css
/* Optimal reading width */
.content {
  max-width: 65ch; /* ~65 characters */
}

/* Or fixed width */
.article {
  max-width: 680px;
}
```

---

## 6. Animation Guidelines (MEDIUM)

### 6.1 Animation Duration

**Rule:** Micro-interactions: 150-300ms, Page transitions: 300-500ms.

**Incorrect:**
```css
/* Too slow - feels unresponsive */
.button {
  transition: all 0.8s ease;
}
```

**Correct:**
```css
/* Snappy micro-interaction */
.button {
  transition: background-color 200ms ease, transform 150ms ease;
}

/* Page transition */
.page-transition {
  animation: fade-in 300ms ease-out;
}
```

### 6.2 GPU-Accelerated Properties

**Rule:** Animate `transform` and `opacity` only for 60fps performance.

**Incorrect:**
```css
/* Triggers layout/paint - janky */
.card:hover {
  width: 320px;
  height: 240px;
  left: 10px;
}
```

**Correct:**
```css
/* GPU accelerated - smooth */
.card:hover {
  transform: scale(1.05) translateX(10px);
}

/* For size changes, use transform: scale() or FLIP technique */
```

---

## 7. UI Style Database

### 7.1 Style Categories

| Style | Best For | Key Characteristics |
|-------|----------|---------------------|
| **Minimalism** | SaaS, portfolios | Clean, whitespace, functional |
| **Glassmorphism** | Dashboards, modals | Transparency, blur effects |
| **Neumorphism** | Calculator apps, controls | Soft shadows, extruded look |
| **Brutalism** | Creative portfolios | Bold colors, raw aesthetics |
| **Claymorphism** | Playful apps, games | Soft 3D, rounded forms |
| **Bento Grid** | Dashboards, showcases | Card-based grid layouts |
| **Dark Mode** | Media, coding, night | High contrast, reduced eye strain |
| **Skeuomorphism** | Rich media, music apps | Real-world metaphors |

### 7.2 Style Selection Matrix

| Product Type | Recommended Style | Alternative |
|--------------|-------------------|-------------|
| SaaS Dashboard | Minimalism + Glassmorphism | Bento Grid |
| E-commerce Luxury | Elegant Minimalism | Dark Mode |
| Healthcare | Clean Minimalism | Soft Neumorphism |
| Fintech | Professional Minimalism | Dark Mode |
| Gaming | Cyberpunk/Dark | Brutalism |
| Creative Portfolio | Brutalism | Experimental |
| Education | Friendly Minimalism | Claymorphism |

---

## 8. Color Palette Database

### 8.1 Palette Categories by Product Type

| Product Type | Primary | Secondary | Background | Accent |
|--------------|---------|-----------|------------|--------|
| **SaaS Corporate** | #2563EB | #3B82F6 | #F8FAFC | #0F172A |
| **Healthcare** | #0D9488 | #14B8A6 | #F0FDFA | #F97316 |
| **Fintech** | #059669 | #10B981 | #F0FDF4 | #F59E0B |
| **E-commerce Luxury** | #1E1B4B | #4338CA | #FAFAF9 | #D4AF37 |
| **Gaming** | #7C3AED | #8B5CF6 | #0F172A | #EC4899 |
| **Beauty/Spa** | #DB2777 | #EC4899 | #FDF2F8 | #F472B6 |
| **Food/Restaurant** | #DC2626 | #EF4444 | #FEF2F2 | #F59E0B |

### 8.2 Dark Mode Palettes

| Style | Background | Surface | Primary | Text |
|-------|------------|---------|---------|------|
| **Deep Space** | #0A0A0F | #12121A | #6366F1 | #E2E8F0 |
| **Midnight** | #0F172A | #1E293B | #3B82F6 | #F1F5F9 |
| **Obsidian** | #18181B | #27272A | #A855F7 | #FAFAFA |

---

## 9. Typography Database

### 9.1 Font Pairings

| Mood | Heading Font | Body Font | Best For |
|------|--------------|-----------|----------|
| **Professional** | Inter | Inter | SaaS, corporate |
| **Editorial** | Playfair Display | Source Sans Pro | Blogs, magazines |
| **Modern** | Space Grotesk | Inter | Tech startups |
| **Friendly** | Nunito | Open Sans | Education, consumer |
| **Luxury** | Cormorant Garamond | Montserrat | High-end brands |
| **Technical** | JetBrains Mono | Inter | Developer tools |
| **Playful** | Fredoka | Nunito | Children's apps |

### 9.2 Type Scale

```
Base: 16px / 1rem
Scale: 1.25 (Major Third)

xs:     0.75rem  (12px)   - Captions, fine print
sm:     0.875rem (14px)   - Secondary text
base:   1rem     (16px)   - Body text
lg:     1.125rem (18px)   - Lead paragraphs
xl:     1.25rem  (20px)   - Small headings
2xl:    1.5rem   (24px)   - H4
3xl:    1.875rem (30px)   - H3
4xl:    2.25rem  (36px)   - H2
5xl:    3rem     (48px)   - H1
6xl:    3.75rem  (60px)   - Hero
```

---

## 10. Stack-Specific Guidelines

### 10.1 HTML + Tailwind CSS

```html
<!-- Component structure -->
<div class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
  <h3 class="text-lg font-semibold text-gray-900">Card Title</h3>
  <p class="mt-2 text-gray-600">Card content with proper contrast.</p>
  <button class="mt-4 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
    Action
  </button>
</div>
```

### 10.2 React + Tailwind

```jsx
// Component with proper accessibility
function Button({ children, onClick, isLoading, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || isLoading}
      className="rounded-md bg-blue-600 px-4 py-2 text-white transition-colors duration-200 hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      aria-busy={isLoading}
    >
      {isLoading ? <Spinner /> : children}
    </button>
  );
}
```

### 10.3 shadcn/ui

```jsx
// Using shadcn/ui components
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

<Card>
  <CardHeader>
    <CardTitle>Feature Title</CardTitle>
  </CardHeader>
  <CardContent>
    <p>Content with built-in accessibility.</p>
    <Button variant="default">Get Started</Button>
  </CardContent>
</Card>
```

---

## 11. Pre-Delivery Checklist

### Visual Quality
- [ ] No emojis used as icons (use SVG: Heroicons/Lucide)
- [ ] All icons from consistent icon set
- [ ] Brand logos are correct (verified from Simple Icons)
- [ ] Hover states don't cause layout shift
- [ ] Use theme colors directly

### Interaction
- [ ] All clickable elements have `cursor-pointer`
- [ ] Hover states provide clear visual feedback
- [ ] Transitions are smooth (150-300ms)
- [ ] Focus states visible for keyboard navigation

### Light/Dark Mode
- [ ] Light mode text has sufficient contrast (4.5:1 minimum)
- [ ] Glass/transparent elements visible in light mode
- [ ] Borders visible in both modes
- [ ] Test both modes before delivery

### Layout
- [ ] Floating elements have proper spacing from edges
- [ ] No content hidden behind fixed navbars
- [ ] Responsive at 375px, 768px, 1024px, 1440px
- [ ] No horizontal scroll on mobile

### Accessibility
- [ ] All images have alt text
- [ ] Form inputs have labels
- [ ] Color is not the only indicator
- [ ] `prefers-reduced-motion` respected

---

## 12. Design System Generation

When creating a design system, follow this workflow:

### Step 1: Analyze Requirements
Extract from user request:
- **Product type**: SaaS, e-commerce, portfolio, dashboard
- **Style keywords**: minimal, playful, professional, elegant, dark mode
- **Industry**: healthcare, fintech, gaming, education
- **Stack**: React, Vue, or default to HTML+Tailwind

### Step 2: Select Components
Based on product type, choose:
1. **Landing Pattern** → from landing guidelines
2. **UI Style** → from style database (Section 7)
3. **Color Palette** → from color database (Section 8)
4. **Typography** → from font pairings (Section 9)
5. **Key Effects** → based on selected style

### Step 3: Apply Stack Guidelines
Implement using the selected stack's best practices (Section 10).

### Step 4: Verify Checklist
Run through pre-delivery checklist (Section 11) before finalizing.

---

## 13. Common Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Emoji as icons | Inconsistent, accessibility issues | Use SVG icons |
| Missing cursor-pointer | Users don't know it's clickable | Add cursor-pointer |
| Instant state changes | Jarring experience | Add 150-300ms transitions |
| Low contrast text | Unreadable | Minimum 4.5:1 ratio |
| No focus states | Keyboard users lost | Visible focus rings |
| Layout shift on load | Poor UX, affects metrics | Reserve space |
| Fixed without safe area | Notch/rounded corners hidden | Use safe-area-inset |

---

## References

- [WCAG 2.2 Guidelines](https://www.w3.org/WAI/WCAG22/quickref/)
- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [Material Design 3](https://m3.material.io/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Radix UI Primitives](https://www.radix-ui.com/)
