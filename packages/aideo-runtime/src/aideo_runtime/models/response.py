"""Unified backend response and output models."""

from dataclasses import dataclass, field
from typing import Any, TypeAlias


@dataclass(slots=True)
class TextOutput:
    """A textual model output."""

    text: str
    mime_type: str = "text/plain"


@dataclass(slots=True)
class ImageOutput:
    """An image output represented by a URI or inline data."""

    uri: str
    mime_type: str = "image/png"


@dataclass(slots=True)
class VideoOutput:
    """A video output represented by a URI or inline data."""

    uri: str
    mime_type: str = "video/mp4"


@dataclass(slots=True)
class AudioOutput:
    """An audio output represented by a URI or inline data."""

    uri: str
    mime_type: str = "audio/mpeg"


@dataclass(slots=True)
class EmbeddingOutput:
    """A vector embedding output."""

    values: list[float]
    index: int = 0


Output: TypeAlias = (
    TextOutput | ImageOutput | VideoOutput | AudioOutput | EmbeddingOutput
)


@dataclass(slots=True)
class BackendResponse:
    """A provider-independent completed inference response."""

    outputs: list[Output] = field(default_factory=list)
    usage: dict[str, int | float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
