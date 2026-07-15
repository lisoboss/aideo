"""Tests for the deterministic local demo backend."""

from aideo_runtime.backend.providers.demo import create_backend
from aideo_runtime.capabilities import Capability
from aideo_runtime.models import (
    BackendRequest,
    DeltaEvent,
    DoneEvent,
    TextOutput,
)


async def test_demo_backend_returns_stable_response_and_stream() -> None:
    """Demo chat requests should return stable JSON and SSE-compatible events."""
    backend = create_backend()
    request = BackendRequest(Capability.CHAT, "demo-chat", {"messages": []})

    response = await backend.invoke(request)
    events = [event async for event in backend.stream(request)]

    assert response.outputs == [TextOutput("demo response")]
    assert events == [
        DeltaEvent("demo response"),
        DoneEvent({"model": "demo-chat", "provider": "demo"}),
    ]
