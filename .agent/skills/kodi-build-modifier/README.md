# kodi-build-modifier

A specialized agent skill designed to automate the modification, standardization, and synchronization of navigation structures in complex Kodi build environments.

## Overview

Managing multiple portable Kodi builds often leads to "configuration drift," where navigational improvements made in a test environment are not correctly replicated in the primary build. This skill encapsulates the domain knowledge required to navigate the `script.skinshortcuts` configuration layer, providing a systematic approach to synchronizing submenus, widgets, and backgrounds while ensuring all absolute paths remain valid for each build's unique directory structure.

## Key Features

- **Automated Submenu Sync**: Replicates horizontal menu bars and custom category links between builds.
- **Path Normalization**: Smart correction of absolute file paths to prevent "broken icon" issues across different portable installations.
- **Shortcut Verification**: Audits `mainmenu.DATA.xml` to ensure custom triggers (like `<submenu>`) are correctly applied.
- **Changelog Integration**: Keeps a precise record of all build modifications in `BUILD_CHANGELOG.md`.

## Installation

To use this skill locally, ensure it is placed in your agent's skills directory:

```bash
# Path to skill
.agent/skills/kodi-build-modifier/
```

## Usage Examples

### Synchronizing a New Submenu
**Command**: "Replicate the Tucinelatino submenu from the second build to the primary build."
**Action**: The skill will detect the `.DATA.xml` file, copy it, adjust paths, and update the main menu configuration in the target build.

### Cleaning Up Navigation
**Command**: "Remove the legacy tecnotv and sr regio entries from the main menu and delete their data files."
**Action**: The skill will purge the entries from `mainmenu.DATA.xml`, remove associated lines from the `.properties` file, and delete the orphaned `.DATA.xml` files.

### Standardizing Widgets
**Command**: "Ensure the trending movies widget for the Plataformas section is identical across both builds."
**Action**: The skill will audit the `widgetPath` and `widgetName` properties and sync them.

## Requirements

- **Script**: `script.skinshortcuts` must be the primary navigation provider.
- **Skin**: Compatible with Xenon 2 and other skins using property-based submenu rendering.
- **Environment**: Support for absolute path mapping in portable installations.

---
*Created by Antigravity AI - 2026*
