"""Tests for the Runtime adapter around the local Faster-Whisper2 model."""

from pathlib import Path

from aideo_models import TranscriptionResult
from aideo_runtime.backend.providers.faster_whisper2 import FasterWhisper2Backend
from aideo_runtime.capabilities import Capability
from aideo_runtime.models import BackendRequest, DoneEvent, TextOutput
from aideo_runtime.paths import PathSettings


class FakeWhisperModel:
    """Small replacement for ``aideo_models.FasterWhisper2Model``."""

    async def transcribe(self, _: object) -> TranscriptionResult:
        """Return a normalized transcript from the local-model boundary."""
        return TranscriptionResult(
            text="hello",
            segments=[],
            language="en",
            language_probability=0.9,
            duration_seconds=1.0,
        )


async def test_faster_whisper2_uses_global_input_and_returns_transcript(
    tmp_path: Path,
) -> None:
    """ASR should resolve input below the shared root and normalize the result."""
    paths = PathSettings(tmp_path / "models", tmp_path / "input", tmp_path / "output")
    paths.input_path("clip.wav").write_bytes(b"audio")
    backend = FasterWhisper2Backend(paths, model_factory=lambda _: FakeWhisperModel())
    request = BackendRequest(
        Capability.ASR, "faster-whisper2", {"audio_path": "clip.wav"}
    )

    response = await backend.invoke(request)
    events = [event async for event in backend.stream(request)]

    assert response.outputs == [TextOutput("hello")]
    assert isinstance(events[-1], DoneEvent)
    assert events[-1].metadata["language"] == "en"
