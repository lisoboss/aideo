"""Tests for the Runtime-independent Faster-Whisper2 local model."""

from pathlib import Path
from types import SimpleNamespace

import aideo_models.whisper as whisper_module
import pytest
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


def test_whisper_model_imports_the_faster_whisper2_module(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The local package name must match the Faster-Whisper2 distribution."""
    imported: list[str] = []
    received: dict[str, object] = {}

    def create_model(*args: object, **kwargs: object) -> FakeWhisper:
        received.update(model=args[0], **kwargs)
        return FakeWhisper()

    def import_fake(name: str) -> object:
        imported.append(name)
        return SimpleNamespace(WhisperModel=create_model)

    monkeypatch.setenv("WHISPER_DEVICE", "cpu")
    monkeypatch.setattr(whisper_module, "import_module", import_fake)
    models_dir = tmp_path / "models"
    local_model = models_dir / "whisper" / "large-v3"
    local_model.mkdir(parents=True)
    model = FasterWhisper2Model(models_dir)

    model._build_model()

    assert imported == ["faster_whisper2"]
    assert received["model"] == str(local_model)
    assert received["device"] == "cpu"


@pytest.mark.parametrize("model_path", ["../outside", "/absolute/model"])
def test_whisper_model_rejects_paths_outside_the_model_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    model_path: str,
) -> None:
    """The Whisper checkpoint must remain below the shared model root."""
    monkeypatch.setenv("WHISPER_MODEL", model_path)

    with pytest.raises(ValueError, match="global model root"):
        FasterWhisper2Model(tmp_path / "models")._local_model_path()


def test_whisper_model_requires_an_existing_local_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The ASR provider should not download a missing checkpoint at runtime."""
    monkeypatch.setenv("WHISPER_MODEL", "whisper/missing")

    with pytest.raises(FileNotFoundError, match="Local Whisper model not found"):
        FasterWhisper2Model(tmp_path / "models")._local_model_path()
