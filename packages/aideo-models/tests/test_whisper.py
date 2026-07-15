"""Tests for the Runtime-independent Faster-Whisper2 local model."""

from pathlib import Path

from aideo_models.models import TranscriptionRequest
from aideo_models.whisper import FasterWhisper2Model


class FakeSegment:
    """Minimal Whisper segment fixture."""

    start, end, text, no_speech_prob = 0.0, 1.0, " hello ", 0.0


class FakeInfo:
    """Minimal Whisper info fixture."""

    language, language_probability, duration = "en", 0.9, 1.0


class FakeWhisper:
    """Deterministic replacement for the heavy Whisper model."""

    def transcribe(
        self, *_: object, **__: object
    ) -> tuple[list[FakeSegment], FakeInfo]:
        """Return one stable segment."""
        return [FakeSegment()], FakeInfo()


async def test_whisper_model_falls_back_to_cpu_and_returns_transcript(
    tmp_path: Path,
) -> None:
    """The local model should only receive an already validated audio path."""
    received: dict[str, str] = {}

    def create_model(*, device: str, compute_type: str) -> FakeWhisper:
        received.update(device=device, compute_type=compute_type)
        return FakeWhisper()

    model = FasterWhisper2Model(
        tmp_path / "models",
        model_factory=create_model,
        cuda_available=lambda: False,
    )
    result = await model.transcribe(
        TranscriptionRequest(audio_path=tmp_path / "input" / "voice.wav", language="en")
    )

    assert received == {"device": "cpu", "compute_type": "int8"}
    assert result.text == "hello"
    assert result.language == "en"
