"""Provider-neutral inference runtime public API."""

from aideo_runtime.app import create_app
from aideo_runtime.backend import Backend, BackendManager, HttpBackend
from aideo_runtime.capabilities import Capability
from aideo_runtime.config import RuntimeSettings
from aideo_runtime.models import BackendRequest, BackendResponse, ModelInfo
from aideo_runtime.paths import PathSettings
from aideo_runtime.registry import ModelRegistry
from aideo_runtime.server import main as server_main


def main() -> None:
    """Start the Runtime HTTP service."""
    server_main()


__all__ = [
    "Backend",
    "BackendManager",
    "BackendRequest",
    "BackendResponse",
    "Capability",
    "HttpBackend",
    "ModelInfo",
    "ModelRegistry",
    "PathSettings",
    "RuntimeSettings",
    "create_app",
    "main",
]
