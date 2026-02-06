import threading
import queue
import time
import os
import shutil
import subprocess
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from ..api.websockets import manager
from .models import Task, TaskStatus
from .database import Database

# Re-use the existing utils logic where possible, but adapted
# (We might want to move these to a shared utils file later, but keeping here for now)

WIN32 = os.name == "nt"

def which_yt_dlp() -> Optional[str]:
    return shutil.which("yt-dlp")

def which_aria2c() -> Optional[str]:
    return shutil.which("aria2c")

def create_flags_no_window() -> int:
    return subprocess.CREATE_NO_WINDOW if WIN32 else 0

def create_startupinfo_no_window():
    if not WIN32: return None
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    return si

DEFAULT_OUTPUT_TPL = "%(title).100s [%(width)sx%(height)s] [%(id)s].%(ext)s"

# Regex parsers (simplified for brevity, assume we use the same robust ones)
import re
PROGRESS_RE = re.compile(
    r"\[download\]\s+(?P<pct>\d+(?:\.\d+)?)%\s+of\s+(?P<size>~?\s*[\d\.]+\s*[KMGTP]?i?B)"
    r"(?:\s+at\s+(?P<speed>[\d\.\s]+[KMGTP]?i?B/s))?"
    r"(?:\s+ETA\s+(?P<eta>[\d:]+))?", re.IGNORECASE
)
ARIA2_PROGRESS_RE = re.compile(
    r"\[aria2c\]\s+Downloaded\s+(?P<downloaded>[\d\.]+\s*[KMGTP]?i?B)\s+of\s+(?P<size>[\d\.]+\s*[KMGTP]?i?B)\s+\((?P<pct>\d+(?:\.\d+)?)%\)", re.IGNORECASE
)
FILENAME_RE = re.compile(r"(?:\[download\]\s+Destination:\s+(?P<dest>.*))|(?:\[Merger\]\s+Merging formats into\s+\"(?P<merge>.*)\")")
URL_RE = re.compile(r"(?P<url>https?://[^\s<>'\"`]+)", re.IGNORECASE)

def normalize_url(url: str) -> str:
    if not url: return url
    u = url.strip().split("#", 1)[0]
    if u.endswith("/") and "://" in u:
        scheme, rest = u.split("://", 1)
        if "/" in rest and not rest.endswith("://"):
            u = u.rstrip("/")
    return u

def extract_urls(text: str) -> list[str]:
    if not text: return []
    return list(dict.fromkeys(URL_RE.findall(text.strip())))

class DownloadController:
    def __init__(self):
        # We start the loop in a background thread or use FastAPI's loop?
        # For now, we keep the Thread-based manager loop because subprocess calls are blocking/synchronous 
        # unless we rewrite everything to asyncio.subprocess which is a larger refactor.
        # We will use `asyncio.run_coroutine_threadsafe` to bridge back to WebSockets.

        self.sem = threading.Semaphore(2) # Default 2
        self.tasks_lock = threading.Lock()
        self.tasks: Dict[str, Task] = {}
        self.stop_event = threading.Event()
        self.destination = os.path.join(os.path.expanduser("~"), "Downloads")
        
        self.aria2c_path = which_aria2c()
        self.auto_delete_finished = False
        
        # Throttle state
        self._last_progress_post_ts: Dict[str, float] = {}
        
        # Start manager
        self.manager_thread = threading.Thread(target=self._manager_loop, daemon=True)
        self.manager_thread.start()
        
        # DB ref
        self.db = None # Set by main app

    def set_db(self, db: Database):
        self.db = db
        # Restore queue logic here if needed, or caller does it

    # ---------- Async Message Bridge ----------
    def _broadcast_sync(self, msg_type: str, payload: dict):
        """Helper to call async broadcast from sync threads"""
        try:
            # We need the running event loop. In standard FastAPI (uvicorn), there is one.
            # But we are in a thread. We need to find the loop.
            # A simple way for now allows "fire and forget" via a helper or global loop ref.
            # We'll rely on the fact that 'manager' functions are async.
            
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                pass
            
            if not loop:
                # If we can't find a loop (shouldn't happen in main thread, but this is a worker thread),
                # we technically need a reference to the main loop.
                # IMPLEMENTATION DETAIL: In production, we'd pass the loop to __init__.
                # For this prototype, let's assume we can get it or fail gracefully.
                pass 

            # ACTUALLY: The correct pattern is to pass the loop instance to the controller 
            # or use a thread-safe queue that an async worker drains.
            # Let's implement a queue-drainer pattern in main.py, similar to the old UI queue.
            # For now, we will push to a simple queue, and main.py will have a background async task.
            pass
        except Exception:
            pass

    # We'll simply use a queue, main.py will consume it and broadcast via WS
    msg_queue = queue.Queue()

    def post(self, msg_type: str, payload: Any):
        self.msg_queue.put((msg_type, payload))

    # ---------- Control API ----------
    def add_urls(self, raw_text: str):
        urls = extract_urls(raw_text)
        added = 0
        with self.tasks_lock:
            for u in urls:
                norm = normalize_url(u)
                if norm and norm not in self.tasks:
                    self.tasks[norm] = Task(url=norm, status=TaskStatus.INFO)
                    added += 1
        if added:
            self.post("toast", f"Added {added} tasks")
            self.post("refresh", self._get_all_tasks_dict())

    def interact(self, url: str, action: str):
        with self.tasks_lock:
            task = self.tasks.get(url)
            if not task: return

            if action == "pause":
                if task.status == TaskStatus.DOWNLOADING and hasattr(task, 'process'):
                    # The process attribute is not in Pydantic model (it's transient).
                    # We store transient objects in a separate dict or attach to model (but exclude from serialization).
                    # Refactor: Controller should store transient state (process, popen) separately from Task model.
                    pass 

    # To handle transient state (Process objects) which cannot go into Pydantic/DB:
    # We will maintain a parallel dictionary `self._transient_state = {}`
    _transient_processes: Dict[str, subprocess.Popen] = {}

    def _terminate_process(self, url):
        proc = self._transient_processes.get(url)
        if proc:
            try:
                proc.terminate()
            except Exception:
                pass
            self._transient_processes.pop(url, None)

    def pause(self, url: str):
        with self.tasks_lock:
            task = self.tasks.get(url)
            if task and task.status == TaskStatus.DOWNLOADING:
                self._terminate_process(url)
                task.status = TaskStatus.PAUSED
                task.eta = None
                task.speed = None
        self.post("refresh", self._get_all_tasks_dict())

    def resume(self, url: str):
        with self.tasks_lock:
            task = self.tasks.get(url)
            if task and task.status == TaskStatus.PAUSED:
                task.status = TaskStatus.QUEUED
                task.progress = 0.0
        self.post("refresh", self._get_all_tasks_dict())

    def cancel(self, url: str):
        with self.tasks_lock:
            task = self.tasks.get(url)
            if not task: return
            self._terminate_process(url)
            task.status = TaskStatus.CANCELLED
        self.post("refresh", self._get_all_tasks_dict())

    def remove(self, url: str):
        with self.tasks_lock:
            if url in self.tasks:
                del self.tasks[url]
            self._transient_processes.pop(url, None)
        self.post("refresh", self._get_all_tasks_dict())

    def retry(self, url: str):
        with self.tasks_lock:
            task = self.tasks.get(url)
            if task and task.status == TaskStatus.FAILED:
                task.status = TaskStatus.QUEUED
                task.retries = 0
                task.progress = 0.0
        self.post("refresh", self._get_all_tasks_dict())

    def set_max_concurrent(self, n: int):
        self.max_concurrent = max(1, min(6, n))
        self.sem = threading.Semaphore(self.max_concurrent)

    def _get_all_tasks_dict(self):
        # Helper for efficient serialization
        # In a real app we might only send diffs, but for <100 tasks full refresh is fine locally
        with self.tasks_lock:
             return [t.model_dump() for t in self.tasks.values()]

    def get_stats(self):
        with self.tasks_lock:
            completed = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
            count = len(completed)
            total_bytes = 0.0
            
            # Regex for "10.5MiB", "10.5 MiB", "10MB", etc.
            import re
            import os
            pat = re.compile(r"(?P<val>[\d\.]+)\s*(?P<unit>[KMGTP]?)(?:i?B)?", re.IGNORECASE)

            for t in completed:
                # 1. Try file on disk
                if t.filename and os.path.exists(t.filename):
                    try:
                        total_bytes += os.path.getsize(t.filename)
                        continue
                    except Exception:
                        pass # fall back to string parsing

                # 2. Fall back to parsing t.size string
                if t.size:
                    try:
                        # cleanup
                        s = t.size.replace("~", "").strip()
                        m = pat.search(s)
                        if m:
                            val = float(m.group("val"))
                            unit = (m.group("unit") or "").upper()
                            
                            mult = 1
                            if "K" in unit: mult = 1024
                            elif "M" in unit: mult = 1024*1024
                            elif "G" in unit: mult = 1024*1024*1024
                            elif "T" in unit: mult = 1024*1024*1024*1024
                            
                            total_bytes += val * mult
                    except Exception:
                        pass
            
            # Force MB output
            mb_val = total_bytes / (1024 * 1024)
            size_str = f"{mb_val:.2f} MB"

            return {
                "today_count": count,
                "total_data": size_str
            }

    # ---------- Worker Logic (Simplified) ----------
    def _manager_loop(self):
        while not self.stop_event.is_set():
            try:
                with self.tasks_lock:
                    # Fetches
                    info_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.INFO]
                    for t in info_tasks:
                        t.status = TaskStatus.FETCHING_INFO
                        threading.Thread(target=self._fetch_info_worker, args=(t.url,), daemon=True).start()

                    # Downloads
                    dl_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.QUEUED]
                    for t in dl_tasks:
                        if self.sem.acquire(blocking=False):
                            t.status = TaskStatus.DOWNLOADING
                            threading.Thread(target=self._download_worker, args=(t.url,), daemon=True).start()
            except Exception as e:
                logging.error(f"Manager error: {e}")
            time.sleep(0.3)

    def _fetch_info_worker(self, url: str):
        yt = which_yt_dlp()
        if not yt:
            self._mark_failed(url, "yt-dlp not found")
            return

        try:
            cmd = [yt, "--dump-json", "--no-warnings", url]
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", 
                                 creationflags=create_flags_no_window(), startupinfo=create_startupinfo_no_window())
            if res.returncode != 0:
                raise Exception(res.stderr or "Unknown error")
            
            info = json.loads(res.stdout)
            with self.tasks_lock:
                task = self.tasks.get(url)
                if task:
                    task.title = info.get("title", "Unknown")
                    task.vid = info.get("id")
                    task.width = info.get("width")
                    task.height = info.get("height")
                    # Duplicate check logic here...
                    task.status = TaskStatus.QUEUED
                    
            self.post("refresh", self._get_all_tasks_dict())

        except Exception as e:
            self._mark_failed(url, str(e))

    def _download_worker(self, url: str):
        yt = which_yt_dlp()
        with self.tasks_lock:
            task = self.tasks.get(url)
            if not task: 
                self.sem.release()
                return
            folder = task.dest or self.destination
            retries = task.retries
        
        # Strategy selection
        cmd = [yt, "--newline", "--progress", "-P", folder, "-o", DEFAULT_OUTPUT_TPL, "--no-warnings", "--no-overwrites"]
        # ... Add strategy flags ...
        if retries == 0:
            cmd.extend(["--concurrent-fragments", "4"])
            task.strategy = "Strategy A"
        elif retries == 1 and self.aria2c_path:
            cmd.extend(["--downloader", "aria2c", "--downloader-args", "aria2c:-x16 -s16 -k1M"])
            task.strategy = "Strategy B"
        else:
            task.strategy = "Strategy C"
            
        cmd.append(url)

        try:
            # We must use Popen to capture stdout line by line
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                    text=True, encoding="utf-8", creationflags=create_flags_no_window(),
                                    startupinfo=create_startupinfo_no_window())
            
            with self.tasks_lock:
                self._transient_processes[url] = proc
            
            for line in iter(proc.stdout.readline, ""):
                if not line: continue
                # Parse progress
                # ... Regex parsing ...
                # If progress update:
                # self._maybe_post_progress(url, pct)
                
                # Simplified for prototype:
                m = PROGRESS_RE.search(line)
                if m:
                    pct = float(m.group("pct"))
                    with self.tasks_lock:
                        t = self.tasks.get(url)
                        if t:
                            t.progress = pct / 100.0
                            t.speed = (m.group("speed") or "").strip()
                            t.eta = (m.group("eta") or "").strip()
                    


                # Detect Merging
                if "[Merger]" in line or "Merging formats" in line:
                    with self.tasks_lock:
                        t = self.tasks.get(url)
                        if t:
                            t.status = TaskStatus.MERGING
                            t.speed = "Processing"
                            t.eta = "Merging..."
                            
                            # Try to parse filename from merge line: [Merger] Merging formats into "filename"
                            if "into " in line:
                                parts = line.split("into ")
                                if len(parts) > 1:
                                    fname = parts[1].strip().strip('"')
                                    # Ensure absolute path if possible, or join with dest
                                    # But yt-dlp usually outputs full path or relative to CWD
                                    # It runs in CWD. If dest is absolute, it outputs absolute.
                                    t.filename = fname

                            self.post("task_update", t.model_dump())
                            continue
                
                # Check for filename in other lines
                fname_candidate = None
                if "[download] Destination: " in line:
                    fname_candidate = line.split("Destination: ")[1].strip()
                elif "has already been downloaded" in line:
                    # [download] ... has already been downloaded
                    # Extract filename from: [download] filename has already been downloaded
                    prefix = "[download] "
                    suffix = " has already been downloaded"
                    if line.startswith(prefix) and suffix in line:
                        fname_candidate = line[len(prefix):line.index(suffix)].strip()
                
                if fname_candidate:
                    with self.tasks_lock:
                        t = self.tasks.get(url)
                        if t: t.filename = fname_candidate
                    
                # Throttle updates
                now = time.monotonic()
                last = self._last_progress_post_ts.get(url, 0)
                if now - last > 0.5:
                    self._last_progress_post_ts[url] = now
                    # We send single task update for bandwidth efficiency
                    with self.tasks_lock:
                        t = self.tasks.get(url)
                        if t: self.post("task_update", t.model_dump())

            ret = proc.wait()
            with self.tasks_lock:
                self._transient_processes.pop(url, None)
                t = self.tasks.get(url)
                if t:
                    if ret == 0:
                        t.status = TaskStatus.COMPLETED
                        t.progress = 1.0
                    else:
                        # Retry logic
                        if t.retries < 2:
                            t.retries += 1
                            t.status = TaskStatus.QUEUED
                        else:
                            t.status = TaskStatus.FAILED
                            
            self.post("refresh", self._get_all_tasks_dict())
            self.post("stats_update", self.get_stats())

        except Exception as e:
            self._mark_failed(url, str(e))
        finally:
            self.sem.release()

    def _mark_failed(self, url, error):
        with self.tasks_lock:
            t = self.tasks.get(url)
            if t: 
                t.status = TaskStatus.FAILED
                t.title = f"Error: {error}"
        self.post("refresh", self._get_all_tasks_dict())

    def open_folder(self, url: str):
        with self.tasks_lock:
            t = self.tasks.get(url)
            if not t: return # or error
            
            # Use filename if exists, else task.dest, else self.destination
            path_to_open = None
            if t.filename and os.path.exists(t.filename):
               path_to_open = t.filename
            elif t.dest and os.path.exists(t.dest):
               path_to_open = t.dest
            elif os.path.exists(self.destination):
               path_to_open = self.destination
            
            if path_to_open:
                self._open_in_explorer(path_to_open)

    def open_destination(self):
        if os.path.exists(self.destination):
            self._open_in_explorer(self.destination)

    def browse_folder(self):
        # Must run in main thread usually, but for tkinter we can create a ephemeral root
        # This blocks the request! But that's okay for local app.
        import tkinter
        from tkinter import filedialog
        
        try:
            root = tkinter.Tk()
            root.withdraw() # Hide window
            root.attributes('-topmost', True) # Bring to front
            folder = filedialog.askdirectory(initialdir=self.destination, title="Select Download Folder")
            root.destroy()
            return folder
        except Exception as e:
            print(f"Browse error: {e}")
            return None

    def _open_in_explorer(self, path):
        import subprocess
        import platform
        
        if platform.system() == "Windows":
            if os.path.isfile(path):
                subprocess.Popen(['explorer', '/select,', path])
            else:
                os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

download_controller = DownloadController()
