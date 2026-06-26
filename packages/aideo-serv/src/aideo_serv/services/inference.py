"""Client for communicating with the LTX-2 inference service."""

from uuid import UUID

import httpx


class InferenceClient:
    """Async HTTP client for the LTX-2 inference service."""

    def __init__(self, base_url: str = "http://localhost:9090"):
        """Initialize with the inference service base URL."""
        self.base_url = base_url.rstrip("/")

    async def submit(
        self,
        task_id: UUID,
        prompt: str,
        params: dict | None = None,
        callback_url: str = "",
    ) -> None:
        """Submit a generation task to the inference service."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/generate",
                json={
                    "task_id": str(task_id),
                    "prompt": prompt,
                    "params": params or {},
                    "callback_url": callback_url,
                },
            )
            response.raise_for_status()

    async def health_check(self) -> bool:
        """Check if the inference service is reachable and healthy."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except httpx.HTTPError:
            return False
