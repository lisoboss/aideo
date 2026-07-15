"""Tests for LTX async video-job protocol translation."""

import pytest
from aideo_runtime.capabilities import Capability
from aideo_runtime.models import (
    BackendRequest,
    DoneEvent,
    ErrorEvent,
    ProgressEvent,
    VideoOutput,
)
from aideo_runtime.protocol import LTXProtocol
from aideo_runtime.transport import HttpResponse


def test_ltx_encodes_video_request_and_decodes_completed_job() -> None:
    """Video generation should map to LTX v2 request and video output URI."""
    protocol = LTXProtocol()
    request = BackendRequest(
        Capability.VIDEO,
        "ltx-2-3-fast",
        {"prompt": "running dog"},
        {"duration": 5, "resolution": "1080p"},
    )

    encoded = protocol.encode(request, "https://ltx.example")
    decoded = protocol.decode(
        HttpResponse(
            200,
            {},
            b'{"id":"job-1","status":"completed","result":{"video_url":"https://cdn.example/video.mp4"}}',
        )
    )

    assert encoded.url == "https://ltx.example/v2/text-to-video"
    assert encoded.json["prompt"] == "running dog"
    assert decoded.outputs == [VideoOutput("https://cdn.example/video.mp4")]


def test_ltx_maps_job_status_and_rejects_non_video_requests() -> None:
    """LTX job states should become progress, completion, and failure events."""
    protocol = LTXProtocol()

    assert protocol.decode_job(
        HttpResponse(200, {}, b'{"id":"job-1","status":"processing","progress":0.4}')
    ) == ProgressEvent(0.4)
    assert protocol.decode_job(
        HttpResponse(
            200,
            {},
            b'{"id":"job-1","status":"completed","result":{"video_url":"https://cdn.example/video.mp4"}}',
        )
    ) == DoneEvent({"job_id": "job-1", "video_url": "https://cdn.example/video.mp4"})
    assert protocol.decode_job(
        HttpResponse(
            200,
            {},
            b'{"id":"job-1","status":"failed","error":{"code":"bad","message":"no"}}',
        )
    ) == ErrorEvent("no", "bad")
    with pytest.raises(ValueError, match="video"):
        protocol.encode(
            BackendRequest(Capability.CHAT, "ltx", {"messages": []}),
            "https://ltx.example",
        )
