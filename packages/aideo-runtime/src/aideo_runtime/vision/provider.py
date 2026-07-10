"""Abstract interface for image-to-text (vision) providers."""

from abc import abstractmethod
from collections.abc import AsyncGenerator

from aideo_runtime.provider import BaseProvider

PROVIDERS = {}


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


def register_provider(provider: type[VisionProvider]) -> None:
    """Register a vision provider."""
    if not issubclass(provider, VisionProvider):
        raise TypeError(f"{provider} is not a subclass of VisionProvider")
    if provider.provider_name in PROVIDERS:
        raise ValueError(f"Provider {provider.provider_name} is already registered")
    PROVIDERS[provider.provider_name] = provider


def get_provider(name: str) -> type[VisionProvider]:
    """Get a vision provider by name."""
    if name not in PROVIDERS:
        raise ValueError(f"Provider {name} is not registered")
    return PROVIDERS[name]
