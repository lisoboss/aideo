"""Abstract interface for text conversation (LLM) providers."""

from abc import abstractmethod
from collections.abc import AsyncGenerator

from aideo_runtime.provider import BaseProvider


class ChatProvider(BaseProvider):
    """A provider for conversational text generation."""

    @abstractmethod
    async def run(
        self,
        messages: list[dict],
        params: dict | None = None,
        task_id: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        """Generate a reply from a conversation history."""
        ...
