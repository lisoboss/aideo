"""Lazy Faster-Whisper2 local speech model without Runtime dependencies."""

import asyncio
import os
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import Any

from aideo_models.models import TranscriptionRequest, TranscriptionResult


class FasterWhisper2Model:
    """Load and execute Faster-Whisper2 on demand."""

    def __init__(
        self,
        models_dir: Path,
        model_factory: Callable[..., Any] | None = None,
        cuda_available: Callable[[], bool] | None = None,
    ) -> None:
        """Configure model storage and optional test collaborators."""
        self._models_dir = models_dir
        self._model_factory = model_factory
        self._cuda_available = cuda_available
        self._model: Any | None = None
        self._device = os.environ.get("WHISPER_DEVICE", "cuda")
        self._compute_type = os.environ.get("WHISPER_COMPUTE_TYPE", "float16")
        self._model_name = os.environ.get("WHISPER_MODEL", "whisper/large-v3")

    async def transcribe(self, request: TranscriptionRequest) -> TranscriptionResult:
        """Transcribe audio at a path already validated by Runtime."""
        await self._load()
        model = self._model
        if model is None:
            raise RuntimeError("Faster-Whisper2 model failed to initialize")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._transcribe, model, request)

    async def aclose(self) -> None:
        """Release the loaded model."""
        self._model = None

    async def _load(self) -> None:
        if self._model is not None:
            return
        loop = asyncio.get_running_loop()
        self._model = await loop.run_in_executor(None, self._build_model)

    def _build_model(self) -> Any:
        device, compute_type = self._execution_config()
        if self._model_factory is not None:
            return self._model_factory(device=device, compute_type=compute_type)
        whisper_module = import_module("faster_whisper2")
        whisper_model = getattr(whisper_module, "WhisperModel")
        model_path = self._local_model_path()
        return whisper_model(
            str(model_path),
            device=device,
            compute_type=compute_type,
        )

    def _local_model_path(self) -> Path:
        """Resolve the configured local checkpoint below the model root."""
        configured_path = Path(self._model_name)
        if configured_path.is_absolute():
            raise ValueError("WHISPER_MODEL must be relative to the global model root")
        model_root = self._models_dir.resolve()
        model_path = (model_root / configured_path).resolve()
        try:
            model_path.relative_to(model_root)
        except ValueError as error:
            raise ValueError(
                "WHISPER_MODEL must be relative to the global model root"
            ) from error
        if not model_path.is_dir():
            raise FileNotFoundError(f"Local Whisper model not found: {model_path}")
        return model_path

    def _execution_config(self) -> tuple[str, str]:
        """Select CUDA when available and safely fall back to CPU int8."""
        if self._device != "cuda":
            return self._device, self._compute_type
        cuda_available = self._cuda_available
        if cuda_available is None and self._model_factory is not None:
            return self._device, self._compute_type
        if cuda_available is None:
            torch_module = import_module("torch")
            cuda_available = getattr(torch_module.cuda, "is_available")
        if cuda_available():
            return self._device, self._compute_type
        return "cpu", "int8"

    @staticmethod
    def _transcribe(
        model: Any,
        request: TranscriptionRequest,
    ) -> TranscriptionResult:
        segments, info = model.transcribe(
            str(request.audio_path),
            language=request.language,
            beam_size=request.beam_size,
            word_timestamps=request.word_timestamps,
            vad_filter=request.vad_filter,
        )
        normalized_segments = [
            {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
                "no_speech_prob": segment.no_speech_prob,
            }
            for segment in segments
        ]
        return TranscriptionResult(
            text=" ".join(item["text"] for item in normalized_segments),
            segments=normalized_segments,
            language=info.language,
            language_probability=info.language_probability,
            duration_seconds=info.duration,
        )
