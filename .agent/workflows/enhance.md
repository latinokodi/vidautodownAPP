---
description: Add or update features in existing application. Used for iterative development.
---

# /enhance - Update Application

$ARGUMENTS

---

## Task

This command adds features or makes updates to existing application using `intelligent-routing` and `app-optimizer`.

### Steps:

1. **Understand Current State & Audit**
   - Load project state with `python .agent/scripts/session_manager.py info`.
   - Run `app-optimizer` Phase 1 (Audit) to identify optimization opportunities.
   - Analyze dependencies and architecture.

2. **Intelligent Planning**
   - Use `intelligent-routing` to suggest the best specialist agent.
   - Determine affected files and breaking changes.
   - Use `architecture` skill for trade-off analysis.

3. **Present Plan to User**
   - Provide a concise summary of changes.
   - Highlight any risk factors or conflicting technologies.

4. **Apply Enhancement**
   - Coordinate specialist agents:
     - `kodi-expert` → Addon logic
     - `site-to-kodi` → Streaming site conversion
     - `media-engineer` → Media processing
     - `frontend-specialist` → UI/UX
     - `ui-ux-pro-max` → Design system adherence
     - `icon-specialist` → Advanced iconography implementation
     - `chrome-extension-developer` → Chrome Extension Manifest V3 & script context enhancement
   - Use `svg-icon-generator` or `/iconography` for UI assets and icon library management.

5. **Validation**
   - Run `python .agent/scripts/checklist.py .` to verify quality.
   - Confirm enhancement matches requirements.

---

## Usage Examples

```
/enhance add HLS support to Kodi resolvers
/enhance optimize scraper concurrency
/enhance add dark mode via ui-ux-pro-max
/enhance integrate Elementum for torrent playback
```

---

## Caution

- **Agent Integrity**: Always use the specialist agent's persona.
- **Audit First**: Never skip the `session_manager.py` check.
- **Verify**: Enhancements are not complete without a successful `checklist.py` run.
