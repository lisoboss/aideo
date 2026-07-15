"""Runtime adapter for the local aideo-models Faster-Whisper2 model."""

from collections.abc import AsyncIterator, Callable
from pathlib import Path

from aideo_models import (
    FasterWhisper2Model,
    TranscriptionRequest,
    TranscriptionResult,
)
from aideo_runtime.capabilities import Capability
from aideo_runtime.models import (
    BackendEvent,
    BackendRequest,
    BackendResponse,
    DoneEvent,
    ErrorEvent,
    HealthStatus,
    ModelInfo,
    ProgressEvent,
    TextOutput,
)
from aideo_runtime.paths import PathSettings

_MODELS = [
    ModelInfo("faster-whisper2", "faster_whisper2", Capability.ASR, online=False)
]
ModelFactory = Callable[[Path], FasterWhisper2Model]


class FasterWhisper2Backend:
    """Adapt the local Whisper model to Runtime requests and events."""

    def __init__(
        self,
        paths: PathSettings,
        model_factory: ModelFactory = FasterWhisper2Model,
    ) -> None:
        """Configure Runtime-owned paths and a local model factory."""
        self._paths = paths
        self._model_factory = model_factory
        self._model: FasterWhisper2Model | None = None

    async def invoke(self, request: BackendRequest) -> BackendResponse:
        """Run ASR and return a completed unified response."""
        final: DoneEvent | None = None
        async for event in self.stream(request):
            if isinstance(event, ErrorEvent):
                raise ValueError(event.message)
            if isinstance(event, DoneEvent):
                final = event
        if final is None:
            raise RuntimeError("ASR completed without a result")
        return BackendResponse(
            outputs=[TextOutput(final.metadata["text"])], metadata=final.metadata
        )

    async def stream(self, request: BackendRequest) -> AsyncIterator[BackendEvent]:
        """Resolve Runtime input paths, then stream a completed transcript."""
        if request.capability is not Capability.ASR:
            yield ErrorEvent("Faster-Whisper2 supports asr capability")
            return
        audio_path = request.input.get("audio_path")
        if not isinstance(audio_path, str):
            yield ErrorEvent("ASR requests require input.audio_path")
            return
        path = self._paths.input_path(audio_path)
        if not path.is_file():
            yield ErrorEvent(f"Audio file not found: {audio_path}")
            return
        model = self._model or self._model_factory(self._paths.models_dir)
        self._model = model
        local_request = TranscriptionRequest(
            audio_path=path,
            language=(
                request.input.get("language")
                if isinstance(request.input.get("language"), str)
                else None
            ),
            beam_size=int(request.parameters.get("beam_size", 5)),
            word_timestamps=bool(request.parameters.get("word_timestamps", True)),
            vad_filter=bool(request.parameters.get("vad_filter", False)),
        )
        yield ProgressEvent(0.1, "Transcribing audio")
        result = await model.transcribe(local_request)
        yield DoneEvent(self._metadata(result))

    @staticmethod
    def _metadata(result: TranscriptionResult) -> dict[str, object]:
        """Convert a local transcription result to Runtime metadata."""
        return {
            "text": result.text,
            "segments": result.segments,
            "language": result.language,
            "language_probability": result.language_probability,
            "duration_seconds": result.duration_seconds,
        }

    async def health(self) -> HealthStatus:
        """Report availability without forcing model initialization."""
        return HealthStatus.HEALTHY

    async def models(self) -> list[ModelInfo]:
        """Return ASR model metadata."""
        return models()

    async def aclose(self) -> None:
        """Release the locally loaded model when it exists."""
        if self._model is not None:
            await self._model.aclose()
        self._model = None


def models() -> list[ModelInfo]:
    """Return Faster-Whisper2 model metadata."""
    return list(_MODELS)


def create_backend(paths: PathSettings) -> FasterWhisper2Backend:
    """Create an ASR Runtime adapter using shared Runtime paths."""
    return FasterWhisper2Backend(paths)
