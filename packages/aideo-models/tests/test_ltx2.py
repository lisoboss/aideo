"""Tests for the Runtime-independent LTX2 local model."""

from pathlib import Path

from aideo_models.ltx2 import LTX2Model
from aideo_models.models import VideoGenerationRequest


class FakePipeline:
    """Small replacement for the expensive LTX pipeline."""

    def __call__(self, **_: object) -> tuple[list[object], None]:
        """Return a placeholder video and no audio."""
        return [], None


async def test_ltx2_model_generates_to_a_validated_output_path(
    tmp_path: Path,
) -> None:
    """The local model should receive paths already validated by Runtime."""
    output = tmp_path / "output" / "dog.mp4"
    request = VideoGenerationRequest(prompt="dog", output_path=output, num_frames=1)

    def encode(*_: object, output_path: str, **__: object) -> None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"video")

    model = LTX2Model(
        tmp_path / "models",
        pipeline_factory=lambda: FakePipeline(),
        encoder=encode,
    )

    result = await model.generate(request)

    assert result == output
    assert output.read_bytes() == b"video"
