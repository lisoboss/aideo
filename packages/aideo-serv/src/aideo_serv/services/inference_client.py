"""HTTP+SSE client for aideo-runtime.

Replaces the WS-based ``InferenceServiceManager``. Calls
``POST runtime_url/api/v1/{category}/{name}`` and consumes
the SSE response stream, forwarding progress/completed/error
to the TaskService.

Memory preemption: pass ``X-Memory-Preempt: true`` header
for video generation or whenever exclusive GPU access is desired.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Awaitable, Callable

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Task type → runtime category + provider name
# ---------------------------------------------------------------------------

TASK_TO_PROVIDER: dict[str, tuple[str, str]] = {
    "video_generation": ("video", "ltx2"),
    "speech_to_text": ("speech", "faster-whisper"),
    "text_conversation": ("chat", "stub"),
    "image_to_text": ("vision", "stub"),
}


def resolve_provider(task_type: str) -> tuple[str, str]:
    """Map task_type → (category, provider_name)."""
    if task_type not in TASK_TO_PROVIDER:
        raise ValueError(
            f"Unknown task_type '{task_type}'. Known: {list(TASK_TO_PROVIDER)}"
        )
    return TASK_TO_PROVIDER[task_type]


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


@dataclass
class TaskCallbacks:
    """Called by InferenceClient as SSE events arrive."""

    on_progress: Callable[[float, str], Awaitable[None]]
    on_completed: Callable[[dict], Awaitable[None]]
    on_error: Callable[[str], Awaitable[None]]


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class InferenceClient:
    """HTTP+SSE client for aideo-runtime.

    Does NOT maintain persistent connections — each ``run()`` opens
    a new HTTP request and streams the SSE response.
    """

    def __init__(self, runtime_url: str = "http://localhost:9090") -> None:
        self._runtime_url = runtime_url.rstrip("/")

    @property
    def runtime_url(self) -> str:
        return self._runtime_url

    async def run(
        self,
        task_type: str,
        payload: dict,
        callbacks: TaskCallbacks,
        *,
        preempt: bool = False,
    ) -> None:
        """Execute inference via aideo-runtime, streaming SSE → callbacks.

        Parameters
        ----------
        task_type:
            e.g. ``"video_generation"``, ``"speech_to_text"``.
        payload:
            JSON body forwarded to the runtime's ``run(**payload)``.
        callbacks:
            Called for each SSE event.
        preempt:
            If True, sends ``X-Memory-Preempt`` header to unload all
            other models before running this one.
        """
        category, name = resolve_provider(task_type)
        url = f"{self._runtime_url}/api/v1/{category}/{name}"

        headers = {"Content-Type": "application/json"}
        if preempt:
            headers["X-Memory-Preempt"] = "true"

        logger.info("Inference request: POST %s (preempt=%s)", url, preempt)

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    text = await resp.aread()
                    await callbacks.on_error(
                        f"Runtime returned {resp.status_code}: {text.decode()[:500]}"
                    )
                    return

                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    try:
                        data = json.loads(line[5:].strip())
                    except json.JSONDecodeError:
                        continue

                    progress = float(data.get("progress", 0))
                    message = str(data.get("message", ""))
                    result_data = data.get("result_data")

                    if progress >= 100.0 and result_data is not None:
                        await callbacks.on_completed(result_data)
                        return
                    elif progress >= 100.0 and result_data is None:
                        # Error or cancelled — data["message"] contains reason
                        await callbacks.on_error(message)
                        return
                    else:
                        await callbacks.on_progress(progress, message)

        # If we exit the loop without returning (empty body, connection closed),
        # treat as error.
        await callbacks.on_error("Inference connection closed without result")


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_client: InferenceClient | None = None


def get_inference_client() -> InferenceClient:
    """Return the global InferenceClient singleton."""
    global _client
    if _client is None:
        _client = InferenceClient()
    return _client


def set_inference_client(client: InferenceClient) -> None:
    """Replace the global singleton (for testing)."""
    global _client
    _client = client
