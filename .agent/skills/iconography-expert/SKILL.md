---
name: iconography-expert
description: Ensure proper use of FontAwesome, Material Icons, and other icon sets, including Content Security Policy (CSP) configuration, accessibility, and consistent usage.
---

# Iconography Expert Skill

## Purpose
To ensure that applications correctly implement and configure icon libraries such as FontAwesome, Material Icons, Lucide, and Heroicons. This includes handling Content Security Policy (CSP) for webfonts, ensuring accessibility (a11y), and maintaining visual consistency across the project.

## When to Use This Skill
- Adding new icon libraries to a project.
- Debugging missing or "square" icons (often caused by CSP issues).
- Reviewing UI code for accessibility compliance regarding icons.
- Standardizing icon usage across a codebase.

## Core Capabilities
1. **CSP Configuration**: Ensure `font-src`, `style-src`, and `img-src` allow the appropriate CDNs or local paths.
2. **Accessibility (a11y)**: Enforce the use of `aria-hidden="true"` for decorative icons and screen-reader-only text for semantic icons.
3. **Consistency**: Prevent mixing of different icon families (e.g., mixing FontAwesome Solid with Material Outlined) within the same UI context.
4. **Performance**: Recommend SVG usage over webfonts when appropriate to reduce bundle size and render blocking.

## Guidelines

### 1. Content Security Policy (CSP) for Webfonts
When using CDNs like `cdnjs.cloudflare.com` for FontAwesome or Google Fonts for Material Icons, the CSP must explicitly allow the webfonts to load.
- **FontAwesome via CDNJS**: Must include `https://cdnjs.cloudflare.com` in both `style-src` and `font-src`.
- **Material Icons**: Must include `https://fonts.googleapis.com` in `style-src` and `https://fonts.gstatic.com` in `font-src`.
*Failure to configure CSP correctly will result in browsers rendering empty squares or replacement characters instead of the icons.*

### 2. Accessibility Best Practices
Icons must be accessible to screen readers:
- **Decorative Icons**: If an icon is purely visual and accompanied by text (e.g., a search icon next to the word "Search"), hide it from screen readers:
  ```html
  <i class="fas fa-search" aria-hidden="true"></i>
  <span>Search</span>
  ```
- **Semantic Icons**: If an icon stands alone without visible text (e.g., an "X" icon to close a modal), provide accessible text:
  ```html
  <button aria-label="Close dialog">
      <i class="fas fa-times" aria-hidden="true"></i>
  </button>
  ```
  *Alternatively, use `.sr-only` class for screen-reader-only text.*

### 3. SVG vs Webfonts
Whenever possible, prefer inline SVGs (like Heroicons or Lucide) over large monolithic webfonts (like full FontAwesome) unless the project heavily relies on the entire icon set. SVGs eliminate CSP font issues and improve performance.

### 4. Consistency Rules
- Do not mix solid and outlined icons within the same navigation or toolbar unless indicating active/inactive states.
- Stick to a single primary icon library per project.

## Debugging Flow for Missing Icons
1. Check the browser console for CSP violation errors.
2. Verify that `font-src` explicitly allows the font's origin URL.
3. Check the network tab to ensure `.woff2` or `.ttf` files are successfully downloading (HTTP 200).
4. Verify the correct class names are being used (e.g., `fas` vs `far` for FontAwesome).
