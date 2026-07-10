"""Asset (reference image/video) data models."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Asset(BaseModel):
    """Metadata for an uploaded reference file (image, video, audio)."""

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID | None = None
    filename: str
    content_type: str  # MIME type, e.g. image/jpeg
    size: int  # bytes
    media_type: str = "image"  # image | video | audio
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    url: str = ""
    metadata: dict = Field(default_factory=dict)


class AssetListResponse(BaseModel):
    """Paginated asset list."""

    items: list[Asset]
    total: int
    offset: int
    limit: int
