"""Runtime-independent local model requests and results."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class VideoGenerationRequest:
    """A validated local video generation request."""

    prompt: str
    output_path: Path
    seed: int = 42
    height: int = 512
    width: int = 768
    num_frames: int = 121
    frame_rate: float = 24.0
    enhance_prompt: bool = True


@dataclass(frozen=True, slots=True)
class TranscriptionRequest:
    """A validated local speech transcription request."""

    audio_path: Path
    language: str | None = None
    beam_size: int = 5
    word_timestamps: bool = True
    vad_filter: bool = False


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    """Normalized transcript and source-model metadata."""

    text: str
    segments: list[dict[str, Any]]
    language: str
    language_probability: float
    duration_seconds: float
