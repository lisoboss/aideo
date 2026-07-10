"""Abstract interface for text-to-video providers."""

from abc import abstractmethod
from collections.abc import AsyncGenerator

from aideo_runtime.provider import BaseProvider


class VideoProvider(BaseProvider):
    """A provider that turns a text prompt into a video."""

    @abstractmethod
    async def run(
        self, prompt: str, params: dict | None = None, task_id: str | None = None
    ) -> AsyncGenerator[dict, None]:
        """Generate a video from a text prompt."""
        ...
