from __future__ import annotations
import os
import sys
import logging
import json
import sqlite3
import re
import time
import random
import threading
import queue
import subprocess
import shutil
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional
import webview

# ==========================================
# CONFIG
# ==========================================

APP_NAME = "VidAutoDown"

# Files saved in working directory
LOG_FILE = "vidautodown.log"
DB_FILE = "vidautodown.db"
MANAGER_TICK_MS = 300
EVENT_POLL_MS = 100  # slightly slower than tk
AUTO_SAVE_SEC = 10
MAX_RETRIES = 2
DEFAULT_MAX_CONCURRENT = 2
DEFAULT_OUTPUT_TPL = "%(title).100s [%(width)sx%(height)s] [%(id)s].%(ext)s"

WIN32 = os.name == "nt"

# ==========================================
# UTILS: LOGGER
# ==========================================

class ColoredFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + FORMAT + reset,
        logging.INFO: green + FORMAT + reset,
        logging.WARNING: yellow + FORMAT + reset,
        logging.ERROR: red + FORMAT + reset,
        logging.CRITICAL: bold_red + FORMAT + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

def setup_logging(level: int = logging.INFO) -> None:
    if getattr(setup_logging, "_configured", False):
        return
    if WIN32:
        os.system('')
    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(ColoredFormatter())
    logging.basicConfig(level=level, handlers=[file_handler, stream_handler])
    setup_logging._configured = True

# ==========================================
# UTILS: SYSTEM
# ==========================================

def which_yt_dlp() -> Optional[str]:
    return shutil.which("yt-dlp")

def which_aria2c() -> Optional[str]:
    return shutil.which("aria2c")

def create_flags_no_window() -> int:
    return subprocess.CREATE_NO_WINDOW if WIN32 else 0

def create_startupinfo_no_window():
    if not WIN32:
        return None
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    return si

def open_path(path: str) -> None:
    try:
        if WIN32:
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass

# ==========================================
# UTILS: PARSING
# ==========================================

PROGRESS_RE = re.compile(
    r"\[download\]\s+(?P<pct>\d+(?:\.\d+)?)%\s+of\s+(?P<size>~?\s*[\d\.]+\s*[KMGTP]?i?B)"
    r"(?:\s+at\s+(?P<speed>[\d\.\s]+[KMGTP]?i?B/s))?"
    r"(?:\s+ETA\s+(?P<eta>[\d:]+))?",
    re.IGNORECASE,
)
ARIA2_PROGRESS_RE = re.compile(
    r"\[aria2c\]\s+Downloaded\s+(?P<downloaded>[\d\.]+\s*[KMGTP]?i?B)\s+of\s+(?P<size>[\d\.]+\s*[KMGTP]?i?B)\s+\((?P<pct>\d+(?:\.\d+)?)%\)",
    re.IGNORECASE,
)
FILENAME_RE = re.compile(
    r"(?:\[download\]\s+Destination:\s+(?P<dest>.*))|(?:\[Merger\]\s+Merging formats into\s+\"(?P<merge>.*)\")"
)
URL_RE = re.compile(r"(?P<url>https?://[^\s<>'\"`]+)", re.IGNORECASE)

@dataclass(slots=True)
class ProgressLine:
    pct: float
    size: str | None
    speed: str | None
    eta: str | None

def parse_progress(line: str) -> ProgressLine | None:
    m = PROGRESS_RE.search(line)
    if m:
        return ProgressLine(
            pct=float(m.group("pct")),
            size=(m.group("size") or "").replace("~", "").strip() or None,
            speed=(m.group("speed") or "").strip() or None,
            eta=(m.group("eta") or "").strip() or None
        )
    m = ARIA2_PROGRESS_RE.search(line)
    if m:
        return ProgressLine(
            pct=float(m.group("pct")),
            size=(m.group("size") or "").strip() or None,
            speed=None,
            eta=None
        )
    return None

def parse_filename(line: str) -> str | None:
    m = FILENAME_RE.search(line)
    if not m:
        return None
    return (m.group("dest") or m.group("merge") or "").strip() or None

def extract_urls(text: str) -> list[str]:
    if not text:
        return []
    return list(dict.fromkeys(URL_RE.findall(text.strip())))

def normalize_url(url: str) -> str:
    if not url: return url
    u = url.strip()
    u = u.split("#", 1)[0]
    if u.endswith("/") and "://" in u:
        scheme, rest = u.split("://", 1)
        if "/" in rest and not rest.endswith("://"):
            u = u.rstrip("/")
    return u

# ==========================================
# CORE: MODELS
# ==========================================

@dataclass
class Task:
    url: str
    status: str = "queued"
    progress: float = 0.0
    title: str = "Fetching info..."
    filename: Optional[str] = None
    size: Optional[str] = None
    speed: Optional[str] = None
    eta: Optional[str] = None
    retries: int = 0
    added_ts: float = field(default_factory=time.time)
    vid: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    dest: Optional[str] = None
    process: Optional[subprocess.Popen] = None
    strategy: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "status": self.status,
            "progress": self.progress,
            "title": self.title,
            "filename": self.filename,
            "size": self.size,
            "speed": self.speed,
            "eta": self.eta,
            "retries": self.retries,
            "added_ts": self.added_ts,
            "vid": self.vid,
            "width": self.width,
            "height": self.height,
            "dest": self.dest,
            "strategy": self.strategy
        }

# ==========================================
# UTILS: DB
# ==========================================

_SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
    url TEXT PRIMARY KEY,
    status TEXT,
    progress REAL,
    title TEXT,
    filename TEXT,
    size TEXT,
    speed TEXT,
    eta TEXT,
    retries INTEGER,
    added_ts REAL,
    vid TEXT,
    width INTEGER,
    height INTEGER,
    dest TEXT
);
"""

class Database:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, timeout=10, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self._init_schema()
        self.lock = threading.Lock()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.executescript(_SCHEMA)

    def get_setting(self, key: str, default: Any = None) -> Any:
        with self.lock:
            cur = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cur.fetchone()
        if not row:
            return default
        try:
            return json.loads(row[0])
        except Exception:
            return default

    def set_setting(self, key: str, value: Any) -> None:
        payload = json.dumps(value)
        with self.lock:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO settings(key, value) VALUES(?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, payload),
                )

    def save_tasks(self, tasks: Iterable[Task]) -> None:
        items = []
        for t in tasks:
            items.append((
                t.url,
                t.status,
                float(t.progress or 0.0),
                t.title,
                t.filename,
                t.size,
                t.speed,
                t.eta,
                int(t.retries or 0),
                float(t.added_ts),
                t.vid,
                t.width,
                t.height,
                t.dest,
            ))
        with self.lock:
            with self.conn:
                self.conn.execute("DELETE FROM tasks;")
                self.conn.executemany(
                    "INSERT INTO tasks (url, status, progress, title, filename, size, speed, eta, retries, added_ts, vid, width, height, dest) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    items,
                )

    def load_tasks(self) -> List[Task]:
        with self.lock:
            cur = self.conn.execute(
                "SELECT url, status, progress, title, filename, size, speed, eta, retries, added_ts, vid, width, height, dest "
                "FROM tasks ORDER BY added_ts ASC"
            )
            rows = cur.fetchall()
        tasks: List[Task] = []
        for row in rows:
            tasks.append(Task(
                url=row[0],
                status=row[1] or "queued",
                progress=float(row[2] or 0.0),
                title=row[3] or "Fetching info...",
                filename=row[4],
                size=row[5],
                speed=row[6],
                eta=row[7],
                retries=int(row[8] or 0),
                added_ts=float(row[9]),
                vid=row[10],
                width=row[11],
                height=row[12],
                dest=row[13],
            ))
        return tasks

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass

# ==========================================
# CORE: CRAWLER SERVICE
# ==========================================

class CrawlerService:
    def __init__(self, ui_queue: "queue.Queue[tuple]"):
        self.ui_queue = ui_queue
        self._active_process: Optional[subprocess.Popen] = None
        self._cancel_event = threading.Event()
        self._lock = threading.Lock()

    def extract_urls(self, page_url: str) -> None:
        def worker():
            yt_dlp_path = which_yt_dlp()
            if not yt_dlp_path:
                logging.error("CRAWLER: yt-dlp not found")
                self.ui_queue.put(("crawl_error", {"error": "yt-dlp not found"}))
                return

            logging.info(f"CRAWLER: Starting extraction from {page_url}")
            self.ui_queue.put(("crawl_start", {"page_url": page_url}))

            cmd = [
                yt_dlp_path, "--flat-playlist", "--dump-json", "--no-warnings", page_url
            ]
            logging.info(f"CRAWLER: Running command: {' '.join(cmd)}")

            urls_found = []

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,  # Capture stderr too
                    stdin=subprocess.DEVNULL,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=create_flags_no_window(),
                    startupinfo=create_startupinfo_no_window()
                )

                with self._lock:
                    self._active_process = proc

                # Read stderr in separate thread for logging
                def log_stderr():
                    if proc.stderr:
                        for line in proc.stderr:
                            logging.debug(f"CRAWLER stderr: {line.strip()}")

                stderr_thread = threading.Thread(target=log_stderr, daemon=True)
                stderr_thread.start()

                if proc.stdout:
                    for line in proc.stdout:
                        if self._cancel_event.is_set():
                            proc.terminate()
                            logging.info("CRAWLER: Cancelled by user")
                            self.ui_queue.put(("crawl_cancelled", {}))
                            return

                        line = line.strip()
                        if not line:
                            continue

                        try:
                            data = json.loads(line)
                            url = data.get("url") or data.get("webpage_url")
                            title = data.get("title", "Unknown")
                            vid = data.get("id", "")

                            if url:
                                # Convert http to https for video sites
                                if url.startswith("http://"):
                                    url = "https://" + url[7:]

                                logging.info(f"CRAWLER: Found URL: {url} | Title: {title[:50] if title else '?'}")
                                urls_found.append({
                                    "url": url,
                                    "title": title,
                                    "id": vid
                                })
                                self.ui_queue.put(("crawl_progress", {"count": len(urls_found), "latest": title}))
                            else:
                                logging.warning(f"CRAWLER: No URL in JSON: {data.keys()}")
                        except json.JSONDecodeError as e:
                            logging.warning(f"CRAWLER: JSON decode error: {e}")
                            continue

                proc.wait()
                logging.info(f"CRAWLER: Process exited with code {proc.returncode}")

                if not self._cancel_event.is_set():
                    logging.info(f"CRAWLER: Complete - {len(urls_found)} URLs found")
                    self.ui_queue.put(("crawl_complete", {"urls": urls_found}))

            except Exception as e:
                logging.error(f"CRAWLER: Exception: {e}", exc_info=True)
                if not self._cancel_event.is_set():
                    self.ui_queue.put(("crawl_error", {"error": str(e)}))
            finally:
                with self._lock:
                    self._active_process = None

        self._cancel_event.clear()
        threading.Thread(target=worker, daemon=True).start()

    def cancel(self) -> None:
        self._cancel_event.set()
        with self._lock:
            if self._active_process:
                try:
                    self._active_process.terminate()
                except Exception:
                    pass
                self._active_process = None


# ==========================================
# CORE: CONTROLLER (Same as before, stripped of UI refs)
# ==========================================

class DownloadController:
    def __init__(self, ui_queue: "queue.Queue[tuple]"):
        self.ui_queue = ui_queue
        self.sem = threading.Semaphore(DEFAULT_MAX_CONCURRENT)
        self.info_sem = threading.Semaphore(DEFAULT_MAX_CONCURRENT)  # Limit concurrent info fetches
        self.tasks_lock = threading.Lock()
        self.tasks: Dict[str, Task] = {}
        self.stop_event = threading.Event()
        # Default destination: User's Downloads folder
        self.destination = os.path.join(os.path.expanduser("~"), "Downloads")
        self.output_tpl = DEFAULT_OUTPUT_TPL
        self.max_concurrent = DEFAULT_MAX_CONCURRENT
        self._last_progress_post_ts: Dict[str, float] = {}
        self._last_progress_pct: Dict[str, float] = {}
        self.auto_delete_finished = False

        self.aria2c_path = which_aria2c()

        self.manager_thread = threading.Thread(target=self._manager_loop, daemon=True)
        self.manager_thread.start()

    def set_auto_delete(self, enabled: bool) -> None:
        self.auto_delete_finished = enabled
        self.post(("log", f"Auto-delete finished: {enabled}"))

    def set_destination(self, folder: str) -> None:
        self.destination = folder

    def set_max_concurrent(self, n: int) -> None:
        self.max_concurrent = max(1, min(6, n))
        self.sem = threading.Semaphore(self.max_concurrent)
        self.info_sem = threading.Semaphore(self.max_concurrent)
        self.post(("log", f"Max concurrent downloads: {self.max_concurrent}"))

    def add_urls(self, urls: List[str]) -> None:
        with self.tasks_lock:
            added = 0
            for raw in urls:
                url = normalize_url(raw)
                if url and url not in self.tasks:
                    self.tasks[url] = Task(url=url, status="info")
                    added += 1
        if added:
            self.post(("log", f"Queued {added} new item(s)."))
            self.post(("refresh", None))

    def resume(self, url: str) -> None:
        with self.tasks_lock:
            task = self.tasks.get(url)
            if task and task.status == "paused":
                task.status = "queued"
                task.progress = 0.0
                task.eta = None
                task.speed = None
                self.post(("log", f"Resumed: {self._disp(url)}"))
        self.post(("refresh", None))

    def pause(self, url: str) -> None:
        with self.tasks_lock:
            task = self.tasks.get(url)
            if task and task.status == "downloading" and task.process:
                try:
                    task.process.terminate()
                except Exception as e:
                    logging.error(f"Error terminating process for {url}: {e}")
                task.status = "paused"
                task.process = None
                task.eta = None
                task.speed = None
        self.post(("log", f"Paused: {self._disp(url)}"))
        self.post(("refresh", None))

    def cancel(self, url: str) -> None:
        with self.tasks_lock:
            task = self.tasks.get(url)
            if not task:
                return
            if task.process:
                try:
                    task.process.terminate()
                except Exception:
                    pass
            task.status = "cancelled"
            task.process = None
        self.post(("log", f"Cancelled: {self._disp(url)}"))
        self.post(("refresh", None))

    def retry(self, url: str) -> None:
        with self.tasks_lock:
            task = self.tasks.get(url)
            if task and task.status == "failed":
                task.status = "queued"
                task.retries = 0
                task.progress = 0.0
        self.post(("refresh", None))

    def remove(self, url: str) -> None:
        with self.tasks_lock:
            if url in self.tasks:
                del self.tasks[url]
        self._last_progress_post_ts.pop(url, None)
        self._last_progress_pct.pop(url, None)
        self.post(("refresh", None))

    def clear_finished(self) -> None:
        with self.tasks_lock:
            before = len(self.tasks)
            self.tasks = {
                url: t
                for url, t in self.tasks.items()
                if t.status not in ("completed", "failed", "cancelled")
            }
            cleared = before - len(self.tasks)
        if cleared:
            self.post(("log", f"Cleared {cleared} finished task(s)."))
        self.post(("refresh", None))

    def stop(self) -> None:
        self.stop_event.set()
        with self.tasks_lock:
            for task in self.tasks.values():
                if task.process:
                    try:
                        task.process.terminate()
                    except Exception:
                        pass

    def post(self, evt: tuple) -> None:
        try:
            self.ui_queue.put_nowait(evt)
        except queue.Full:
            pass

    def _disp(self, url: str) -> str:
        with self.tasks_lock:
            t = self.tasks.get(url)
            if not t: return url
            return t.title if t.title and t.title != "..." else url

    def _manager_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                with self.tasks_lock:
                    info_tasks = [t for t in self.tasks.values() if t.status == "info"]
                    for t in info_tasks:
                        if self.info_sem.acquire(blocking=False):
                            t.status = "fetching-info"
                            threading.Thread(target=self._fetch_info_worker, args=(t.url,), daemon=True).start()

                    download_tasks = [t for t in self.tasks.values() if t.status == "queued"]
                    for t in download_tasks:
                        if self.sem.acquire(blocking=False):
                            t.status = "downloading"
                            threading.Thread(target=self._download_worker, args=(t.url,), daemon=True).start()
            except Exception:
                pass
            time.sleep(MANAGER_TICK_MS / 1000.0)

    def _fetch_info_worker(self, url: str) -> None:
        yt_dlp_path = which_yt_dlp()
        if not yt_dlp_path:
            logging.error("DOWNLOAD: yt-dlp not found")
            self.post(("log", "Error: yt-dlp not found"))
            with self.tasks_lock:
                task = self.tasks.get(url)
                if task: task.status = "failed"
            self.post(("refresh", None))
            self.info_sem.release()
            return

        logging.info(f"DOWNLOAD: Fetching info for {url}")
        try:
            cmd = [yt_dlp_path, "--dump-json", "--no-warnings", url]
            logging.debug(f"DOWNLOAD: Running {' '.join(cmd)}")
            proc = subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                creationflags=create_flags_no_window(), startupinfo=create_startupinfo_no_window(),
                check=True, stdin=subprocess.DEVNULL
            )
            info = json.loads(proc.stdout)
            logging.info(f"DOWNLOAD: Got info for '{info.get('title', '?')[:50]}' - {url}")
            with self.tasks_lock:
                task = self.tasks.get(url)
                if task:
                    task.title = info.get("title", "Unknown Title")
                    task.vid = info.get("id")
                    task.width = info.get("width")
                    task.height = info.get("height")
                    if task.vid:
                        for other_url, other in list(self.tasks.items()):
                            if other_url == url: continue
                            if other.vid == task.vid:
                                keep = other if other.added_ts <= task.added_ts else task
                                drop = task if keep is other else other
                                drop.status = "cancelled"
                                self.post(("log", f"Duplicate: {keep.title}"))
                                break
                    if task.status != "cancelled":
                        task.status = "queued"
        except Exception as e:
            logging.error(f"DOWNLOAD: Failed to fetch info for {url}: {e}", exc_info=True)
            with self.tasks_lock:
                task = self.tasks.get(url)
                if task:
                    task.status = "failed"
                    task.title = f"Error: {str(e)[:50]}"
        finally:
            self.info_sem.release()
            self.post(("refresh", None))

    def _maybe_post_progress(self, url: str, pct_value_0_100: float) -> None:
        now = time.monotonic()
        last_ts = self._last_progress_post_ts.get(url, 0.0)
        last_pct = self._last_progress_pct.get(url, -1.0)
        if (now - last_ts) >= 0.2 or abs(pct_value_0_100 - last_pct) >= 1.0:
            self._last_progress_post_ts[url] = now
            self._last_progress_pct[url] = pct_value_0_100
            self.post(("progress", url))

    def _download_worker(self, url: str) -> None:
        yt_dlp_path = which_yt_dlp()
        logging.info(f"DOWNLOAD: Starting download worker for {url}")
        try:
            with self.tasks_lock:
                task = self.tasks.get(url)
                if not task:
                    self.sem.release()
                    return
                folder = task.dest or self.destination
                current_retry = task.retries

            if not folder:
                logging.error(f"DOWNLOAD: No destination folder for {url}")
                self.post(("log", "Error: Destination not set."))
                with self.tasks_lock:
                    if task: task.status = "failed"
                self.sem.release()
                return
            
            os.makedirs(folder, exist_ok=True)
            with self.tasks_lock:
                if task: task.dest = folder

            base_cmd = [
                yt_dlp_path, "--newline", "--progress", "-S", "res,ext:mp4:m4a", "--recode", "mp4",
                "-P", folder, "-o", self.output_tpl, "--no-warnings", "--no-overwrites", "--continue",
                "--retries", "10", "--fragment-retries", "10"
            ]
            cmd = list(base_cmd)
            strategy_name = ""

            if current_retry == 0:
                strategy_name = "Strategy A"
                cmd.extend(["--concurrent-fragments", "4"])
                with self.tasks_lock:
                    if task: task.strategy = "Strategy A"
            elif current_retry == 1:
                if self.aria2c_path:
                    strategy_name = "Strategy B"
                    cmd.extend(["--downloader", "aria2c", "--downloader-args", "aria2c:-x16 -s16 -k1M"])
                    with self.tasks_lock:
                        if task: task.strategy = "Strategy B"
                else:
                    raise FileNotFoundError("aria2c not found")
            else:
                strategy_name = "Strategy C"
                with self.tasks_lock:
                    if task: task.strategy = "Strategy C"

            cmd.append(url)

            logging.info(f"DOWNLOAD: Running yt-dlp for {url} with {strategy_name}")
            logging.debug(f"DOWNLOAD: Command: {' '.join(cmd)}")

            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="replace",
                universal_newlines=True, creationflags=create_flags_no_window(), startupinfo=create_startupinfo_no_window(),
                stdin=subprocess.DEVNULL
            )

            with self.tasks_lock:
                task = self.tasks.get(url)
                if task: task.process = proc

            if proc.stdout:
                for raw in iter(proc.stdout.readline, ""):
                    s = raw.strip()
                    if not s: continue

                    # Log errors and warnings from yt-dlp
                    if s.startswith("ERROR") or s.startswith("WARNING"):
                        logging.warning(f"yt-dlp: {s}")

                    with self.tasks_lock:
                        task = self.tasks.get(url)
                        if not task or task.status != "downloading": break

                    pg = parse_progress(s)
                    if pg:
                        with self.tasks_lock:
                            task.progress = pg.pct / 100.0
                            task.size = pg.size
                            task.speed = pg.speed
                            task.eta = pg.eta
                        self._maybe_post_progress(url, pg.pct)
                        continue
                    
                    dest = parse_filename(s)
                    if dest:
                        with self.tasks_lock:
                            task.filename = os.path.basename(dest)
                        self.post(("progress", url))

            ret = proc.wait()
            with self.tasks_lock:
                task = self.tasks.get(url)
                if not task:
                    self.sem.release()
                    return

            if task.status in ("paused", "cancelled"):
                pass
            elif ret == 0:
                logging.info(f"DOWNLOAD: Completed {url}")
                with self.tasks_lock:
                    task.status = "completed"
                    task.progress = 1.0
                self.post(("log", f"Completed: {task.title or url}"))
                self.post(("progress", url))
                if self.auto_delete_finished:
                    self.remove(url)
            else:
                logging.error(f"DOWNLOAD: yt-dlp exited with code {ret} for {url}")
                with self.tasks_lock:
                    if task.retries < MAX_RETRIES:
                        task.retries += 1
                        task.status = "queued"
                        threading.Thread(target=lambda: (time.sleep(1)), daemon=True).start()
                    else:
                        task.status = "failed"
                        self.post(("log", f"Failed: {task.title or url}"))
        except Exception as e:
            logging.error(f"DOWNLOAD: Exception for {url}: {e}", exc_info=True)
            with self.tasks_lock:
                task = self.tasks.get(url)
                if task:
                    if task.retries < MAX_RETRIES:
                        task.retries += 1
                        task.status = "queued"
                        threading.Thread(target=lambda: (time.sleep(1)), daemon=True).start()
                    else:
                        task.status = "failed"
        finally:
            self._last_progress_post_ts.pop(url, None)
            self._last_progress_pct.pop(url, None)
            with self.tasks_lock:
                task = self.tasks.get(url)
                if task: task.process = None
            self.sem.release()
            self.post(("refresh", None))


# ==========================================
# UI: WEBVIEW APP
# ==========================================

class Api:
    def __init__(self, ctrl: DownloadController, crawler: CrawlerService, db: Database, window):
        self.ctrl = ctrl
        self.crawler = crawler
        self.db = db
        self.window = window

    def add_links(self, text: str):
        urls = extract_urls(text)
        if urls:
            logging.info(f"API: Adding {len(urls)} URLs to queue: {urls[:3]}{'...' if len(urls) > 3 else ''}")
            self.ctrl.add_urls(urls)
        else:
            logging.warning(f"API: No URLs found in input: {text[:100]}...")

    def crawl_extract(self, page_url: str):
        """Start URL extraction from a page."""
        if page_url and page_url.strip():
            self.crawler.extract_urls(page_url.strip())

    def crawl_cancel(self):
        """Cancel ongoing extraction."""
        self.crawler.cancel()

    def browse_destination(self):
        # Using pywebview's native folder dialog
        folder = self.window.create_file_dialog(webview.FOLDER_DIALOG)
        if folder and isinstance(folder, (list, tuple)) and len(folder) > 0:
            folder = folder[0]
        
        if folder and isinstance(folder, str):
            self.ctrl.set_destination(folder)
            self.db.set_setting("last_folder", folder)
            return folder
        return None

    def open_folder(self):
        folder = self.db.get_setting("last_folder", "")
        if folder and os.path.isdir(folder):
            open_path(folder)

    def set_max_concurrent(self, val: int):
        self.ctrl.set_max_concurrent(val)
        self.db.set_setting("max_concurrent", val)

    def set_auto_delete(self, enabled: bool):
        self.ctrl.set_auto_delete(enabled)
        self.db.set_setting("auto_delete", 1 if enabled else 0)

    def clear_finished(self):
        self.ctrl.clear_finished()

    def pause_task(self, url: str):
        self.ctrl.pause(url)

    def resume_task(self, url: str):
        self.ctrl.resume(url)

    def cancel_task(self, url: str):
        self.ctrl.cancel(url)

    def remove_task(self, url: str):
        self.ctrl.remove(url)
    
    def retry_task(self, url: str):
        self.ctrl.retry(url)

    def open_task_file(self, url: str):
        with self.ctrl.tasks_lock:
            task = self.ctrl.tasks.get(url)
            if not task: return
            folder = task.dest or self.db.get_setting("last_folder") or ""
            filename = task.filename
        
        if folder and filename:
            full = os.path.join(folder, filename)
            if os.path.isfile(full):
                open_path(full)
                return
        if folder and os.path.isdir(folder):
            open_path(folder)


def main():
    setup_logging()

    # 1. Setup Backend
    db = Database(DB_FILE)
    ui_queue = queue.Queue(maxsize=1000)
    ctrl = DownloadController(ui_queue)
    crawler = CrawlerService(ui_queue)

    # 2. Restore settings
    last_folder = db.get_setting("last_folder", "")
    if last_folder and os.path.isdir(last_folder):
        ctrl.set_destination(last_folder)

    max_c = db.get_setting("max_concurrent", DEFAULT_MAX_CONCURRENT)
    if isinstance(max_c, int):
        ctrl.set_max_concurrent(max_c)

    auto_del = bool(db.get_setting("auto_delete", 0))
    ctrl.set_auto_delete(auto_del)

    # 3. Restore queue
    saved_tasks = db.load_tasks()
    with ctrl.tasks_lock:
        for t in saved_tasks:
            if t.status not in ("completed", "cancelled"):
                if t.status == "downloading": t.status = "queued"
                ctrl.tasks[t.url] = t

    # 4. Create Window
    window = webview.create_window(
        APP_NAME,
        url="web/index.html",
        width=1000,
        height=700,
        resizable=True,
        background_color='#0f2027'
    )

    # 5. Bind API
    api = Api(ctrl, crawler, db, window)
    window.expose(
        api.add_links,
        api.crawl_extract,
        api.crawl_cancel,
        api.browse_destination,
        api.open_folder,
        api.set_max_concurrent,
        api.set_auto_delete,
        api.clear_finished,
        api.pause_task,
        api.resume_task,
        api.cancel_task,
        api.remove_task,
        api.retry_task,
        api.open_task_file
    )

    # 6. Periodic Background Workers
    running = True

    def event_poller():
        # Wait for window to load
        time.sleep(1)

        # Initial settings push
        window.evaluate_js(f"updateSettings({{ 'last_folder': {json.dumps(last_folder)}, 'max_concurrent': {max_c}, 'auto_delete': {json.dumps(auto_del)} }})")
        window.evaluate_js(f"refreshTasks({json.dumps([t.to_dict() for t in ctrl.tasks.values()])})")

        while running:
            # Drain queue
            refresh_needed = False
            try:
                while True:
                    evt, payload = ui_queue.get_nowait()
                    if evt == "log":
                        # clean strings for JS
                        safe_msg = json.dumps(payload)
                        window.evaluate_js(f"logMessage({safe_msg})")
                    elif evt in ("progress", "refresh"):
                        refresh_needed = True
                    elif evt.startswith("crawl_"):
                        # Crawler events
                        window.evaluate_js(f"handleCrawlMessage({{ 'type': {json.dumps(evt)}, 'payload': {json.dumps(payload)} }})")
            except queue.Empty:
                pass

            if refresh_needed:
                with ctrl.tasks_lock:
                    tasks_list = [t.to_dict() for t in ctrl.tasks.values()]
                window.evaluate_js(f"refreshTasks({json.dumps(tasks_list)})")

            time.sleep(0.1)

    def autosave_loop():
        while running:
            time.sleep(AUTO_SAVE_SEC)
            try:
                with ctrl.tasks_lock:
                    snap = list(ctrl.tasks.values())
                db.save_tasks(snap)
            except Exception:
                pass

    def on_closed():
        nonlocal running
        running = False
        ctrl.stop()
        try:
            with ctrl.tasks_lock:
                snap = list(ctrl.tasks.values())
            db.save_tasks(snap)
            db.close()
        except Exception:
            pass

    window.events.closed += on_closed
    
    # Start threads
    threading.Thread(target=event_poller, daemon=True).start()
    threading.Thread(target=autosave_loop, daemon=True).start()

    # Start App
    webview.start(debug=True)

if __name__ == "__main__":
    main()
