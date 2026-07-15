"""Local model implementations without Runtime service dependencies."""

from aideo_models.ltx2 import LTX2Model
from aideo_models.models import (
    TranscriptionRequest,
    TranscriptionResult,
    VideoGenerationRequest,
)
from aideo_models.whisper import FasterWhisper2Model

__all__ = [
    "FasterWhisper2Model",
    "LTX2Model",
    "TranscriptionRequest",
    "TranscriptionResult",
    "VideoGenerationRequest",
]
