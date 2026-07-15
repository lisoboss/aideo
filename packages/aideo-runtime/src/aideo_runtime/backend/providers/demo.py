"""Deterministic demo provider used for local HTTP contract verification."""

from collections.abc import AsyncIterator

from aideo_runtime.capabilities import Capability
from aideo_runtime.models import (
    BackendEvent,
    BackendRequest,
    BackendResponse,
    DeltaEvent,
    DoneEvent,
    HealthStatus,
    ModelInfo,
    TextOutput,
)

_MODELS = [
    ModelInfo(
        "demo-chat",
        "demo",
        Capability.CHAT,
        online=False,
        context_length=4096,
        max_tokens=1024,
    )
]


class DemoBackend:
    """A local, deterministic backend that supports chat requests."""

    async def invoke(self, request: BackendRequest) -> BackendResponse:
        """Return a deterministic response for a chat request."""
        self._validate(request)
        return BackendResponse(
            outputs=[TextOutput("demo response")],
            metadata={"model": request.model, "provider": "demo"},
        )

    async def stream(self, request: BackendRequest) -> AsyncIterator[BackendEvent]:
        """Yield a deterministic delta followed by a completion event."""
        self._validate(request)
        yield DeltaEvent("demo response")
        yield DoneEvent({"model": request.model, "provider": "demo"})

    async def health(self) -> HealthStatus:
        """Return the fixed health status for this in-process backend."""
        return HealthStatus.HEALTHY

    async def models(self) -> list[ModelInfo]:
        """Return the demo model catalog."""
        return models()

    def _validate(self, request: BackendRequest) -> None:
        """Reject requests outside the intentionally narrow demo contract."""
        if request.capability is not Capability.CHAT:
            raise ValueError("Demo backend supports only chat")
        if request.model not in {model.id for model in _MODELS}:
            raise ValueError(f"Demo model is not registered: {request.model}")


def models() -> list[ModelInfo]:
    """Return metadata for models served by the demo provider."""
    return list(_MODELS)


def create_backend(*_: object) -> DemoBackend:
    """Create the demo provider's backend instance."""
    return DemoBackend()
