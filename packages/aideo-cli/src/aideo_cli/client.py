"""Async HTTP + WebSocket client for aideo-serv API."""

import json
from pathlib import Path

import httpx
import websockets


class AideoClient:
    """Thin wrapper around aideo-serv REST + WebSocket API."""

    def __init__(self, server: str = "http://localhost:8000"):
        """Initialize with aideo-serv base URL."""
        self.server = server.rstrip("/")
        self.api_url = f"{self.server}/api/v1"

    async def submit(
        self,
        prompt: str,
        params: dict | None = None,
        task_type: str = "video_generation",
        input_files: list[dict] | None = None,
    ) -> dict:
        """Submit a new generation task."""
        async with httpx.AsyncClient() as client:
            body: dict = {"prompt": prompt, "params": params, "task_type": task_type}
            if input_files:
                body["input_files"] = input_files
            resp = await client.post(f"{self.api_url}/tasks", json=body)
            resp.raise_for_status()
            return resp.json()

    async def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
        params: dict | None = None,
    ) -> dict:
        """Submit a speech-to-text task with an audio file."""
        input_files = [{"path": audio_path, "type": "audio"}]
        task_params = params or {}
        if language:
            task_params["language"] = language
        return await self.submit(
            prompt=f"Transcribe {audio_path}",
            params=task_params,
            task_type="speech_to_text",
            input_files=input_files,
        )

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

        Yields parsed JSON events as dicts.  Exits gracefully when the
        server closes the connection (task reached a terminal state).
        """
        ws_url = self.server.replace("http", "ws")
        try:
            async with websockets.connect(
                f"{ws_url}/api/v1/ws/tasks/{task_id}"
            ) as ws:
                async for message in ws:
                    yield json.loads(message)
        except websockets.exceptions.ConnectionClosed:
            pass  # Server closed the connection — exit gracefully

    async def stream_transcribe(
        self, audio_chunks
    ):
        """Stream audio chunks for real-time speech-to-text transcription.

        Parameters
        ----------
        audio_chunks : iterable of bytes
            An iterable (sync or async) yielding raw audio bytes — one
            utterance per chunk (PCM 16kHz 16-bit mono or WAV).  Each chunk
            is sent as a binary WebSocket frame.

        Yields
        ------
        dict
            JSON event dicts from the server:
            ``{"type": "status_change", "data": {"status": "..."}}``
            ``{"type": "progress", "data": {"progress": ..., "message": "..."}}``
            ``{"type": "result", "data": {"full_text": "...", "segments": [...]}}``
            ``{"type": "error", "data": {"message": "..."}}``
        """
        ws_url = self.server.replace("http", "ws")
        try:
            async with websockets.connect(
                f"{ws_url}/api/v1/ws/transcribe"
            ) as ws:
                for chunk in audio_chunks:
                    if isinstance(chunk, str):
                        chunk = chunk.encode()
                    elif not isinstance(chunk, bytes):
                        chunk = bytes(chunk)

                    await ws.send(chunk)

                    # Receive events until a terminal result/error arrives
                    while True:
                        raw = await ws.recv()
                        event = json.loads(raw)
                        yield event
                        if event.get("type") in ("result", "error"):
                            break

        except websockets.exceptions.ConnectionClosed:
            pass  # Server closed the connection — exit gracefully
