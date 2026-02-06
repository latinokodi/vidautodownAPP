from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import time

class TaskStatus(str, Enum):
    QUEUED = "queued"
    INFO = "info"
    FETCHING_INFO = "fetching-info"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"
    MERGING = "merging"

class TaskStrategy(str, Enum):
    STRATEGY_A = "Strategy A"
    STRATEGY_B = "Strategy B"
    STRATEGY_C = "Strategy C"

class Task(BaseModel):
    url: str
    status: TaskStatus = TaskStatus.QUEUED
    progress: float = 0.0
    title: str = "Fetching info..."
    filename: Optional[str] = None
    size: Optional[str] = None
    speed: Optional[str] = None
    eta: Optional[str] = None
    retries: int = 0
    added_ts: float = Field(default_factory=time.time)
    vid: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    dest: Optional[str] = None
    strategy: Optional[str] = None

    class Config:
        from_attributes = True
