"""Minimal Server-Sent Events parsing primitives."""

from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SSEEvent:
    """A parsed Server-Sent Event frame."""

    data: str
    event: str | None = None
    event_id: str | None = None


async def iter_sse_events(lines: AsyncIterator[str]) -> AsyncIterator[SSEEvent]:
    """Parse an async sequence of SSE lines into event frames."""
    data: list[str] = []
    event: str | None = None
    event_id: str | None = None
    async for line in lines:
        if not line:
            if data:
                yield SSEEvent("\n".join(data), event, event_id)
            data, event, event_id = [], None, None
            continue
        if line.startswith(":"):
            continue
        field, separator, value = line.partition(":")
        if not separator:
            continue
        value = value.removeprefix(" ")
        if field == "data":
            data.append(value)
        elif field == "event":
            event = value
        elif field == "id":
            event_id = value
    if data:
        yield SSEEvent("\n".join(data), event, event_id)
