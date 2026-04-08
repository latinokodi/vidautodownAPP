# UX Guidelines Reference

Complete database of 99 UX best practices organized by category.

---

## Navigation Patterns

### 1.1 Primary Navigation
- Keep primary navigation to 5-7 items maximum
- Use clear, action-oriented labels
- Highlight current location
- Ensure touch targets are 44px+ on mobile
- Consider sticky navigation for long pages

### 1.2 Breadcrumb Navigation
- Show hierarchy, not history
- Include current page (non-clickable)
- Use ">" or "/" as separators
- Helpful for sites 3+ levels deep

### 1.3 Mobile Navigation
- Hamburger menu for 5+ items
- Tab bar for 3-5 primary actions
- Bottom navigation within thumb reach
- Swipe gestures for secondary actions

---

## Form Design

### 2.1 Input Fields
- Match input length to expected content
- Use appropriate input types (email, tel, number)
- Show field requirements upfront
- Group related fields

### 2.2 Labels
- Always visible (not just placeholder)
- Position above or left of input
- Use sentence case
- Associate with `for` attribute

### 2.3 Validation
- Validate on blur, not just submit
- Show inline error messages
- Be specific about errors
- Preserve user input on error

### 2.4 Buttons
- Primary action most prominent
- Secondary actions visually muted
- Destructive actions require confirmation
- Loading state during submission

---

## Error Handling

### 3.1 Error Prevention
- Disable submit until valid
- Confirm destructive actions
- Auto-save draft content
- Provide undo for irreversible actions

### 3.2 Error Messages
- Clear, human language
- Explain what happened
- Suggest how to fix
- Place near the problem

### 3.3 404 Pages
- Acknowledge the error
- Offer search functionality
- Suggest popular pages
- Maintain site navigation

---

## Feedback & Status

### 4.1 Loading States
- Show progress for long operations
- Skeleton screens for content loading
- Disable buttons during submission
- Prevent double-submission

### 4.2 Success Messages
- Confirm action completed
- Auto-dismiss after 3-5 seconds
- Include next steps if relevant
- Non-blocking (toast preferred)

### 4.3 Empty States
- Explain why content is missing
- Provide clear CTA to add content
- Use friendly illustrations
- Help users get started

---

## Responsive Design

### 5.1 Breakpoints
```
Mobile:     < 640px
Tablet:     640px - 1024px
Desktop:    1024px - 1280px
Large:      > 1280px
```

### 5.2 Mobile-First Approach
- Design for mobile constraints first
- Progressive enhancement for larger screens
- Touch-friendly targets minimum 44px
- Consider thumb zones for navigation

### 5.3 Content Priority
- Most important content first
- Simplify navigation on mobile
- Consider accordion for long content
- Hide decorative elements if needed

---

## Visual Hierarchy

### 6.1 Size & Scale
- Headings establish content structure
- Important elements are larger
- Consistent type scale throughout
- Whitespace creates separation

### 6.2 Color & Contrast
- Primary actions use primary color
- Secondary actions are neutral
- Errors are red (consistent)
- Success states are green

### 6.3 Spacing
- 8px grid system recommended
- Consistent vertical rhythm
- Group related items closer
- Separate distinct sections

---

## Accessibility

### 7.1 Keyboard Navigation
- All functionality keyboard accessible
- Visible focus indicators
- Logical tab order
- Skip links for main content

### 7.2 Screen Readers
- Descriptive alt text for images
- Proper heading hierarchy (h1-h6)
- ARIA labels for icon buttons
- Table headers properly marked

### 7.3 Motion
- Respect prefers-reduced-motion
- Don't auto-play video/audio
- Allow pausing carousels
- Subtle animations only

---

## Performance UX

### 8.1 Perceived Performance
- Show loading indicators quickly
- Progressive image loading
- Skeleton screens
- Optimistic UI updates

### 8.2 Content Loading
- Above-fold content first
- Lazy load below-fold images
- Infinite scroll vs pagination
- Preload critical resources

---

## Common Patterns

### 9.1 Cards
- Consistent internal padding
- Clear visual boundaries
- Hover states for interactivity
- Shadow or border (not both)

### 9.2 Modals/Dialogs
- Focus trap when open
- Close on Escape key
- Click outside to close (optional)
- Prevent background scrolling

### 9.3 Dropdowns
- Clear selected state
- Search for long lists
- Keyboard navigation support
- Close on selection

### 9.4 Tooltips
- Brief, helpful text
- Show on hover/focus
- Position to avoid clipping
- Don't repeat visible text

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Alternative |
|--------------|--------------|-------------|
| Mystery meat navigation | Users can't predict destination | Clear, descriptive labels |
| Infinite scroll + footer | Users can never reach footer | Pagination or sticky footer |
| Auto-playing carousel | Distracting, poor engagement | Static hero or user-controlled |
| Placeholder as label | Disappears when typing | Persistent labels above |
| Hidden password requirements | Users frustrated on error | Show requirements upfront |
| Disabled submit with no feedback | Users don't know what's wrong | Inline validation |
| Double navigation | Confusing hierarchy | Simplified, clear structure |
| Breaking back button | Users lose trust | Proper history management |
| Modal on modal | Confusing depth | Replace or sequential |
| Tiny click targets | Accessibility fail | Minimum 44px touch targets |

---

## Platform-Specific Guidelines

### iOS
- Follow Human Interface Guidelines
- Use SF Pro font family
- Respect safe areas
- Support Dynamic Type

### Android
- Follow Material Design 3
- Use Roboto font family
- Support edge-to-edge
- Handle system bars

### Web
- Progressive enhancement
- Cross-browser testing
- Responsive breakpoints
- Print stylesheets (if relevant)
