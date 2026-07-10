"""Abstract interface for image-to-text (vision) providers."""

from abc import abstractmethod
from collections.abc import AsyncGenerator

from aideo_runtime.provider import BaseProvider


class VisionProvider(BaseProvider):
    """A provider that describes images in text."""

    @abstractmethod
    async def run(
        self,
        image_path: str,
        prompt: str = "",
        params: dict | None = None,
        task_id: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Generate text from an image, yielding progress then result."""
        ...
