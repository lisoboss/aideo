"""Uvicorn entry point for the Runtime HTTP service."""

import uvicorn
from aideo_runtime.app import create_app
from aideo_runtime.config import RuntimeSettings


def main() -> None:
    """Start the Runtime HTTP service with environment configuration."""
    settings = RuntimeSettings.from_env()
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port)
