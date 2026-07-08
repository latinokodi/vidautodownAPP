---
description: Create new application command. Triggers App Builder skill and starts interactive dialogue with user.
---

# /create - Create Application

$ARGUMENTS

---

## Task

This command starts a new application creation process powered by the `app-builder` skill.

### Steps:

1. **Request Analysis & Socratic Discovery**
   - Use `brainstorming` skill to ask Socratic questions.
   - Understand domains (Web, Mobile, Kodi, Desktop, etc.).
   - If info is missing, use `Socratic Gate` protocol.

2. **Project Planning**
   - Use `project-planner` agent for task breakdown.
   - Use `architecture` skill for tech stack selection.
   - Determine specialist agents needed (e.g., `kodi-expert`, `site-to-kodi`).
   - Create `implementation_plan.md`.

3. **Application Building (After Approval)**
   - Orchestrate with `app-builder` skill.
   - Coordinate specialist agents:
     - `database-architect` → Schema/DB
     - `backend-specialist` → API/Logic
     - `frontend-specialist` → UI/UX (Web)
     - `mobile-developer` → UI/UX (React Native/Flutter)
     - `android-engineer` → Native Android/Kotlin/Compose
     - `android-tester` → Android testing setup
     - **Specialized Experts**:
       - `kodi-expert` → Kodi Addon logic
       - `site-to-kodi` → Streaming site conversion
       - `media-engineer` → FFmpeg/Media processing
       - `api-reverse-engineer` → Undocumented API analyst
       - `python-cli-architect` → Premium Python CLI design
       - `playwright-actor-engineer` → Browser automation bots
       - `chrome-extension-developer` → Manifest V3 Chrome Extension design & scripts
   - Use `svg-icon-generator` for branding/icons.

4. **Validation & Preview**
   - Run `python .agent/scripts/checklist.py .` to verify build quality.
   - Start with `auto_preview.py` if applicable.
   - Present final architecture to user.

---

## Usage Examples

```
/create blog site
/create Kodi video addon for Pelisgo
/create resilient media scraper for movies
/create todo app with NestJS and Prisma
```

---

## Before Starting

Ask these Socratic questions:
- What is the primary platform (Web, Kodi, Mobile)?
- What are the core media/data sources?
- What are the specific performance or security requirements?

Use `app-builder` defaults for non-specified parts.
