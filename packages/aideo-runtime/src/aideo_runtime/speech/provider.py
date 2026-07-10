"""Abstract interface for speech-to-text providers."""

from abc import abstractmethod
from collections.abc import AsyncGenerator
from typing import Optional

from aideo_runtime.provider import BaseProvider
from pydantic import BaseModel, Field

PROVIDERS = {}


class SpeechIn(BaseModel):
    audio_path: str = Field(..., description="Path to the audio file to transcribe")
    language: str = Field(..., description="Language of the audio")
    params: dict = Field(
        default_factory=dict, description="Additional parameters for the transcription"
    )


class SpeechOut(BaseModel):
    text: str = Field(..., description="Transcribed text from the audio")


class SpeechProvider(BaseProvider):
    """A provider that transcribes audio into text."""

    In = SpeechIn
    Out = SpeechOut

    @abstractmethod
    async def submit(self, params: SpeechIn) -> str:
        """Return a unique task ID for this inference run."""
        ...

    @abstractmethod
    async def result(self) -> SpeechOut:
        """Return the final result of an inference run, if available."""
        ...


def register_provider(provider: type[SpeechProvider]) -> None:
    """Register a speech provider."""
    if not issubclass(provider, SpeechProvider):
        raise TypeError(f"{provider} is not a subclass of SpeechProvider")
    if provider.provider_name in PROVIDERS:
        raise ValueError(f"Provider {provider.provider_name} is already registered")
    PROVIDERS[provider.provider_name] = provider


def get_provider(name: str) -> type[SpeechProvider]:
    """Get a speech provider by name."""
    if name not in PROVIDERS:
        raise ValueError(f"Provider {name} is not registered")
    return PROVIDERS[name]
