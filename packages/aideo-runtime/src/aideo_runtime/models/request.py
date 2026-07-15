"""Unified backend request model."""

from dataclasses import dataclass, field
from typing import Any

from aideo_runtime.capabilities import Capability


@dataclass(slots=True)
class BackendRequest:
    """A provider-independent inference request.

    Attributes:
        capability: Capability the agent wants to invoke.
        model: Registry model identifier.
        input: Capability-specific, JSON-compatible source input.
        parameters: Optional generation or inference parameters.
        stream: Whether incremental events are requested.
    """

    capability: Capability
    model: str
    input: dict[str, Any]
    parameters: dict[str, Any] = field(default_factory=dict)
    stream: bool = False
