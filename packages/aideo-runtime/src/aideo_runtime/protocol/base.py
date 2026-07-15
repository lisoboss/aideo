"""Provider protocol adapter interface."""

from collections.abc import AsyncIterator
from typing import Protocol

from aideo_runtime.models import BackendEvent, BackendRequest, BackendResponse
from aideo_runtime.transport import HttpRequest, HttpResponse, SSEEvent


class ProtocolAdapter(Protocol):
    """Translates unified data at the HTTP/SSE provider boundary.

    Providers with WebSocket progress or polling job status may add explicit
    provider methods while retaining these core request/response methods.
    """

    def encode(self, request: BackendRequest, endpoint: str) -> HttpRequest:
        """Encode a backend request into a provider HTTP request."""
        ...

    def decode(self, response: HttpResponse) -> BackendResponse:
        """Decode a provider HTTP response into a unified response."""
        ...

    def decode_stream(
        self, events: AsyncIterator[SSEEvent]
    ) -> AsyncIterator[BackendEvent]:
        """Decode provider SSE frames into normalized runtime events."""
        ...
