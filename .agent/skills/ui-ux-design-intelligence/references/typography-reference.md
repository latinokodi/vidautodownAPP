# Typography Reference

Complete database of 57 font pairings with implementation guidance.

## Font Loading

### Google Fonts (Standard)
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### Google Fonts (Variable)
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap" rel="stylesheet">
```

### Font Display Strategy
Always use `&display=swap` to prevent FOIT (Flash of Invisible Text).

---

## Professional / Corporate

### Inter + Inter (Modern Default)
**Best for:** SaaS, corporate sites, dashboards
**Mood:** Clean, modern, highly legible

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
```

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### Plus Jakarta Sans + Inter
**Best for:** Tech startups, modern brands
**Mood:** Contemporary, friendly professional

```css
/* Heading */
font-family: 'Plus Jakarta Sans', sans-serif;
/* Body */
font-family: 'Inter', sans-serif;
```

### Manrope + Inter
**Best for:** Product landing pages
**Mood:** Geometric, modern

---

## Editorial / Content

### Playfair Display + Source Sans Pro
**Best for:** Blogs, magazines, luxury brands
**Mood:** Elegant, editorial, sophisticated

```html
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Source+Sans+Pro:wght@400;600&display=swap" rel="stylesheet">
```

```css
/* Heading */
font-family: 'Playfair Display', Georgia, serif;
/* Body */
font-family: 'Source Sans Pro', sans-serif;
```

### Merriweather + Open Sans
**Best for:** Long-form content, publishing
**Mood:** Classic, readable, trustworthy

### Cormorant Garamond + Montserrat
**Best for:** Luxury brands, high-end products
**Mood:** Elegant, refined, premium

```html
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600&family=Montserrat:wght@400;500;600&display=swap" rel="stylesheet">
```

### Lora + Inter
**Best for:** Blogs, literary sites
**Mood:** Warm, approachable editorial

---

## Modern / Creative

### Space Grotesk + Inter
**Best for:** Tech startups, creative agencies
**Mood:** Modern, slightly quirky, distinctive

```html
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
```

### Syne + Inter
**Best for:** Creative portfolios, design agencies
**Mood:** Artistic, bold, expressive

### Clash Display + Satoshi
**Best for:** Bold brands, modern apps
**Mood:** Strong, contemporary, impactful

---

## Friendly / Approachable

### Nunito + Open Sans
**Best for:** Education, consumer apps, children's products
**Mood:** Rounded, friendly, approachable

```html
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&family=Open+Sans:wght@400;600&display=swap" rel="stylesheet">
```

### Quicksand + Nunito
**Best for:** Apps, casual products
**Mood:** Soft, rounded, playful

### Fredoka + Nunito
**Best for:** Children's products, games
**Mood:** Playful, fun, energetic

---

## Technical / Code

### JetBrains Mono + Inter
**Best for:** Developer tools, technical docs
**Mood:** Monospace headers, clean body

```html
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@400;500&display=swap" rel="stylesheet">
```

### Fira Code + Inter
**Best for:** Code-focused products
**Mood:** Developer-friendly

---

## Luxury / Premium

### Cormorant + Montserrat Light
**Best for:** High-end brands, fashion
**Mood:** Elegant, luxurious, refined

### Cormorant Garamond + Lato Light
**Best for:** Luxury goods, hospitality
**Mood:** Classic elegance

### Oranienbaum + Montserrat
**Best for:** Premium services
**Mood:** Sophisticated, distinctive

---

## Bold / Impact

### Syne + Inter
**Best for:** Creative agencies, portfolios
**Mood:** Bold, artistic, statement-making

### Cabinet Grotesk + Inter
**Best for:** Modern brands, startups
**Mood:** Strong, contemporary

### General Sans + Inter
**Best for:** Modern SaaS, tech
**Mood:** Geometric, confident

---

## Classic / Timeless

### Georgia + System Sans
**Best for:** Traditional publications
**Mood:** Classic, trustworthy

### Times New Roman + Arial
**Best for:** Formal documents
**Mood:** Traditional, conservative

---

## Type Scale

### Major Third Scale (1.25)
Common for web applications:

```
12px  (0.75rem)   - Caption, helper text
14px  (0.875rem)  - Small text, labels
16px  (1rem)      - Body text (base)
18px  (1.125rem)  - Lead text
20px  (1.25rem)   - Small headings
24px  (1.5rem)    - H4
30px  (1.875rem)  - H3
36px  (2.25rem)   - H2
48px  (3rem)      - H1
60px  (3.75rem)   - Hero text
```

### Tailwind Config
```js
module.exports = {
  theme: {
    fontSize: {
      'xs': ['0.75rem', { lineHeight: '1rem' }],
      'sm': ['0.875rem', { lineHeight: '1.25rem' }],
      'base': ['1rem', { lineHeight: '1.5rem' }],
      'lg': ['1.125rem', { lineHeight: '1.75rem' }],
      'xl': ['1.25rem', { lineHeight: '1.75rem' }],
      '2xl': ['1.5rem', { lineHeight: '2rem' }],
      '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
      '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
      '5xl': ['3rem', { lineHeight: '1' }],
      '6xl': ['3.75rem', { lineHeight: '1' }],
    }
  }
}
```

---

## Line Height Guidelines

| Element | Line Height | Notes |
|---------|-------------|-------|
| Body text | 1.5 - 1.75 | Comfortable reading |
| Headings | 1.2 - 1.4 | Tight, impactful |
| Display/Hero | 1.0 - 1.1 | Very tight |
| Captions | 1.4 - 1.5 | Slightly tighter than body |
| Code | 1.5 - 1.7 | Monospace needs more space |

---

## Font Weight Usage

| Weight | Name | Usage |
|--------|------|-------|
| 400 | Regular | Body text, descriptions |
| 500 | Medium | UI elements, labels |
| 600 | Semi-bold | Subheadings, emphasis |
| 700 | Bold | Headings, CTAs |
| 800 | Extra-bold | Hero text, impact |

---

## Letter Spacing

| Element | Letter Spacing | Notes |
|---------|----------------|-------|
| Body | 0 | Normal tracking |
| Headings | -0.02em | Tighter for impact |
| Caps/Labels | 0.05em | Wider for small caps |
| Code | 0 | Monospace default |

---

## Font Pairing Quick Reference

| Use Case | Heading Font | Body Font | Loading URL |
|----------|--------------|-----------|-------------|
| SaaS Default | Inter | Inter | `family=Inter:wght@400;500;600;700` |
| Editorial | Playfair Display | Source Sans Pro | `family=Playfair+Display:wght@400;600\|Source+Sans+Pro:wght@400;600` |
| Luxury | Cormorant Garamond | Montserrat | `family=Cormorant+Garamond:wght@400;600\|Montserrat:wght@400;500` |
| Modern Tech | Space Grotesk | Inter | `family=Space+Grotesk:wght@400;500;600\|Inter:wght@400;500` |
| Friendly | Nunito | Open Sans | `family=Nunito:wght@400;600;700\|Open+Sans:wght@400;600` |
| Developer | JetBrains Mono | Inter | `family=JetBrains+Mono:wght@400;600\|Inter:wght@400;500` |
| Creative | Syne | Inter | `family=Syne:wght@400;600;700\|Inter:wght@400;500` |

---

## Best Practices

### Performance
1. Limit to 2-3 font families maximum
2. Load only necessary weights (400, 500, 600, 700)
3. Use `display=swap` to prevent FOIT
4. Consider self-hosting for critical fonts
5. Preload critical fonts:
   ```html
   <link rel="preload" href="/fonts/inter.woff2" as="font" type="font/woff2" crossorigin>
   ```

### Accessibility
1. Minimum 16px for body text (prevents zoom on iOS)
2. Line height 1.5+ for readability
3. Sufficient contrast between text and background
4. Don't use overly thin weights for body text
5. Test with dyslexia-friendly fonts when appropriate

### System Font Stack (Fallback)
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
```
