"""Per-connection event queues for WebSocket broadcast."""

import asyncio
from uuid import UUID


class ConnectionManager:
    """Per-connection event queues, broadcast via put_nowait (thread-safe).

    Supports both per-task subscriptions (WS /ws/tasks/{id}) and
    per-project subscriptions (WS /ws/projects/{id}).
    """

    def __init__(self):
        """Initialize with empty queue registries."""
        # Per-task queues: {task_id: [queue, ...]}
        self._queues: dict[UUID, list[asyncio.Queue]] = {}
        # Per-project queues: {project_id: [queue, ...]}
        self._project_queues: dict[UUID, list[asyncio.Queue]] = {}

    # ------------------------------------------------------------------
    # Per-task subscriptions (v1 + backward compat)
    # ------------------------------------------------------------------

    def subscribe(self, task_id: UUID) -> asyncio.Queue:
        """Create a new queue for a WS connection listening to a task."""
        q: asyncio.Queue = asyncio.Queue()
        self._queues.setdefault(task_id, []).append(q)
        return q

    def broadcast(self, task_id: UUID, event: dict) -> None:
        """Push event to all connected clients for a task."""
        for q in self._queues.get(task_id, []):
            q.put_nowait(event)

    def close_task(self, task_id: UUID) -> None:
        """Push sentinel (None) to all queues for a task, then clean up."""
        for q in self._queues.pop(task_id, []):
            q.put_nowait(None)

    def unsubscribe(self, task_id: UUID, q: asyncio.Queue) -> None:
        """Remove a single connection's queue."""
        queues = self._queues.get(task_id, [])
        if q in queues:
            queues.remove(q)
            if not queues:
                self._queues.pop(task_id, None)

    # ------------------------------------------------------------------
    # Per-project subscriptions (v2 multiplexed WS)
    # ------------------------------------------------------------------

    def subscribe_project(self, project_id: UUID) -> asyncio.Queue:
        """Create a new queue for a WS connection listening to a project."""
        q: asyncio.Queue = asyncio.Queue()
        self._project_queues.setdefault(project_id, []).append(q)
        return q

    def broadcast_project(self, project_id: UUID, event: dict) -> None:
        """Push event to all connected clients for a project."""
        for q in self._project_queues.get(project_id, []):
            q.put_nowait(event)

    def close_project(self, project_id: UUID) -> None:
        """Push sentinel (None) to all queues for a project, then clean up."""
        for q in self._project_queues.pop(project_id, []):
            q.put_nowait(None)

    def unsubscribe_project(self, project_id: UUID, q: asyncio.Queue) -> None:
        """Remove a single connection's queue from a project."""
        queues = self._project_queues.get(project_id, [])
        if q in queues:
            queues.remove(q)
            if not queues:
                self._project_queues.pop(project_id, None)


_mgr: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """Return the global ConnectionManager singleton."""
    global _mgr
    if _mgr is None:
        _mgr = ConnectionManager()
    return _mgr


def set_connection_manager(mgr: ConnectionManager) -> None:
    """Replace the global singleton (for testing)."""
    global _mgr
    _mgr = mgr
