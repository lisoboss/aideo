"""Tests for the Runtime-independent local model contracts."""

from pathlib import Path

from aideo_models.models import (
    TranscriptionRequest,
    TranscriptionResult,
    VideoGenerationRequest,
)


def test_local_model_contracts_only_use_standard_python_values() -> None:
    """Local model requests and results must not depend on Runtime types."""
    video = VideoGenerationRequest(prompt="dog", output_path=Path("/output/dog.mp4"))
    transcription = TranscriptionRequest(
        audio_path=Path("/input/voice.wav"),
        language="en",
    )
    result = TranscriptionResult(
        text="hello",
        segments=[{"start": 0.0, "end": 1.0, "text": "hello"}],
        language="en",
        language_probability=0.9,
        duration_seconds=1.0,
    )

    assert video.output_path == Path("/output/dog.mp4")
    assert transcription.audio_path == Path("/input/voice.wav")
    assert result.text == "hello"
