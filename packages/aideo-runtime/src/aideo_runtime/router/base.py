"""Backend routing interface."""

from typing import Protocol

from aideo_runtime.backend import Backend
from aideo_runtime.models import BackendRequest, BackendState


class Router(Protocol):
    """Selects a backend from eligible candidates for a request."""

    def select(
        self,
        request: BackendRequest,
        candidates: list[tuple[Backend, BackendState]],
    ) -> Backend:
        """Select one backend using a routing policy."""
        ...
