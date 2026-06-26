"""Progress callback sender — posts events back to aideo-serv."""

from uuid import UUID

import httpx


async def send_progress(
    callback_url: str,
    task_id: UUID,
    event_type: str,
    data: dict,
) -> None:
    """POST a progress event to the aideo-serv callback URL."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(
                callback_url,
                json={
                    "type": event_type,
                    "task_id": str(task_id),
                    "data": data,
                },
            )
        except httpx.HTTPError:
            pass  # Don't crash if aideo-serv is temporarily unreachable
