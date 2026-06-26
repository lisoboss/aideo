"""Task data models for aideo-serv."""

from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    """Video generation task lifecycle states."""

    QUEUED = "queued"
    RUNNING = "running"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskCreate(BaseModel):
    """Payload for creating a new video generation task."""

    prompt: str = Field(min_length=1, max_length=4096)
    params: dict | None = None


class Task(BaseModel):
    """A video generation task with full lifecycle state."""

    id: UUID
    prompt: str
    params: dict | None = None
    status: TaskStatus = TaskStatus.QUEUED
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result_path: str | None = None
    result_url: str | None = None
    previews: list[str] = Field(default_factory=list)
    error_message: str | None = None


class TaskListResponse(BaseModel):
    """Paginated list of tasks."""

    tasks: list[Task]
    total: int
    offset: int
    limit: int
