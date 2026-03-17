# External Integrations

**Analysis Date:** 2026-03-17

## APIs & External Services

**Video Download Engine:**
- yt-dlp - Command-line video downloader
  - SDK/Client: Subprocess invocation via `shutil.which("yt-dlp")`
  - Used for: Video info fetching (`--dump-json`) and downloading
  - Supports: YouTube, Vimeo, and 1000+ other platforms
  - Location: `F:/PyApps/vidautodownAPP/backend/core/controller.py` (lines 20-24)

**External Downloader (Optional):**
- aria2c - High-performance download utility
  - SDK/Client: Subprocess invocation via yt-dlp `--downloader` flag
  - Used for: Retry strategy (Strategy B) when default download fails
  - Location: `F:/PyApps/vidautodownAPP/backend/core/controller.py` (lines 336-338)
  - Installation: Downloaded automatically by `run.bat` if not present

## Data Storage

**Databases:**
- SQLite - Local file-based database
  - Connection: `vidautodown.db` in project root
  - Client: Python stdlib `sqlite3` module
  - Mode: WAL (Write-Ahead Logging) for concurrent access
  - Tables: `settings`, `tasks`
  - Location: `F:/PyApps/vidautodownAPP/backend/core/database.py`

**File Storage:**
- Local filesystem only
- Default destination: `~/Downloads`
- User-configurable via folder browser dialog

**Caching:**
- None - Real-time data only

## Authentication & Identity

**Auth Provider:**
- Not applicable - Local desktop application
- No authentication required
- No multi-user support

## Communication Protocols

**WebSocket:**
- Protocol: `ws://localhost:8000/ws`
- Purpose: Real-time task updates to frontend
- Message types:
  - `task_update` - Single task progress update
  - `refresh` - Full task list refresh
  - `toast` - User notification message
  - `stats_update` - Statistics refresh
- Location: `F:/PyApps/vidautodownAPP/backend/api/websockets.py`

**REST API:**
- Base URL: `http://localhost:8000/api`
- Endpoints:
  - `GET /tasks` - List all tasks
  - `POST /tasks` - Add new tasks from text
  - `POST /action` - Task actions (pause, resume, cancel, retry, remove)
  - `GET /settings` - Get current settings
  - `POST /settings` - Update settings
  - `POST /browse_folder` - Open folder picker dialog
  - `POST /open_destination` - Open destination folder in file manager
  - `GET /stats` - Get download statistics
- Location: `F:/PyApps/vidautodownAPP/backend/api/routes.py`

## Monitoring & Observability

**Error Tracking:**
- None - Local application

**Logs:**
- File logging to `vidautodown.log`
- Console output with colored formatting
- Location: `F:/PyApps/vidautodownAPP/vidautodown_webview.py` (lines 40-73)

## CI/CD & Deployment

**Hosting:**
- Local desktop application - no deployment target
- Development mode only (no production build process)

**CI Pipeline:**
- None

## Environment Configuration

**Required env vars:**
- None - All configuration stored in SQLite database

**Secrets location:**
- Not applicable - No secrets or API keys required

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Third-Party Tools

**yt-dlp Integration Details:**
- Binary detection: `shutil.which("yt-dlp")` in `F:/PyApps/vidautodownAPP/backend/core/controller.py`
- Info fetching: `yt-dlp --dump-json --no-warnings <url>`
- Download command template:
  ```
  yt-dlp --newline --progress -S res,ext:mp4:m4a --recode mp4
         -P <folder> -o "<output_template>" --no-warnings --no-overwrites
         --continue --retries 10 --fragment-retries 10 <url>
  ```
- Output template: `%(title).100s [%(width)sx%(height)s] [%(id)s].%(ext)s`

**Download Strategies:**
- Strategy A (first attempt): `--concurrent-fragments 4`
- Strategy B (retry 1): `--downloader aria2c --downloader-args "aria2c:-x16 -s16 -k1M"`
- Strategy C (retry 2+): Basic download with standard settings

---

*Integration audit: 2026-03-17*