# /iconography - Icon Implementation and Auditing

$ARGUMENTS

---

## Purpose

This command activates the `icon-specialist` agent to implement, debug, or audit iconography across the project, leveraging the `iconography-expert` skill.

---

## Behavior

When `/iconography` is triggered:

1. **Information Gathering & Context**
   - Identify the current icon library in use (e.g., FontAwesome, Material Icons, SVGs).
   - Locate the Content Security Policy (CSP) headers or meta tags in the project.
   - Check existing icon implementation for accessibility attributes.

2. **Analysis & Debugging**
   - Check if webfonts are correctly referenced and if their CDNs are allowed via `font-src` and `style-src` in CSP.
   - Look for incorrect icon classes, mixed families (e.g., solid and outline together), or misaligned sizes.

3. **Implementation & Refactoring**
   - Provide the specific fixes needed (e.g., updating CSP, adding `aria-hidden="true"`).
   - If migrating to a new library, provide step-by-step instructions for implementing SVGs or webfonts.

4. **Verification**
   - Ensure the updated UI passes the `ux_audit.py` checklist criteria for accessibility.
   - Ensure the application still works correctly without rendering broken squares for icons.

---

## Output Format

```markdown
## 🎨 Iconography Audit: [Task/Issue]

### 1. Current State
[What library is in use + any identified issues like CSP blocks or a11y failures]

### 2. Required Fixes
- **CSP**: [Required changes to Content Security Policy]
- **Accessibility**: [Required changes to aria labels or aria-hidden attributes]
- **Implementation**: [Code changes needed for the icons themselves]

### 3. Action Taken
**Applying changes...** [Details of what was changed]

### 4. Verification
✅ Verified CSP allows webfonts.
✅ Verified icons are hidden from screen readers if decorative.
```

---

## Usage Examples

```
/iconography fix missing square icons in the navbar
/iconography audit accessibility of all buttons
/iconography migrate from FontAwesome to Lucide SVGs
```

---

## Key Principles

- **No Empty Squares**: Always check CSP before assuming an icon library is broken.
- **A11y First**: Semantic icons need labels; decorative icons need hiding.
- **Consistency**: Keep icon families consistent.
