"""HTTP transport implemented with a reusable httpx client."""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

import httpx
from aideo_runtime.transport.sse import SSEEvent, iter_sse_events


@dataclass(slots=True)
class HttpRequest:
    """A transport-level HTTP request."""

    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    json: Any | None = None
    params: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class HttpResponse:
    """A fully buffered transport-level HTTP response."""

    status_code: int
    headers: dict[str, str]
    content: bytes

    def json(self) -> Any:
        """Decode the response body as JSON."""
        return httpx.Response(self.status_code, content=self.content).json()


class HttpTransport:
    """Executes HTTP and server-sent-event requests with connection pooling."""

    def __init__(
        self,
        *,
        timeout: httpx.Timeout | float = 30.0,
        limits: httpx.Limits | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the transport, optionally accepting an owned client."""
        self._owns_client = client is None
        if client is not None:
            self._client = client
        elif limits is None:
            self._client = httpx.AsyncClient(timeout=timeout)
        else:
            self._client = httpx.AsyncClient(timeout=timeout, limits=limits)

    async def send(self, request: HttpRequest) -> HttpResponse:
        """Send a request and return its buffered response."""
        response = await self._client.request(
            request.method,
            request.url,
            headers=request.headers,
            json=request.json,
            params=request.params,
        )
        response.raise_for_status()
        return HttpResponse(
            response.status_code, dict(response.headers), response.content
        )

    async def stream(self, request: HttpRequest) -> AsyncIterator[SSEEvent]:
        """Send a request and yield parsed SSE events."""
        async with self._client.stream(
            request.method,
            request.url,
            headers=request.headers,
            json=request.json,
            params=request.params,
        ) as response:
            response.raise_for_status()
            async for event in iter_sse_events(response.aiter_lines()):
                yield event

    async def aclose(self) -> None:
        """Close the owned HTTP connection pool."""
        if self._owns_client:
            await self._client.aclose()
