"""Abstract interface for speech-to-text providers."""

from abc import abstractmethod
from collections.abc import AsyncGenerator

from aideo_runtime.provider import BaseProvider


class SpeechProvider(BaseProvider):
    """A provider that transcribes audio into text."""

    @abstractmethod
    async def run(
        self,
        audio_path: str,
        language: str | None = None,
        params: dict | None = None,
        task_id: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Transcribe an audio file, yielding progress then result."""
        ...
