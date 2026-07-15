"""Runtime adapter for the local aideo-models LTX2 implementation."""

from collections.abc import AsyncIterator, Callable
from pathlib import Path

from aideo_models import LTX2Model, VideoGenerationRequest
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
    VideoOutput,
)
from aideo_runtime.paths import PathSettings

_MODELS = [ModelInfo("ltx2", "ltx2", Capability.VIDEO, online=False)]
ModelFactory = Callable[[Path], LTX2Model]


class LTX2Backend:
    """Adapt the local LTX2 model to Runtime requests and events."""

    def __init__(
        self,
        paths: PathSettings,
        model_factory: ModelFactory = LTX2Model,
    ) -> None:
        """Configure Runtime-owned paths and a local model factory."""
        self._paths = paths
        self._model_factory = model_factory
        self._model: LTX2Model | None = None

    async def invoke(self, request: BackendRequest) -> BackendResponse:
        """Generate video and return a completed unified response."""
        final: DoneEvent | None = None
        async for event in self.stream(request):
            if isinstance(event, ErrorEvent):
                raise ValueError(event.message)
            if isinstance(event, DoneEvent):
                final = event
        if final is None:
            raise RuntimeError("LTX completed without output")
        return BackendResponse(
            outputs=[VideoOutput(final.metadata["uri"])], metadata=final.metadata
        )

    async def stream(self, request: BackendRequest) -> AsyncIterator[BackendEvent]:
        """Resolve Runtime paths, then emit LTX generation lifecycle events."""
        if request.capability is not Capability.VIDEO:
            yield ErrorEvent("LTX2 supports video capability")
            return
        prompt = request.input.get("prompt")
        if not isinstance(prompt, str) or not prompt:
            yield ErrorEvent("LTX2 requests require input.prompt")
            return
        model = self._model or self._model_factory(self._paths.models_dir)
        self._model = model
        filename = str(request.input.get("filename", "video.mp4"))
        output = self._paths.output_path(filename)
        local_request = VideoGenerationRequest(
            prompt=prompt,
            output_path=output,
            seed=int(request.parameters.get("seed", 42)),
            height=int(request.parameters.get("height", 512)),
            width=int(request.parameters.get("width", 768)),
            num_frames=int(request.parameters.get("num_frames", 121)),
            frame_rate=float(request.parameters.get("frame_rate", 24.0)),
            enhance_prompt=bool(request.parameters.get("enhance_prompt", True)),
        )
        yield ProgressEvent(0.05, "Pipeline ready")
        yield ProgressEvent(0.5, "Stage 1/2: denoising")
        await model.generate(local_request)
        yield ProgressEvent(0.8, "Stage 2/2: upscaling")
        yield ProgressEvent(0.95, "Encoding video")
        yield DoneEvent({"uri": self._paths.output_uri(output)})

    async def health(self) -> HealthStatus:
        """Report availability without loading the heavy local model."""
        return HealthStatus.HEALTHY

    async def models(self) -> list[ModelInfo]:
        """Return local LTX model metadata."""
        return models()

    async def aclose(self) -> None:
        """Release the locally loaded model when it exists."""
        if self._model is not None:
            await self._model.aclose()
        self._model = None


def models() -> list[ModelInfo]:
    """Return LTX model metadata."""
    return list(_MODELS)


def create_backend(paths: PathSettings) -> LTX2Backend:
    """Create an LTX2 Runtime adapter using shared Runtime paths."""
    return LTX2Backend(paths)
