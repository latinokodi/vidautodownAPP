# Architecture

**Analysis Date:** 2026-03-17

## Pattern Overview

**Overall:** Layered Client-Server Architecture with Desktop Wrapper

**Key Characteristics:**
- FastAPI backend serves REST API + WebSocket for real-time updates
- Next.js frontend with React components and Zustand state management
- PyWebView desktop wrapper for native application experience
- Thread-based download workers with async-queue bridge to WebSockets
- SQLite persistence for task state and settings

## Layers

**Presentation Layer (Frontend):**
- Purpose: User interface with drag-and-drop, paste-to-download, real-time progress
- Location: `frontend/`
- Contains: Next.js pages, React components, Zustand store, Tailwind CSS styles
- Depends on: Backend REST API and WebSocket
- Used by: Desktop WebView wrapper

**API Layer (Backend):**
- Purpose: HTTP endpoints and WebSocket connections
- Location: `backend/api/`
- Contains: FastAPI routes, WebSocket connection manager
- Depends on: Core controller, Pydantic models
- Used by: Frontend HTTP/WebSocket clients

**Business Logic Layer (Core):**
- Purpose: Download orchestration, task management, concurrency control
- Location: `backend/core/`
- Contains: DownloadController (singleton), Task models, Database operations
- Depends on: yt-dlp CLI, aria2c CLI, SQLite
- Used by: API layer

**External Tools Layer:**
- Purpose: Video download and acceleration
- Location: System PATH (yt-dlp, aria2c)
- Contains: External CLI executables
- Depends on: Operating system
- Used by: Controller workers via subprocess

## Data Flow

**Add URL Flow:**

1. User pastes/drops URL in frontend
2. Frontend POSTs to `/api/tasks` with URL text
3. Controller extracts URLs, creates Task objects with `INFO` status
4. Controller posts "refresh" message to queue
5. WebSocket bridge broadcasts update to all connected clients
6. Frontend receives and updates Zustand store

**Download Flow:**

1. Manager loop detects `QUEUED` tasks
2. Acquires semaphore slot (concurrency limit)
3. Spawns worker thread for download
4. Worker executes yt-dlp via subprocess, parses stdout
5. Progress updates posted to queue, broadcast via WebSocket
6. On completion/failure, status updated and broadcast

**Real-time Update Flow:**

1. Backend thread posts to `msg_queue` (sync Queue)
2. `bridge_queue_to_ws()` async task drains queue
3. Messages broadcast via `ConnectionManager.broadcast()`
4. Frontend WebSocket `onmessage` handler updates Zustand store
5. React re-renders affected components

**State Management:**
- Backend: In-memory `Dict[str, Task]` with `threading.Lock` + SQLite persistence
- Frontend: Zustand store with `tasks[]`, `isConnected`, `settings`, `stats`
- Sync: WebSocket messages (refresh, task_update, toast, stats_update)

## Key Abstractions

**Task:**
- Purpose: Represents a download job with status, progress, metadata
- Examples: `backend/core/models.py`, `frontend/lib/store.ts`
- Pattern: Pydantic model (backend) / TypeScript interface (frontend)

**DownloadController:**
- Purpose: Singleton managing all download operations
- Examples: `backend/core/controller.py`
- Pattern: Thread-safe manager with semaphore for concurrency, queue for async bridge

**ConnectionManager:**
- Purpose: Manages WebSocket connections and broadcasts
- Examples: `backend/api/websockets.py`
- Pattern: Simple connection list with broadcast method

**useStore:**
- Purpose: Frontend global state management
- Examples: `frontend/lib/store.ts`
- Pattern: Zustand store with actions and WebSocket integration

## Entry Points

**Desktop Application Entry:**
- Location: `run_all.py`
- Triggers: User runs `run.bat` or `python run_all.py`
- Responsibilities: Starts backend (uvicorn), frontend (npm dev), creates WebView window, handles cleanup on close

**Backend Server Entry:**
- Location: `backend/main.py`
- Triggers: uvicorn ASGI server
- Responsibilities: FastAPI app creation, CORS middleware, lifespan (DB init, task restore, background tasks), route registration

**Frontend Page Entry:**
- Location: `frontend/app/page.tsx`
- Triggers: Next.js router
- Responsibilities: Renders TaskManager component, sets up main layout

**WebSocket Connection:**
- Location: `frontend/lib/store.ts` (`connectWs` action)
- Triggers: TaskManager component mount (`useEffect`)
- Responsibilities: Establishes WebSocket connection, handles reconnection, dispatches messages to store

## Error Handling

**Strategy:** Graceful degradation with retry logic

**Patterns:**
- Download failures: Up to 2 retries with different strategies (Strategy A, B, C with aria2c)
- WebSocket disconnect: Automatic reconnection with 2s delay
- Process errors: Caught in worker threads, task marked FAILED with error message
- API errors: HTTPException with detail message, frontend shows toast notification

## Cross-Cutting Concerns

**Logging:** Python `logging` module with colored console output and file logging to `vidautodown.log`

**Validation:** Pydantic models for request/response schemas, URL regex extraction

**Authentication:** None (local desktop application)

**Concurrency:** `threading.Semaphore` limits concurrent downloads (default 2, max 6)

**Persistence:** SQLite with WAL mode, auto-save every 10 seconds, restore on startup

---

*Architecture analysis: 2026-03-17*