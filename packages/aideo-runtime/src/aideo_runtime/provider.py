"""Abstract base for all inference providers."""

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
        """
        ...

    @property
    def is_loaded(self) -> bool:
        """Whether the model is currently in memory."""
        return getattr(self, "_loaded", False)
