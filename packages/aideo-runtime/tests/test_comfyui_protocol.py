"""Tests for ComfyUI local workflow protocol translation."""

import pytest
from aideo_runtime.capabilities import Capability
from aideo_runtime.models import (
    BackendRequest,
    DoneEvent,
    ErrorEvent,
    ImageOutput,
    ProgressEvent,
)
from aideo_runtime.protocol import ComfyUIProtocol
from aideo_runtime.transport import HttpResponse


def test_comfyui_encodes_workflow_and_decodes_history_images() -> None:
    """Image workflows should submit to prompt and history outputs become URIs."""
    protocol = ComfyUIProtocol()
    request = BackendRequest(
        Capability.IMAGE,
        "flux",
        {"workflow": {"1": {"class_type": "KSampler", "inputs": {}}}},
    )

    encoded = protocol.encode(request, "http://comfy")
    decoded = protocol.decode(
        HttpResponse(
            200,
            {},
            b'{"p1":{"outputs":{"9":{"images":[{"filename":"cat.png","subfolder":"","type":"output"}]}}}}',
        )
    )

    assert encoded.url == "http://comfy/prompt"
    assert encoded.json["prompt"]["1"]["class_type"] == "KSampler"
    assert decoded.outputs == [ImageOutput("comfyui://output/cat.png")]


def test_comfyui_maps_websocket_events_and_rejects_missing_workflow() -> None:
    """Comfy execution events should map to progress, completion, and errors."""
    protocol = ComfyUIProtocol()

    assert protocol.decode_ws_event(
        {"type": "progress", "data": {"value": 5, "max": 10}}
    ) == ProgressEvent(0.5)
    assert (
        protocol.decode_ws_event({"type": "executing", "data": {"node": None}})
        == DoneEvent()
    )
    assert protocol.decode_ws_event(
        {"type": "execution_error", "data": {"exception_message": "bad"}}
    ) == ErrorEvent("bad")
    with pytest.raises(ValueError, match="workflow"):
        protocol.encode(
            BackendRequest(Capability.IMAGE, "flux", {"prompt": "cat"}), "http://comfy"
        )
