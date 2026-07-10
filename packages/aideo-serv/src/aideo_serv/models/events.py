"""Event models for client-facing WebSocket progress updates."""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class WSEvent(BaseModel):
    """Event pushed to WebSocket clients for task progress updates."""

    type: str
    task_id: str
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
