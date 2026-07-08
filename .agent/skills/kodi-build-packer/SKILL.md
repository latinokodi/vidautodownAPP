---
name: kodi-build-packer
description: "Create distribution zip packages for Kodi portable builds with standardized naming, exclusions, and folder organization."
category: kodi
risk: safe
source: community
tags: "[kodi, build-packaging, distribution, zip, 7-zip, versioning]"
date_added: "2026-04-17"
triggers: "[pack kodi, package build, create zip, LKU, portable_data, oldversions]"
---

# kodi-build-packer

## Purpose

Create distribution-ready zip packages for Kodi portable builds with standardized naming conventions, optimized exclusions, and proper folder organization. This skill ensures builds are packaged efficiently for distribution across platforms.

## When to Use This Skill

This skill should be used when:
- **Creating Distribution Packages**: Packaging portable_data folders for user downloads.
- **Version Updates**: Creating new versioned zips when builds are updated.
- **Build Organization**: Managing current vs. old versions in the repository.
- **Naming Standardization**: Renaming builds to follow consistent naming patterns.

## Build Tiers & Platforms

### Tier Definitions

| Tier | Platforms | Suffix Rule |
|------|-----------|-------------|
| micro | Android only | No suffix |
| lite | Android only | No suffix |
| mega | Windows & Android | `-win` / `-and` suffix |
| pro | Universal (both) | No suffix |

### Naming Convention

**Format**: `LKU-{tier}-v{version}{suffix}.zip`

**Examples**:
- `LKU-micro-v1.3.zip` (Android only)
- `LKU-lite-v4.3.zip` (Android only)
- `LKU-mega-v1.6-win.zip` (Windows variant)
- `LKU-mega-v1.6-and.zip` (Android variant)
- `LKU-pro-v2.3.zip` (Universal - both platforms)

## Packaging Exclusions

When creating zips, exclude the following from `portable_data`:

### Addons Folder Exclusions
- `addons/packages/` - Downloaded package cache
- `addons/temp/` - Temporary extraction folder
- `addons/metadata.*` - Metadata scrapers (all folders starting with `metadata.`)

### Userdata Folder Exclusions
- `userdata/Thumbnails/*` - Thumbnail cache (keep empty folder)

## Zip Creation Process

### 7-Zip Setup

Check for 7-Zip availability before packaging:
```bash
# Try PATH first, then default install location
if command -v 7z &>/dev/null; then
  SEVENZIP="7z"
elif [ -f "C:/Program Files/7-Zip/7z.exe" ]; then
  SEVENZIP="C:/Program Files/7-Zip/7z.exe"
else
  echo "7-Zip not found - install from https://7-zip.org/download.html"
  exit 1
fi
```

### Using 7-Zip (Recommended)

7-Zip provides fast, efficient compression with exclusion filters without needing temp folders.

**Command Template**:
```bash
"${SEVENZIP}" a -tzip "{output_path}" \
    "{build_path}/portable_data/addons" \
    "{build_path}/portable_data/userdata" \
    -x!"addons/packages" \
    -x!"addons/temp" \
    -x!"addons/metadata.*" \
    -x!"userdata/Thumbnails/*" \
    -mx5 -r
```

**Parameters**:
- `-tzip`: Create standard zip format
- `-mx5`: Compression level 5 (balanced speed/size)
- `-r`: Recursive
- `-x!`: Exclusion filter

### PowerShell Alternative (Slower)

If 7-Zip is unavailable, PowerShell can be used but requires copying to a temp folder first:
```powershell
Compress-Archive -Path $tempAddons, $tempUserdata -DestinationPath $zipPath -CompressionLevel Optimal
```

## Folder Organization

### Directory Structure

```
D:\Latino Kodi 100\Latino Kodi 100 Wizard\
├── LKUmicro\              (Android build folder)
├── LKUlite\               (Android build folder)
├── LKUmega-win\           (Windows build folder)
├── LKUmega-and\           (Android build folder)
├── LKUpro\                (Universal build folder)
├── LKU-micro-v1.3.zip     (Current version)
├── LKU-lite-v4.3.zip      (Current version)
├── LKU-mega-v1.6-win.zip  (Current version)
├── LKU-mega-v1.6-and.zip  (Current version)
├── LKU-pro-v2.3.zip       (Current version)
└── oldversions\           (Archived versions)
    ├── lkumicro.v1.1.zip
    ├── lkumicro.v1.2.zip
    ├── lkulite.v4.1e.zip
    ├── lkulite.v4.2.zip
    └── ...
```

### Version Management

- **Current versions**: Place in main Wizard folder
- **Old versions**: Move to `oldversions/` subfolder
- Clean naming for current versions, preserve original names in archive

## Build Folder Mapping

| Build Folder | Zip Output |
|--------------|------------|
| LKUmicro | LKU-micro-v{version}.zip |
| LKUlite | LKU-lite-v{version}.zip |
| LKUmega-win | LKU-mega-v{version}-win.zip |
| LKUmega-and | LKU-mega-v{version}-and.zip |
| LKUpro | LKU-pro-v{version}.zip |

## Workflow

### Step 1: Prepare Build

Ensure the build folder has correct structure:
```
{build_folder}/
├── portable_data/
│   ├── addons/
│   └── userdata/
```

### Step 2: Determine Version

Check existing zips to determine next version number, or use specified version.

**Version Detection Commands**:
```bash
# Get current version for a specific tier
ls LKU-{tier}-v*.zip 2>/dev/null | grep -oP 'v\d+\.\d+' | tail -1

# Get all current versions
for tier in micro lite mega pro; do
  echo "$tier: $(ls LKU-${tier}-v*.zip 2>/dev/null | grep -oP 'v\d+\.\d+' | tail -1)"
done
```

**Increment Version Example**:
- Current: `v1.3` → Next: `v1.4`
- Current: `v4.3` → Next: `v4.4`

### Step 3: Create Zip

Execute 7-Zip with exclusion filters targeting the build's portable_data.

### Step 4: Verify Zip

Check zip contents to confirm exclusions applied correctly:
```bash
# Use path-specific patterns to avoid false positives
"${SEVENZIP}" l {zip_path} | grep -E "addons/packages/|addons/temp/|addons/metadata\.|userdata/Thumbnails/"
```

Should show no matches. Note: Simple patterns like `packages` match legitimate files like `packages.py` - use path prefixes for accurate verification.

### Step 5: Organize Versions

Move previous version zips to `oldversions/` folder if new version replaces them.

### Step 6: Rename to Standard

Apply naming convention if zip doesn't match standard format.

## Batch Packaging Workflow

When packaging all tiers simultaneously with incremented versions:

### Step 1: Archive Current Versions

Move existing zips to oldversions folder:
```bash
mv LKU-micro-v*.zip oldversions/
mv LKU-lite-v*.zip oldversions/
mv LKU-mega-v*-win.zip oldversions/
mv LKU-mega-v*-and.zip oldversions/
mv LKU-pro-v*.zip oldversions/
```

### Step 2: Create All Packages in Parallel

Run 7-Zip commands for all 5 builds concurrently:
```bash
# Example with incremented versions (v1.4, v4.4, v1.7, v2.4)
"${SEVENZIP}" a -tzip "LKU-micro-v1.4.zip" "LKUmicro/portable_data/addons" "LKUmicro/portable_data/userdata" -x!"addons/packages" -x!"addons/temp" -x!"addons/metadata.*" -x!"userdata/Thumbnails/*" -mx5 -r &

"${SEVENZIP}" a -tzip "LKU-lite-v4.4.zip" "LKUlite/portable_data/addons" "LKUlite/portable_data/userdata" -x!"addons/packages" -x!"addons/temp" -x!"addons/metadata.*" -x!"userdata/Thumbnails/*" -mx5 -r &

"${SEVENZIP}" a -tzip "LKU-mega-v1.7-win.zip" "LKUmega-win/portable_data/addons" "LKUmega-win/portable_data/userdata" -x!"addons/packages" -x!"addons/temp" -x!"addons/metadata.*" -x!"userdata/Thumbnails/*" -mx5 -r &

"${SEVENZIP}" a -tzip "LKU-mega-v1.7-and.zip" "LKUmega-and/portable_data/addons" "LKUmega-and/portable_data/userdata" -x!"addons/packages" -x!"addons/temp" -x!"addons/metadata.*" -x!"userdata/Thumbnails/*" -mx5 -r &

"${SEVENZIP}" a -tzip "LKU-pro-v2.4.zip" "LKUpro/portable_data/addons" "LKUpro/portable_data/userdata" -x!"addons/packages" -x!"addons/temp" -x!"addons/metadata.*" -x!"userdata/Thumbnails/*" -mx5 -r &

wait  # Wait for all background jobs to complete
```

### Step 3: Verify Largest Package Only

For efficiency, verify exclusions on the largest zip (pro tier) only:
```bash
"${SEVENZIP}" l LKU-pro-v*.zip | grep -E "addons/packages/|addons/temp/|addons/metadata\.|userdata/Thumbnails/"
```

Should return empty (no matches).

### Batch Packaging Summary Table

| Build Folder | Zip Output | Typical Size |
|--------------|------------|--------------|
| LKUmicro | LKU-micro-v{version}.zip | ~60 MB |
| LKUlite | LKU-lite-v{version}.zip | ~165 MB |
| LKUmega-win | LKU-mega-v{version}-win.zip | ~180 MB |
| LKUmega-and | LKU-mega-v{version}-and.zip | ~185 MB |
| LKUpro | LKU-pro-v{version}.zip | ~350 MB |

## Best Practices

- **Always use 7-Zip**: Faster and no temp folder required
- **Verify exclusions**: Check that packages, temp, metadata.*, and Thumbnails content are excluded
- **Keep Thumbnails folder**: Empty folder should exist in zip
- **Clean old versions**: Move outdated zips to archive folder
- **Consistent naming**: Follow LKU-{tier}-v{version}{suffix} format

## Troubleshooting

- **Zip too large**: Check if packages or Thumbnails were accidentally included
- **7-Zip not found**: Install from https://7-zip.org/download.html or use PowerShell fallback
- **Exclusions not working**: Use `-x!` syntax with folder names relative to included paths
- **Wrong platform suffix**: Refer to tier definitions table above
- **False positives in verification**: Avoid grep patterns like `packages` alone - use `addons/packages/` to exclude legitimate files like `packages.py`
- **Parallel packaging fails**: Ensure sufficient memory; reduce concurrent jobs if needed