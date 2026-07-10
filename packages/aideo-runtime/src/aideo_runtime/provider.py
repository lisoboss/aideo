"""Abstract base for all inference providers."""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ProgressStatus(BaseModel):
    """Emitted during ``run()`` — intermediate progress or final result."""

    progress: float = 0.0
    message: str = ""
    result_data: dict | None = None


class BaseProvider(ABC):
    """Every inference provider implements this.

    Subclasses MUST set ``provider_name`` as a class-level str, e.g.
    ``provider_name = "faster-whisper@speech"``.
    """

    provider_name: str   # set by subclass

    def __init__(self) -> None:
        self._cancel_event = asyncio.Event()

    @abstractmethod
    async def load(self) -> None:
        """Load the model into memory. Called on first request."""
        ...

    @abstractmethod
    async def unload(self) -> None:
        """Release the model from memory. Called after idle timeout."""
        ...

    @abstractmethod
    async def run(self, **kwargs) -> AsyncGenerator[ProgressStatus, None]:
        """Execute inference, yielding intermediate progress then final result.

        The last yield should have ``result_data`` populated.

        Providers should periodically check ``self._cancel_event.is_set()``
        during long operations and exit early if cancelled.
        """
        ...

    def cancel(self) -> None:
        """Signal the provider to stop inference. Client disconnected."""
        self._cancel_event.set()

    def reset_cancel(self) -> None:
        """Clear the cancel flag before starting a new run."""
        self._cancel_event.clear()

    @property
    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    @property
    def is_loaded(self) -> bool:
        """Whether the model is currently in memory."""
        return getattr(self, "_loaded", False)
