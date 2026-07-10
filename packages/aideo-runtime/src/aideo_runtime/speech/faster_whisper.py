"""Faster-Whisper speech-to-text provider."""

import asyncio
import logging
import os
import time
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Callable

import torch
from aideo_runtime.provider import ProgressStatus
from aideo_runtime.speech.provider import SpeechProvider, register_provider
from faster_whisper import WhisperModel
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ModelKwargs(BaseModel):
    model_size_or_path: str = Field(
        "large-v3", description="Model size or path for faster-whisper"
    )
    device: str = Field("cuda", description="Device to run the model on")
    compute_type: str = Field("float16", description="Compute type for the model")
    model_root: str | None = Field(
        None, description="Root directory for model downloads"
    )
    beam_size: int = Field(5, description="Beam size for transcription")
    word_timestamps: bool = Field(
        True, description="Whether to return word-level timestamps"
    )
    vad_filter: bool = Field(False, description="Whether to apply VAD filtering")


def processing(
    audio_path: Path,
    model_kwargs: ModelKwargs,
    progress: Callable[[ProgressStatus], None],
):
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    if not audio_path.is_file():
        raise ValueError(f"Audio path is not a file: {audio_path}")

    download_root = model_kwargs.model_root or os.environ.get("WHISPER_MODEL_ROOT", "")

    progress(
        {
            "progress": 1.0,
            "message": f"Loading WhisperModel: {model_kwargs.model_size_or_path} (device={model_kwargs.device}, compute={model_kwargs.compute_type}, download_root={download_root})",
        }
    )
    model = WhisperModel(
        model_kwargs.model_size_or_path,
        device=model_kwargs.device,
        compute_type=model_kwargs.compute_type,
        download_root=download_root,
    )

    progress({"progress": 10.0, "message": "Model loaded, starting transcription..."})
    segments, _ = model.transcribe(
        str(audio_path),
        language=model_kwargs.language,
        beam_size=model_kwargs.beam_size,
        word_timestamps=model_kwargs.word_timestamps,
        vad_filter=model_kwargs.vad_filter,
    )

    words = []

    for idx, seg in enumerate(segments):
        word = seg.text.strip()
        progress(
            {
                "progress": 20.0 + idx,
                "message": f"Transcribed segment: {seg.start:.2f}-{seg.end:.2f}s: {word}",
            }
        )
        words.append(word)

    progress({"progress": 100.0, "message": "Transcription complete"})
    return " ".join(words)


class FasterWhisperProvider(SpeechProvider):
    """Speech-to-text via faster-whisper."""

    provider_name = "faster-whisper@speech.provider"

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @staticmethod
    def _cuda_available() -> bool:
        """Check if CUDA libraries are loadable."""
        try:
            return torch.cuda.is_available()
        except OSError:
            return False

    def _detect_device(self, requested: str) -> tuple[str, str]:
        """Return (device, compute_type) — falls back to CPU if CUDA is missing."""
        if requested == "cuda" and not self._cuda_available():
            logger.warning("CUDA not available, falling back to CPU")
            return "cpu", "int8"
        if requested == "cuda":
            return "cuda", "float16"
        if requested == "cpu":
            return "cpu", "int8"
        return requested, "int8"

    async def load(self) -> None:
        loop = asyncio.get_running_loop()

        def _build():
            from faster_whisper import WhisperModel

            download_root = self._model_root or None
            logger.info(
                "Loading WhisperModel: %s (device=%s, compute=%s, download_root=%s)",
                self._model_size_or_path,
                self._device,
                self._compute_type,
                download_root,
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

    async def run(
        self,
        audio_path: str,
        language: str | None = None,
        params: dict | None = None,
        task_id: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        # Validate input before loading model
        audio_file = Path(audio_path)
        if not audio_file.exists():
            yield {
                "progress": 100.0,
                "message": "Audio file not found",
                "result_data": {"error": f"File not found: {audio_path}"},
            }
            return

        if not self._loaded or self._model is None:
            await self.load()

        params = params or {}
        beam_size = int(params.get("beam_size", 5))
        word_timestamps = bool(params.get("word_timestamps", True))
        vad_filter = bool(params.get("vad_filter", False))

        yield {"progress": 10.0, "message": "Model loaded, starting transcription..."}

        loop = asyncio.get_running_loop()

        def _run():
            segments, info = self._model.transcribe(
                str(audio_file),
                language=language,
                beam_size=beam_size,
                word_timestamps=word_timestamps,
                vad_filter=vad_filter,
            )
            segment_list = []
            for seg in segments:
                segment_list.append(
                    {
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text.strip(),
                        "no_speech_prob": seg.no_speech_prob,
                        "words": (
                            [
                                {
                                    "word": w.word,
                                    "start": w.start,
                                    "end": w.end,
                                    "probability": w.probability,
                                }
                                for w in (seg.words or [])
                            ]
                            if word_timestamps
                            else []
                        ),
                    }
                )
            return segment_list, {
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
            }

        task = loop.run_in_executor(None, _run)
        t0 = time.monotonic()

        while not task.done():
            elapsed = time.monotonic() - t0
            pct = min(95.0, 10.0 + elapsed * 5)
            yield {
                "progress": round(pct, 1),
                "message": f"Transcribing... ({elapsed:.0f}s)",
            }
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=3)
            except TimeoutError:
                pass

        segments, info = await task
        full_text = " ".join(s["text"] for s in segments)

        yield {
            "progress": 100.0,
            "message": "Transcription complete",
            "result_data": {
                "full_text": full_text,
                "segments": segments,
                "language": info["language"],
                "language_probability": info["language_probability"],
                "duration_seconds": info["duration"],
                "segment_count": len(segments),
            },
        }


# Register the faster_whisper provider so it can be used in the system.
register_provider(FasterWhisperProvider)
