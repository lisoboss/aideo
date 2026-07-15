"""Unit tests for unified runtime data models."""

from aideo_runtime.capabilities import Capability
from aideo_runtime.models import (
    AudioOutput,
    BackendRequest,
    BackendResponse,
    EmbeddingOutput,
    ImageOutput,
    TextOutput,
    VideoOutput,
)


def test_backend_request_defaults_to_non_streaming() -> None:
    """A request should provide empty parameters and disable streaming by default."""
    request = BackendRequest(
        capability=Capability.CHAT,
        model="gpt-5",
        input={"messages": []},
    )

    assert request.parameters == {}
    assert request.stream is False


def test_backend_response_supports_all_builtin_output_types() -> None:
    """A response should carry mixed outputs without changing its interface."""
    outputs = [
        TextOutput("hello"),
        ImageOutput("https://example.test/image.png"),
        VideoOutput("https://example.test/video.mp4"),
        AudioOutput("https://example.test/audio.mp3"),
        EmbeddingOutput([0.1, 0.2]),
    ]
    response = BackendResponse(outputs=outputs, usage={"input_tokens": 2})

    assert response.outputs == outputs
    assert response.usage == {"input_tokens": 2}
    assert response.metadata == {}
