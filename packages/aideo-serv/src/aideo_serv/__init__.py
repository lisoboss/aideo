"""aideo-serv — AI Video Generator Studio API server."""


def main() -> None:
    """CLI entry point (backwards-compatible)."""
    print("Hello from aideo-serv!")


from aideo_serv.app import create_app  # noqa: E402
from aideo_serv.config import Settings  # noqa: E402
from aideo_serv.models.task import Task, TaskCreate, TaskStatus  # noqa: E402

__all__ = ["main", "create_app", "Settings", "Task", "TaskCreate", "TaskStatus"]
