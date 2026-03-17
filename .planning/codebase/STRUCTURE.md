# Codebase Structure

**Analysis Date:** 2026-03-17

## Directory Layout

```
vidautodownAPP/
├── backend/              # FastAPI backend server
│   ├── api/              # HTTP routes and WebSocket handlers
│   ├── core/             # Business logic, models, database
│   ├── main.py           # FastAPI app entry point
│   ├── test_controller.py # Unit tests
│   └── venv/             # Python virtual environment
├── frontend/             # Next.js frontend application
│   ├── app/              # Next.js App Router pages
│   ├── components/       # React components
│   ├── lib/              # Utilities and state management
│   ├── public/           # Static assets
│   ├── node_modules/     # JavaScript dependencies
│   └── package.json      # NPM configuration
├── .planning/            # Planning documents (generated)
│   └── codebase/         # Codebase analysis documents
├── vidautodown_webview.py # Legacy webview entry (single-file app)
├── vidautodown_single.py  # Legacy single-file implementation
├── run_all.py            # Desktop launcher (backend + frontend + webview)
├── run.bat               # Windows batch launcher
├── requirements.txt      # Python dependencies
└── vidautodown.db        # SQLite database (runtime)
```

## Directory Purposes

**backend/api:**
- Purpose: HTTP endpoints and WebSocket handling
- Contains: Route definitions, request/response schemas, connection manager
- Key files: `routes.py`, `websockets.py`

**backend/core:**
- Purpose: Core business logic and data models
- Contains: Download controller, task models, database operations
- Key files: `controller.py`, `models.py`, `database.py`

**frontend/app:**
- Purpose: Next.js App Router pages
- Contains: Page components, layouts, global styles
- Key files: `page.tsx`, `layout.tsx`, `globals.css`

**frontend/components:**
- Purpose: Reusable React components
- Contains: UI components for task management
- Key files: `TaskManager.tsx`, `TaskList.tsx`, `TaskItem.tsx`, `SettingsPanel.tsx`

**frontend/lib:**
- Purpose: Utilities and client-side state
- Contains: Zustand store, helper functions
- Key files: `store.ts`, `utils.ts`

## Key File Locations

**Entry Points:**
- `run_all.py`: Desktop application launcher
- `backend/main.py`: FastAPI server entry point
- `frontend/app/page.tsx`: Main page component
- `run.bat`: Windows convenience launcher

**Configuration:**
- `requirements.txt`: Python dependencies
- `frontend/package.json`: Node.js dependencies and scripts
- `frontend/next.config.ts`: Next.js configuration
- `frontend/app/globals.css`: Global Tailwind CSS

**Core Logic:**
- `backend/core/controller.py`: Download management singleton (507 lines)
- `backend/core/models.py`: Task and status definitions
- `backend/core/database.py`: SQLite operations
- `frontend/lib/store.ts`: Zustand state management

**Testing:**
- `backend/test_controller.py`: Unit tests for download controller

## Naming Conventions

**Files:**
- Python: `snake_case.py` (e.g., `download_controller.py`, `websockets.py`)
- TypeScript/TSX: `PascalCase.tsx` for components (e.g., `TaskManager.tsx`)
- TypeScript utilities: `camelCase.ts` (e.g., `store.ts`, `utils.ts`)

**Directories:**
- Python packages: `snake_case/` (e.g., `api/`, `core/`)
- Next.js: App Router convention `app/`, `components/`, `lib/`

**Identifiers:**
- Python classes: `PascalCase` (e.g., `Task`, `DownloadController`, `ConnectionManager`)
- Python functions/methods: `snake_case` (e.g., `add_urls`, `_download_worker`)
- TypeScript: `camelCase` for functions/variables, `PascalCase` for interfaces/types

## Where to Add New Code

**New Feature (Backend):**
- Route: Add to `backend/api/routes.py` or create new router file
- Logic: Add methods to `backend/core/controller.py` or create new module in `core/`
- Model: Add to `backend/core/models.py` or create new model file
- Database: Add schema to `_SCHEMA` in `backend/core/database.py`

**New Feature (Frontend):**
- Component: Create in `frontend/components/` as `PascalCase.tsx`
- State: Add to `frontend/lib/store.ts` Zustand store
- Page: Create in `frontend/app/` as Next.js App Router page

**New Utility:**
- Backend: Create `backend/utils.py` or add to existing controller
- Frontend: Add to `frontend/lib/utils.ts` or create new utility file

**Tests:**
- Backend: Add test methods to `backend/test_controller.py` or create new test file

## Special Directories

**backend/venv:**
- Purpose: Python virtual environment with isolated dependencies
- Generated: Yes (created by `python -m venv`)
- Committed: No (should be in .gitignore)

**frontend/node_modules:**
- Purpose: Node.js dependencies
- Generated: Yes (created by `npm install`)
- Committed: No

**frontend/.next:**
- Purpose: Next.js build output and cache
- Generated: Yes (created by `npm run dev` or `npm run build`)
- Committed: No

**.planning/codebase:**
- Purpose: GSD planning documents
- Generated: Yes (created by `/gsd:map-codebase`)
- Committed: Yes (part of project documentation)

---

*Structure analysis: 2026-03-17*