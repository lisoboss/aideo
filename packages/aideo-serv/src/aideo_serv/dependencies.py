"""FastAPI dependency injection for aideo-serv."""

from aideo_serv.services.connection_manager import (  # noqa: F401
    get_connection_manager,
    set_connection_manager,
)
from aideo_serv.services.task_service import TaskService

_task_service: TaskService | None = None


def get_task_service() -> TaskService:
    """Dependency: return the TaskService singleton."""
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service


def set_task_service(svc: TaskService) -> None:
    """Replace the global TaskService singleton (for testing)."""
    global _task_service
    _task_service = svc
