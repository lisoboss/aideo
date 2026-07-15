"""LTX v2 asynchronous video-job protocol models and adapter."""

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
    Output,
    ProgressEvent,
    VideoOutput,
)
from aideo_runtime.transport import HttpRequest, HttpResponse, SSEEvent


@dataclass(frozen=True, slots=True)
class LTXJob:
    """A normalized LTX asynchronous job status."""

    id: str
    status: str
    progress: float | None = None
    video_url: str | None = None


class LTXProtocol:
    """Translate unified video requests to LTX v2 asynchronous jobs."""

    def encode(self, request: BackendRequest, endpoint: str) -> HttpRequest:
        """Encode a text-to-video request for ``POST /v2/text-to-video``."""
        if request.capability is not Capability.VIDEO:
            raise ValueError("LTX protocol supports video capability")
        prompt = request.input.get("prompt")
        if not isinstance(prompt, str) or not prompt:
            raise ValueError("LTX video requests require input.prompt")
        body: dict[str, Any] = {"model": request.model, "prompt": prompt}
        for key in ("duration", "resolution", "seed"):
            if key in request.parameters:
                body[key] = request.parameters[key]
        return HttpRequest(
            method="POST", url=f"{endpoint.rstrip('/')}/v2/text-to-video", json=body
        )

    def decode(self, response: HttpResponse) -> BackendResponse:
        """Decode an LTX job response into a completed video response when ready."""
        payload: dict[str, Any] = response.json()
        result = payload.get("result") or {}
        video_url = result.get("video_url")
        outputs: list[Output] = [VideoOutput(video_url)] if video_url else []
        return BackendResponse(
            outputs=outputs,
            metadata={"job_id": payload.get("id"), "status": payload.get("status")},
        )

    async def decode_stream(
        self, events: AsyncIterator[SSEEvent]
    ) -> AsyncIterator[BackendEvent]:
        """Reject SSE because LTX async jobs are monitored through polling."""
        del events
        raise ValueError("LTX streaming requires decode_job() polling")
        yield  # pragma: no cover

    def decode_job(self, response: HttpResponse) -> BackendEvent:
        """Map one LTX job status response to a unified Runtime event."""
        payload: dict[str, Any] = response.json()
        status = payload.get("status")
        job_id = str(payload.get("id", ""))
        if status in {"queued", "processing", "in_progress"}:
            return ProgressEvent(float(payload.get("progress", 0.0)))
        if status == "completed":
            video_url = (payload.get("result") or {}).get("video_url")
            return DoneEvent({"job_id": job_id, "video_url": video_url})
        error = payload.get("error") or {}
        return ErrorEvent(
            str(error.get("message", "LTX job failed")), error.get("code")
        )
