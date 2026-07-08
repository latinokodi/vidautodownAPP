# XML Patterns for Kodi Navigation

Technical reference for modifying and validating `script.skinshortcuts` data files.

## Submenu Data Structure (.DATA.xml)

Standard template for any custom submenu file.

```xml
<shortcuts>
	<shortcut>
		<defaultID />
		<label>Visible Title</label>
		<label2>Type Label</label2>
		<icon>DefaultShortcut.png</icon>
		<thumb>image://D%3a%5cPath%5cto%5cimage.jpg/</thumb>
		<action>ActivateWindow(Videos,"plugin://id/?action=name",return)</action>
	</shortcut>
</shortcuts>
```

## Main Menu Linking Pattern

To force a shortcut to use a specific submenu file, add the `<submenu>` tag.

```xml
<shortcut>
    <defaultID>custom_id</defaultID>
    <label>Section Name</label>
    ...
    <submenu>my_submenu_filename</submenu>
</shortcut>
```

## Regex for Build Synchronization

### Absolute Path Normalization
Use this pattern to sync absolute paths between portable builds.

**Pattern (Perl-style)**:
`s/LKOmega21\.3Tests2/LKOmega21.3Tests/g`

### Submenu Link Injection
Inject a submenu tag if missing from a specific shortcut.

**Find**:
`(<label>Tucinelatino<\/label>[\s\S]*?<action>[\s\S]*?<\/action>)`

**Replace**:
`$1\n\t\t<submenu>tucinelatino<\/submenu>`

## Common Properties

| Property | Value Example | Description |
| :--- | :--- | :--- |
| `hasSubmenu` | `True`/`False` | Determines if the skin renders a secondary menu. |
| `submenuVisibility` | `tucinelatino` | Name of the visibility ID (usually matches filename). |
| `widgetPath` | `plugin://...` | The source URL for the widget data. |
| `widgetArt` | `Square Poster` | Aspect ratio for widget thumbnails. |
| `translatedPath` | `ActivateWindow(...)` | The final resolved action string. |

## Path Encoding Table

| Character | URL Encoded |
| --- | --- |
| `:` | `%3a` |
| `\` | `%5c` |
| `/` | `%2f` |
| ` ` | `%20` |
