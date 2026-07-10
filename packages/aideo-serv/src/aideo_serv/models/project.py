"""Project data models for aideo-serv v2."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Canvas data (round-trip compatible with iPad SwiftData)
# ---------------------------------------------------------------------------


class CanvasViewport(BaseModel):
    """Scroll/zoom state of the infinite canvas."""

    center_x: float = 0.0
    center_y: float = 0.0
    scale: float = 1.0


class CanvasData(BaseModel):
    """The full canvas graph — 1:1 with iPad's 4 node arrays + connections."""

    prompt_blocks: list[dict] = Field(default_factory=list)
    media_outputs: list[dict] = Field(default_factory=list)
    reference_nodes: list[dict] = Field(default_factory=list)
    ai_enhance_nodes: list[dict] = Field(default_factory=list)
    connections: list[dict] = Field(default_factory=list)
    viewport: CanvasViewport = Field(default_factory=CanvasViewport)


# ---------------------------------------------------------------------------
# Project CRUD models
# ---------------------------------------------------------------------------


class ProjectCreate(BaseModel):
    """Payload for creating a new project."""

    name: str = Field(min_length=1, max_length=256, default="Untitled Project")
    canvas_data: CanvasData = Field(default_factory=CanvasData)
    metadata: dict = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    """Partial update — all fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=256)
    canvas_data: CanvasData | None = None
    metadata: dict | None = None


class Project(BaseModel):
    """A canvas project."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    canvas_data: CanvasData = Field(default_factory=CanvasData)
    metadata: dict = Field(default_factory=dict)
    task_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectListResponse(BaseModel):
    """Paginated project list."""

    items: list[Project]
    total: int
    offset: int
    limit: int
