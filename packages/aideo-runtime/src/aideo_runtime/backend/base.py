"""Backend interface."""

from collections.abc import AsyncIterator
from typing import Protocol

from aideo_runtime.models import (
    BackendEvent,
    BackendRequest,
    BackendResponse,
    HealthStatus,
    ModelInfo,
)


class Backend(Protocol):
    """A provider-independent inference backend."""

    async def invoke(self, request: BackendRequest) -> BackendResponse:
        """Run a non-streaming inference request."""
        ...

    def stream(self, request: BackendRequest) -> AsyncIterator[BackendEvent]:
        """Run an inference request that produces incremental events."""
        ...

    async def health(self) -> HealthStatus:
        """Return the backend health status."""
        ...

    async def models(self) -> list[ModelInfo]:
        """Return models exposed by the backend."""
        ...
