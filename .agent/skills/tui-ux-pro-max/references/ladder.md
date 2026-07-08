# The Ladder of CLI UX

The highest level of CLI interactivity you can realistically build today is a full-screen TUI app that behaves like a lightweight terminal GUI: panels, forms, keybindings, mouse support, live updates, searchable lists, progress bars, syntax highlighting, and animated transitions within terminal limits.

## Interactivity Levels

- **Level 1: Basic CLI**: flags, commands, plain stdout/stderr.
- **Level 2: Enhanced CLI**: colors, spinners, tables, progress bars, confirmations.
- **Level 3: Interactive Prompt CLI**: selectable menus, autocompletion, wizard flows, fuzzy search, validation.
- **Level 4: Full TUI App**: panes, keyboard navigation, mouse support, reactive state, live refresh, modal dialogs, full-screen layouts.

## Best Libraries by Language

### Python
- `prompt_toolkit`: Advanced input, autocomplete, keybindings, mouse, full-screen TUI foundations.
- `Rich`: Tables, progress bars, styled logs, syntax-highlighted output.
- `Textual`: App-like widgets and layouts with CSS-like styling.
- `Questionary`: Elegant interactive prompts.

### Node.js
- `Inquirer` / `Enquirer`: Prompts, selections, wizard-like flows.
- `Commander`: Subcommands and argument structure.
- `Chalk`: Styling.
- `Ora`: Spinners/loading feedback.
- `Ink`: React-style component model for terminal apps.
- `Boxen`: Boxes in terminal.

### Go
- `Bubble Tea`: Full reactive TUI apps (The Elm Architecture for CLI).
- `Lip Gloss`: Layout and style.
- `Cobra`: Command architecture.
- `Viper`: Configuration.
- `Survey`: Prompts.

## Recommendation by Goal

- **Python**: Choose for rich input and fast productivity. Great for REPLs and dashboards.
- **Go**: Choose for robust, single-binary full-screen TUI apps. Highly admired for performance and portability.
- **Node.js**: Choose for ecosystem familiarity and prompt-heavy developer tooling.
