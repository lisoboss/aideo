"""aideo-cli — CLI client for aideo-serv."""

from aideo_cli.client import AideoClient
from aideo_cli.main import app


def main() -> None:
    """Entry point for the aideo CLI."""
    app()


__all__ = ["AideoClient", "app", "main"]
