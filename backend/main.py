import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from .core.controller import download_controller
from .core.crawler import init_crawler_service, crawler_service
from .core.database import Database
from .api.routes import router as api_router
from .api.websockets import manager

DB_PATH = "vidautodown.db" # In root or backend? Let's put in root for compatibility

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db = Database(DB_PATH)
    download_controller.set_db(db)

    # Initialize crawler service with shared message queue
    init_crawler_service(download_controller.msg_queue)
    
    # Restore settings
    max_c = db.get_setting("max_concurrent", 2)
    download_controller.set_max_concurrent(max_c)
    
    last_folder = db.get_setting("last_folder")
    if last_folder and os.path.isdir(last_folder):
        download_controller.destination = last_folder

    # Restore tasks
    tasks = db.load_tasks()
    with download_controller.tasks_lock:
        for t in tasks:
            if t.status not in ("completed", "cancelled"):
                if t.status == "downloading": t.status = "queued"
                download_controller.tasks[t.url] = t

    # Background task to drain controller queue -> WebSocket
    asyncio.create_task(bridge_queue_to_ws())
    
    # Auto-save loop
    asyncio.create_task(autosave_loop())

    yield
    
    # Shutdown
    # Save state
    with download_controller.tasks_lock:
        snap = list(download_controller.tasks.values())
    db.save_tasks(snap)
    db.close()
    download_controller.stop_event.set()

async def bridge_queue_to_ws():
    while True:
        # Non-blocking get from Sync Queue
        try:
            while not download_controller.msg_queue.empty():
                msg_type, payload = download_controller.msg_queue.get_nowait()
                await manager.broadcast({"type": msg_type, "payload": payload})
            await asyncio.sleep(0.1)
        except Exception:
            await asyncio.sleep(0.1)

async def autosave_loop():
    while True:
        await asyncio.sleep(10)
        try:
            if download_controller.db:
                with download_controller.tasks_lock:
                    snap = list(download_controller.tasks.values())
                download_controller.db.save_tasks(snap)
        except Exception:
            pass

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow dev frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle client messages if any (e.g. ping)
    except Exception:
        manager.disconnect(websocket)
