"""HTTP backend that delegates provider formats to a protocol adapter."""

from collections.abc import AsyncIterator

from aideo_runtime.models import (
    BackendEvent,
    BackendRequest,
    BackendResponse,
    HealthStatus,
    ModelInfo,
)
from aideo_runtime.protocol import ProtocolAdapter
from aideo_runtime.transport import HttpRequest, HttpTransport


class HttpBackend:
    """Reusable HTTP backend with connection pooling and SSE support."""

    def __init__(
        self,
        endpoint: str,
        adapter: ProtocolAdapter,
        *,
        transport: HttpTransport | None = None,
        model_catalog: list[ModelInfo] | None = None,
        health_endpoint: str | None = None,
    ) -> None:
        """Initialize the backend with its endpoint and protocol adapter."""
        self._endpoint = endpoint.rstrip("/")
        self._adapter = adapter
        self._transport = transport or HttpTransport()
        self._model_catalog = model_catalog or []
        self._health_endpoint = health_endpoint

    async def invoke(self, request: BackendRequest) -> BackendResponse:
        """Encode, send, and decode a non-streaming request."""
        http_request = self._adapter.encode(request, self._endpoint)
        return self._adapter.decode(await self._transport.send(http_request))

    async def stream(self, request: BackendRequest) -> AsyncIterator[BackendEvent]:
        """Encode, stream, and decode an SSE request."""
        http_request = self._adapter.encode(request, self._endpoint)
        async for event in self._adapter.decode_stream(
            self._transport.stream(http_request)
        ):
            yield event

    async def health(self) -> HealthStatus:
        """Probe the configured health endpoint when one is available."""
        if self._health_endpoint is None:
            return HealthStatus.UNKNOWN
        health_url = self._health_endpoint
        if not health_url.startswith(("http://", "https://")):
            health_url = f"{self._endpoint}/{health_url.lstrip('/')}"
        try:
            await self._transport.send(HttpRequest(method="GET", url=health_url))
        except Exception:
            return HealthStatus.UNHEALTHY
        return HealthStatus.HEALTHY

    async def models(self) -> list[ModelInfo]:
        """Return the static model catalog for this backend."""
        return list(self._model_catalog)

    async def aclose(self) -> None:
        """Close the underlying transport connection pool."""
        await self._transport.aclose()
