"""Per-connection event queues for WebSocket broadcast."""

import asyncio
from uuid import UUID


class ConnectionManager:
    """Per-connection event queues, broadcast via put_nowait (thread-safe)."""

    def __init__(self):
        """Initialize with empty queue registry."""
        self._queues: dict[UUID, list[asyncio.Queue]] = {}

    def subscribe(self, task_id: UUID) -> asyncio.Queue:
        """Create a new queue for a WS connection."""
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
