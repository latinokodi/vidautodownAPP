---
name: kodi-build-modifier
description: "To automate and standardize modifications to Kodi build environments, specializing in skin shortcut configuration, submenu management, and multi-build synchronization."
category: kodi
risk: safe
source: community
tags: "[kodi, build-maintenance, skin-shortcuts, navigation, automation]"
date_added: "2026-04-14"
---

# kodi-build-modifier

## Purpose

To automate and standardize modifications to Kodi build environments, specializing in skin shortcut configuration, submenu management, and multi-build synchronization. This skill ensures that navigational changes, such as custom submenus or widget arrangements, are applied consistently across primary and secondary portable build installations while maintaining accurate path normalization and documentation.

## When to Use This Skill

This skill should be used when:
- **Submenu Management**: Creating, expanding, or synchronizing submenu data files (`.DATA.xml`) for the `script.skinshortcuts` addon.
- **Navigation Standardization**: Ensuring that main menu entries, labels, and properties (like `hasSubmenu` or `submenuVisibility`) match across multiple builds.
- **Path Normalization**: Adjusting absolute file paths (e.g., icons, thumbs, or local addon resources) to reflect the specific directory structure of different portable Kodi installations.
- **Build Cleanup**: Removing legacy navigation entries or redundant properties that persist after addon removals or rebranding.
- **Multi-Build Sync**: Replicating a verified modification from a secondary "test" build to a primary "production" build with zero configuration drift.

## Core Capabilities

1. **Shortcut Data Parsing**: Analyzing and modifying `mainmenu.DATA.xml` and custom `.DATA.xml` files used by `script.skinshortcuts`.
2. **Property Synchronization**: Auditing and aligning properties within `skin.xenon2.properties` (or similar skin configuration files) to ensure correct widget rendering and submenu triggers.
3. **Automated Path Adjustment**: Programmatically detecting build-specific folder names (e.g., `LKOmega21.3Tests` vs. `LKOmega21.3Tests2`) and updating all internal references to media assets.
4. **Change Logging**: Integrating with project `BUILD_CHANGELOG.md` to automatically document structural changes for auditing and future replication.
5. **Cross-Build Comparison**: Identifying discrepancies in menu structure or asset configuration between different portable instances.
6. **Widget Enrichment**: Diagnosing and fixing interactivity issues in custom/legacy skin templates, ensuring consistent `<onclick>` behavior and optimized content targeting.

## Workflow

### Step 1: Discovery & Environment Mapping

Before applying changes, map the build environment to identify the primary and secondary installations.

**Key Files to Identify:**
- `userdata/addon_data/script.skinshortcuts/mainmenu.DATA.xml`
- `userdata/addon_data/script.skinshortcuts/skin.xenon2.properties`
- `userdata/addon_data/script.skinshortcuts/*.DATA.xml` (Custom submenus)
- `BUILD_CHANGELOG.md` (Project root)

**Detection Logic:**
Detect the base directory for each build. For example:
- `D:\Latino Kodi 100\Latino Kodi 100 Wizard\LKOmega21.3Tests`
- `D:\Latino Kodi 100\Latino Kodi 100 Wizard\LKOmega21.3Tests2`

### Step 2: Analysis of the Working Mod

If one build is already "working" (e.g., a test build), analyze its configuration to extract the successful pattern.

1. **Inspect `.DATA.xml`**: Check categories, labels, and actions.
2. **Inspect Main Menu**: Identify if the item has an explicit `<submenu>` tag or relies on automatic naming.
3. **Inspect Properties**: Check `widgetPath`, `background`, and submenu properties in the `.properties` file.

### Step 3: Modification & Normalization

Apply the changes to the target build, ensuring all absolute paths are normalized.

**Path Normalization Pattern:**
When copying a shortcut with a thumb path:
- **Source**: `image://D%3a%5c...%5cLKOmega21.3Tests2%5c...`
- **Target**: `image://D%3a%5c...%5cLKOmega21.3Tests%5c...`

**Submenu Trigger Enforcement:**
If a submenu is present but not showing, explicitly add the trigger to the shortcut in `mainmenu.DATA.xml`:
```xml
<shortcut>
    ...
    <submenu>filename_without_extension</submenu>
</shortcut>
```

### Step 4: Multi-Build Synchronization

Once the modification is validated in the target build, replicate it across all managed builds. 

1. **Batch Copy**: Use automated tools to copy `.DATA.xml` files.
2. **Property Sync**: Bulk update the properties file to match the desired state.
3. **Hash Invalidation**: If necessary, touch or delete the `.hash` files in the `script.skinshortcuts` directory to force the skin to rebuild its includes.

### Step 5: Verification & Documentation

1. **Visual Audit**: Verify the resulting `script-skinshortcuts-includes.xml` contains the expected `hasSubmenu="True"` properties.
2. **Changelog Update**: Append a concise entry to the project changelog:
    ```markdown
    ## [Date] - Build Name - Feature
    - **Feature**: Description of what was added/synced.
    - **Files Modified**: List of XML and property files.
    ```

## Best Practices

- **Atomic Changes**: Modify one submenu or section at a time to avoid complex menu corruption.
- **Case-Sensitivity**: Always match the `.DATA.xml` filename (all lowercase is standard) with the label or the explicit `<submenu>` tag.
- **Backup Properties**: The `skin.xenon2.properties` file is fragile; always verify its integrity after bulk edits.
- **Relative Media**: Prefer `special://` paths where possible, but if using `image://` absolute paths, always perform string substitution during sync.

## Technical Details

### Script-SkinShortcuts Metadata
The XML files follow a standard structure:
```xml
<shortcuts>
    <shortcut>
        <defaultID />
        <label>Label name</label>
        <label2>Subtitle/Type</label2>
        <icon>DefaultShortcut.png</icon>
        <thumb>Path to media</thumb>
        <action>Kodi Action String</action>
    </shortcut>
</shortcuts>
```

### Property Mapping
Properties are stored as a JSON array in the `.properties` file. The skill should prioritize entries prefixed by the section name (e.g., `["mainmenu", "tucinelatino", "background", "..."]`).

## Troubleshooting

- **Submenu Not Showing**: 
    - Check if the `.DATA.xml` file exists in the correct folder.
    - Ensure the label in `mainmenu.DATA.xml` matches the filename.
    - Add the explicit `<submenu>` tag to the shortcut.
- **Thumbnails Missing**: 
    - Verify the absolute path for `LKOmega21.xTests` vs `Tests2`.
    - Check for URL encoding (e.g., `%5c` for backslash).
- **Menu Revert**: 
    - If changes disappear after a Kodi restart, the `mainmenu.DATA.xml` might be corrupted or out of sync with the properties hash.
- **Widgets Visible but Not Clickable**:
    - **Symptom**: Items are focusable but clicking `Enter`/`Select` does nothing.
    - **Root Cause**: The inclusion template (e.g., `WidgetListCategories`) lacks an `<onclick>` handler.
    - **Fix**: Add a robust handler to the control:
      ```xml
      <onclick condition="!String.IsEmpty($PARAM[onclick_action])">$PARAM[onclick_action]</onclick>
      <onclick condition="String.IsEmpty($PARAM[onclick_action]) + [!String.IsEmpty(ListItem.AddonID) | String.StartsWith(ListItem.FolderPath,plugin://)]">ActivateWindow(Videos,$INFO[ListItem.FolderPath],return)</onclick>
      <onclick condition="String.IsEmpty($PARAM[onclick_action]) + String.IsEmpty(ListItem.AddonID) + !String.StartsWith(ListItem.FolderPath,plugin://)">Action(Select)</onclick>
      ```
    - **Optimization**: For `addons://` content, always pass `widget_target` (e.g., `videos`, `music`, `programs`) in the calling include to ensure correct window routing.

## References

- **Kodi Skin Shortcuts Documentation**: Standard formats for `.DATA.xml`.
- **Xenon Skin Navigation Patterns**: Specific inclusion of `hasSubmenu` in `Includes_Home.xml`.
- **Build Changelog**: Repository for historical modification patterns.
