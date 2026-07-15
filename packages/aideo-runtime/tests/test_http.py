"""HTTP transport and backend interaction tests."""

from collections.abc import AsyncIterator
from typing import Any

import httpx
from aideo_runtime.backend import HttpBackend
from aideo_runtime.capabilities import Capability
from aideo_runtime.models import (
    BackendEvent,
    BackendRequest,
    BackendResponse,
    DeltaEvent,
    DoneEvent,
    HealthStatus,
    ModelInfo,
    TextOutput,
)
from aideo_runtime.transport import HttpRequest, HttpResponse, HttpTransport, SSEEvent


class TestAdapter:
    """Small protocol adapter for exercising the HTTP backend boundary."""

    def encode(self, request: BackendRequest, endpoint: str) -> HttpRequest:
        """Encode a request into a test JSON endpoint."""
        return HttpRequest(
            method="POST",
            url=f"{endpoint}/invoke",
            headers={"x-model": request.model},
            json={"stream": request.stream},
        )

    def decode(self, response: HttpResponse) -> BackendResponse:
        """Decode the test service JSON response."""
        payload: dict[str, Any] = response.json()
        return BackendResponse(outputs=[TextOutput(payload["text"])])

    async def decode_stream(
        self, events: AsyncIterator[SSEEvent]
    ) -> AsyncIterator[BackendEvent]:
        """Map test SSE frames to normalized events."""
        async for event in events:
            if event.data == "[DONE]":
                yield DoneEvent()
            else:
                yield DeltaEvent(event.data)


def make_transport(handler: httpx.MockTransport) -> HttpTransport:
    """Create a transport backed by an in-memory HTTP service."""
    return HttpTransport(client=httpx.AsyncClient(transport=handler))


async def test_http_transport_sends_json_and_decodes_response() -> None:
    """Buffered requests should forward method, headers, params, and JSON."""
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["query"] = request.url.query.decode()
        seen["header"] = request.headers["x-request-id"]
        seen["json"] = request.content
        return httpx.Response(200, json={"ok": True})

    transport = make_transport(httpx.MockTransport(handler))
    response = await transport.send(
        HttpRequest(
            method="POST",
            url="https://runtime.test/invoke",
            headers={"x-request-id": "req-1"},
            params={"mode": "fast"},
            json={"prompt": "cat"},
        )
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert seen == {
        "method": "POST",
        "path": "/invoke",
        "query": "mode=fast",
        "header": "req-1",
        "json": b'{"prompt":"cat"}',
    }


async def test_http_transport_parses_sse_frames() -> None:
    """SSE transport should yield data, event type, and final frame."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/stream"
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=b"event: progress\ndata: 50\n\ndata: [DONE]\n\n",
        )

    transport = make_transport(httpx.MockTransport(handler))
    events = [
        event
        async for event in transport.stream(
            HttpRequest(method="GET", url="https://runtime.test/stream")
        )
    ]

    assert events == [SSEEvent(data="50", event="progress"), SSEEvent(data="[DONE]")]


async def test_http_backend_invokes_streams_and_checks_health() -> None:
    """The backend should compose adapter, transport, SSE, catalog, and health."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(200)
        if request.headers.get("x-model") == "stream-model":
            return httpx.Response(200, content=b"data: first\n\ndata: [DONE]\n\n")
        return httpx.Response(200, json={"text": "completed"})

    model = ModelInfo("chat-model", "test", Capability.CHAT, online=True)
    backend = HttpBackend(
        "https://runtime.test/api/",
        TestAdapter(),
        transport=make_transport(httpx.MockTransport(handler)),
        model_catalog=[model],
        health_endpoint="/health",
    )
    request = BackendRequest(Capability.CHAT, "chat-model", {"messages": []})
    stream_request = BackendRequest(
        Capability.CHAT, "stream-model", {"messages": []}, stream=True
    )

    response = await backend.invoke(request)
    events = [event async for event in backend.stream(stream_request)]

    assert response.outputs == [TextOutput("completed")]
    assert events == [DeltaEvent("first"), DoneEvent()]
    assert await backend.health() is HealthStatus.HEALTHY
    assert await backend.models() == [model]
