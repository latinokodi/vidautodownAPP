# Codebase Concerns

**Analysis Date:** 2026-03-17

## Tech Debt

**Legacy Monolithic Files:**
- Issue: Two large monolithic Python files (`vidautodown_single.py` - 1397 lines, `vidautodown_webview.py` - 873 lines) contain duplicated code and predate the modular backend/frontend architecture.
- Files: `F:/PyApps/vidautodownAPP/vidautodown_single.py`, `F:/PyApps/vidautodownAPP/vidautodown_webview.py`
- Impact: Maintenance burden, duplicated logic (ColoredFormatter, progress parsing, database code exists in both legacy files and new backend). Confusion about which code is canonical.
- Fix approach: Remove legacy files after confirming all functionality exists in new backend/frontend architecture. Extract any unique utilities to shared modules first.

**Incomplete Controller Implementation:**
- Issue: `DownloadController._broadcast_sync()` method contains dead code with `pass` statements and comments about implementation details rather than actual implementation.
- Files: `F:/PyApps/vidautodownAPP/backend/core/controller.py` (lines 95-123)
- Impact: Dead code that could confuse developers. The actual implementation uses a queue pattern but the comment suggests this was abandoned mid-implementation.
- Fix approach: Remove dead code or complete the implementation. Current queue-based approach in `msg_queue` works correctly.

**Inconsistent Requirements:**
- Issue: `requirements.txt` at project root only lists 4 packages but `backend/` has its own venv with many more dependencies (FastAPI, uvicorn, pydantic, etc.). Root requirements don't match actual backend dependencies.
- Files: `F:/PyApps/vidautodownAPP/requirements.txt`, `F:/PyApps/vidautodownAPP/backend/`
- Impact: Running `pip install -r requirements.txt` from root won't install all needed packages. New developers may have broken setups.
- Fix approach: Consolidate requirements to `backend/requirements.txt` or create a proper root requirements with all dependencies.

## Known Bugs

**Duplicate Property Definition:**
- Issue: Zustand store has `isConnected: false` defined twice on lines 36-37.
- Files: `F:/PyApps/vidautodownAPP/frontend/lib/store.ts` (lines 36-37)
- Symptoms: JavaScript allows duplicate object keys (last wins), so no runtime error but indicates copy-paste error.
- Trigger: Always present, but functionally harmless due to JS behavior.
- Workaround: None needed, but should be cleaned up.

**Settings Persistence Race Condition:**
- Issue: `set_max_concurrent()` creates a new `Semaphore` each time, which could allow more concurrent downloads than expected if called while downloads are in progress.
- Files: `F:/PyApps/vidautodownAPP/backend/core/controller.py` (lines 211-213)
- Symptoms: Changing concurrent limit during active downloads may not immediately take effect or could allow burst downloads.
- Trigger: Changing `max_concurrent` setting while downloads are running.
- Workaround: Pause all downloads before changing concurrency limit.

## Security Considerations

**Overly Permissive CORS:**
- Risk: CORS middleware allows all origins (`allow_origins=["*"]`), which could expose the API to cross-site attacks if the app is ever exposed to a network.
- Files: `F:/PyApps/vidautodownAPP/backend/main.py` (line 77)
- Current mitigation: App binds to localhost only (127.0.0.1), limiting exposure to local machine.
- Recommendations: Restrict CORS to specific origins or remove wildcard when moving to production/network deployment.

**No Input Validation on URL Endpoint:**
- Risk: The `/api/tasks` endpoint accepts arbitrary text and attempts to extract URLs. Malicious input could cause unexpected behavior.
- Files: `F:/PyApps/vidautodownAPP/backend/api/routes.py` (lines 17-20)
- Current mitigation: URL extraction regex filters for http/https URLs only.
- Recommendations: Add explicit URL validation, limit text length, and sanitize URLs before passing to yt-dlp.

**Arbitrary File Path Acceptance:**
- Risk: Settings endpoint accepts arbitrary file paths for `destination` without validation, potentially allowing writes to sensitive directories.
- Files: `F:/PyApps/vidautodownAPP/backend/api/routes.py` (lines 69-84)
- Current mitigation: App runs with user privileges, limiting damage.
- Recommendations: Validate paths are within expected directories (e.g., user's home or Downloads folder).

## Performance Bottlenecks

**Full Task List Serialization on Every Update:**
- Problem: Every state change broadcasts the complete task list via WebSocket, even for single task updates.
- Files: `F:/PyApps/vidautodownAPP/backend/core/controller.py` (method `_get_all_tasks_dict`, line 215)
- Cause: Simplicity over efficiency - "for <100 tasks full refresh is fine locally" per comment.
- Improvement path: Implement differential updates for single task changes. Already partially done via `task_update` message type but `refresh` is still used frequently.

**Blocking Tkinter Dialog in API Handler:**
- Problem: `browse_folder()` creates a Tkinter dialog that blocks the entire FastAPI event loop while waiting for user input.
- Files: `F:/PyApps/vidautodownAPP/backend/core/controller.py` (lines 475-490)
- Cause: Tkinter must run on main thread, but API handlers run in thread pool.
- Improvement path: Move file browser to frontend native file dialog or run in separate process. For local desktop app, acceptable but will block all other requests during dialog.

**Polling-Based Manager Loop:**
- Problem: Manager loop polls every 300ms for new tasks, creating constant CPU wakeups.
- Files: `F:/PyApps/vidautodownAPP/backend/core/controller.py` (line 289)
- Cause: Simple implementation using `time.sleep(0.3)`.
- Improvement path: Use `threading.Condition` or `queue.Queue` for event-driven task dispatch.

## Fragile Areas

**Transient Process Management:**
- Files: `F:/PyApps/vidautodownAPP/backend/core/controller.py` (lines 158-167)
- Why fragile: Process handles stored in `_transient_processes` dict are not thread-safe. Race conditions possible between manager loop, download workers, and action handlers when accessing/terminating processes.
- Safe modification: Always acquire `tasks_lock` before accessing `_transient_processes`. Consider consolidating into a single data structure with proper locking.
- Test coverage: No tests for process termination edge cases (e.g., terminating while process is exiting).

**WebSocket Reconnection:**
- Files: `F:/PyApps/vidautodownAPP/frontend/lib/store.ts` (lines 69-71)
- Why fragile: Reconnection uses `setTimeout(..., 2000)` without cleanup. If component unmounts during reconnection wait, callback will still fire and potentially cause memory leaks or state updates on unmounted component.
- Safe modification: Use `useRef` to track mounted state and cancel pending timeouts in `useEffect` cleanup.
- Test coverage: No tests for reconnection behavior.

**Database Save Operations:**
- Files: `F:/PyApps/vidautodownAPP/backend/core/database.py` (lines 69-96)
- Why fragile: `save_tasks()` deletes all tasks then re-inserts. If crash occurs between delete and insert, all task state is lost.
- Safe modification: Use transaction properly (already in `with self.conn:` block) but consider backup before delete or upsert pattern.
- Test coverage: No tests for crash recovery scenarios.

## Scaling Limits

**In-Memory Task Storage:**
- Current capacity: Designed for "less than 100 tasks" per comment in controller.
- Limit: Memory-bound. No pagination on task list. Large task counts will slow down UI rendering and WebSocket broadcasts.
- Scaling path: Implement database-backed task history with pagination. Current SQLite DB stores tasks but only for persistence, not as primary source during runtime.

**Concurrent Download Semaphore:**
- Current capacity: Hardcoded max of 6 concurrent downloads.
- Limit: Arbitrary limit set in `set_max_concurrent()` with `max(1, min(6, n))`.
- Scaling path: Allow higher limits for power users, or remove artificial cap and let system resources determine limits.

## Dependencies at Risk

**yt-dlp:**
- Risk: Frequent updates required to keep up with video platform changes. Outdated version may fail on newer videos.
- Impact: Core functionality broken - downloads will fail.
- Migration plan: Not applicable - yt-dlp is the only viable option. Keep auto-update in `run.bat` (line 49).

**aria2c External Binary:**
- Risk: Downloaded as external binary, not managed by pip. May become outdated or incompatible with new yt-dlp versions.
- Impact: Strategy B downloads (aria2c accelerated) may fail, falling back to Strategy C.
- Migration plan: Already has fallback in controller (line 336-340). Consider managing aria2c via pip package `aria2p` or similar.

**PyWebView:**
- Risk: Desktop window wrapper that may have compatibility issues with OS updates.
- Impact: Desktop window may fail to open or render incorrectly.
- Migration plan: Alternative could be Electron or Tauri, but PyWebView is lightweight and appropriate for this use case.

## Missing Critical Features

**Error Reporting to User:**
- Problem: Errors during download are stored in `task.title` as "Error: {error}" but detailed error information is not preserved or displayed properly.
- Blocks: Users cannot understand why downloads fail or take corrective action beyond retry.

**Download History:**
- Problem: No separate history view. Completed tasks remain in main list until manually removed. No way to see past downloads after removal.
- Blocks: Users lose visibility into download history after cleanup.

**Cancel During Info Fetch:**
- Problem: Cannot cancel tasks while in `INFO` or `FETCHING_INFO` status. The cancel action only works for certain statuses.
- Blocks: Users stuck waiting for slow/unreachable URL info fetches.

## Test Coverage Gaps

**Controller Thread Safety:**
- What's not tested: Concurrent access to `tasks` dict, `_transient_processes` dict, and semaphore from multiple threads.
- Files: `F:/PyApps/vidautodownAPP/backend/core/controller.py`
- Risk: Race conditions could cause task state corruption, lost updates, or deadlocks.
- Priority: High

**WebSocket Message Handling:**
- What's not tested: Message parsing, reconnection, multiple client handling.
- Files: `F:/PyApps/vidautodownAPP/backend/api/websockets.py`, `F:/PyApps/vidautodownAPP/frontend/lib/store.ts`
- Risk: Frontend may display incorrect state or fail silently.
- Priority: Medium

**Download Worker Error Paths:**
- What's not tested: yt-dlp not found, network errors, disk full, permission denied, partial downloads.
- Files: `F:/PyApps/vidautodownAPP/backend/core/controller.py` (lines 320-444)
- Risk: Errors may not be handled gracefully, leaving tasks in wrong state.
- Priority: High

**Database Recovery:**
- What's not tested: Database corruption recovery, concurrent write conflicts, WAL mode behavior.
- Files: `F:/PyApps/vidautodownAPP/backend/core/database.py`
- Risk: Data loss on crash or power failure.
- Priority: Medium

**Frontend Component Rendering:**
- What's not tested: Any React components, state updates, WebSocket integration.
- Files: `F:/PyApps/vidautodownAPP/frontend/components/`
- Risk: UI bugs may go undetected until user encounters them.
- Priority: Medium

---

*Concerns audit: 2026-03-17*