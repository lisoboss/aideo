"""Abstract interface for text conversation (LLM) providers."""

from abc import abstractmethod
from collections.abc import AsyncGenerator

from aideo_runtime.provider import BaseProvider

PROVIDERS = {}


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


def register_provider(provider: type[ChatProvider]) -> None:
    """Register a chat provider."""
    if not issubclass(provider, ChatProvider):
        raise TypeError(f"{provider} is not a subclass of ChatProvider")
    if provider.provider_name in PROVIDERS:
        raise ValueError(f"Provider {provider.provider_name} is already registered")
    PROVIDERS[provider.provider_name] = provider


def get_provider(name: str) -> type[ChatProvider]:
    """Get a chat provider by name."""
    if name not in PROVIDERS:
        raise ValueError(f"Provider {name} is not registered")
    return PROVIDERS[name]
