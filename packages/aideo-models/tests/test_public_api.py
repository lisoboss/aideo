"""Tests for the public aideo-models import surface."""

from aideo_models import (
    FasterWhisper2Model,
    LTX2Model,
    TranscriptionRequest,
    TranscriptionResult,
    VideoGenerationRequest,
)


def test_public_api_exports_local_models_without_runtime_dependency() -> None:
    """Consumers should import all stable contracts from the package root."""
    assert FasterWhisper2Model.__name__ == "FasterWhisper2Model"
    assert LTX2Model.__name__ == "LTX2Model"
    assert TranscriptionRequest.__name__ == "TranscriptionRequest"
    assert TranscriptionResult.__name__ == "TranscriptionResult"
    assert VideoGenerationRequest.__name__ == "VideoGenerationRequest"
