"""aideo-serv — AI Video Generator Studio API server."""

from aideo_serv.app import create_app
from aideo_serv.config import Settings
from aideo_serv.models.task import Task, TaskCreate, TaskStatus


def main() -> None:
    """CLI entry point — starts the aideo-serv API server."""
    from aideo_serv.main import main as _server_main

    _server_main()


__all__ = ["main", "create_app", "Settings", "Task", "TaskCreate", "TaskStatus"]
