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

import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


WIN32 = sys.platform == "win32"
DB_PATH = Path(__file__).parent.parent / "vidautodown.db"
DEFAULT_OUTPUT_TPL = "%(uploader|playlist_title|creator|Unknown)s - %(title).150s.%(ext)s"

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


def get_subprocess_env() -> Dict[str, str]:
    env = os.environ.copy()
    venv_scripts = str(Path(__file__).parent.parent / "venv" / "Scripts")
    current_path = env.get("PATH", "")
    if venv_scripts not in current_path:
        env["PATH"] = venv_scripts + os.pathsep + current_path
    return env


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

    # Normalize xHamster pornstar URLs to creators URLs for yt-dlp compatibility
    import urllib.parse
    try:
        parsed = urllib.parse.urlparse(u)
        if parsed.netloc and "xhamster" in parsed.netloc.lower():
            path_parts = parsed.path.strip("/").split("/")
            if path_parts and path_parts[0].lower() == "pornstars":
                path_parts[0] = "creators"
                new_path = "/" + "/".join(path_parts)
                u = urllib.parse.urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    new_path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment
                ))
    except Exception:
        pass

    return u


def encode_base36(num):
    if num == 0:
        return '0'
    digits = '0123456789abcdefghijklmnopqrstuvwxyz'
    res = []
    while num:
        num, rem = divmod(num, 36)
        res.append(digits[rem])
    return ''.join(reversed(res))


def calc_hash(vid_hash):
    parts = []
    for i in range(0, 32, 8):
        chunk = vid_hash[i:i+8]
        val = int(chunk, 16)
        parts.append(encode_base36(val))
    return ''.join(parts)


def resolve_eporner_video(url: str):
    """
    Given an Eporner video URL, resolves the direct MP4 URL and metadata.
    Returns: (title, direct_url, size_bytes) or (None, None, None)
    """
    video_id_match = re.search(r'/(?:video|hd-porn|embed)-([a-zA-Z0-9]+)', url)
    if not video_id_match:
        video_id_match = re.search(r'/embed/([a-zA-Z0-9]+)', url)
    if not video_id_match:
        video_id_match = re.search(r'eporner\.com/(?:(?:hd-porn|embed)/|video-)(?P<id>\w+)', url)
        
    if not video_id_match:
        logger.error(f"[Eporner Extractor] Could not parse video ID from URL: {url}")
        return None, None, None
        
    video_id = video_id_match.group(1) if 'id' not in video_id_match.groupdict() else video_id_match.group('id')
    
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc or "www.eporner.com"
    
    import cloudscraper
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    try:
        res = scraper.get(url, timeout=15)
        if res.status_code != 200:
            logger.error(f"[Eporner Extractor] Failed to get video page: status {res.status_code}")
            return None, None, None
            
        title_match = re.search(r'<title>(.+?) - EPORNER', res.text, re.IGNORECASE)
        title = title_match.group(1) if title_match else "Eporner Video"
        
        hash_match = re.search(r'hash\s*[:=]\s*["\']([\da-f]{32})', res.text)
        if not hash_match:
            logger.error(f"[Eporner Extractor] Could not extract hash from page")
            return None, None, None
            
        vid_hash = hash_match.group(1)
        query_hash = calc_hash(vid_hash)
        
        xhr_url = f"https://{domain}/xhr/video/{video_id}"
        params = {
            'hash': query_hash,
            'device': 'generic',
            'domain': domain,
            'fallback': 'false'
        }
        
        xhr_res = scraper.get(xhr_url, params=params, timeout=15)
        if xhr_res.status_code != 200:
            logger.error(f"[Eporner Extractor] Failed to fetch XHR: status {xhr_res.status_code}")
            return None, None, None
            
        data = xhr_res.json()
        sources = data.get("sources", {})
        
        mp4_formats = sources.get("mp4", {})
        if not mp4_formats or not isinstance(mp4_formats, dict):
            for k, v in sources.items():
                if isinstance(v, dict) and k != 'hls':
                    mp4_formats = v
                    break
                    
        if not mp4_formats:
            logger.error(f"[Eporner Extractor] No mp4 format sources found")
            return None, None, None
            
        best_src = None
        best_height = -1
        
        for fmt_name, fmt_info in mp4_formats.items():
            if isinstance(fmt_info, dict) and fmt_info.get("src"):
                height_match = re.search(r'(\d+)[pP]', fmt_name)
                height = int(height_match.group(1)) if height_match else 360
                if height > best_height:
                    best_height = height
                    best_src = fmt_info.get("src")
                    
        if not best_src:
            logger.error(f"[Eporner Extractor] Could not find a src link in formats")
            return None, None, None
            
        size_bytes = 0
        try:
            head_res = scraper.head(best_src, timeout=10)
            if 'Content-Length' in head_res.headers:
                size_bytes = int(head_res.headers['Content-Length'])
        except Exception as he:
            logger.warning(f"[Eporner Extractor] Failed to get Content-Length via HEAD request: {he}")
            
        return title, best_src, size_bytes
    except Exception as e:
        logger.error(f"[Eporner Extractor] Exception in resolve: {e}")
        return None, None, None


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
    DUPLICATE = "duplicate"
    INCOMPLETE = "incomplete"
    FORCE_DOWNLOAD = "force-download"


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
    model_name: Optional[str] = None
    force_download: bool = False
    existing_file: Optional[Dict] = None
    expected_size: Optional[int] = None


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
    strategy TEXT,
    model_name TEXT
);

CREATE TABLE IF NOT EXISTS download_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vid TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    filename TEXT,
    filepath TEXT,
    downloaded_at REAL NOT NULL,
    filesize INTEGER,
    UNIQUE(vid, filepath)
);

CREATE INDEX IF NOT EXISTS idx_history_vid ON download_history(vid);
CREATE INDEX IF NOT EXISTS idx_history_url ON download_history(url);
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
                # Migration: Add model_name to tasks if it doesn't exist
                try:
                    cur = self.conn.execute("PRAGMA table_info(tasks)")
                    columns = [row[1] for row in cur.fetchall()]
                    if "model_name" not in columns:
                        logger.info("Migrating database: adding model_name column to tasks table")
                        self.conn.execute("ALTER TABLE tasks ADD COLUMN model_name TEXT")
                except Exception as e:
                    logger.error(f"Migration error: {e}")

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
                    t.model_name,
                )
            )
        with self.lock:
            with self.conn:
                self.conn.execute("DELETE FROM tasks;")
                self.conn.executemany(
                    "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", items
                )

    def load_tasks(self) -> List[Task]:
        with self.lock:
            cur = self.conn.execute(
                "SELECT url, status, progress, title, filename, size, speed, eta, retries, added_ts, vid, width, height, dest, strategy, model_name FROM tasks ORDER BY added_ts"
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
                model_name=r[15] if len(r) > 15 else None,
            )
            for r in rows
        ]

    def add_to_history(
        self,
        vid: str,
        url: str,
        title: str,
        filename: str,
        filepath: str,
        filesize: int = None,
    ):
        with self.lock:
            with self.conn:
                self.conn.execute(
                    """INSERT OR REPLACE INTO download_history 
                       (vid, url, title, filename, filepath, downloaded_at, filesize)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (vid, url, title, filename, filepath, time.time(), filesize),
                )

    def get_history_by_vid(self, vid: str) -> Optional[Dict]:
        with self.lock:
            cur = self.conn.execute(
                "SELECT * FROM download_history WHERE vid = ? ORDER BY downloaded_at DESC LIMIT 1",
                (vid,),
            )
            row = cur.fetchone()
        if row:
            return {
                "id": row[0],
                "vid": row[1],
                "url": row[2],
                "title": row[3],
                "filename": row[4],
                "filepath": row[5],
                "downloaded_at": row[6],
                "filesize": row[7],
            }
        return None

    def get_history_by_url(self, url: str) -> Optional[Dict]:
        norm_url = normalize_url(url)
        with self.lock:
            cur = self.conn.execute(
                "SELECT * FROM download_history WHERE url = ? ORDER BY downloaded_at DESC LIMIT 1",
                (norm_url,),
            )
            row = cur.fetchone()
        if row:
            return {
                "id": row[0],
                "vid": row[1],
                "url": row[2],
                "title": row[3],
                "filename": row[4],
                "filepath": row[5],
                "downloaded_at": row[6],
                "filesize": row[7],
            }
        return None

    def get_all_history(self, limit: int = 100) -> List[Dict]:
        with self.lock:
            cur = self.conn.execute(
                "SELECT * FROM download_history ORDER BY downloaded_at DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "vid": r[1],
                "url": r[2],
                "title": r[3],
                "filename": r[4],
                "filepath": r[5],
                "downloaded_at": r[6],
                "filesize": r[7],
            }
            for r in rows
        ]

    def clear_history(self):
        with self.lock:
            with self.conn:
                self.conn.execute("DELETE FROM download_history")

    def close(self):
        try:
            self.conn.close()
        except:
            pass


class DuplicateCheckResult:
    IS_DUPLICATE = "duplicate"
    IS_NEW = "new"
    DUPLICATE_SOURCE_FILESYSTEM = "filesystem"
    DUPLICATE_SOURCE_HISTORY = "history"
    DUPLICATE_SOURCE_ACTIVE = "active"


class DuplicateHandler:
    def __init__(
        self,
        db: Database,
        get_destination: Callable[[], str],
        get_tasks: Callable[[], Dict[str, Task]],
    ):
        self.db = db
        self.get_destination = get_destination
        self.get_tasks = get_tasks

    def check_by_vid(self, vid: str, exclude_url: str = None) -> Optional[Dict]:
        if not vid:
            return None

        active_tasks = self.get_tasks()
        for url, task in active_tasks.items():
            if exclude_url and url == exclude_url:
                continue
            if task.vid == vid and task.status not in (
                TaskStatus.CANCELLED,
                TaskStatus.FAILED,
            ):
                return {
                    "source": DuplicateCheckResult.DUPLICATE_SOURCE_ACTIVE,
                    "vid": vid,
                    "title": task.title,
                    "status": task.status.value,
                    "progress": task.progress,
                    "url": url,
                }

        history = self.db.get_history_by_vid(vid)
        if history:
            filepath = history.get("filepath")
            if filepath and Path(filepath).exists():
                return {
                    "source": DuplicateCheckResult.DUPLICATE_SOURCE_HISTORY,
                    "vid": vid,
                    "title": history.get("title"),
                    "filename": history.get("filename"),
                    "filepath": filepath,
                    "downloaded_at": history.get("downloaded_at"),
                    "url": history.get("url"),
                }

        destination = self.get_destination()
        if destination and Path(destination).exists():
            vid_regex = re.compile(rf"\[{re.escape(vid)}\]", re.IGNORECASE)
            patterns = ["*.mp4", "*.mkv", "*.webm", "*.avi"]
            for pattern in patterns:
                for filepath in Path(destination).glob(pattern):
                    if filepath.is_file() and vid_regex.search(filepath.name):
                        filesize = filepath.stat().st_size
                        if filesize > 0:
                            return {
                                "source": DuplicateCheckResult.DUPLICATE_SOURCE_FILESYSTEM,
                                "vid": vid,
                                "filename": filepath.name,
                                "filepath": str(filepath),
                                "filesize": filesize,
                            }
        return None

    def check_existing_file(
        self, expected_filename: str, expected_size_bytes: int = None
    ) -> Optional[Dict]:
        destination = self.get_destination()
        if not destination or not Path(destination).exists() or not expected_filename:
            return None

        filepath = Path(destination) / expected_filename
        if not filepath.exists():
            return None

        actual_size = filepath.stat().st_size

        if expected_size_bytes and actual_size > 0:
            size_ratio = actual_size / expected_size_bytes
            if size_ratio < 0.9:
                return {
                    "source": "incomplete",
                    "filename": expected_filename,
                    "filepath": str(filepath),
                    "actual_size": actual_size,
                    "expected_size": expected_size_bytes,
                    "size_ratio": size_ratio,
                }

        if actual_size > 0:
            return {
                "source": DuplicateCheckResult.DUPLICATE_SOURCE_FILESYSTEM,
                "filename": expected_filename,
                "filepath": str(filepath),
                "filesize": actual_size,
            }

        return None

    def check_by_url(self, url: str, exclude_self: bool = True) -> Optional[Dict]:
        norm_url = normalize_url(url)

        if not exclude_self:
            active_tasks = self.get_tasks()
            if norm_url in active_tasks:
                task = active_tasks[norm_url]
                if task.status in (
                    TaskStatus.DOWNLOADING,
                    TaskStatus.PAUSED,
                    TaskStatus.COMPLETED,
                ):
                    if task.status == TaskStatus.COMPLETED and task.filename:
                        dest = self.get_destination()
                        if dest:
                            filepath = Path(dest) / task.filename
                            if filepath.exists():
                                return {
                                    "source": DuplicateCheckResult.DUPLICATE_SOURCE_ACTIVE,
                                    "url": norm_url,
                                    "title": task.title,
                                    "filename": task.filename,
                                    "filepath": str(filepath),
                                }
                    elif task.status in (TaskStatus.DOWNLOADING, TaskStatus.PAUSED):
                        return {
                            "source": DuplicateCheckResult.DUPLICATE_SOURCE_ACTIVE,
                            "url": norm_url,
                            "title": task.title,
                            "status": task.status.value,
                            "progress": task.progress,
                        }

        history = self.db.get_history_by_url(norm_url)
        if history:
            filepath = history.get("filepath")
            if (
                filepath
                and Path(filepath).exists()
                and Path(filepath).stat().st_size > 0
            ):
                return {
                    "source": DuplicateCheckResult.DUPLICATE_SOURCE_HISTORY,
                    "vid": history.get("vid"),
                    "title": history.get("title"),
                    "filename": history.get("filename"),
                    "filepath": filepath,
                    "downloaded_at": history.get("downloaded_at"),
                    "url": norm_url,
                }
        return None

    def check_duplicate(self, url: str, vid: str = None) -> Dict:
        url_result = self.check_by_url(url)
        if url_result:
            return {"status": DuplicateCheckResult.IS_DUPLICATE, "info": url_result}

        if vid:
            vid_result = self.check_by_vid(vid, exclude_url=url)
            if vid_result:
                return {"status": DuplicateCheckResult.IS_DUPLICATE, "info": vid_result}

        return {"status": DuplicateCheckResult.IS_NEW, "info": None}

    def record_download(
        self,
        vid: str,
        url: str,
        title: str,
        filename: str,
        filepath: str,
        filesize: int = None,
    ):
        if vid:
            self.db.add_to_history(
                vid, normalize_url(url), title, filename, filepath, filesize
            )

    def scan_destination_for_existing(self) -> List[Dict]:
        destination = self.get_destination()
        if not Path(destination).exists():
            return []

        existing = []
        patterns = [
            "*.mp4",
            "*.mkv",
            "*.webm",
            "*.avi",
            "*.mp3",
            "*.m4a",
            "*.opus",
            "*.wav",
        ]
        for pattern in patterns:
            for filepath in Path(destination).glob(pattern):
                filename = filepath.name
                vid = self._extract_vid_from_filename(filename)
                filesize = filepath.stat().st_size if filepath.exists() else None
                existing.append(
                    {
                        "filename": filename,
                        "filepath": str(filepath),
                        "vid": vid,
                        "filesize": filesize,
                    }
                )
        return existing

    def _extract_vid_from_filename(self, filename: str) -> Optional[str]:
        match = re.search(r"\[([a-zA-Z0-9_-]{6,15})\](?:\.\w+)?$", filename)
        if match:
            return match.group(1)
        return None


class CrawlerService:
    def __init__(self, broadcast):
        self.broadcast = broadcast
        self._active_process: Optional[subprocess.Popen] = None
        self._cancel_event = threading.Event()
        self._lock = threading.Lock()

    def crawl(self, page_url: str):
        logger.info(f"[Crawler] ========== CRAWL INITIATED ==========")
        logger.info(f"[Crawler] Input URL: {page_url}")

        def worker():
            try:
                # 1. Normalize and check if it is an XVideos/XNXX profile/channel page
                normalized_page_url = normalize_url(page_url)
                
                import urllib.parse
                is_xv_profile = False
                xv_username = None
                domain = "www.xvideos.com"
                
                is_eporner_profile = False
                eporner_username = None
                eporner_domain = "www.eporner.com"
                
                parsed = urllib.parse.urlparse(normalized_page_url)
                if parsed.netloc:
                    domain_lower = parsed.netloc.lower()
                    if any(x in domain_lower for x in ['xvideos', 'xnxx']):
                        domain = domain_lower
                        path = parsed.path.strip('/')
                        if path:
                            parts = path.split('/')
                            first_segment = parts[0].lower()
                            
                            system_paths = {
                                'video', 'tags', 'c', 'best', 'new', 'channels-index', 'pornstars-index',
                                'rss', 'manifest.json', 'account', 'switch-sexual-orientation', 'favorite',
                                'my-feed', 'history', 'watch-later', 'change-currency', 'amateurs', 'pornstars',
                                'channels', 'profiles', 'model', 'models', 'video-channels', 'uploads', 'outputs'
                            }
                            
                            channel_prefixes = {
                                'profiles', 'channels', 'model', 'models', 'amateurs', 'pornstars',
                                'video-channels', 'amateur-channels', 'model-channels'
                            }
                            
                            if first_segment in channel_prefixes:
                                if len(parts) >= 2:
                                    is_xv_profile = True
                                    xv_username = parts[1]
                            elif first_segment not in system_paths:
                                if not (re.match(r'^video\d+', first_segment) or re.match(r'^video\.', first_segment)):
                                    is_xv_profile = True
                                    xv_username = first_segment
                    elif 'eporner' in domain_lower:
                        eporner_domain = domain_lower
                        path = parsed.path.strip('/')
                        if path:
                            parts = path.split('/')
                            if len(parts) >= 2 and parts[0].lower() == 'profile':
                                is_eporner_profile = True
                                eporner_username = parts[1]
                
                if is_xv_profile and xv_username:
                    import cloudscraper
                    logger.info(f"[Crawler] Detected XVideos profile for username: {xv_username} on domain: {domain}")
                    self.broadcast("crawl_start", {"url": normalized_page_url})
                    parent_title = xv_username
                    
                    all_urls_found = []
                    playlist_count = None
                    page = 0
                    
                    scraper = cloudscraper.create_scraper(
                        browser={
                            'browser': 'chrome',
                            'platform': 'windows',
                            'desktop': True
                        }
                    )
                    
                    while True:
                        if self._cancel_event.is_set():
                            logger.info("[Crawler] Cancelled by user")
                            self.broadcast("crawl_cancelled", {})
                            return
                            
                        # Default sorting to best
                        ajax_url = f"https://{domain}/channels/{xv_username}/videos/best/{page}"
                        logger.info(f"[Crawler] Fetching page {page} AJAX: {ajax_url}")
                        
                        res = scraper.get(ajax_url, timeout=15)
                        if res.status_code != 200:
                            logger.error(f"[Crawler] Failed to fetch page {page}: {res.status_code}")
                            break
                            
                        try:
                            data = res.json()
                        except Exception as je:
                            logger.error(f"[Crawler] Failed to parse JSON on page {page}: {je}")
                            break
                            
                        videos = data.get("videos")
                        if not videos or not isinstance(videos, list):
                            logger.info(f"[Crawler] No more videos found or invalid format on page {page}")
                            break
                            
                        if playlist_count is None and data.get("nb_videos"):
                            playlist_count = int(data.get("nb_videos"))
                            logger.info(f"[Crawler] Playlist count detected: {playlist_count}")
                            
                        page_new_urls = []
                        for v in videos:
                            eid = v.get("eid")
                            v_id = v.get("id")
                            u = v.get("u")
                            title = v.get("t", "Unknown")
                            
                            if not u:
                                continue
                                
                            slug = u.split('/')[-1]
                            if eid:
                                video_url = f"https://{domain}/video.{eid}/{slug}"
                            elif v_id:
                                video_url = f"https://{domain}/video{v_id}/{slug}"
                            else:
                                continue
                                
                            normalized = normalize_url(video_url)
                            if not any(item["url"] == normalized for item in all_urls_found):
                                all_urls_found.append({"url": normalized, "title": title})
                                page_new_urls.append(normalized)
                                logger.info(f"[Crawler] Found #{len(all_urls_found)}: {title[:60]}")
                                self.broadcast(
                                    "crawl_progress",
                                    {
                                        "count": len(all_urls_found),
                                        "latest": title[:50],
                                        "total": playlist_count,
                                    },
                                )
                                
                        if not page_new_urls:
                            logger.info(f"[Crawler] No new videos on page {page}, ending loop")
                            break
                            
                        page += 1
                        if playlist_count and len(all_urls_found) >= playlist_count:
                            logger.info(f"[Crawler] Crawled all {len(all_urls_found)} videos, ending loop")
                            break
                            
                    logger.info(f"[Crawler] ========== COMPLETE: {len(all_urls_found)} URLs ==========")
                    if not self._cancel_event.is_set():
                        self.broadcast("crawl_complete", {"urls": all_urls_found, "parent_title": parent_title})
                    return

                if is_eporner_profile and eporner_username:
                    import cloudscraper
                    from bs4 import BeautifulSoup
                    import random
                    import time
                    
                    logger.info(f"[Crawler] Detected EPORNER profile for username: {eporner_username} on domain: {eporner_domain}")
                    self.broadcast("crawl_start", {"url": normalized_page_url})
                    
                    # Determine parent_title for cleaner folders
                    parent_title = eporner_username
                    path_stripped = parsed.path.strip('/')
                    path_parts = path_stripped.split('/')
                    if len(path_parts) >= 5 and path_parts[2].lower() == 'playlist':
                        parent_title = f"{eporner_username}_playlist_{path_parts[4]}"
                        
                    all_urls_found = []
                    playlist_count = None
                    page = 1
                    visited_urls = set()
                    
                    # Normalize start URL for base profile to go to uploaded-videos tab
                    current_url = normalized_page_url
                    if len(path_parts) == 2 and path_parts[0].lower() == 'profile':
                        current_url = f"https://{eporner_domain}/profile/{eporner_username}/uploaded-videos/"
                        
                    scraper = cloudscraper.create_scraper(
                        browser={
                            'browser': 'chrome',
                            'platform': 'windows',
                            'desktop': True
                        }
                    )
                    
                    while current_url:
                        if self._cancel_event.is_set():
                            logger.info("[Crawler] Cancelled by user")
                            self.broadcast("crawl_cancelled", {})
                            return
                            
                        if current_url in visited_urls:
                            logger.info(f"[Crawler] URL already visited: {current_url}, ending loop")
                            break
                        visited_urls.add(current_url)
                        
                        logger.info(f"[Crawler] Fetching page {page}: {current_url}")
                        res = scraper.get(current_url, timeout=15)
                        if res.status_code != 200:
                            logger.error(f"[Crawler] Failed to fetch page {page}: {res.status_code}")
                            break
                            
                        soup = BeautifulSoup(res.text, "html.parser")
                        
                        # Try to detect total uploads on first page
                        if playlist_count is None:
                            total_match = re.search(r'Uploaded videos\s*\(\s*([\d,.]+)\s*\)', res.text, re.IGNORECASE)
                            if total_match:
                                playlist_count = int(total_match.group(1).replace(',', '').replace('.', ''))
                                logger.info(f"[Crawler] Playlist count detected: {playlist_count}")
                                
                        page_new_urls = []
                        for a in soup.find_all("a", href=lambda h: h and h.startswith("/video-")):
                            href = a.get("href")
                            title = a.get("title") or a.get_text(strip=True)
                            full_url = f"https://{eporner_domain}{href}" if href.startswith('/') else href
                            normalized = normalize_url(full_url)
                            
                            existing = next((item for item in all_urls_found if item["url"] == normalized), None)
                            if not existing:
                                item = {"url": normalized, "title": title or "Unknown"}
                                all_urls_found.append(item)
                                page_new_urls.append(normalized)
                                logger.info(f"[Crawler] Found #{len(all_urls_found)}: {(title or 'Unknown')[:60]}")
                                self.broadcast(
                                    "crawl_progress",
                                    {
                                        "count": len(all_urls_found),
                                        "latest": (title or "Unknown")[:50],
                                        "total": playlist_count,
                                    },
                                )
                            elif title and (existing["title"] == "Unknown" or not existing["title"]):
                                existing["title"] = title
                                
                        if not page_new_urls:
                            logger.info(f"[Crawler] No new videos on page {page}, ending loop")
                            break
                            
                        if playlist_count and len(all_urls_found) >= playlist_count:
                            logger.info(f"[Crawler] Crawled all {len(all_urls_found)} videos, ending loop")
                            break
                            
                        # Find next page link
                        next_link = soup.find("a", class_=lambda c: c and "nmnext" in c)
                        if next_link and next_link.get("href"):
                            next_href = next_link.get("href")
                            current_url = f"https://{eporner_domain}{next_href}" if next_href.startswith('/') else next_href
                            page += 1
                            
                            # Sleep a random time between 0.5 and 1.0 seconds to avoid Cloudflare/rate limits
                            sleep_time = random.uniform(0.5, 1.0)
                            logger.info(f"[Crawler] Sleeping {sleep_time:.2f}s before fetching next page...")
                            time.sleep(sleep_time)
                        else:
                            logger.info("[Crawler] No NEXT page link found, ending loop")
                            break
                            
                    logger.info(f"[Crawler] ========== COMPLETE: {len(all_urls_found)} URLs ==========")
                    if not self._cancel_event.is_set():
                        self.broadcast("crawl_complete", {"urls": all_urls_found, "parent_title": parent_title})
                    return

                # 2. Fallback to existing yt-dlp scraper logic
                yt = which_yt_dlp()
                if not yt:
                    logger.error("[Crawler] yt-dlp not found!")
                    self.broadcast("crawl_error", "yt-dlp not found")
                    return

                logger.info(f"[Crawler] yt-dlp path: {yt}")
                self.broadcast("crawl_start", {"url": page_url})

                # Attempt to get parent title (e.g. Playlist title or Model name)
                parent_title = None
                
                # Special case: Extract model/user name from URL for cleaner folder names
                model_match = re.search(r'/(?:model|users?|channels?|pornstars?)/([^/?#]+)', page_url, re.IGNORECASE)
                if model_match:
                    parent_title = model_match.group(1)
                    logger.info(f"[Crawler] Extracted name from URL: {parent_title}")

                if not parent_title:
                    try:
                        title_cmd = [yt] + get_base_yt_dlp_args() + ["--print", "%(uploader|creator|playlist_uploader|playlist_title|title)s", "--playlist-items", "1", "--no-warnings", page_url]
                        logger.info(f"[Crawler] Fetching parent title: {' '.join(title_cmd)}")
                        res = subprocess.run(
                            title_cmd,
                            capture_output=True,
                            text=True,
                            encoding="utf-8",
                            errors="replace",
                            timeout=20,
                            creationflags=create_flags(),
                            startupinfo=create_startupinfo(),
                            env=get_subprocess_env(),
                        )
                        if res.returncode == 0:
                            parent_title = res.stdout.strip()
                            # Clean up common suffixes
                            parent_title = re.sub(r' - Pornhub$', '', parent_title, flags=re.IGNORECASE)
                            parent_title = re.sub(r'^Videos - ', '', parent_title, flags=re.IGNORECASE)
                            logger.info(f"[Crawler] Detected parent title: {parent_title}")
                    except Exception as te:
                        logger.warning(f"[Crawler] Could not fetch parent title: {te}")

                cmd = (
                    [yt]
                    + get_base_yt_dlp_args()
                    + ["--flat-playlist", "--dump-json", "--no-warnings", page_url]
                )
                logger.info(f"[Crawler] Running: {' '.join(cmd)}")

                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=create_flags(),
                    startupinfo=create_startupinfo(),
                    env=get_subprocess_env(),
                )
                with self._lock:
                    self._active_process = proc

                logger.info(f"[Crawler] Process started (PID: {proc.pid})")

                all_urls_found = []
                playlist_count = None

                while True:
                    if self._cancel_event.is_set():
                        logger.info("[Crawler] Cancelled by user")
                        proc.terminate()
                        self.broadcast("crawl_cancelled", {})
                        return

                    line = proc.stdout.readline()
                    if not line:
                        break

                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        url = data.get("url") or data.get("webpage_url")
                        title = data.get("title", "Unknown")

                        if playlist_count is None and data.get("playlist_count"):
                            playlist_count = data.get("playlist_count")
                            logger.info(
                                f"[Crawler] Playlist count detected: {playlist_count}"
                            )

                        if url:
                            url = normalize_url(url)
                            if not any(u["url"] == url for u in all_urls_found):
                                all_urls_found.append({"url": url, "title": title})
                                logger.info(
                                    f"[Crawler] Found #{len(all_urls_found)}: {title[:60]}"
                                )
                                self.broadcast(
                                    "crawl_progress",
                                    {
                                        "count": len(all_urls_found),
                                        "latest": title[:50],
                                        "total": playlist_count,
                                    },
                                )
                    except json.JSONDecodeError as je:
                        logger.warning(f"[Crawler] JSON parse error: {line[:100]}")
                        continue

                proc.wait()
                logger.info(f"[Crawler] Process finished (code: {proc.returncode})")

                if proc.returncode != 0:
                    stderr = proc.stderr.read()
                    logger.error(f"[Crawler] yt-dlp error: {stderr[:500]}")

                logger.info(
                    f"[Crawler] ========== COMPLETE: {len(all_urls_found)} URLs =========="
                )

                if not self._cancel_event.is_set():
                    self.broadcast("crawl_complete", {"urls": all_urls_found, "parent_title": parent_title})
            except Exception as e:
                logger.error(f"[Crawler] Exception: {e}")
                import traceback

                logger.error(traceback.format_exc())
                if not self._cancel_event.is_set():
                    self.broadcast("crawl_error", str(e))
            finally:
                with self._lock:
                    self._active_process = None
                logger.info("[Crawler] Worker finished")

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
        self.skip_duplicates = True

        self._load_settings()
        self._load_tasks()
        self.duplicate_handler = DuplicateHandler(
            db, lambda: self.destination, lambda: self.tasks
        )
        self.crawler = CrawlerService(broadcast)
        self._start_manager()

    def _load_settings(self):
        self.destination = self.db.get_setting("destination", self.destination)
        self.max_concurrent = int(
            self.db.get_setting("max_concurrent", self.max_concurrent)
        )
        self.auto_delete = bool(self.db.get_setting("auto_delete", self.auto_delete))
        self.skip_duplicates = bool(
            self.db.get_setting("skip_duplicates", self.skip_duplicates)
        )
        self.sem = threading.Semaphore(self.max_concurrent)
        logger.info(
            f"Loaded settings: dest={self.destination}, max={self.max_concurrent}, auto_delete={self.auto_delete}, skip_duplicates={self.skip_duplicates}"
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
        
        is_eporner = 'eporner.com' in url.lower()
        if is_eporner:
            try:
                title, direct_url, size_bytes = resolve_eporner_video(url)
                if not direct_url:
                    raise Exception("Failed to resolve Eporner direct video link")
                
                if not hasattr(self, '_eporner_direct_urls'):
                    self._eporner_direct_urls = {}
                self._eporner_direct_urls[url] = direct_url
                
                video_id_match = re.search(r'/(?:video|hd-porn|embed)-([a-zA-Z0-9]+)', url)
                vid = video_id_match.group(1) if video_id_match else "eporner_vid"
                
                width, height = 1280, 720
                if "1080" in direct_url:
                    width, height = 1920, 1080
                elif "720" in direct_url:
                    width, height = 1280, 720
                elif "480" in direct_url:
                    width, height = 854, 480
                elif "360" in direct_url:
                    width, height = 640, 360
                    
                expected_filename = f"{title[:100]} [{width}x{height}] [{vid}].mp4"
                
                with self.lock:
                    task = self.tasks.get(url)
                    if not task:
                        return
                    task.title = title
                    task.vid = vid
                    task.width = width
                    task.height = height
                    task.expected_size = size_bytes
                    task.filename = expected_filename
                    
                    if task.force_download:
                        task.status = TaskStatus.QUEUED
                        logger.info(f"Force download enabled for Eporner: {url}")
                        self._broadcast_refresh()
                        return
                        
                if self.skip_duplicates and vid:
                    existing = self.duplicate_handler.check_existing_file(expected_filename, size_bytes)
                    if existing:
                        if existing.get("source") == "incomplete":
                            with self.lock:
                                task = self.tasks.get(url)
                                if task:
                                    task.status = TaskStatus.INCOMPLETE
                                    task.filename = expected_filename
                                    task.existing_file = existing
                                    task.title = f"[INCOMPLETE - {int(existing['size_ratio'] * 100)}%] {title}"
                            logger.info(f"Incomplete file detected for Eporner URL {url}")
                            self._broadcast_refresh()
                            return
                        else:
                            with self.lock:
                                task = self.tasks.get(url)
                                if task:
                                    task.status = TaskStatus.DUPLICATE
                                    task.filename = existing.get("filename")
                                    task.title = f"[DUPLICATE - filesystem] {title}"
                                    task.existing_file = existing
                            logger.info(f"Duplicate file detected for Eporner URL {url}")
                            self._broadcast_refresh()
                            return
                            
                with self.lock:
                    task = self.tasks.get(url)
                    if task and task.status not in (TaskStatus.CANCELLED, TaskStatus.DUPLICATE, TaskStatus.INCOMPLETE):
                        task.status = TaskStatus.QUEUED
                self._broadcast_refresh()
                return
            except Exception as e:
                logger.error(f"Eporner fetch info failed: {e}")
                self._mark_failed(url, str(e)[:100])
                return

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
                env=get_subprocess_env(),
            )
            if res.returncode != 0:
                raise Exception(res.stderr or "Unknown error")

            info = json.loads(res.stdout)
            vid = info.get("id")
            title = info.get("title", "Unknown")[:80]
            width = info.get("width")
            height = info.get("height")
            filesize_bytes = info.get("filesize") or info.get("filesize_approx")

            expected_filename = None
            if vid and title:
                ext = info.get("ext", "mp4")
                expected_filename = f"{title[:100]} [{width}x{height}] [{vid}].{ext}"

            with self.lock:
                task = self.tasks.get(url)
                if not task:
                    return

                task.title = title
                task.vid = vid
                task.width = width
                task.height = height
                task.expected_size = filesize_bytes

                if task.force_download:
                    task.status = TaskStatus.QUEUED
                    logger.info(f"Force download enabled for: {url}")
                    self._broadcast_refresh()
                    return

            if self.skip_duplicates and vid:
                if expected_filename and filesize_bytes:
                    existing = self.duplicate_handler.check_existing_file(
                        expected_filename, filesize_bytes
                    )
                    if existing:
                        if existing.get("source") == "incomplete":
                            with self.lock:
                                task = self.tasks.get(url)
                                if task:
                                    task.status = TaskStatus.INCOMPLETE
                                    task.filename = expected_filename
                                    task.existing_file = existing
                                    task.title = f"[INCOMPLETE - {int(existing['size_ratio'] * 100)}%] {title}"
                            logger.info(
                                f"Incomplete file detected for {url}: {existing['actual_size']}/{filesize_bytes} bytes"
                            )
                            self._broadcast_refresh()
                            return
                        else:
                            with self.lock:
                                task = self.tasks.get(url)
                                if task:
                                    task.status = TaskStatus.DUPLICATE
                                    task.filename = existing.get("filename")
                                    task.title = f"[DUPLICATE - filesystem] {title}"
                                    task.existing_file = existing
                            logger.info(f"Duplicate file detected for {url}")
                            self._broadcast_refresh()
                            return

                dup_result = self.duplicate_handler.check_duplicate(url, vid)
                if dup_result["status"] == DuplicateCheckResult.IS_DUPLICATE:
                    dup_info = dup_result["info"]
                    source = dup_info.get("source", "unknown")
                    with self.lock:
                        task = self.tasks.get(url)
                        if task:
                            task.status = TaskStatus.DUPLICATE
                            task.filename = dup_info.get("filename")
                            task.title = f"[DUPLICATE - {source}] {title}"
                            task.existing_file = dup_info
                    logger.info(
                        f"Duplicate detected for {url}: source={source}, vid={vid}"
                    )
                    self._broadcast_refresh()
                    return

            with self.lock:
                task = self.tasks.get(url)
                if task and task.status not in (
                    TaskStatus.CANCELLED,
                    TaskStatus.DUPLICATE,
                    TaskStatus.INCOMPLETE,
                ):
                    task.status = TaskStatus.QUEUED
            self._broadcast_refresh()
        except Exception as e:
            self._mark_failed(url, str(e)[:100])

    def _download_eporner_http(self, url: str, direct_url: str):
        with self.lock:
            task = self.tasks.get(url)
            if not task:
                self.sem.release()
                return
            folder = task.dest or self.destination
            filename = task.filename or "eporner_video.mp4"
            expected_size = task.expected_size or 0
            
        os.makedirs(folder, exist_ok=True)
        filepath = Path(folder) / filename
        
        with self.lock:
            task = self.tasks.get(url)
            if task:
                task.strategy = "HTTP Downloader"
                task.status = TaskStatus.DOWNLOADING
                task.progress = 0.0
        self._broadcast_refresh()
        
        import cloudscraper
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        downloaded_bytes = 0
        try:
            logger.info(f"Downloading Eporner HTTP: {direct_url} to {filepath}")
            res = scraper.get(direct_url, stream=True, timeout=30)
            if res.status_code not in (200, 206):
                raise Exception(f"HTTP download returned status: {res.status_code}")
                
            total_size = int(res.headers.get('content-length', expected_size or 0))
            
            import time
            start_time = time.time()
            last_broadcast = start_time
            last_bytes = 0
            
            with open(filepath, 'wb') as f:
                for chunk in res.iter_content(chunk_size=1024 * 64):
                    if self._cancel_event.is_set():
                        logger.info(f"Eporner download cancelled: {url}")
                        break
                        
                    with self.lock:
                        if url not in self.tasks or self.tasks[url].status != TaskStatus.DOWNLOADING:
                            logger.info(f"Eporner download stopped or task removed: {url}")
                            break
                            
                    if chunk:
                        f.write(chunk)
                        downloaded_bytes += len(chunk)
                        
                        now = time.time()
                        if now - last_broadcast > 0.5:
                            elapsed = now - start_time
                            pct = (downloaded_bytes / total_size) * 100.0 if total_size > 0 else 0.0
                            
                            bytes_since_last = downloaded_bytes - last_bytes
                            time_since_last = now - last_broadcast
                            speed_val = (bytes_since_last / time_since_last) / (1024 * 1024) if time_since_last > 0 else 0.0
                            speed_str = f"{speed_val:.2f} MiB/s"
                            
                            size_str = f"{downloaded_bytes / (1024*1024):.1f}M / {total_size / (1024*1024):.1f}M" if total_size > 0 else f"{downloaded_bytes / (1024*1024):.1f}M"
                            
                            if speed_val > 0 and total_size > 0:
                                remaining_bytes = total_size - downloaded_bytes
                                remaining_seconds = remaining_bytes / (speed_val * 1024 * 1024)
                                
                                mins, secs = divmod(int(remaining_seconds), 60)
                                hours, mins = divmod(mins, 60)
                                if hours > 0:
                                    eta_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
                                else:
                                    eta_str = f"{mins:02d}:{secs:02d}"
                            else:
                                eta_str = "--:--"
                                
                            with self.lock:
                                t = self.tasks.get(url)
                                if t:
                                    t.progress = pct / 100.0
                                    t.speed = speed_str
                                    t.size = size_str
                                    t.eta = eta_str
                                    
                            self._maybe_broadcast_progress(url, pct)
                            
                            last_broadcast = now
                            last_bytes = downloaded_bytes
                            
            if self._cancel_event.is_set() or (url in self.tasks and self.tasks[url].status != TaskStatus.DOWNLOADING):
                if url in self.tasks and self.tasks[url].status not in (TaskStatus.CANCELLED, TaskStatus.FAILED):
                    with self.lock:
                        t = self.tasks.get(url)
                        if t:
                            t.status = TaskStatus.CANCELLED
                    self._broadcast_refresh()
            else:
                with self.lock:
                    t = self.tasks.get(url)
                    if t:
                        t.status = TaskStatus.COMPLETED
                        t.progress = 1.0
                        t.speed = "0.00 MiB/s"
                        t.eta = "00:00"
                self._broadcast_refresh()
                try:
                    self.db.add_to_history(
                        vid=task.vid or "eporner_vid",
                        url=url,
                        title=task.title or "Eporner Video",
                        filename=filename,
                        filepath=str(filepath),
                        filesize=total_size,
                    )
                except Exception as dbe:
                    logger.warning(f"Failed to add download history: {dbe}")
                    
        except Exception as e:
            logger.error(f"Eporner HTTP download exception: {e}")
            self._mark_failed(url, str(e)[:100])
        finally:
            self.sem.release()

    def _download(self, url: str):
        is_eporner = 'eporner.com' in url.lower()
        if is_eporner:
            direct_url = getattr(self, '_eporner_direct_urls', {}).get(url)
            if not direct_url:
                try:
                    _, direct_url, _ = resolve_eporner_video(url)
                except Exception as e:
                    logger.error(f"Failed to resolve Eporner url on download: {e}")
            
            if not direct_url:
                self._mark_failed(url, "Failed to resolve Eporner download link")
                self.sem.release()
                return
                
            self._download_eporner_http(url, direct_url)
            return

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

        output_tpl = DEFAULT_OUTPUT_TPL
        if task.model_name:
            # If we have a model name, use it specifically in the filename
            # Escape % for yt-dlp template and remove potential problematic characters
            safe_model = task.model_name.replace('%', '%%')
            output_tpl = f"{safe_model} - %(title).150s.%(ext)s"

        # Use a .tmp folder for temporary/fragment files to avoid clutter
        temp_folder = str(Path(folder) / ".tmp")
        os.makedirs(temp_folder, exist_ok=True)

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
                f"home:{folder}",
                "-P",
                f"temp:{temp_folder}",
                "-o",
                output_tpl,
                "--no-warnings",
                "--continue",
                "--retries",
                "10",
                "--fragment-retries",
                "10",
                url,
            ]
        )

        if task.force_download:
            cmd.append("--force-overwrites")
            logger.info(f"Force overwrite enabled for: {url}")
        else:
            cmd.append("--no-overwrites")

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
                env=get_subprocess_env(),
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

                        if task.vid and task.filename:
                            filepath = Path(folder) / task.filename
                            filesize = (
                                filepath.stat().st_size if filepath.exists() else None
                            )
                            self.duplicate_handler.record_download(
                                vid=task.vid,
                                url=url,
                                title=task.title,
                                filename=task.filename,
                                filepath=str(filepath),
                                filesize=filesize,
                            )
                            logger.info(
                                f"Recorded download: {task.vid} -> {task.filename}"
                            )

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
            "skip_duplicates": self.skip_duplicates,
            "yt_dlp_available": bool(which_yt_dlp()),
        }
        self.broadcast("settings", settings)

    def add_urls(self, text: str, folder: Optional[str] = None):
        urls = extract_urls(text)
        added = 0
        with self.lock:
            for u in urls:
                norm = normalize_url(u)
                if norm and norm not in self.tasks:
                    dest = None
                    if folder:
                        # Sanitize folder name: remove invalid characters
                        safe_folder = re.sub(r'[<>:"/\\|?*]', '_', folder).strip()
                        if safe_folder:
                            dest = str(Path(self.destination) / safe_folder)
                    
                    self.tasks[norm] = Task(url=norm, status=TaskStatus.INFO, dest=dest, model_name=folder)
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

    def cancel_all(self):
        with self.lock:
            for url, proc in self.processes.items():
                proc.terminate()
            for url, task in self.tasks.items():
                if task.status in (TaskStatus.QUEUED, TaskStatus.DOWNLOADING, TaskStatus.PAUSED, TaskStatus.FETCHING_INFO):
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

    def force_download(self, url: str):
        with self.lock:
            task = self.tasks.get(url)
            if task and task.status in (TaskStatus.INCOMPLETE, TaskStatus.DUPLICATE):
                task.force_download = True
                task.status = TaskStatus.INFO
                task.progress = 0.0
                if task.existing_file and task.existing_file.get("filepath"):
                    existing_path = Path(task.existing_file["filepath"])
                    if existing_path.exists():
                        try:
                            existing_path.unlink()
                            logger.info(f"Deleted incomplete file: {existing_path}")
                        except Exception as e:
                            logger.warning(f"Failed to delete file: {e}")
        self._broadcast_refresh()

    def clear_finished(self):
        with self.lock:
            self.tasks = {
                k: v
                for k, v in self.tasks.items()
                if v.status
                not in (
                    TaskStatus.COMPLETED,
                    TaskStatus.FAILED,
                    TaskStatus.CANCELLED,
                    TaskStatus.DUPLICATE,
                )
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

    def set_skip_duplicates(self, value):
        with self.lock:
            self.skip_duplicates = bool(value)
        self.db.set_setting("skip_duplicates", 1 if self.skip_duplicates else 0)
        logger.info(f"Skip-duplicates set to: {self.skip_duplicates}")
        self._broadcast_settings()
        self._broadcast_refresh()

    def check_duplicate_url(self, url: str):
        return self.duplicate_handler.check_by_url(url)

    def get_download_history(self, limit: int = 100):
        return self.db.get_all_history(limit)

    def clear_download_history(self):
        self.db.clear_history()
        self._broadcast_settings()

    def scan_existing_files(self):
        return self.duplicate_handler.scan_destination_for_existing()

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
                    result = controller.add_urls(data.get("text", ""), data.get("folder"))
                    await ws.send_str(
                        json.dumps({"type": "result", "command": "add", "data": result})
                    )
                elif cmd == "pause":
                    controller.pause(data.get("url"))
                elif cmd == "resume":
                    controller.resume(data.get("url"))
                elif cmd == "cancel":
                    controller.cancel(data.get("url"))
                elif cmd == "cancel_all":
                    controller.cancel_all()
                elif cmd == "remove":
                    controller.remove(data.get("url"))
                elif cmd == "retry":
                    controller.retry(data.get("url"))
                elif cmd == "force_download":
                    controller.force_download(data.get("url"))
                elif cmd == "clear_finished":
                    controller.clear_finished()
                elif cmd == "set_destination":
                    controller.set_destination(data.get("path"))
                elif cmd == "set_max_concurrent":
                    controller.set_max_concurrent(int(data.get("value", 3)))
                elif cmd == "set_auto_delete":
                    controller.set_auto_delete(bool(data.get("value")))
                elif cmd == "set_skip_duplicates":
                    controller.set_skip_duplicates(bool(data.get("value")))
                elif cmd == "check_duplicate":
                    result = controller.check_duplicate_url(data.get("url", ""))
                    await ws.send_str(
                        json.dumps({"type": "duplicate_check", "data": result})
                    )
                elif cmd == "get_history":
                    history = controller.get_download_history(
                        int(data.get("limit", 100))
                    )
                    await ws.send_str(json.dumps({"type": "history", "data": history}))
                elif cmd == "clear_history":
                    controller.clear_download_history()
                elif cmd == "scan_existing":
                    existing = controller.scan_existing_files()
                    await ws.send_str(
                        json.dumps({"type": "existing_files", "data": existing})
                    )
                elif cmd == "crawl":
                    controller.crawler.crawl(data.get("url"))
                elif cmd == "cancel_crawl":
                    controller.crawler.cancel()
                elif cmd == "get_settings":
                    settings = {
                        "destination": controller.destination,
                        "max_concurrent": controller.max_concurrent,
                        "auto_delete": controller.auto_delete,
                        "skip_duplicates": controller.skip_duplicates,
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
            "skip_duplicates": controller.skip_duplicates,
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
    if "skip_duplicates" in data:
        controller.set_skip_duplicates(bool(data["skip_duplicates"]))
    return web.json_response({"status": "ok"})


async def http_get_history(request):
    limit = int(request.query.get("limit", 100))
    history = controller.get_download_history(limit)
    return web.json_response(history)


async def http_check_duplicate(request):
    data = await request.json()
    url = data.get("url", "")
    result = controller.check_duplicate_url(url)
    return web.json_response(result)


async def http_scan_existing(request):
    existing = controller.scan_existing_files()
    return web.json_response(existing)


def create_app():
    app = web.Application()
    app.router.add_get("/ws", ws_handler)
    app.router.add_post("/api/add", http_add_urls)
    app.router.add_get("/api/tasks", http_get_tasks)
    app.router.add_get("/api/settings", http_get_settings)
    app.router.add_post("/api/settings", http_post_settings)
    app.router.add_get("/api/history", http_get_history)
    app.router.add_post("/api/check_duplicate", http_check_duplicate)
    app.router.add_get("/api/scan_existing", http_scan_existing)

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
