"""Abstract base for all inference providers."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Optional

from pydantic import BaseModel


class ProgressStatus(BaseModel):
    progress: float
    message: str
    result_data: Optional[dict]


class BaseProvider(ABC):
    """Every inference provider (video, speech, chat, vision) implements this."""

    @abstractmethod
    async def __load__(self) -> None:
        """Load the model into memory."""
        ...

    @abstractmethod
    async def __unload__(self) -> None:
        """Unload the model from memory."""
        ...

    async def __aenter__(self) -> "BaseProvider":
        await self.__load__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.__unload__()

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier (e.g. 'ltx2@video.provider', 'faster-whisper@speech.provider')."""
        ...

    @abstractmethod
    async def submit(self, **kwargs) -> str:
        """Return a unique task ID for this inference run."""
        ...

    @abstractmethod
    async def cancel(self) -> None:
        """Cancel an inference run."""
        ...

    @abstractmethod
    async def result(self) -> dict:
        """Return the final result of an inference run, if available."""
        ...

    @abstractmethod
    async def progress(self) -> AsyncGenerator[ProgressStatus, None]:
        """Execute inference, yielding progress dicts then a final result.

        Progress yields: ``{"progress": float, "message": str}``
        Final yield:     ``{"progress": 100.0, "message": str, "result_data": {...}}``
        """
        ...
