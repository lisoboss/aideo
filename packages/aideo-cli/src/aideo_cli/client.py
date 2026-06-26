"""Async HTTP + WebSocket client for aideo-serv API."""

from pathlib import Path

import httpx
import websockets


class AideoClient:
    """Thin wrapper around aideo-serv REST + WebSocket API."""

    def __init__(self, server: str = "http://localhost:8000"):
        """Initialize with aideo-serv base URL."""
        self.server = server.rstrip("/")
        self.api_url = f"{self.server}/api/v1"

    async def submit(self, prompt: str, params: dict | None = None) -> dict:
        """Submit a new video generation task."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.api_url}/tasks",
                json={"prompt": prompt, "params": params},
            )
            resp.raise_for_status()
            return resp.json()

    async def list_tasks(self, status: str | None = None, limit: int = 20) -> dict:
        """List tasks with optional status filter."""
        params: dict[str, str | int] = {"offset": 0, "limit": limit}
        if status:
            params["status"] = status
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.api_url}/tasks", params=params)
            resp.raise_for_status()
            return resp.json()

    async def get_task(self, task_id: str) -> dict:
        """Get a single task by ID."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.api_url}/tasks/{task_id}")
            resp.raise_for_status()
            return resp.json()

    async def cancel_task(self, task_id: str) -> dict:
        """Cancel a task."""
        async with httpx.AsyncClient() as client:
            resp = await client.delete(f"{self.api_url}/tasks/{task_id}")
            resp.raise_for_status()
            return resp.json()

    async def download_result(self, task_id: str, output_path: str) -> Path:
        """Download a generated video to a local file."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.api_url}/results/{task_id}/download")
            resp.raise_for_status()
            path = Path(output_path)
            path.write_bytes(resp.content)
            return path

    async def connect_ws(self, task_id: str):
        """Connect to the WebSocket progress stream for a task.

        Yields parsed JSON events as dicts.
        """
        ws_url = self.server.replace("http", "ws")
        async with websockets.connect(f"{ws_url}/api/v1/ws/tasks/{task_id}") as ws:
            async for message in ws:
                import json

                yield json.loads(message)
