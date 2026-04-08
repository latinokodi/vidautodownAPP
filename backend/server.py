"""
VidAutoDown Backend - aiohttp server for yt-dlp operations.
"""

import asyncio
import json
import logging
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from enum import Enum
from aiohttp import web

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


WIN32 = sys.platform == "win32"
DB_PATH = Path(__file__).parent.parent / "vidautodown.db"
DEFAULT_OUTPUT_TPL = "%(title).100s [%(width)sx%(height)s] [%(id)s].%(ext)s"

PROGRESS_RE = re.compile(
    r"\[download\]\s+(?P<pct>\d+(?:\.\d+)?)%\s+of\s+(?P<size>~?\s*[\d\.]+\s*[KMGTP]?i?B)"
    r"(?:\s+at\s+(?P<speed>[\d\.\s]+[KMGTP]?i?B/s))?"
    r"(?:\s+ETA\s+(?P<eta>[\d:]+))?",
    re.IGNORECASE,
)
FILENAME_RE = re.compile(
    r"(?:\[download\]\s+Destination:\s+(?P<dest>.*))|(?:\[Merger\]\s+Merging formats into\s+\"(?P<merge>.*)\")"
)
URL_RE = re.compile(r"(?P<url>https?://[^\s<>'\"`]+)", re.IGNORECASE)

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def get_base_yt_dlp_args() -> List[str]:
    """Returns standard robust arguments for all yt-dlp calls."""
    return [
        "--no-check-certificates",
        "--geo-bypass",
        "--user-agent",
        DEFAULT_USER_AGENT,
        "--prefer-free-formats",
        "--no-part",
        "--no-mtime",
    ]


def create_startupinfo():
    if not WIN32:
        return None
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    return si


def create_flags():
    return subprocess.CREATE_NO_WINDOW if WIN32 else 0


def which_yt_dlp():
    # Check venv first
    venv_bin = Path(__file__).parent.parent / "venv" / "Scripts" / "yt-dlp.exe"
    if venv_bin.exists():
        return str(venv_bin)
    return shutil.which("yt-dlp")


def extract_urls(text: str) -> List[str]:
    if not text:
        return []
    return list(dict.fromkeys(URL_RE.findall(text.strip())))


def normalize_url(url: str) -> str:
    if not url:
        return url
    u = url.strip().split("#", 1)[0]
    if u.endswith("/") and "://" in u:
        scheme, rest = u.split("://", 1)
        if "/" in rest and not rest.endswith("://"):
            u = u.rstrip("/")
    return u


class TaskStatus(str, Enum):
    QUEUED = "queued"
    FETCHING_INFO = "fetching-info"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    MERGING = "merging"
    INFO = "info"


@dataclass
class Task:
    url: str
    status: TaskStatus = TaskStatus.QUEUED
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
    strategy: Optional[str] = None

    def to_dict(self):
        d = asdict(self)
        d["status"] = self.status.value
        return d


SCHEMA = """
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
    dest TEXT,
    strategy TEXT
);
"""


class Database:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, timeout=10, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.lock = threading.Lock()
        self._init_schema()

    def _init_schema(self):
        with self.lock:
            with self.conn:
                self.conn.executescript(SCHEMA)

    def get_setting(self, key: str, default=None):
        with self.lock:
            cur = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cur.fetchone()
        if not row:
            return default
        try:
            return json.loads(row[0])
        except:
            return default

    def set_setting(self, key: str, value):
        payload = json.dumps(value)
        with self.lock:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO settings(key, value) VALUES(?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, payload),
                )

    def save_tasks(self, tasks: List[Task]):
        items = []
        for t in tasks:
            items.append(
                (
                    t.url,
                    t.status.value,
                    t.progress,
                    t.title,
                    t.filename,
                    t.size,
                    t.speed,
                    t.eta,
                    t.retries,
                    t.added_ts,
                    t.vid,
                    t.width,
                    t.height,
                    t.dest,
                    t.strategy,
                )
            )
        with self.lock:
            with self.conn:
                self.conn.execute("DELETE FROM tasks;")
                self.conn.executemany(
                    "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", items
                )

    def load_tasks(self) -> List[Task]:
        with self.lock:
            cur = self.conn.execute(
                "SELECT url, status, progress, title, filename, size, speed, eta, retries, added_ts, vid, width, height, dest FROM tasks ORDER BY added_ts"
            )
            rows = cur.fetchall()
        return [
            Task(
                url=r[0],
                status=TaskStatus(r[1])
                if r[1] in [s.value for s in TaskStatus]
                else TaskStatus.QUEUED,
                progress=r[2] or 0,
                title=r[3] or "Fetching info...",
                filename=r[4],
                size=r[5],
                speed=r[6],
                eta=r[7],
                retries=r[8] or 0,
                added_ts=r[9] or time.time(),
                vid=r[10],
                width=r[11],
                height=r[12],
                dest=r[13],
                strategy=r[14] if len(r) > 14 else None,
            )
            for r in rows
        ]

    def close(self):
        try:
            self.conn.close()
        except:
            pass


class CrawlerService:
    def __init__(self, broadcast):
        self.broadcast = broadcast
        self._active_process: Optional[subprocess.Popen] = None
        self._cancel_event = threading.Event()
        self._lock = threading.Lock()

    def crawl(self, page_url: str):
        def worker():
            yt = which_yt_dlp()
            if not yt:
                self.broadcast("crawl_error", "yt-dlp not found")
                return

            self.broadcast("crawl_start", {"url": page_url})

            # Use robust base arguments
            cmd = (
                [yt]
                + get_base_yt_dlp_args()
                + ["--flat-playlist", "--dump-json", "--no-warnings", page_url]
            )

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=create_flags(),
                    startupinfo=create_startupinfo(),
                )
                with self._lock:
                    self._active_process = proc

                urls_found = []
                for line in iter(proc.stdout.readline, ""):
                    if self._cancel_event.is_set():
                        proc.terminate()
                        self.broadcast("crawl_cancelled", {})
                        return

                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        url = data.get("url") or data.get("webpage_url")
                        title = data.get("title", "Unknown")
                        if url:
                            urls_found.append({"url": url, "title": title})
                            self.broadcast(
                                "crawl_progress",
                                {"count": len(urls_found), "latest": title},
                            )
                    except:
                        continue

                proc.wait()
                if not self._cancel_event.is_set():
                    self.broadcast("crawl_complete", {"urls": urls_found})
            except Exception as e:
                if not self._cancel_event.is_set():
                    self.broadcast("crawl_error", str(e))
            finally:
                with self._lock:
                    self._active_process = None

        self._cancel_event.clear()
        threading.Thread(target=worker, daemon=True).start()

    def cancel(self):
        self._cancel_event.set()
        with self._lock:
            if self._active_process:
                try:
                    self._active_process.terminate()
                except:
                    pass
                self._active_process = None


class DownloadController:
    def __init__(self, db: Database, broadcast):
        self.db = db
        self.broadcast = broadcast
        self.tasks: Dict[str, Task] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.lock = threading.Lock()
        self.sem = threading.Semaphore(3)
        self.max_concurrent = 3
        self.destination = str(Path.home() / "Downloads")
        self.stop_event = threading.Event()
        self._progress_ts: Dict[str, float] = {}
        self.auto_delete = False

        self._load_settings()
        self._load_tasks()
        self.crawler = CrawlerService(broadcast)
        self._start_manager()

    def _load_settings(self):
        self.destination = self.db.get_setting("destination", self.destination)
        self.max_concurrent = int(
            self.db.get_setting("max_concurrent", self.max_concurrent)
        )
        self.auto_delete = bool(self.db.get_setting("auto_delete", self.auto_delete))
        self.sem = threading.Semaphore(self.max_concurrent)
        logger.info(
            f"Loaded settings: dest={self.destination}, max={self.max_concurrent}, auto_delete={self.auto_delete}"
        )

    def _load_tasks(self):
        tasks = self.db.load_tasks()
        with self.lock:
            for t in tasks:
                if t.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
                    # Recovery logic: anything that was in progress becomes queued
                    if t.status in (
                        TaskStatus.DOWNLOADING,
                        TaskStatus.FETCHING_INFO,
                        TaskStatus.MERGING,
                    ):
                        t.status = TaskStatus.QUEUED
                        t.speed = "Recovered"
                    self.tasks[t.url] = t

    def _start_manager(self):
        def manager_loop():
            while not self.stop_event.is_set():
                try:
                    with self.lock:
                        for t in list(self.tasks.values()):
                            if t.status == TaskStatus.INFO:
                                t.status = TaskStatus.FETCHING_INFO
                                threading.Thread(
                                    target=self._fetch_info, args=(t.url,), daemon=True
                                ).start()
                            elif t.status == TaskStatus.QUEUED:
                                if self.sem.acquire(blocking=False):
                                    t.status = TaskStatus.DOWNLOADING
                                    threading.Thread(
                                        target=self._download,
                                        args=(t.url,),
                                        daemon=True,
                                    ).start()
                except Exception as e:
                    logger.error(f"Manager error: {e}")
                time.sleep(0.3)

        threading.Thread(target=manager_loop, daemon=True).start()

    def _fetch_info(self, url: str):
        logger.info(f"Fetching info for: {url}")
        yt = which_yt_dlp()
        if not yt:
            yt = which_yt_dlp()
        if not yt:
            self._mark_failed(url, "yt-dlp not found")
            return

        cmd = [yt] + get_base_yt_dlp_args() + ["--dump-json", "--no-warnings", url]
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                creationflags=create_flags(),
                startupinfo=create_startupinfo(),
            )
            if res.returncode != 0:
                # If it still fails with PhantomJS, try a cache clear and one retry
                if "PhantomJS not found" in (res.stderr or ""):
                    logger.warning(
                        "PhantomJS error detected. Clearing yt-dlp cache and retrying..."
                    )
                    subprocess.run(
                        [yt, "--rm-cache-dir"],
                        capture_output=True,
                        creationflags=create_flags(),
                        startupinfo=create_startupinfo(),
                    )
                    # Minimal delay
                    time.sleep(1)
                    res = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        creationflags=create_flags(),
                        startupinfo=create_startupinfo(),
                    )

                if res.returncode != 0:
                    raise Exception(res.stderr or "Unknown error")

            info = json.loads(res.stdout)
            with self.lock:
                task = self.tasks.get(url)
                if task:
                    task.title = info.get("title", "Unknown")[:80]
                    task.vid = info.get("id")
                    task.width = info.get("width")
                    task.height = info.get("height")

                    # Duplicate detection by Video ID
                    if task.vid:
                        for other_url, other in list(self.tasks.items()):
                            if other_url == url:
                                continue
                            if other.vid == task.vid:
                                # Keep the one that already has more progress or is older
                                logger.info(
                                    f"Duplicate video ID detected: {task.vid}. Cancelling duplicate."
                                )
                                task.status = TaskStatus.CANCELLED
                                task.title = f"[DUPLICATE] {task.title}"
                                break

                    if task.status != TaskStatus.CANCELLED:
                        task.status = TaskStatus.QUEUED
            self._broadcast_refresh()
        except Exception as e:
            self._mark_failed(url, str(e)[:100])

    def _download(self, url: str):
        yt = which_yt_dlp()
        if not yt:
            self._mark_failed(url, "yt-dlp not found")
            self.sem.release()
            return

        with self.lock:
            task = self.tasks.get(url)
            if not task:
                self.sem.release()
                return
            folder = task.dest or self.destination
            retries = task.retries

        os.makedirs(folder, exist_ok=True)

        cmd = (
            [
                yt,
                "--newline",
                "--progress",
            ]
            + get_base_yt_dlp_args()
            + [
                "-S",
                "res,ext:mp4:m4a",
                "--recode",
                "mp4",
                "-P",
                folder,
                "-o",
                DEFAULT_OUTPUT_TPL,
                "--no-warnings",
                "--no-overwrites",
                "--continue",
                "--retries",
                "10",
                "--fragment-retries",
                "10",
                url,
            ]
        )

        # Strategy logic
        if retries == 0:
            task.strategy = "Strategy A (Fast)"
            cmd.extend(["--concurrent-fragments", "4"])
        elif retries == 1:
            task.strategy = "Strategy B (Safe)"
            # Strategy B: default flags are already safe-ish
        else:
            task.strategy = "Strategy C (Fallback)"
            # Strategy C: maybe avoid some options
            if "--recode" in cmd:
                idx = cmd.index("--recode")
                cmd.pop(idx + 1)
                cmd.pop(idx)

        logger.info(f"Starting {task.strategy} for: {url}")
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=create_flags(),
                startupinfo=create_startupinfo(),
            )

            with self.lock:
                self.processes[url] = proc

            for line in iter(proc.stdout.readline, ""):
                if not line:
                    continue
                with self.lock:
                    if url not in self.tasks or self.tasks[url].status != "downloading":
                        proc.terminate()
                        break

                m = PROGRESS_RE.search(line)
                if m:
                    pct = float(m.group("pct"))
                    with self.lock:
                        task = self.tasks.get(url)
                        if task:
                            task.progress = pct / 100.0
                            task.size = (m.group("size") or "").replace("~", "").strip()
                            task.speed = (m.group("speed") or "").strip()
                            task.eta = (m.group("eta") or "").strip()
                    self._maybe_broadcast_progress(url, pct)

                elif "[Merger]" in line:
                    with self.lock:
                        task = self.tasks.get(url)
                        if task:
                            task.status = "merging"
                            task.speed = "Processing"
                            if "into " in line:
                                parts = line.split("into ")
                                if len(parts) > 1:
                                    task.filename = os.path.basename(
                                        parts[1].strip().strip('"')
                                    )
                    self._broadcast_refresh()

                elif "Destination: " in line:
                    fname = line.split("Destination: ")[-1].strip()
                    with self.lock:
                        task = self.tasks.get(url)
                        if task:
                            task.filename = os.path.basename(fname)

                elif "has already been downloaded" in line:
                    m = re.search(
                        r"\[download\] (.+?) has already been downloaded", line
                    )
                    if m:
                        with self.lock:
                            task = self.tasks.get(url)
                            if task:
                                task.filename = m.group(1).strip()

            ret = proc.wait()
            with self.lock:
                self.processes.pop(url, None)
                task = self.tasks.get(url)
                if task:
                    if ret == 0:
                        task.status = TaskStatus.COMPLETED
                        task.progress = 1.0
                        if self.auto_delete:
                            del self.tasks[url]
                    elif task.status == TaskStatus.DOWNLOADING:
                        if task.retries < 2:
                            task.retries += 1
                            task.status = TaskStatus.QUEUED
                        else:
                            task.status = TaskStatus.FAILED

            self._broadcast_refresh()

        except Exception as e:
            logger.error(f"Download error for {url}: {e}")
            self._mark_failed(url, str(e)[:50])
        finally:
            self.sem.release()

    def _maybe_broadcast_progress(self, url: str, pct: float):
        now = time.monotonic()
        last = self._progress_ts.get(url, 0)
        if now - last > 0.3:
            self._progress_ts[url] = now
            with self.lock:
                task = self.tasks.get(url)
                if task:
                    self.broadcast("progress", task.to_dict())

    def _mark_failed(self, url: str, error: str):
        with self.lock:
            task = self.tasks.get(url)
            if task:
                task.status = TaskStatus.FAILED
                task.title = f"Error: {error}"
        self._broadcast_refresh()

    def _broadcast_refresh(self):
        with self.lock:
            data = [t.to_dict() for t in self.tasks.values()]
        self.broadcast("refresh", data)

    def _broadcast_settings(self):
        settings = {
            "destination": self.destination,
            "max_concurrent": self.max_concurrent,
            "auto_delete": self.auto_delete,
            "yt_dlp_available": bool(which_yt_dlp()),
        }
        self.broadcast("settings", settings)

    def add_urls(self, text: str):
        urls = extract_urls(text)
        added = 0
        with self.lock:
            for u in urls:
                norm = normalize_url(u)
                if norm and norm not in self.tasks:
                    self.tasks[norm] = Task(url=norm, status=TaskStatus.INFO)
                    added += 1
        if added:
            self._broadcast_refresh()
        return {"added": added}

    def pause(self, url: str):
        with self.lock:
            task = self.tasks.get(url)
            proc = self.processes.get(url)
            if task and task.status == TaskStatus.DOWNLOADING:
                if proc:
                    proc.terminate()
                task.status = TaskStatus.PAUSED
                task.speed = None
                task.eta = None
        self._broadcast_refresh()

    def resume(self, url: str):
        with self.lock:
            task = self.tasks.get(url)
            if task and task.status == TaskStatus.PAUSED:
                task.status = TaskStatus.QUEUED
                task.progress = 0.0
        self._broadcast_refresh()

    def cancel(self, url: str):
        with self.lock:
            task = self.tasks.get(url)
            proc = self.processes.get(url)
            if proc:
                proc.terminate()
            if task:
                task.status = TaskStatus.CANCELLED
        self._broadcast_refresh()

    def remove(self, url: str):
        with self.lock:
            self.tasks.pop(url, None)
            self.processes.pop(url, None)
        self._broadcast_refresh()

    def retry(self, url: str):
        with self.lock:
            task = self.tasks.get(url)
            if task and task.status == TaskStatus.FAILED:
                task.status = TaskStatus.QUEUED
                task.retries = 0
                task.progress = 0.0
        self._broadcast_refresh()

    def clear_finished(self):
        with self.lock:
            self.tasks = {
                k: v
                for k, v in self.tasks.items()
                if v.status
                not in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
            }
        self._broadcast_refresh()

    def set_destination(self, path: str):
        with self.lock:
            self.destination = path
        self.db.set_setting("destination", path)
        self._broadcast_settings()
        self._broadcast_refresh()

    def set_max_concurrent(self, n: int):
        with self.lock:
            self.max_concurrent = max(1, min(8, n))
            # Note: We don't replace the semaphore object here to avoid race conditions.
            # The manager loop pulls from the queue based on the current count.
        self.db.set_setting("max_concurrent", self.max_concurrent)
        self._broadcast_settings()
        self._broadcast_refresh()

    def set_auto_delete(self, value):
        with self.lock:
            self.auto_delete = bool(value)
        self.db.set_setting("auto_delete", 1 if self.auto_delete else 0)
        logger.info(f"Auto-delete set to: {self.auto_delete}")
        self._broadcast_settings()
        self._broadcast_refresh()

    def get_stats(self):
        with self.lock:
            completed = [
                t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED
            ]
            return {
                "completed": len(completed),
                "active": len(
                    [
                        t
                        for t in self.tasks.values()
                        if t.status == TaskStatus.DOWNLOADING
                    ]
                ),
                "queued": len(
                    [t for t in self.tasks.values() if t.status == TaskStatus.QUEUED]
                ),
            }

    def save(self):
        with self.lock:
            self.db.save_tasks(list(self.tasks.values()))

    def stop(self):
        self.stop_event.set()
        with self.lock:
            for proc in self.processes.values():
                proc.terminate()
        self.save()


db = Database(str(DB_PATH))
clients = set()


main_loop: Optional[asyncio.AbstractEventLoop] = None


async def broadcast_handler(msg_type: str, data):
    msg = json.dumps({"type": msg_type, "data": data})
    for ws in list(clients):
        try:
            await ws.send_str(msg)
        except:
            clients.discard(ws)


def bridge_broadcast(msg_type: str, data):
    if main_loop and main_loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast_handler(msg_type, data), main_loop)
    else:
        # Fallback for during startup/shutdown
        logger.debug(f"Broadcast {msg_type} queued or ignored (no loop)")


controller = DownloadController(db, bridge_broadcast)


async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    clients.add(ws)

    await ws.send_str(
        json.dumps(
            {
                "type": "refresh",
                "data": [t.to_dict() for t in controller.tasks.values()],
            }
        )
    )

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)
                cmd = data.get("command")

                if cmd == "add":
                    result = controller.add_urls(data.get("text", ""))
                    await ws.send_str(
                        json.dumps({"type": "result", "command": "add", "data": result})
                    )
                elif cmd == "pause":
                    controller.pause(data.get("url"))
                elif cmd == "resume":
                    controller.resume(data.get("url"))
                elif cmd == "cancel":
                    controller.cancel(data.get("url"))
                elif cmd == "remove":
                    controller.remove(data.get("url"))
                elif cmd == "retry":
                    controller.retry(data.get("url"))
                elif cmd == "clear_finished":
                    controller.clear_finished()
                elif cmd == "set_destination":
                    controller.set_destination(data.get("path"))
                elif cmd == "set_max_concurrent":
                    controller.set_max_concurrent(int(data.get("value", 3)))
                elif cmd == "set_auto_delete":
                    controller.set_auto_delete(bool(data.get("value")))
                elif cmd == "crawl":
                    controller.crawler.crawl(data.get("url"))
                elif cmd == "cancel_crawl":
                    controller.crawler.cancel()
                elif cmd == "get_settings":
                    settings = {
                        "destination": controller.destination,
                        "max_concurrent": controller.max_concurrent,
                        "auto_delete": controller.auto_delete,
                        "yt_dlp_available": bool(which_yt_dlp()),
                    }
                    await ws.send_str(
                        json.dumps({"type": "settings", "data": settings})
                    )
                elif cmd == "get_stats":
                    stats = controller.get_stats()
                    await ws.send_str(json.dumps({"type": "stats", "data": stats}))

            except Exception as e:
                logger.error(f"WS message error: {e}")

    clients.discard(ws)
    return ws


async def http_add_urls(request):
    data = await request.json()
    result = controller.add_urls(data.get("text", ""))
    return web.json_response(result)


async def http_get_tasks(request):
    with controller.lock:
        tasks = [t.to_dict() for t in controller.tasks.values()]
    return web.json_response(tasks)


async def http_get_settings(request):
    return web.json_response(
        {
            "destination": controller.destination,
            "max_concurrent": controller.max_concurrent,
            "auto_delete": controller.auto_delete,
            "yt_dlp_available": bool(which_yt_dlp()),
        }
    )


async def http_post_settings(request):
    data = await request.json()
    if "destination" in data:
        controller.set_destination(data["destination"])
    if "max_concurrent" in data:
        controller.set_max_concurrent(int(data["max_concurrent"]))
    if "auto_delete" in data:
        controller.set_auto_delete(bool(data["auto_delete"]))
    return web.json_response({"status": "ok"})


def create_app():
    app = web.Application()
    app.router.add_get("/ws", ws_handler)
    app.router.add_post("/api/add", http_add_urls)
    app.router.add_get("/api/tasks", http_get_tasks)
    app.router.add_get("/api/settings", http_get_settings)
    app.router.add_post("/api/settings", http_post_settings)

    cors_middleware = lambda app: app
    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    app = create_app()
    logger.info(f"Starting backend server on port {port}")

    # Track the main loop for thread-safe operations
    main_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(main_loop)

    try:
        web.run_app(app, host="127.0.0.1", port=port, print=None, loop=main_loop)
    finally:
        controller.stop()
        db.close()
