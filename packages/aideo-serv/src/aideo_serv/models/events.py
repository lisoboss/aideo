"""WebSocket event models for real-time task progress."""

from datetime import datetime, timezone
from typing import Literal

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


# ---------------------------------------------------------------------------
# Internal WebSocket protocol between aideo-serv and inference services
# ---------------------------------------------------------------------------

ServiceType = Literal["aideo-runtime", "ltx2", "whisper"]
TaskType = Literal["video_generation", "speech_to_text", "text_conversation", "image_to_text"]
MessageType = Literal[
    "register", "registered",
    "task_submit", "task_cancel",
    "progress", "completed", "error", "cancelled",
]


class InferenceRegistration(BaseModel):
    """First message sent by an inference service after WS connect."""

    type: str = "register"
    service_type: ServiceType
    capabilities: list[TaskType]
    version: str = "0.1.0"


class InferenceMessage(BaseModel):
    """Generic message envelope for the internal inference protocol.

    Direction-neutral: both aideo-serv and inference services use this
    shape to exchange messages over the internal WebSocket.
    """

    type: MessageType
    task_id: str | None = None
    task_type: TaskType | None = None
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
