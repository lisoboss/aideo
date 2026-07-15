"""Tests for the Runtime adapter around the local LTX2 model."""

from pathlib import Path

from aideo_runtime.backend.providers.ltx2 import LTX2Backend
from aideo_runtime.capabilities import Capability
from aideo_runtime.models import BackendRequest, DoneEvent, ProgressEvent, VideoOutput
from aideo_runtime.paths import PathSettings


class FakeLTX2Model:
    """Small replacement for ``aideo_models.LTX2Model``."""

    async def generate(self, request: object) -> Path:
        """Write a stable video at the Runtime-selected output path."""
        output_path = getattr(request, "output_path")
        output_path.write_bytes(b"video")
        return output_path


async def test_ltx2_writes_to_global_output_and_returns_runtime_uri(
    tmp_path: Path,
) -> None:
    """Video generation should never use a provider-private output root."""
    paths = PathSettings(tmp_path / "models", tmp_path / "input", tmp_path / "output")

    backend = LTX2Backend(paths, model_factory=lambda _: FakeLTX2Model())
    request = BackendRequest(
        Capability.VIDEO, "ltx2", {"prompt": "dog"}, {"num_frames": 1}
    )

    response = await backend.invoke(request)
    events = [event async for event in backend.stream(request)]

    assert response.outputs == [VideoOutput("runtime://output/video.mp4")]
    assert isinstance(events[-1], DoneEvent)
    assert [event.progress for event in events if isinstance(event, ProgressEvent)] == [
        0.05,
        0.5,
        0.8,
        0.95,
    ]
    assert (tmp_path / "output/video.mp4").is_file()
