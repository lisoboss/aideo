"""Normalized streaming event models."""

from dataclasses import dataclass, field
from typing import Any, TypeAlias


@dataclass(slots=True)
class DeltaEvent:
    """An incremental output fragment."""

    delta: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProgressEvent:
    """A long-running inference progress update."""

    progress: float
    message: str | None = None


@dataclass(slots=True)
class LogEvent:
    """A non-terminal backend log message."""

    message: str
    level: str = "info"


@dataclass(slots=True)
class DoneEvent:
    """The terminal success event."""

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ErrorEvent:
    """The terminal failure event."""

    message: str
    code: str | None = None
    retryable: bool = False
    details: dict[str, Any] = field(default_factory=dict)


BackendEvent: TypeAlias = DeltaEvent | ProgressEvent | LogEvent | DoneEvent | ErrorEvent
