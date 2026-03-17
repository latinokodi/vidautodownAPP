from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from ..core.controller import download_controller
from ..core.database import Database
from ..core.models import Task
from ..core.crawler import crawler_service

router = APIRouter()

class AddUrlRequest(BaseModel):
    text: str

class SettingsUpdate(BaseModel):
    max_concurrent: Optional[int] = None
    destination: Optional[str] = None

@router.post("/tasks")
def add_tasks(req: AddUrlRequest):
    download_controller.add_urls(req.text)
    return {"status": "ok"}

@router.get("/tasks", response_model=List[Task])
def get_tasks():
    with download_controller.tasks_lock:
        return list(download_controller.tasks.values())

@router.get("/stats")
def get_stats():
    return download_controller.get_stats()

@router.post("/tasks/{url_safe}/pause")
def pause_task(url_safe: str):
    # In real app, we'd use ID or decode safe URL
    # For prototype, we assume client sends url encoded or we use body
    pass # See action endpoint below

class ActionRequest(BaseModel):
    url: str
    action: str # pause, resume, cancel, retry, remove

@router.post("/action")
def task_action(req: ActionRequest):
    if req.action == "pause":
        download_controller.pause(req.url)
    elif req.action == "resume":
        download_controller.resume(req.url)
    elif req.action == "cancel":
        download_controller.cancel(req.url)
    elif req.action == "retry":
        download_controller.retry(req.url)
    elif req.action == "remove":
        download_controller.remove(req.url)
    elif req.action == "open_folder":
        download_controller.open_folder(req.url)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    return {"status": "ok"}

@router.get("/settings")
def get_settings():
    if not download_controller.db:
        return {}
    return {
        "max_concurrent": download_controller.max_concurrent,
        "destination": download_controller.destination,
        # "last_folder": ...
    }

@router.post("/settings")
def update_settings(settings: SettingsUpdate):
    if settings.max_concurrent:
        download_controller.set_max_concurrent(settings.max_concurrent)
        if download_controller.db:
            download_controller.db.set_setting("max_concurrent", settings.max_concurrent)
            
    if settings.destination:
        download_controller.destination = settings.destination
        # Ensure dir exists
        import os
        os.makedirs(settings.destination, exist_ok=True)
        if download_controller.db:
            download_controller.db.set_setting("last_folder", settings.destination)
            
    return {"status": "ok"}

@router.post("/browse_folder")
def browse_folder():
    folder = download_controller.browse_folder()
    return {"folder": folder}

@router.post("/open_destination")
def open_destination():
    download_controller.open_destination()
    return {"status": "ok"}


# Crawler API endpoints

class CrawlRequest(BaseModel):
    page_url: str


@router.post("/crawl")
def start_crawl(req: CrawlRequest):
    """Start URL extraction from a web page using yt-dlp."""
    if not crawler_service:
        raise HTTPException(status_code=503, detail="Crawler service not initialized")

    if not req.page_url or not req.page_url.strip():
        raise HTTPException(status_code=400, detail="URL is required")

    crawler_service.extract_urls(req.page_url.strip())
    return {"status": "started"}


@router.post("/crawl/cancel")
def cancel_crawl():
    """Cancel any active URL extraction."""
    if crawler_service:
        crawler_service.cancel()
    return {"status": "cancelled"}
