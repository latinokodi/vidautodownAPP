# Technology Stack

**Analysis Date:** 2026-03-17

## Languages

**Primary:**
- Python 3.10+ - Backend API, download orchestration, desktop wrapper
- TypeScript - Frontend React components and state management

**Secondary:**
- JavaScript - Frontend runtime (transpiled from TypeScript)
- Batch/CMD - Windows launcher script (`run.bat`)

## Runtime

**Environment:**
- Python 3.10+ (managed via venv)
- Node.js (for Next.js frontend development)

**Package Manager:**
- pip (Python) - Backend dependencies
- npm (Node.js) - Frontend dependencies
- Lockfiles: `package-lock.json` present, no pip lockfile

## Frameworks

**Core:**
- FastAPI 0.110+ - Python async web framework for REST API and WebSocket server
- Next.js 16.1.4 - React framework for frontend UI
- React 19.2.3 - UI component library

**Testing:**
- Not detected - No test framework configured

**Build/Dev:**
- Uvicorn 0.27+ - ASGI server for FastAPI
- Tailwind CSS 4 - Utility-first CSS framework
- TypeScript 5 - Static typing for JavaScript

## Key Dependencies

**Critical (Backend):**
- `yt-dlp` 2024.04.09+ - Video download engine (core functionality)
- `pywebview` 5.0+ - Desktop window wrapper (creates native OS window)
- `websockets` 12.0+ - WebSocket protocol support
- `pydantic` 2.0+ - Data validation and serialization

**Critical (Frontend):**
- `zustand` 5.0.10 - Lightweight state management
- `framer-motion` 12.29.0 - Animation library
- `lucide-react` 0.563.0 - Icon library
- `react-hot-toast` 2.6.0 - Toast notifications

**Infrastructure:**
- SQLite3 - Local database (via Python stdlib)
- aria2c (optional) - External downloader for retry strategy

## Configuration

**Environment:**
- No `.env` file required - configuration stored in SQLite database
- Settings persisted in `vidautodown.db` (WAL mode enabled)

**Build:**
- Backend: No build step (interpreted Python)
- Frontend: Next.js dev server (`npm run dev`) or build (`npm run build`)

**Key Config Files:**
- `F:/PyApps/vidautodownAPP/backend/requirements.txt` - Python dependencies
- `F:/PyApps/vidautodownAPP/frontend/package.json` - Node dependencies
- `F:/PyApps/vidautodownAPP/frontend/tsconfig.json` - TypeScript configuration
- `F:/PyApps/vidautodownAPP/pyproject.toml` - Project metadata

## Platform Requirements

**Development:**
- Python 3.10+ with pip
- Node.js 18+ with npm
- Windows (primary target) - uses `subprocess.CREATE_NO_WINDOW` for hidden processes

**Production:**
- Windows desktop application
- Can run as standalone web app (frontend + backend separately)
- Requires yt-dlp binary in PATH or venv
- Optional: aria2c for enhanced download performance

## Application Modes

**Three execution modes available:**

1. **Full Desktop App** (`run_all.py`)
   - Launches FastAPI backend on port 8000
   - Starts Next.js dev server on port 3000
   - Opens pywebview window pointing to localhost:3000
   - Location: `F:/PyApps/vidautodownAPP/run_all.py`

2. **WebView Desktop** (`vidautodown_webview.py`)
   - Single-file monolithic version
   - Uses pywebview with embedded HTML/JS
   - All logic in one file
   - Location: `F:/PyApps/vidautodownAPP/vidautodown_webview.py`

3. **Split Architecture** (backend/ + frontend/)
   - FastAPI backend: `F:/PyApps/vidautodownAPP/backend/main.py`
   - Next.js frontend: `F:/PyApps/vidautodownAPP/frontend/`
   - Communicates via REST API + WebSocket

---

*Stack analysis: 2026-03-17*