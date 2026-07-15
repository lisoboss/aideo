"""Backend lifecycle and health management."""

from collections.abc import Mapping
from time import monotonic

from aideo_runtime.backend.base import Backend
from aideo_runtime.models import BackendState, HealthStatus


class BackendManager:
    """Owns registered backends and their operational state."""

    def __init__(self) -> None:
        """Initialize an empty backend collection."""
        self._backends: dict[str, Backend] = {}
        self._states: dict[str, BackendState] = {}

    def register(
        self, backend_id: str, backend: Backend, *, max_jobs: int | None = None
    ) -> None:
        """Register a backend and initialize its state."""
        if backend_id in self._backends:
            raise ValueError(f"Backend already registered: {backend_id}")
        self._backends[backend_id] = backend
        self._states[backend_id] = BackendState(max_jobs=max_jobs)

    def unregister(self, backend_id: str) -> Backend:
        """Remove and return a backend."""
        self._states.pop(backend_id)
        return self._backends.pop(backend_id)

    def get(self, backend_id: str) -> Backend:
        """Return a registered backend by identifier."""
        return self._backends[backend_id]

    @property
    def states(self) -> Mapping[str, BackendState]:
        """Return a read-only view of current backend states."""
        return self._states

    async def check_health(self, backend_id: str) -> HealthStatus:
        """Probe one backend and update its health and latency state."""
        started = monotonic()
        status = await self._backends[backend_id].health()
        state = self._states[backend_id]
        state.latency = monotonic() - started
        state.healthy = status is HealthStatus.HEALTHY
        return status

    async def check_all_health(self) -> dict[str, HealthStatus]:
        """Probe every backend and return statuses by backend identifier."""
        return {
            backend_id: await self.check_health(backend_id)
            for backend_id in self._backends
        }
