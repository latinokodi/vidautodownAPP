---
description: Plan and implement high-interactivity TUIs
---

# tui-ux-pro-max

Comprehensive guide for building elite terminal user interfaces. Covers layout design, framework selection, and implementation patterns for Python, Node.js, and Go.

## Prerequisites

Ensure you have the necessary TUI libraries for your chosen stack:

**Python:**
```bash
pip install textual rich prompt_toolkit questionary
```

**Node.js:**
```bash
npm install ink react ink-select-input chalk ora boxen
```

**Go:**
```bash
go get github.com/charmbracelet/bubbletea github.com/charmbracelet/lipgloss
```

---

## How to Use This Workflow

When a user requests a new CLI or TUI, or wants to improve an existing one, follow these steps:

### Step 1: Determine the Interactivity Level

Use the "Ladder of CLI UX" to define the goal:
- **Level 2 (Enhanced)**: Focus on output styling (Rich/Chalk).
- **Level 3 (Interactive Prompt)**: Focus on input wizards (Questionary/Inquirer).
- **Level 4 (Full TUI)**: Focus on reactive layouts (Textual/Ink/Bubble Tea).

### Step 2: Framework Selection (REQUIRED)

Run the TUI Recommendation tool to get the best stack for the project:

```bash
python3 .agent/.shared/tui-ux-pro-max/scripts/tui_search.py "<project_description> <requirements>"
```

### Step 3: Design the Layout

Before coding, define the terminal layout. **Avoid mixing strict Grid layouts on the Screen with Docking inside nested containers.**
- **Header**: Title, version, status, and system clock.
- **Main Area**: Use `Horizontal` or `Vertical` containers for side-by-side panes.
- **Sidebar**: (Fixed width) For persistent stats and configuration toggles.
- **Footer**: Mandatory keybinding reference.

### Step 4: Implement Reactive State & Background Tasks

- **Progress Tracking**: For long-running batches, use a dedicated scrollable area with reactive `ProgressBar` widgets. Never rely on log-text percentages for primary feedback.
- **Interactive Modals**: Use `ModalScreen` for complex inputs (checkbox lists, path selection) or confirmation interrupts ("Already processed?").
- **Async Safety**: Use `@work` (Textual) or equivalent to ensure long tasks don't block the UI loop. Use `call_from_thread` or messages to update UI from background threads.

---

## TUI Best Practices

### Interaction
- **Keybindings**: Use intuitive keys (`q` to quit, `?` for help, vim-keys for navigation).
- **Startup Audit**: Log a "System Audit" on mount to confirm environment status (DB connected, external tools detected, etc.).
- **Feedback**: Every keypress should result in a visual change (Notifications or UI updates).

### Visuals
- **Layout Stability**: Prefer `min-height` and `width: 1fr` over absolute sizes to handle varied terminal dimensions.
- **Contrast**: Use bold colors (Magenta/Cyan) for interactive headers and subtle colors (Dim/Grey) for secondary info.
- **Aesthetic Polish**: Use Unicode icons (⚙, 📊, ⚡) in headers to give a "Premium" feel.

---

## Pre-Delivery Checklist

- [ ] App handles `SIGINT` (Ctrl+C) gracefully.
- [ ] UI clears and restores the terminal on exit.
- [ ] Application responds to window resize events without content vanishing.
- [ ] No layout "shifting" when items are mounted/removed (use placeholders or min-sizes).
- [ ] All critical keybindings are visible in the footer.
- [ ] Progress bars are smooth and non-blocking.
