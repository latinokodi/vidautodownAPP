"""
CrawlerService module for extracting video URLs from web pages using yt-dlp.

This service uses yt-dlp's --flat-playlist --dump-json feature to extract
video URLs from any supported site (1000+ platforms) without downloading.
"""

import subprocess
import threading
import queue
import json
import logging
import shutil
import os
from typing import Optional, List, Dict, Any

# Windows subprocess flags to prevent console window popup
WIN32 = os.name == "nt"


def create_flags_no_window() -> int:
    """Return CREATE_NO_WINDOW flag on Windows to prevent console popup."""
    return subprocess.CREATE_NO_WINDOW if WIN32 else 0


def create_startupinfo_no_window():
    """Return STARTUPINFO configured to hide console window on Windows."""
    if not WIN32:
        return None
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    return si


def which_yt_dlp() -> Optional[str]:
    """Find yt-dlp executable in PATH."""
    return shutil.which("yt-dlp")


class CrawlerService:
    """
    Service for extracting video URLs from web pages using yt-dlp.

    Uses yt-dlp --flat-playlist --dump-json to extract URLs without downloading.
    Runs extraction in background threads and sends progress messages via queue.
    """

    def __init__(self, msg_queue: queue.Queue):
        """
        Initialize CrawlerService with a message queue for broadcasting.

        Args:
            msg_queue: Queue for sending messages to WebSocket bridge
        """
        self.msg_queue = msg_queue
        self._active_process: Optional[subprocess.Popen] = None
        self._cancel_event = threading.Event()
        self._extraction_thread: Optional[threading.Thread] = None

    def _post(self, msg_type: str, payload: Any):
        """Send a message to the queue."""
        self.msg_queue.put((msg_type, payload))

    def extract_urls(self, page_url: str):
        """
        Start extracting video URLs from a web page in background thread.

        The subprocess is started synchronously to allow immediate testing,
        while output processing runs in a background thread.

        Args:
            page_url: URL of the page to extract videos from
        """
        # Clear any previous cancel state
        self._cancel_event.clear()

        yt_path = which_yt_dlp()
        if not yt_path:
            self._post("crawl_error", {"error": "yt-dlp not found"})
            return

        # Check if cancelled before starting
        if self._cancel_event.is_set():
            self._post("crawl_cancelled", {})
            return

        # Send start message
        self._post("crawl_start", {"page_url": page_url})

        try:
            # Build yt-dlp command for flat playlist extraction
            cmd = [
                yt_path,
                "--flat-playlist",
                "--dump-json",
                "--no-warnings",
                page_url
            ]

            # Start subprocess with hidden console (synchronously for testability)
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                creationflags=create_flags_no_window(),
                startupinfo=create_startupinfo_no_window()
            )

            self._active_process = proc

            # Start background thread to read output
            def output_reader():
                urls_found: List[Dict[str, str]] = []
                count = 0

                try:
                    # Read JSON lines from stdout
                    for line in proc.stdout:
                        if self._cancel_event.is_set():
                            proc.terminate()
                            self._post("crawl_cancelled", {})
                            return

                        line = line.strip()
                        if not line:
                            continue

                        try:
                            info = json.loads(line)
                            url_info = {
                                "url": info.get("url", ""),
                                "title": info.get("title", "Unknown"),
                                "id": info.get("id", "")
                            }
                            urls_found.append(url_info)
                            count += 1

                            # Send progress update every 5 items
                            if count % 5 == 0:
                                self._post("crawl_progress", {
                                    "count": count,
                                    "latest": url_info.get("title", "")
                                })
                        except json.JSONDecodeError:
                            # Skip malformed JSON lines
                            continue

                    # Wait for process to complete
                    proc.wait()
                    self._active_process = None

                    if self._cancel_event.is_set():
                        self._post("crawl_cancelled", {})
                        return

                    if proc.returncode != 0:
                        stderr_output = proc.stderr.read() if proc.stderr else ""
                        error_msg = stderr_output.strip() or f"Process exited with code {proc.returncode}"
                        self._post("crawl_error", {"error": error_msg})
                        return

                    # Send completion message with all found URLs
                    self._post("crawl_complete", {"urls": urls_found})

                except Exception as e:
                    self._active_process = None
                    if not self._cancel_event.is_set():
                        self._post("crawl_error", {"error": str(e)})

            # Start output reader thread
            self._extraction_thread = threading.Thread(target=output_reader, daemon=True)
            self._extraction_thread.start()

        except Exception as e:
            self._active_process = None
            self._post("crawl_error", {"error": str(e)})

    def cancel(self):
        """
        Cancel any active URL extraction.

        Sets the cancellation event and terminates the active subprocess.
        """
        self._cancel_event.set()

        if self._active_process:
            try:
                self._active_process.terminate()
            except Exception:
                pass
            self._active_process = None

        self._post("crawl_cancelled", {})


# Singleton instance
crawler_service: Optional[CrawlerService] = None


def init_crawler_service(msg_queue: queue.Queue):
    """
    Initialize the singleton CrawlerService instance.

    Args:
        msg_queue: Queue for sending messages to WebSocket bridge
    """
    global crawler_service
    crawler_service = CrawlerService(msg_queue)