"""Abstract interface for speech-to-text providers."""

from abc import abstractmethod
from collections.abc import AsyncGenerator

from pydantic import BaseModel, Field

from aideo_runtime.provider import BaseProvider, ProgressStatus

PROVIDERS: dict[str, type[BaseProvider]] = {}


class SpeechIn(BaseModel):
    audio_path: str = Field(..., description="Path to the audio file to transcribe")
    language: str | None = Field(None, description="Language of the audio")
    params: dict = Field(default_factory=dict, description="Additional parameters")


class SpeechOut(BaseModel):
    text: str = Field(..., description="Transcribed text from the audio")


class SpeechProvider(BaseProvider):
    """A provider that transcribes audio into text."""

    @abstractmethod
    async def run(
        self,
        audio_path: str,
        language: str | None = None,
        params: dict | None = None,
        task_id: str | None = None,
    ) -> AsyncGenerator[ProgressStatus, None]:
        """Transcribe audio file to text, yielding progress then final result."""
        ...


def register_provider(provider_cls: type[SpeechProvider]) -> None:
    """Register a speech provider class."""
    if not issubclass(provider_cls, SpeechProvider):
        raise TypeError(f"{provider_cls} is not a subclass of SpeechProvider")
    name = getattr(provider_cls, "provider_name", None)
    if not name:
        raise ValueError(f"{provider_cls} must define provider_name")
    PROVIDERS[name] = provider_cls


def get_provider(name: str) -> type[SpeechProvider]:
    """Get a speech provider class by name."""
    if name not in PROVIDERS:
        raise ValueError(f"Provider {name} is not registered")
    return PROVIDERS[name]
