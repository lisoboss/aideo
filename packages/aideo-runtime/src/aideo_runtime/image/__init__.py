"""Image edit / upscale providers."""

import aideo_runtime.image.stub  # noqa: F401
from aideo_runtime.image.provider import (
    PROVIDERS,
    ImageProvider,
    get_provider,
    register_provider,
)

__all__ = ["PROVIDERS", "ImageProvider", "get_provider", "register_provider"]
