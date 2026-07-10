"""Abstract base for all inference providers."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


class BaseProvider(ABC):
    """Every inference provider (video, speech, chat, vision) implements this."""

    @abstractmethod
    async def load(self) -> None:
        """Load the model into memory."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier (e.g. 'ltx2', 'faster-whisper')."""
        ...

    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        """Return True if the model is ready for inference."""
        ...

    @abstractmethod
    async def run(self, **kwargs) -> AsyncGenerator[dict, None]:
        """Execute inference, yielding progress dicts then a final result.

        Progress yields: ``{"progress": float, "message": str}``
        Final yield:     ``{"progress": 100.0, "result_data": {...}}``
        """
        ...
