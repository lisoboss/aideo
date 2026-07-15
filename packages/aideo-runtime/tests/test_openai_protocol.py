"""Tests for OpenAI Responses API protocol translation."""

import pytest
from aideo_runtime.capabilities import Capability
from aideo_runtime.models import (
    BackendRequest,
    DeltaEvent,
    DoneEvent,
    ErrorEvent,
    TextOutput,
)
from aideo_runtime.protocol import OpenAIProtocol
from aideo_runtime.transport import HttpResponse, SSEEvent


async def event_source(events: list[SSEEvent]):
    """Yield fixed SSE events for protocol conversion tests."""
    for event in events:
        yield event


def test_openai_encodes_responses_request_and_decodes_output() -> None:
    """Chat requests should map to Responses API input and generation controls."""
    protocol = OpenAIProtocol()
    request = BackendRequest(
        Capability.CHAT,
        "gpt-test",
        {"messages": [{"role": "user", "content": "hello"}]},
        {"max_output_tokens": 64, "temperature": 0.7},
    )

    encoded = protocol.encode(request, "https://api.example")
    decoded = protocol.decode(
        HttpResponse(
            200,
            {},
            b'{"output":[{"type":"message","content":[{"type":"output_text","text":"hi"}]}],"usage":{"input_tokens":2,"output_tokens":1}}',
        )
    )

    assert encoded.url == "https://api.example/v1/responses"
    assert encoded.json["input"][0]["content"] == "hello"
    assert encoded.json["max_output_tokens"] == 64
    assert decoded.outputs == [TextOutput("hi")]
    assert decoded.usage == {"input_tokens": 2, "output_tokens": 1}


async def test_openai_maps_stream_events_and_rejects_other_capabilities() -> None:
    """OpenAI SSE events should become unified deltas, done, and errors."""
    protocol = OpenAIProtocol()
    events = [
        SSEEvent('{"type":"response.output_text.delta","delta":"hi"}'),
        SSEEvent('{"type":"response.completed","response":{"id":"r1"}}'),
        SSEEvent(
            '{"type":"response.failed","response":{"error":{"code":"bad","message":"no"}}}'
        ),
    ]
    mapped = [event async for event in protocol.decode_stream(event_source(events))]

    assert mapped == [
        DeltaEvent("hi"),
        DoneEvent({"response_id": "r1"}),
        ErrorEvent("no", "bad"),
    ]
    with pytest.raises(ValueError, match="chat or vision"):
        protocol.encode(
            BackendRequest(Capability.IMAGE, "gpt", {"prompt": "cat"}),
            "https://api.example",
        )
