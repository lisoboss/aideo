"""Abstract interface for text-to-video providers."""

from abc import abstractmethod
from collections.abc import AsyncGenerator

from aideo_runtime.provider import BaseProvider

PROVIDERS = {}


class VideoProvider(BaseProvider):
    """A provider that turns a text prompt into a video."""

    @abstractmethod
    async def run(
        self, prompt: str, params: dict | None = None, task_id: str | None = None
    ) -> AsyncGenerator[dict, None]:
        """Generate a video from a text prompt."""
        ...


def register_provider(provider: type[VideoProvider]) -> None:
    """Register a video provider."""
    if not issubclass(provider, VideoProvider):
        raise TypeError(f"{provider} is not a subclass of VideoProvider")
    if provider.provider_name in PROVIDERS:
        raise ValueError(f"Provider {provider.provider_name} is already registered")
    PROVIDERS[provider.provider_name] = provider


def get_provider(name: str) -> type[VideoProvider]:
    """Get a video provider by name."""
    if name not in PROVIDERS:
        raise ValueError(f"Provider {name} is not registered")
    return PROVIDERS[name]
