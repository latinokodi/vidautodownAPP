import sqlite3
import json
import threading
from typing import List, Any, Optional
from .models import Task, TaskStatus

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
        # check_same_thread=False allows sharing connection across threads 
        # (safe with lock + WAL mode for this use case)
        self.conn = sqlite3.connect(path, timeout=10, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.lock = threading.Lock()
        self._init_schema()

    def _init_schema(self) -> None:
        with self.lock:
            with self.conn:
                self.conn.executescript(_SCHEMA)

    # ---------- settings ----------
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

    # ---------- tasks ----------
    def save_tasks(self, tasks: List[Task]) -> None:
        items = []
        for t in tasks:
            items.append((
                t.url,
                t.status.value if hasattr(t.status, 'value') else t.status,
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
                status=row[1] or TaskStatus.QUEUED,
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
