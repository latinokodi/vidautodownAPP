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
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk

# ==========================================
# CONFIG
# ==========================================

APP_NAME = "VidAutoDown"

# Files saved in working directory
LOG_FILE = "vidautodown.log"
DB_FILE = "vidautodown.db"  # SQLite database for settings + task queue

# Worker/manager controls
MANAGER_TICK_MS = 300
EVENT_POLL_MS = 75
AUTO_SAVE_SEC = 10
MAX_RETRIES = 2
DEFAULT_MAX_CONCURRENT = 2

# Output template: title + resolution + id + extension
DEFAULT_OUTPUT_TPL = "%(title).100s [%(width)sx%(height)s] [%(id)s].%(ext)s"

WIN32 = os.name == "nt"


# ==========================================
# UTILS: LOGGER
# ==========================================

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to the log output."""
    
    # ANSI escape codes
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
    """Configure global logging once."""
    if getattr(setup_logging, "_configured", False):
        return
    
    # Enable ANSI escape sequences on Windows 10+
    if WIN32:
        os.system('')

    # File handler (no color)
    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    # Stream handler (color)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(ColoredFormatter())

    logging.basicConfig(
        level=level,
        handlers=[file_handler, stream_handler],
    )
    setup_logging._configured = True  # type: ignore[attr-defined]


# ==========================================
# UTILS: SYSTEM
# ==========================================

def which_yt_dlp() -> Optional[str]:
    return shutil.which("yt-dlp")

def which_aria2c() -> Optional[str]:
    return shutil.which("aria2c")

def create_flags_no_window() -> int:
    # Retained for compatibility where only creationflags are used
    return subprocess.CREATE_NO_WINDOW if WIN32 else 0

def create_startupinfo_no_window():
    """StartupInfo that hides console windows on older Windows/Python combos."""
    if not WIN32:
        return None
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0  # SW_HIDE
    return si

def open_path(path: str) -> None:
    try:
        if WIN32:
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        # swallow: UI will log error
        pass


# ==========================================
# UTILS: PARSING
# ==========================================

# Regexes (robust to KiB/MiB/GiB/TiB, speed optional, ETA optional)
# yt-dlp common progress line variants:
# [download]  15.3% of 12.34MiB at 2.3MiB/s ETA 00:02
# [download]  15.3% of ~12.34MiB at 2.3MiB/s ETA 00:02
# [download]  15.3% of 12.34MiB
PROGRESS_RE = re.compile(
    r"\[download\]\s+(?P<pct>\d+(?:\.\d+)?)%\s+of\s+(?P<size>~?\s*[\d\.]+\s*[KMGTP]?i?B)"
    r"(?:\s+at\s+(?P<speed>[\d\.\s]+[KMGTP]?i?B/s))?"
    r"(?:\s+ETA\s+(?P<eta>[\d:]+))?",
    re.IGNORECASE,
)

# [aria2c] Downloaded 10.00MiB of 100.00MiB (10%)
ARIA2_PROGRESS_RE = re.compile(
    r"\[aria2c\]\s+Downloaded\s+(?P<downloaded>[\d\.]+\s*[KMGTP]?i?B)\s+of\s+(?P<size>[\d\.]+\s*[KMGTP]?i?B)\s+\((?P<pct>\d+(?:\.\d+)?)%\)",
    re.IGNORECASE,
)

# Destination/merge lines
FILENAME_RE = re.compile(
    r"(?:\[download\]\s+Destination:\s+(?P<dest>.*))|(?:\[Merger\]\s+Merging formats into\s+\"(?P<merge>.*)\")"
)

# URL extractor
URL_RE = re.compile(r"(?P<url>https?://[^\s<>'\"`]+)", re.IGNORECASE)

@dataclass(slots=True)
class ProgressLine:
    pct: float
    size: str | None
    speed: str | None
    eta: str | None

def parse_progress(line: str) -> ProgressLine | None:
    # Try standard yt-dlp [download]
    m = PROGRESS_RE.search(line)
    if m:
        pct = float(m.group("pct"))
        size = (m.group("size") or "").replace("~", "").strip() or None
        speed = (m.group("speed") or "").strip() or None
        eta = (m.group("eta") or "").strip() or None
        return ProgressLine(pct=pct, size=size, speed=speed, eta=eta)

    # Try aria2c [aria2c]
    m = ARIA2_PROGRESS_RE.search(line)
    if m:
        pct = float(m.group("pct"))
        size = (m.group("size") or "").strip() or None
        # aria2c line usually doesn't have speed/eta in the same format, or it's harder to parse reliably
        # We'll just return pct and size
        return ProgressLine(pct=pct, size=size, speed=None, eta=None)

    return None

def parse_filename(line: str) -> str | None:
    m = FILENAME_RE.search(line)
    if not m:
        return None
    return (m.group("dest") or m.group("merge") or "").strip() or None

def extract_urls(text: str) -> list[str]:
    if not text:
        return []
    # dict.fromkeys -> stable unique
    return list(dict.fromkeys(URL_RE.findall(text.strip())))

def normalize_url(url: str) -> str:
    """Lightweight normalization to reduce duplicates."""
    if not url:
        return url
    u = url.strip()
    # drop fragments
    u = u.split("#", 1)[0]
    # collapse trailing slash if not root
    if u.endswith("/") and "://" in u:
        scheme, rest = u.split("://", 1)
        if "/" in rest and not rest.endswith("://"):
            u = u.rstrip("/")
    return u


# ==========================================
# UTILS: IOJSON
# ==========================================

def json_load(path: str, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def json_atomic_save(path: str, data: Any) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


# ==========================================
# CORE: MODELS
# ==========================================

@dataclass
class Task:
    url: str
    status: str = "queued"  # queued | info | fetching-info | downloading | paused | cancelled | completed | failed
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
    dest: Optional[str] = None  # destination folder for this task (persisted)
    process: Optional[subprocess.Popen] = None
    strategy: Optional[str] = None  # transient: "Strategy A", "Strategy B", etc.

    def to_json(self) -> Dict[str, Any]:
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
        }

    @staticmethod
    def from_json(d: Dict[str, Any]) -> "Task":
        return Task(
            url=d["url"],
            status=d.get("status", "queued"),
            progress=float(d.get("progress", 0)),
            title=d.get("title", "Fetching info..."),
            filename=d.get("filename"),
            size=d.get("size"),
            speed=d.get("speed"),
            eta=d.get("eta"),
            retries=int(d.get("retries", 0)),
            added_ts=float(d.get("added_ts", time.time())),
            vid=d.get("vid"),
            width=d.get("width"),
            height=d.get("height"),
            dest=d.get("dest"),
        )


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
        # Single connection used on UI thread (autosave and loads run from UI events)
        self.conn = sqlite3.connect(path, timeout=10)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.executescript(_SCHEMA)

    # ---------- settings ----------
    def get_setting(self, key: str, default: Any = None) -> Any:
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
        with self.conn:
            self.conn.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, payload),
            )

    # ---------- tasks ----------
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
        with self.conn:
            self.conn.execute("DELETE FROM tasks;")
            self.conn.executemany(
                "INSERT INTO tasks (url, status, progress, title, filename, size, speed, eta, retries, added_ts, vid, width, height, dest) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                items,
            )

    def load_tasks(self) -> List[Task]:
        cur = self.conn.execute(
            "SELECT url, status, progress, title, filename, size, speed, eta, retries, added_ts, vid, width, height, dest "
            "FROM tasks ORDER BY added_ts ASC"
        )
        tasks: List[Task] = []
        for row in cur.fetchall():
            t = Task(
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
            )
            tasks.append(t)
        return tasks

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass


# ==========================================
# CORE: CONTROLLER
# ==========================================

class DownloadController:
    """All background work happens here. Posts UI-safe events to ui_queue."""

    def __init__(self, ui_queue: "queue.Queue[tuple]"):
        self.ui_queue = ui_queue
        self.sem = threading.Semaphore(DEFAULT_MAX_CONCURRENT)
        self.tasks_lock = threading.Lock()
        self.tasks: Dict[str, Task] = {}  # keyed by URL
        self.stop_event = threading.Event()
        self.destination = ""
        self.output_tpl = DEFAULT_OUTPUT_TPL
        self.max_concurrent = DEFAULT_MAX_CONCURRENT
        # Progress throttle state
        self._last_progress_post_ts: Dict[str, float] = {}
        self._last_progress_pct: Dict[str, float] = {}

        self.manager_thread = threading.Thread(target=self._manager_loop, daemon=True)
        self.manager_thread.start()

        self.aria2c_path = which_aria2c()
        self.auto_delete_finished = False

    # ---------- public API ----------
    def set_auto_delete(self, enabled: bool) -> None:
        self.auto_delete_finished = enabled
        self.post(("log", f"Auto-delete finished: {enabled}"))
    def set_destination(self, folder: str) -> None:
        self.destination = folder

    def set_max_concurrent(self, n: int) -> None:
        self.max_concurrent = max(1, min(6, n))
        self.sem = threading.Semaphore(self.max_concurrent)
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
                except Exception as e:
                    logging.error(f"Error terminating process for {url}: {e}")
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
        # clean throttle state
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
                    except Exception as e:
                        logging.error(f"Error terminating process for {task.url}: {e}")

    # ---------- internals ----------
    def post(self, evt: tuple) -> None:
        try:
            self.ui_queue.put_nowait(evt)
        except queue.Full:
            # Drop event on overflow; UI will still refresh periodically
            logging.debug("UI event queue full; dropping an event.")

    def _disp(self, url: str) -> str:
        with self.tasks_lock:
            t = self.tasks.get(url)
            if not t:
                return url
            return t.title if t.title and t.title != "..." else url

    def _manager_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                with self.tasks_lock:
                    # spawn info workers
                    info_tasks = [t for t in self.tasks.values() if t.status == "info"]
                    for t in info_tasks:
                        t.status = "fetching-info"
                        threading.Thread(
                            target=self._fetch_info_worker, args=(t.url,), daemon=True
                        ).start()

                    # spawn download workers
                    download_tasks = [t for t in self.tasks.values() if t.status == "queued"]
                    for t in download_tasks:
                        if self.sem.acquire(blocking=False):
                            t.status = "downloading"
                            threading.Thread(
                                target=self._download_worker, args=(t.url,), daemon=True
                            ).start()

            except Exception as e:
                logging.exception(f"Manager loop error: {e}")
            finally:
                time.sleep(MANAGER_TICK_MS / 1000.0)

    def _fetch_info_worker(self, url: str) -> None:
        yt_dlp_path = which_yt_dlp()
        if not yt_dlp_path:
            logging.error("yt-dlp not found.")
            with self.tasks_lock:
                task = self.tasks.get(url)
                if task:
                    task.status = "failed"
            self.post(("refresh", None))
            return

        try:
            cmd = [yt_dlp_path, "--dump-json", "--no-warnings", url]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=create_flags_no_window(),
                startupinfo=create_startupinfo_no_window(),
                check=True,
                stdin=subprocess.DEVNULL,
            )
            info = json.loads(proc.stdout)
            with self.tasks_lock:
                task = self.tasks.get(url)
                if task:
                    task.title = info.get("title", "Unknown Title")
                    task.vid = info.get("id")
                    task.width = info.get("width")
                    task.height = info.get("height")
                    # Duplicate suppression by video id
                    if task.vid:
                        for other_url, other in list(self.tasks.items()):
                            if other_url == url:
                                continue
                            if other.vid == task.vid:
                                keep = other if other.added_ts <= task.added_ts else task
                                drop = task if keep is other else other
                                drop.status = "cancelled"
                                self.post(("log", f"Duplicate detected (same video id). Keeping first occurrence: {keep.title or keep.url}"))
                                break
                    if task.status != "cancelled":
                        task.status = "queued"

        except subprocess.CalledProcessError as e:
            # yt-dlp returned non-zero exit code (e.g. video unavailable)
            err_msg = e.stderr.strip() if e.stderr else str(e)
            # Try to extract a clean error message
            clean_msg = err_msg
            if "ERROR:" in err_msg:
                clean_msg = err_msg.split("ERROR:", 1)[1].strip()
            
            logging.error(f"yt-dlp failed for {url}: {clean_msg}")
            
            with self.tasks_lock:
                task = self.tasks.get(url)
                if task:
                    task.status = "failed"
                    # Show a bit of the error in the title for the user
                    task.title = f"Error: {clean_msg[:60]}"

        except Exception as e:
            logging.exception(f"Failed to fetch info for {url}: {e}")
            with self.tasks_lock:
                task = self.tasks.get(url)
                if task:
                    task.status = "failed"
                    task.title = "Failed to get info"
        finally:
            self.post(("refresh", None))

    def _maybe_post_progress(self, url: str, pct_value_0_100: float) -> None:
        """Throttle progress events per URL to avoid flooding the UI."""
        now = time.monotonic()
        last_ts = self._last_progress_post_ts.get(url, 0.0)
        last_pct = self._last_progress_pct.get(url, -1.0)

        # Post if at least 0.2s passed or pct moved by >= 1.0
        if (now - last_ts) >= 0.2 or abs(pct_value_0_100 - last_pct) >= 1.0:
            self._last_progress_post_ts[url] = now
            self._last_progress_pct[url] = pct_value_0_100
            self.post(("progress", url))

    def _download_worker(self, url: str) -> None:
        yt_dlp_path = which_yt_dlp()
        if not yt_dlp_path:
            logging.error("yt-dlp not found.")
            with self.tasks_lock:
                task = self.tasks.get(url)
                if task:
                    task.status = "failed"
            self.post(("refresh", None))
            self.sem.release()
            return

        try:
            with self.tasks_lock:
                task = self.tasks.get(url)
                if not task:
                    self.sem.release()
                    return
                # Prefer persisted destination per task; fallback to controller-wide
                folder = task.dest or self.destination
                current_retry = task.retries  # 0, 1, or 2

            if not folder:
                self.post(("log", "Set a destination folder first. Task cancelled."))
                with self.tasks_lock:
                    if task:
                        task.status = "failed"
                self.sem.release()
                return

            os.makedirs(folder, exist_ok=True)

            # Persist dest on task at start
            with self.tasks_lock:
                task = self.tasks.get(url)
                if task:
                    task.dest = folder

            # ---------------------------------------------------------
            # STRATEGY SELECTION
            # ---------------------------------------------------------
            # Strategy A (Retry 0): yt-dlp + --concurrent-fragments 4
            # Strategy B (Retry 1): yt-dlp + aria2c
            # Strategy C (Retry 2): yt-dlp original (safe fallback)
            
            # Base command (common to all strategies)
            # NOTE: We purposely do NOT include "--write-info-json" to avoid extra files.
            base_cmd = [
                yt_dlp_path,
                "--newline",
                "--progress",

                "-S", "res,ext:mp4:m4a",
                "--recode", "mp4",
                "-P", folder,
                "-o", self.output_tpl,
                "--no-warnings",
                "--no-overwrites",
                "--continue",
                "--retries", "10",
                "--fragment-retries", "10",
            ]

            cmd = list(base_cmd)
            strategy_name = ""

            if current_retry == 0:
                # Strategy A: Internal downloader with concurrent fragments
                strategy_name = "Strategy A (Internal + Concurrent)"
                cmd.extend(["--concurrent-fragments", "4"])
                self.post(("log", f"Starting {strategy_name} for: {self._disp(url)}"))
                with self.tasks_lock:
                    if task:
                        task.strategy = "Strategy A"

            elif current_retry == 1:
                # Strategy B: External downloader (aria2c)
                # If aria2c is missing, we must fail this attempt immediately to proceed to Strategy C
                if self.aria2c_path:
                    strategy_name = "Strategy B (External aria2c)"
                    cmd.extend([
                        "--downloader", "aria2c",
                        "--downloader-args", "aria2c:-x16 -s16 -k1M"
                    ])
                    self.post(("log", f"Starting {strategy_name} for: {self._disp(url)}"))
                    with self.tasks_lock:
                        if task:
                            task.strategy = "Strategy B"
                else:
                    # Skip Strategy B if aria2c is missing
                    self.post(("log", f"aria2c not found, skipping Strategy B for: {self._disp(url)}"))
                    raise FileNotFoundError("aria2c not found")

            else:
                # Strategy C: Default / Safe fallback
                # Original args exactly as requested (no concurrent fragments, no external downloader)
                strategy_name = "Strategy C (Safe Fallback)"
                self.post(("log", f"Starting {strategy_name} for: {self._disp(url)}"))
                with self.tasks_lock:
                    if task:
                        task.strategy = "Strategy C"

            cmd.append(url)

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding="utf-8",
                errors="replace",
                universal_newlines=True,
                creationflags=create_flags_no_window(),
                startupinfo=create_startupinfo_no_window(),
                stdin=subprocess.DEVNULL,
            )

            with self.tasks_lock:
                task = self.tasks.get(url)
                if not task:
                    try:
                        proc.terminate()
                    except Exception:
                        pass
                    self.sem.release()
                    return
                task.process = proc

            if proc.stdout:
                for raw in iter(proc.stdout.readline, ""):
                    s = raw.strip()
                    if not s:
                        continue

                    # break if state changed
                    with self.tasks_lock:
                        task = self.tasks.get(url)
                        if not task or task.status != "downloading":
                            break

                    pg = parse_progress(s)
                    if pg:
                        with self.tasks_lock:
                            task = self.tasks.get(url)
                            if task:
                                task.progress = pg.pct / 100.0
                                task.size = pg.size
                                task.speed = pg.speed
                                task.eta = pg.eta
                                pct_value = pg.pct
                        # Throttled progress post
                        self._maybe_post_progress(url, pct_value)
                        continue

                    dest = parse_filename(s)
                    if dest:
                        with self.tasks_lock:
                            task = self.tasks.get(url)
                            if task:
                                task.filename = os.path.basename(dest)
                        self.post(("progress", url))
                        continue

            ret = proc.wait()
            with self.tasks_lock:
                task = self.tasks.get(url)
                if not task:
                    self.sem.release()
                    return

            if task.status in ("paused", "cancelled"):
                pass
            elif ret == 0:
                with self.tasks_lock:
                    task.status = "completed"
                    task.progress = 1.0
                self.post(("log", f"✅ Completed: {task.title or url}"))
                self.post(("progress", url))
                
                # Auto-delete if enabled
                if self.auto_delete_finished:
                    self.remove(url)
            else:
                # Handle failure and retries (Switch Strategy)
                with self.tasks_lock:
                    if task.retries < MAX_RETRIES:
                        task.retries += 1
                        task.status = "queued"
                        # Short delay before next strategy
                        delay = 1.0
                        next_strat = "Strategy B" if task.retries == 1 else "Strategy C"
                        self.post(("log", f"⚠️ {strategy_name} failed. Retrying with {next_strat} in {delay}s..."))
                        threading.Thread(target=lambda: (time.sleep(delay)), daemon=True).start()
                    else:
                        task.status = "failed"
                        self.post(("log", f"❌ Failed: {task.title or url} (All strategies exhausted)"))

        except Exception as e:
            # If we caught an exception (like aria2c missing), we treat it as a failure of the current strategy
            if "aria2c not found" in str(e):
                logging.warning(f"Strategy B skipped: {e}")
            else:
                logging.exception(f"Worker exception for {url}: {e}")
            
            with self.tasks_lock:
                task = self.tasks.get(url)
                if task:
                    if task.retries < MAX_RETRIES:
                        task.retries += 1
                        task.status = "queued"
                        delay = 1.0
                        self.post(("log", f"⚠️ Error in {strategy_name or 'download'}: {e}. Retrying..."))
                        threading.Thread(target=lambda: (time.sleep(delay)), daemon=True).start()
                    else:
                        task.status = "failed"
                        self.post(("log", f"❌ Failed: {task.title or url}"))
        finally:
            # Clean per-URL throttle state
            self._last_progress_post_ts.pop(url, None)
            self._last_progress_pct.pop(url, None)

            with self.tasks_lock:
                task = self.tasks.get(url)
                if task:
                    task.process = None
            self.sem.release()
            self.post(("refresh", None))


# ==========================================
# UI: APP
# ==========================================

BADGE_COLORS = {
    "queued": ("#1f6aa5", "#13466c"),
    "fetching-info": ("#9572ff", "#6e51d1"),
    "downloading": ("#22a15b", "#197a44"),
    "paused": ("#ffaa00", "#c17f00"),
    "cancelled": ("#888888", "#5e5e5e"),
    "completed": ("#2bb673", "#1d7e4f"),
    "failed": ("#ff4d4f", "#b8383a"),
    "info": ("#9572ff", "#6e51d1"),
}

MAX_EVENTS_PER_TICK = 60  # prevent UI starvation
UI_QUEUE_MAXSIZE = 2000   # prevent unbounded memory growth

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        setup_logging()
        self.title(APP_NAME)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        self.geometry("1120x760")
        self.minsize(900, 600)
        self.resizable(True, True)

        # DB
        self.db = Database(DB_FILE)

        # Event bridge from workers -> UI (bounded)
        self.ui_queue: "queue.Queue[tuple]" = queue.Queue(maxsize=UI_QUEUE_MAXSIZE)
        self.ctrl = DownloadController(self.ui_queue)

        # State
        self.task_widgets: Dict[str, Dict[str, Any]] = {}
        self.settings = {
            "last_folder": "",
            "max_concurrent": DEFAULT_MAX_CONCURRENT,
            "auto_delete": False,
        }

        # UI build
        self._build_ui()
        self._load_settings()
        self._load_queue()

        # Tick
        self.after(EVENT_POLL_MS, self._drain_events)
        self.after(AUTO_SAVE_SEC * 1000, self._autosave)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- UI construction ----------
    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)

        left = ctk.CTkFrame(self)
        left.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)

        right = ctk.CTkFrame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right.grid_propagate(True)

        # Input
        inp = ctk.CTkFrame(left)
        inp.pack(fill="x", pady=(0, 10), padx=10)
        ctk.CTkLabel(inp, text="📝 Paste or type links below:", font=("Segoe UI", 14)).pack(pady=5, anchor="w")
        self.link_box = ctk.CTkTextbox(inp, height=90, font=("Segoe UI", 12))
        self.link_box.pack(fill="x", expand=True, padx=5, pady=(0, 5))
        self.link_box.bind("<KeyRelease>", self._on_link_change)
        self._typing_job = None

        # Folder + controls
        top = ctk.CTkFrame(left)
        top.pack(fill="x", pady=5, padx=10)
        self.btn_browse = ctk.CTkButton(top, text="📁 Browse Destination", command=self._browse)
        self.btn_browse.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.btn_open = ctk.CTkButton(top, text="🗂 Open Folder", command=self._open_folder, state="disabled")
        self.btn_open.pack(side="left", fill="x", expand=True)

        # Secondary controls
        row = ctk.CTkFrame(left)
        row.pack(fill="x", pady=5, padx=10)
        ctk.CTkButton(row, text="⏭️ Skip Oldest Download", command=self._skip_oldest).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(row, text="🧹 Clear Finished", command=self._clear_finished).pack(side="left", fill="x", expand=True)

        # Auto-delete checkbox
        self.chk_auto_delete = ctk.CTkCheckBox(left, text="Auto-delete finished", command=self._toggle_auto_delete)
        self.chk_auto_delete.pack(pady=5, padx=10, anchor="w")

        ctk.CTkLabel(left, text="📦 Global Download Status", font=("Segoe UI", 14)).pack(pady=(10, 0), anchor="w", padx=10)
        self.console = ctk.CTkTextbox(left, state="disabled", wrap="word", font=("Consolas", 12))
        self.console.pack(fill="both", expand=True, pady=5, padx=10)

        # Right panel
        rc = ctk.CTkFrame(right)
        rc.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(rc, text="Max Simultaneous Downloads:", font=("Segoe UI", 12)).pack(side="left")
        self.max_var = ctk.StringVar(value=str(DEFAULT_MAX_CONCURRENT))
        ctk.CTkOptionMenu(rc, variable=self.max_var, values=[str(i) for i in range(1, 7)], command=self._set_max).pack(side="right")

        ctk.CTkLabel(right, text="Download Queue", font=("Segoe UI", 14, "bold")).pack(pady=(0, 5), padx=10, anchor="w")
        self.queue_panel = ctk.CTkScrollableFrame(right)
        self.queue_panel.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.queue_panel.bind("<Configure>", self._on_queue_resize)

    # ---------- Event bridge ----------
    def _drain_events(self):
        processed = 0
        try:
            while processed < MAX_EVENTS_PER_TICK:
                try:
                    evt, payload = self.ui_queue.get_nowait()
                except queue.Empty:
                    break

                if evt == "log":
                    self._log(payload)
                elif evt == "progress":
                    self._refresh_task(payload)
                elif evt == "refresh":
                    self._refresh_all()

                processed += 1
        finally:
            # Schedule next tick regardless of errors to keep UI responsive
            self.after(EVENT_POLL_MS, self._drain_events)

    # ---------- Helpers ----------
    def _log(self, s: str):
        try:
            self.console.configure(state="normal")
            self.console.insert("end", s + "\n")
            self.console.see("end")
            self.console.configure(state="disabled")
        except Exception as e:
            logging.error(f"Failed to log to console: {e}")

    def _on_link_change(self, _e):
        if self._typing_job:
            self.after_cancel(self._typing_job)
        self._typing_job = self.after(450, self._consume_links)

    def _consume_links(self):
        text = self.link_box.get("1.0", "end-1c")
        urls = extract_urls(text)
        if urls:
            self.ctrl.add_urls(urls)
            self.link_box.delete("1.0", "end")

    def _browse(self):
        folder = filedialog.askdirectory()
        if folder:
            self.settings["last_folder"] = folder
            self.ctrl.set_destination(folder)
            self._log(f"Destination: {folder}")
            self.btn_open.configure(state="normal")
            self._save_settings()

    def _open_folder(self):
        folder = self.settings.get("last_folder")
        if folder and os.path.isdir(folder):
            open_path(folder)
        else:
            self._log("Destination folder not set or does not exist.")

    def _set_max(self, value: str):
        try:
            n = int(value)
            self.settings["max_concurrent"] = n
            self.ctrl.set_max_concurrent(n)
            self._save_settings()
        except (ValueError, TypeError):
            self._log(f"Invalid max concurrent value: {value}")

    def _skip_oldest(self):
        with self.ctrl.tasks_lock:
            oldest_downloading = min(
                (t for t in self.ctrl.tasks.values() if t.status == "downloading"),
                key=lambda t: t.added_ts,
                default=None,
            )
        if oldest_downloading:
            self.ctrl.cancel(oldest_downloading.url)
        else:
            self._log("No active downloads to skip.")

    def _clear_finished(self):
        self.ctrl.clear_finished()

    def _toggle_auto_delete(self):
        val = self.chk_auto_delete.get() == 1
        self.settings["auto_delete"] = val
        self.ctrl.set_auto_delete(val)
        self._save_settings()

    # ---------- Task UI ----------
    def _on_queue_resize(self, _e):
        # update wraplengths when panel width changes
        for w in self.task_widgets.values():
            frame = w["frame"]
            try:
                width = max(200, frame.winfo_width() - 40)
            except Exception:
                width = 320
            w["title"].configure(wraplength=width)
            w["info"].configure(wraplength=width)

    def _refresh_all(self):
        with self.ctrl.tasks_lock:
            tasks_copy = list(self.ctrl.tasks.values())

        # Remove gone
        task_urls = {t.url for t in tasks_copy}
        for url in list(self.task_widgets.keys()):
            if url not in task_urls:
                if widget := self.task_widgets.pop(url, None):
                    widget["frame"].destroy()

        # Add/update
        for task in tasks_copy:
            if task.url not in self.task_widgets:
                self._add_task_widget(task)
            self._update_task_widget(task)

        # Empty-state label
        if not self.task_widgets and not any(
            isinstance(w, ctk.CTkLabel) and w.cget("text") == "Queue is empty"
            for w in self.queue_panel.winfo_children()
        ):
            ctk.CTkLabel(self.queue_panel, text="Queue is empty", text_color="gray").pack()
        elif self.task_widgets:
            for w in self.queue_panel.winfo_children():
                if isinstance(w, ctk.CTkLabel) and w.cget("text") == "Queue is empty":
                    w.destroy()

    def _add_task_widget(self, task: Task):
        frame = ctk.CTkFrame(self.queue_panel)
        frame.pack(fill="x", padx=5, pady=4)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(6, 0))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        lbl_title = ctk.CTkLabel(header, text="", anchor="w", justify="left", wraplength=360)
        lbl_title.grid(row=0, column=0, sticky="ew")
        lbl_info = ctk.CTkLabel(header, text="", anchor="w", text_color="gray", justify="left", wraplength=360)
        lbl_info.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        badge = ctk.CTkLabel(header, text="", width=90, corner_radius=8, padx=8, pady=6)
        badge.grid(row=0, column=1, rowspan=2, sticky="e", padx=(8, 0))

        pb_var = ctk.DoubleVar(value=task.progress)
        pb = ctk.CTkProgressBar(frame, variable=pb_var)
        pb.pack(fill="x", padx=8, pady=6)

        buttons = ctk.CTkFrame(frame, fg_color="transparent")
        buttons.pack(fill="x", padx=8, pady=(0, 8))

        # Bindings for quick open
        frame.bind("<Double-Button-1>", lambda _e, u=task.url: self._open_task(u))
        header.bind("<Double-Button-1>", lambda _e, u=task.url: self._open_task(u))
        lbl_title.bind("<Double-Button-1>", lambda _e, u=task.url: self._open_task(u))
        lbl_info.bind("<Double-Button-1>", lambda _e, u=task.url: self._open_task(u))

        # Context menu (right click)
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Open File", command=lambda u=task.url: self._open_task(u))
        menu.add_command(label="Open Folder", command=lambda u=task.url: self._open_task_folder(u))
        menu.add_separator()
        menu.add_command(label="Copy URL", command=lambda u=task.url: self._copy_url(u))
        menu.add_separator()
        menu.add_command(label="Remove", command=lambda u=task.url: self.ctrl.remove(u))

        def show_menu(event, u=task.url, m=menu):
            try:
                m.tk_popup(event.x_root, event.y_root)
            finally:
                m.grab_release()

        frame.bind("<Button-3>", show_menu)          # Windows/Linux
        frame.bind("<Button-2>", show_menu)          # macOS (sometimes)
        header.bind("<Button-3>", show_menu)
        lbl_title.bind("<Button-3>", show_menu)
        lbl_info.bind("<Button-3>", show_menu)

        self.task_widgets[task.url] = {
            "frame": frame,
            "title": lbl_title,
            "info": lbl_info,
            "badge": badge,
            "pb_var": pb_var,
            "buttons": buttons,
        }

    def _update_task_widget(self, task: Task):
        widget = self.task_widgets.get(task.url)
        if not widget:
            return

        display_title = task.filename or task.title or task.url
        widget["title"].configure(text=display_title)

        info_parts = [
            f"Size: {task.size or 'N/A'}",
            f"Res: {f'{task.width}x{task.height}' if task.width and task.height else 'N/A'}",
        ]
        if task.speed:
            info_parts.append(f"Speed: {task.speed}")
        if task.eta:
            info_parts.append(f"ETA: {task.eta}")
        if task.strategy:
            info_parts.append(f"[{task.strategy}]")
        widget["info"].configure(text=" | ".join(info_parts))

        # Status badge
        status = task.status
        fg, _hover = BADGE_COLORS.get(status, ("#666666", "#4a4a4a"))
        widget["badge"].configure(text=status.upper(), fg_color=fg, text_color="white")

        widget["pb_var"].set(task.progress)
        self._render_buttons(task)

    def _render_buttons(self, task: Task):
        widget = self.task_widgets.get(task.url)
        if not widget:
            return
        for btn in widget["buttons"].winfo_children():
            btn.destroy()

        if task.status == "downloading":
            ctk.CTkButton(widget["buttons"], text="⏸ Pause", command=lambda u=task.url: self.ctrl.pause(u)).pack(
                side="left", fill="x", expand=True, padx=(0, 5)
            )
        elif task.status == "paused":
            ctk.CTkButton(widget["buttons"], text="▶️ Resume", command=lambda u=task.url: self.ctrl.resume(u)).pack(
                side="left", fill="x", expand=True, padx=(0, 5)
            )

        if task.status in ("downloading", "paused", "queued", "fetching-info", "info"):
            ctk.CTkButton(
                widget["buttons"],
                text="⏹️ Cancel",
                fg_color="red",
                hover_color="darkred",
                command=lambda u=task.url: self.ctrl.cancel(u),
            ).pack(side="left", fill="x", expand=True, padx=(0, 5))

        right_side = widget["buttons"]
        if task.status == "failed":
            ctk.CTkButton(right_side, text="🔁 Retry", command=lambda u=task.url: self.ctrl.retry(u)).pack(side="right")
        elif task.status in ("cancelled", "completed"):
            ctk.CTkButton(right_side, text="🗑 Remove", command=lambda u=task.url: self.ctrl.remove(u)).pack(side="right")

    def _refresh_task(self, url: str):
        with self.ctrl.tasks_lock:
            task = self.ctrl.tasks.get(url)
        if task:
            self._update_task_widget(task)

    def _open_task(self, url: str):
        with self.ctrl.tasks_lock:
            task = self.ctrl.tasks.get(url)
            if not task:
                return
            folder = task.dest or self.settings.get("last_folder") or ""
            filename = task.filename

        if folder and filename:
            full = os.path.join(folder, filename)
            if os.path.isfile(full):
                open_path(full)
                return
        if folder and os.path.isdir(folder):
            open_path(folder)

    def _open_task_folder(self, url: str):
        with self.ctrl.tasks_lock:
            task = self.ctrl.tasks.get(url)
            folder = (task.dest if task else None) or self.settings.get("last_folder")
        if folder and os.path.isdir(folder):
            open_path(folder)

    def _copy_url(self, url: str):
        try:
            self.clipboard_clear()
            self.clipboard_append(url)
        except Exception:
            pass

    # ---------- persistence via SQLite ----------
    def _save_settings(self):
        try:
            self.db.set_setting("last_folder", self.settings.get("last_folder", ""))
            self.db.set_setting("max_concurrent", int(self.settings.get("max_concurrent", DEFAULT_MAX_CONCURRENT)))
            self.db.set_setting("auto_delete", 1 if self.settings.get("auto_delete") else 0)
        except Exception as e:
            logging.exception(f"Save settings failed: {e}")

    def _load_settings(self):
        try:
            last_folder = self.db.get_setting("last_folder", "")
            max_concurrent = self.db.get_setting("max_concurrent", DEFAULT_MAX_CONCURRENT)
            if isinstance(last_folder, str):
                self.settings["last_folder"] = last_folder
            if isinstance(max_concurrent, int):
                self.settings["max_concurrent"] = max_concurrent
            
            # Load auto_delete setting
            auto_delete = self.db.get_setting("auto_delete", 0)
            self.settings["auto_delete"] = bool(auto_delete)

            folder = self.settings.get("last_folder")
            if folder and os.path.isdir(folder):
                self.ctrl.set_destination(folder)
                self.btn_open.configure(state="normal")
                self._log(f"Restored destination: {folder}")

            mc = self.settings.get("max_concurrent")
            if mc:
                # self.max_var.set(str(mc)) # max_var might not exist if slider removed/renamed, check usage
                self.ctrl.set_max_concurrent(int(mc))
            
            # Apply auto_delete setting to UI and Controller
            if self.settings["auto_delete"]:
                self.chk_auto_delete.select()
            else:
                self.chk_auto_delete.deselect()
            self.ctrl.set_auto_delete(self.settings["auto_delete"])

        except Exception as e:
            logging.exception(f"Load settings failed: {e}")

    def _autosave(self):
        try:
            with self.ctrl.tasks_lock:
                snapshot = list(self.ctrl.tasks.values())
            self.db.save_tasks(snapshot)
        except Exception as e:
            logging.exception(f"Autosave queue failed: {e}")
        finally:
            self.after(AUTO_SAVE_SEC * 1000, self._autosave)

    def _load_queue(self):
        try:
            tasks = self.db.load_tasks()
            with self.ctrl.tasks_lock:
                for t in tasks:
                    if t.status not in ("completed", "cancelled"):
                        if t.status == "downloading":
                            t.status = "queued"
                        self.ctrl.tasks[t.url] = t
            self._refresh_all()
        except Exception as e:
            logging.exception(f"Load queue failed: {e}")
            self._log("Could not load previous queue.")

    # ---------- shutdown ----------
    def _on_close(self):
        self.ctrl.stop()
        # manual autosave one more time
        try:
            with self.ctrl.tasks_lock:
                snapshot = list(self.ctrl.tasks.values())
            self.db.save_tasks(snapshot)
        except Exception:
            pass
        try:
            self.db.close()
        except Exception:
            pass
        self.destroy()


# ==========================================
# MAIN
# ==========================================

def main():
    setup_logging()
    if not which_yt_dlp():
        logging.critical("yt-dlp not found on PATH. Please install it.")
        sys.exit(1)
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
