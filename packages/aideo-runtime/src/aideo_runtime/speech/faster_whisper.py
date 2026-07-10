"""Faster-Whisper speech-to-text provider."""

import asyncio
import logging
import os
import time
from collections.abc import AsyncGenerator
from pathlib import Path

import torch
from faster_whisper import WhisperModel

from aideo_runtime.provider import ProgressStatus
from aideo_runtime.speech.provider import SpeechProvider, register_provider

logger = logging.getLogger(__name__)


class FasterWhisperProvider(SpeechProvider):
    """Speech-to-text via faster-whisper."""

    provider_name = "faster-whisper@speech"

    def __init__(
        self,
        model_size_or_path: str | None = None,
        device: str | None = None,
        compute_type: str | None = None,
        model_root: str | None = None,
    ) -> None:
        self._model: WhisperModel | None = None
        self._loaded = False
        self._model_size_or_path = model_size_or_path or os.environ.get("WHISPER_MODEL", "large-v3")
        self._device, self._compute_type = self._detect_device(
            device or os.environ.get("WHISPER_DEVICE", "cuda"),
            compute_type or os.environ.get("WHISPER_COMPUTE_TYPE", "float16"),
        )
        self._model_root = model_root

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    async def load(self) -> None:
        """Load WhisperModel into memory."""
        if self._loaded:
            return
        loop = asyncio.get_running_loop()

        def _build() -> WhisperModel:
            download_root = self._model_root or None
            logger.info(
                "Loading WhisperModel: %s (device=%s, compute=%s, download_root=%s)",
                self._model_size_or_path, self._device, self._compute_type, download_root,
            )
            return WhisperModel(
                self._model_size_or_path,
                device=self._device,
                compute_type=self._compute_type,
                download_root=download_root,
            )

        self._model = await loop.run_in_executor(None, _build)
        self._loaded = True
        logger.info("WhisperModel loaded successfully")

    async def unload(self) -> None:
        """Release WhisperModel from memory."""
        self._model = None
        self._loaded = False
        logger.info("WhisperModel unloaded")

    # ------------------------------------------------------------------
    # Device detection
    # ------------------------------------------------------------------

    @staticmethod
    def _cuda_available() -> bool:
        try:
            return torch.cuda.is_available()
        except OSError:
            return False

    def _detect_device(
        self, requested_device: str, requested_compute: str
    ) -> tuple[str, str]:
        if requested_device == "cuda" and not self._cuda_available():
            logger.warning("CUDA not available, falling back to CPU")
            return "cpu", "int8"
        if requested_device == "cuda":
            return "cuda", requested_compute
        if requested_device == "cpu":
            return "cpu", "int8"
        return requested_device, requested_compute

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    async def run(
        self,
        audio_path: str,
        language: str | None = None,
        params: dict | None = None,
        task_id: str | None = None,
    ) -> AsyncGenerator[ProgressStatus, None]:
        audio_file = Path(audio_path)
        if not audio_file.exists():
            yield ProgressStatus(
                progress=100.0, message="Audio file not found",
                result_data={"error": f"File not found: {audio_path}"},
            )
            return

        if not self._loaded or self._model is None:
            await self.load()

        params = params or {}
        beam_size = int(params.get("beam_size", 5))
        word_timestamps = bool(params.get("word_timestamps", True))
        vad_filter = bool(params.get("vad_filter", False))

        yield ProgressStatus(progress=10.0, message="Model loaded, starting transcription...")

        loop = asyncio.get_running_loop()

        def _run():
            segments, info = self._model.transcribe(
                str(audio_file), language=language,
                beam_size=beam_size, word_timestamps=word_timestamps,
                vad_filter=vad_filter,
            )
            segment_list = []
            for seg in segments:
                segment_list.append({
                    "start": seg.start, "end": seg.end,
                    "text": seg.text.strip(),
                    "no_speech_prob": seg.no_speech_prob,
                    "words": [
                        {"word": w.word, "start": w.start, "end": w.end, "probability": w.probability}
                        for w in (seg.words or [])
                    ] if word_timestamps else [],
                })
            return segment_list, {
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
            }

        task = loop.run_in_executor(None, _run)
        t0 = time.monotonic()

        while not task.done():
            elapsed = time.monotonic() - t0
            yield ProgressStatus(
                progress=round(min(95.0, 10.0 + elapsed * 5), 1),
                message=f"Transcribing... ({elapsed:.0f}s)",
            )
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=3)
            except TimeoutError:
                pass

        segments, info = await task
        full_text = " ".join(s["text"] for s in segments)

        yield ProgressStatus(
            progress=100.0, message="Transcription complete",
            result_data={
                "full_text": full_text, "segments": segments,
                "language": info["language"],
                "language_probability": info["language_probability"],
                "duration_seconds": info["duration"],
                "segment_count": len(segments),
            },
        )


register_provider(FasterWhisperProvider)
