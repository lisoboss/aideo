"""Tests for global Runtime model, input, and output paths."""

from pathlib import Path

import pytest
from aideo_runtime.paths import PathSettings


def test_path_settings_resolves_global_roots_and_output_uri(tmp_path: Path) -> None:
    """Relative paths should resolve below their respective global roots."""
    paths = PathSettings(tmp_path / "models", tmp_path / "input", tmp_path / "output")

    output = paths.output_path("videos/result.mp4")

    assert (
        paths.model_path("ltx2/model.safetensors")
        == tmp_path / "models/ltx2/model.safetensors"
    )
    assert paths.input_path("audio/sample.wav") == tmp_path / "input/audio/sample.wav"
    assert output.parent.is_dir()
    assert paths.output_uri(output) == "runtime://output/videos/result.mp4"


@pytest.mark.parametrize("relative", ["../outside", "/tmp/outside"])
def test_path_settings_rejects_paths_outside_the_global_root(
    tmp_path: Path, relative: str
) -> None:
    """Absolute and traversing paths must never escape Runtime storage roots."""
    paths = PathSettings(tmp_path / "models", tmp_path / "input", tmp_path / "output")

    with pytest.raises(ValueError, match="relative path"):
        paths.input_path(relative)
