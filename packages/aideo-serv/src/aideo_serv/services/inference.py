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
        model_root: str = "",
        output_root: str = "",
        input_root: str = "",
    ) -> None:
        """Submit a generation task to the inference service.

        The inference service returns 202 immediately and reports
        progress asynchronously via callbacks, so we only need a
        short timeout for the initial HTTP handshake.
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/generate",
                json={
                    "task_id": str(task_id),
                    "prompt": prompt,
                    "params": params or {},
                    "callback_url": callback_url,
                    "model_root": model_root,
                    "output_root": output_root,
                    "input_root": input_root,
                },
            )
            response.raise_for_status()

    async def cancel(self, task_id: UUID) -> bool:
        """Cancel a running generation on the inference service."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{self.base_url}/cancel/{task_id}")
                return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def health_check(self) -> bool:
        """Check if the inference service is reachable and healthy."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except httpx.HTTPError:
            return False
