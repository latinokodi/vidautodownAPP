# UI Style Reference

Complete database of 50+ UI styles with implementation guidance.

## Style Categories

### 1. Minimalism
**Best for:** SaaS, portfolios, landing pages
**Characteristics:**
- Clean lines and whitespace
- Functional, content-first approach
- Limited color palette (often monochrome + accent)
- Generous spacing
- Simple typography

**CSS Keywords:**
```
clean, simple, whitespace, functional, modern, professional, elegant
```

**Implementation:**
```css
.card {
  background: white;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 24px;
}
```

---

### 2. Glassmorphism
**Best for:** Dashboards, modals, overlays
**Characteristics:**
- Translucent backgrounds
- Backdrop blur effects
- Subtle borders
- Layered depth

**CSS Keywords:**
```
glass, translucent, blur, backdrop-filter, frosted, layered, depth
```

**Implementation:**
```css
.glass-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 16px;
}

/* Dark mode variant */
.glass-card-dark {
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
```

---

### 3. Neumorphism (Soft UI)
**Best for:** Calculator apps, controls, toggles
**Characteristics:**
- Soft shadows creating extruded look
- Light and dark shadows
- Monochromatic color scheme
- Rounded corners

**CSS Keywords:**
```
neumorphism, soft-ui, extruded, embossed, shadows, tactile, 3d-soft
```

**Implementation:**
```css
.neu-button {
  background: #E0E5EC;
  border-radius: 50px;
  box-shadow: 
    9px 9px 16px #A3B1C6,
    -9px -9px 16px #FFFFFF;
}

.neu-button:active {
  box-shadow: 
    inset 9px 9px 16px #A3B1C6,
    inset -9px -9px 16px #FFFFFF;
}
```

---

### 4. Brutalism
**Best for:** Creative portfolios, art sites, experimental
**Characteristics:**
- Raw, unpolished aesthetics
- Bold colors and high contrast
- Unconventional layouts
- Visible grid systems
- System fonts

**CSS Keywords:**
```
brutalism, raw, bold, high-contrast, experimental, grid, system-fonts
```

**Implementation:**
```css
.brutalist-card {
  border: 3px solid black;
  box-shadow: 8px 8px 0 black;
  background: white;
  padding: 20px;
}

.brutalist-card:hover {
  transform: translate(-4px, -4px);
  box-shadow: 12px 12px 0 black;
}
```

---

### 5. Claymorphism
**Best for:** Playful apps, children's products, games
**Characteristics:**
- Soft, 3D rounded forms
- Dual-tone inner shadows
- Friendly, approachable aesthetic
- Pastel colors

**CSS Keywords:**
```
claymorphism, clay, soft-3d, friendly, playful, rounded, pastel
```

**Implementation:**
```css
.clay-button {
  background: linear-gradient(145deg, #FFB6C1, #FF69B4);
  border-radius: 30px;
  box-shadow: 
    8px 8px 16px rgba(0,0,0,0.15),
    inset -4px -4px 8px rgba(0,0,0,0.1),
    inset 4px 4px 8px rgba(255,255,255,0.3);
  padding: 16px 32px;
}
```

---

### 6. Bento Grid
**Best for:** Dashboards, showcases, feature highlights
**Characteristics:**
- Grid-based card layout
- Varied card sizes
- Consistent spacing
- Clear visual hierarchy

**CSS Keywords:**
```
bento, grid, cards, dashboard, masonry, organized, modular
```

**Implementation:**
```css
.bento-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.bento-item-large {
  grid-column: span 2;
  grid-row: span 2;
}

.bento-item-wide {
  grid-column: span 2;
}
```

---

### 7. Dark Mode / Night
**Best for:** Media apps, coding tools, AMOLED optimization
**Characteristics:**
- Dark backgrounds (#0F172A, #121212)
- High contrast text
- Reduced brightness
- Accent colors pop

**CSS Keywords:**
```
dark-mode, night, amoled, high-contrast, dark-theme, midnight
```

**Implementation:**
```css
.dark-theme {
  --bg-primary: #0F172A;
  --bg-secondary: #1E293B;
  --text-primary: #F1F5F9;
  --text-secondary: #94A3B8;
  --accent: #3B82F6;
}
```

---

### 8. Skeuomorphism
**Best for:** Rich media apps, music players, photography
**Characteristics:**
- Real-world metaphors
- Textures and gradients
- 3D depth
- Familiar physical objects

**CSS Keywords:**
```
skeuomorphism, realistic, textured, 3d, depth, gradients, physical
```

---

### 9. Cyberpunk
**Best for:** Gaming, tech, futuristic products
**Characteristics:**
- Neon colors (pink, cyan, purple)
- Dark backgrounds
- Glow effects
- Grid patterns
- Tech-inspired typography

**CSS Keywords:**
```
cyberpunk, neon, futuristic, glow, tech, synthwave, vaporwave
```

**Implementation:**
```css
.cyberpunk-card {
  background: #0A0A0F;
  border: 1px solid #FF00FF;
  box-shadow: 0 0 20px rgba(255, 0, 255, 0.3);
}

.cyberpunk-text {
  color: #00FFFF;
  text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
}
```

---

### 10. Organic/Natural
**Best for:** Wellness, eco-products, sustainable brands
**Characteristics:**
- Earth tones
- Rounded, organic shapes
- Nature-inspired textures
- Soft gradients

**CSS Keywords:**
```
organic, natural, earthy, eco, wellness, sustainable, soft
```

---

## Style Selection by Product Type

| Product Type | Recommended | Alternative | Avoid |
|--------------|-------------|-------------|-------|
| SaaS Dashboard | Minimalism, Bento Grid | Glassmorphism | Brutalism |
| E-commerce Luxury | Minimalism, Dark Mode | Elegant Skeuomorphism | Brutalism |
| Healthcare | Soft Minimalism | Organic | Brutalism, Cyberpunk |
| Fintech | Minimalism | Dark Mode | Claymorphism |
| Gaming | Cyberpunk | Dark Mode | Minimalism |
| Creative Portfolio | Brutalism | Experimental | - |
| Education | Friendly Minimalism | Claymorphism | Dark Mode |
| Social Media | Minimalism | Glassmorphism | Neumorphism |
| Travel | Organic | Minimalism | Cyberpunk |
| Food/Restaurant | Organic | Claymorphism | Cyberpunk |

---

## Accessibility Considerations by Style

| Style | Accessibility Notes |
|-------|---------------------|
| Minimalism | High contrast easily achievable |
| Glassmorphism | Ensure sufficient contrast with blur backgrounds |
| Neumorphism | Low contrast risk - test carefully |
| Brutalism | High contrast built-in, check color combinations |
| Dark Mode | Watch for eye strain with pure black (#000000) |
| Cyberpunk | Neon on dark can cause eye strain - use sparingly |
