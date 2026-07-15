"""Ollama protocol adapter boundary."""

from collections.abc import AsyncIterator

from aideo_runtime.models import BackendEvent, BackendRequest, BackendResponse
from aideo_runtime.transport import HttpRequest, HttpResponse, SSEEvent


class OllamaProtocol:
    """Adapter skeleton for Ollama APIs."""

    def encode(self, request: BackendRequest, endpoint: str) -> HttpRequest:
        """Encode a unified request when Ollama schema support is installed."""
        raise NotImplementedError("Ollama protocol encoding is not implemented")

    def decode(self, response: HttpResponse) -> BackendResponse:
        """Decode an Ollama response when schema support is installed."""
        raise NotImplementedError("Ollama protocol decoding is not implemented")

    async def decode_stream(
        self, events: AsyncIterator[SSEEvent]
    ) -> AsyncIterator[BackendEvent]:
        """Decode Ollama streaming frames when schema support is installed."""
        raise NotImplementedError("Ollama stream decoding is not implemented")
        yield  # pragma: no cover
