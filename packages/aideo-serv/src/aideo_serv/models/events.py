"""WebSocket event models for real-time task progress."""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class WSEvent(BaseModel):
    """Event pushed to WebSocket clients for task progress updates.

    Event types:
    - status_change: Task lifecycle state changed (queued→running→generating→...)
    - progress: Generation progress update (0-100%)
    - preview: A new intermediate frame/thumbnail is available
    - completed: Task finished successfully, result available
    - error: Task failed, includes error details
    """

    type: str
    task_id: str
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
