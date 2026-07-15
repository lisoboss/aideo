"""OpenAI Responses API protocol models and adapter."""

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from aideo_runtime.capabilities import Capability
from aideo_runtime.models import (
    BackendEvent,
    BackendRequest,
    BackendResponse,
    DeltaEvent,
    DoneEvent,
    ErrorEvent,
    Output,
    TextOutput,
)
from aideo_runtime.transport import HttpRequest, HttpResponse, SSEEvent


@dataclass(frozen=True, slots=True)
class OpenAIError:
    """OpenAI-compatible error body."""

    message: str
    code: str | None = None


class OpenAIProtocol:
    """Translate unified chat and vision requests to the Responses API."""

    def encode(self, request: BackendRequest, endpoint: str) -> HttpRequest:
        """Encode a chat or vision request for ``POST /v1/responses``."""
        if request.capability not in {Capability.CHAT, Capability.VISION}:
            raise ValueError("OpenAI protocol supports chat or vision capabilities")
        messages = request.input.get("messages")
        if not isinstance(messages, list):
            raise ValueError("OpenAI requests require input.messages")
        body: dict[str, Any] = {
            "model": request.model,
            "input": messages,
            "stream": request.stream,
        }
        for key in (
            "max_output_tokens",
            "temperature",
            "top_p",
            "stop",
            "reasoning_effort",
        ):
            if key in request.parameters:
                body[key] = request.parameters[key]
        return HttpRequest(
            method="POST", url=f"{endpoint.rstrip('/')}/v1/responses", json=body
        )

    def decode(self, response: HttpResponse) -> BackendResponse:
        """Decode a completed Responses API response."""
        payload: dict[str, Any] = response.json()
        texts: list[Output] = []
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    texts.append(TextOutput(str(content.get("text", ""))))
        return BackendResponse(
            outputs=texts,
            usage=dict(payload.get("usage", {})),
            metadata={"response_id": payload.get("id")},
        )

    async def decode_stream(
        self, events: AsyncIterator[SSEEvent]
    ) -> AsyncIterator[BackendEvent]:
        """Map OpenAI Responses SSE frames to normalized Runtime events."""
        async for event in events:
            if event.data == "[DONE]":
                yield DoneEvent()
                continue
            payload: dict[str, Any] = json.loads(event.data)
            event_type = payload.get("type")
            if event_type == "response.output_text.delta":
                yield DeltaEvent(str(payload.get("delta", "")))
            elif event_type == "response.completed":
                yield DoneEvent({"response_id": payload.get("response", {}).get("id")})
            elif event_type in {"response.failed", "error"}:
                error = payload.get("response", {}).get("error") or payload.get(
                    "error", {}
                )
                yield ErrorEvent(
                    str(error.get("message", "OpenAI response failed")),
                    error.get("code"),
                )
