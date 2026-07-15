"""Registered model metadata."""

from dataclasses import dataclass

from aideo_runtime.capabilities import Capability


@dataclass(frozen=True, slots=True)
class ModelInfo:
    """Describes a model registered with the runtime."""

    id: str
    provider: str
    capability: Capability
    online: bool
    context_length: int | None = None
    max_tokens: int | None = None
