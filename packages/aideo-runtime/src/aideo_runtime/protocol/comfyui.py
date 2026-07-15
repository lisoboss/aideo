"""ComfyUI local workflow protocol models and adapter."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from aideo_runtime.capabilities import Capability
from aideo_runtime.models import (
    BackendEvent,
    BackendRequest,
    BackendResponse,
    DoneEvent,
    ErrorEvent,
    ImageOutput,
    Output,
    ProgressEvent,
)
from aideo_runtime.transport import HttpRequest, HttpResponse, SSEEvent


@dataclass(frozen=True, slots=True)
class ComfyQueueResponse:
    """Queue response returned by ``POST /prompt``."""

    prompt_id: str
    number: int | None = None


class ComfyUIProtocol:
    """Translate unified image requests to ComfyUI workflow operations."""

    def encode(self, request: BackendRequest, endpoint: str) -> HttpRequest:
        """Encode an API-format image workflow for ``POST /prompt``."""
        if request.capability is not Capability.IMAGE:
            raise ValueError("ComfyUI protocol supports image capability")
        workflow = request.input.get("workflow")
        if not isinstance(workflow, dict):
            raise ValueError("ComfyUI image requests require input.workflow")
        body: dict[str, Any] = {"prompt": workflow}
        if "client_id" in request.input:
            body["client_id"] = request.input["client_id"]
        return HttpRequest(
            method="POST", url=f"{endpoint.rstrip('/')}/prompt", json=body
        )

    def decode(self, response: HttpResponse) -> BackendResponse:
        """Decode ComfyUI history output images into unified image outputs."""
        payload: dict[str, Any] = response.json()
        images: list[Output] = []
        for history in payload.values():
            for output in history.get("outputs", {}).values():
                for image in output.get("images", []):
                    image_type = image.get("type", "output")
                    subfolder = image.get("subfolder", "")
                    filename = image.get("filename", "")
                    path = "/".join(
                        part for part in (image_type, subfolder, filename) if part
                    )
                    images.append(ImageOutput(f"comfyui://{path}"))
        return BackendResponse(outputs=images, metadata={"history": payload})

    async def decode_stream(
        self, events: AsyncIterator[SSEEvent]
    ) -> AsyncIterator[BackendEvent]:
        """Reject SSE because ComfyUI progress uses WebSocket JSON events."""
        del events
        raise ValueError("ComfyUI streaming requires decode_ws_event()")
        yield  # pragma: no cover

    def decode_ws_event(self, payload: dict[str, Any]) -> BackendEvent | None:
        """Map one ComfyUI WebSocket JSON event to a unified event."""
        event_type = payload.get("type")
        data = payload.get("data", {})
        if event_type == "progress":
            maximum = data.get("max", 0)
            progress = data.get("value", 0) / maximum if maximum else 0.0
            return ProgressEvent(progress)
        if event_type == "executing" and data.get("node") is None:
            return DoneEvent()
        if event_type == "execution_error":
            return ErrorEvent(
                str(data.get("exception_message", "ComfyUI execution failed"))
            )
        return None
