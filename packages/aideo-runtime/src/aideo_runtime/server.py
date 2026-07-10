"""Aideo Runtime — HTTP + SSE inference service.

Routes:
    POST /api/v1/{category}/{provider_name}    → SSE stream
    GET  /api/v1/{category}                     → list providers in category
    GET  /api/v1                                 → list all categories + providers
    GET  /health                                 → health check

Auto-loads models on first request, auto-unloads after idle timeout.
"""

import asyncio
import importlib
import logging
import os
import time

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.event_stream import EventSourceResponse

from aideo_runtime.provider import BaseProvider, ProgressStatus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider Manager — auto load / unload
# ---------------------------------------------------------------------------

CATEGORIES = ("speech", "video", "chat", "vision")
IDLE_TIMEOUT = float(os.environ.get("AIDEO_IDLE_TIMEOUT", "300"))


class ProviderManager:
    """Manages provider instances with auto load/unload on idle timeout."""

    def __init__(self) -> None:
        self._instances: dict[str, BaseProvider] = {}
        self._last_used: dict[str, float] = {}
        self._running: set[str] = set()  # keys currently executing run()

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _discover_provider_cls(self, category: str, name: str) -> type[BaseProvider]:
        if category not in CATEGORIES:
            raise ValueError(f"Unknown category: {category}")

        # Video is lazy — trigger import on first request
        if category == "video":
            import aideo_runtime.video.ltx2  # noqa: F401

        mod = importlib.import_module(f"aideo_runtime.{category}")
        providers: dict[str, type[BaseProvider]] = getattr(mod, "PROVIDERS", {})
        cls = providers.get(name)
        if cls is None:
            # Try prefix match (e.g. "faster-whisper" matches "faster-whisper@speech")
            for key, val in providers.items():
                if key.startswith(name):
                    cls = val
                    break
        if cls is None:
            raise ValueError(
                f"Provider '{name}' not found in '{category}'. Available: {list(providers.keys())}"
            )
        return cls

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def get_provider(self, category: str, name: str, **init_kwargs) -> BaseProvider:
        key = f"{category}/{name}"
        if key not in self._instances:
            provider_cls = self._discover_provider_cls(category, name)
            provider = provider_cls(**init_kwargs)
            logger.info("Loading provider: %s", key)
            await provider.load()
            self._instances[key] = provider
        self._last_used[key] = time.monotonic()
        return self._instances[key]

    async def start_idle_sweeper(self) -> None:
        logger.info("Idle sweeper started (timeout=%ss)", IDLE_TIMEOUT)
        while True:
            await asyncio.sleep(60)
            now = time.monotonic()
            for key, last_used in list(self._last_used.items()):
                if now - last_used > IDLE_TIMEOUT:
                    provider = self._instances.pop(key, None)
                    self._last_used.pop(key, None)
                    if provider is not None:
                        logger.info("Unloading idle provider: %s (%.0fs idle)", key, now - last_used)
                        await provider.unload()

    # ------------------------------------------------------------------
    # Memory preemption
    # ------------------------------------------------------------------

    async def preempt_all(self, for_key: str) -> None:
        """Release all loaded models for exclusive use by `for_key`.

        Raises RuntimeError if any provider is currently running.
        """
        running = self._running - {for_key}
        if running:
            raise RuntimeError(
                f"Memory preemption failed: {len(running)} provider(s) still running: {running}"
            )

        for key in list(self._instances.keys()):
            if key == for_key:
                continue
            provider = self._instances.pop(key, None)
            self._last_used.pop(key, None)
            if provider is not None:
                logger.info("Preempt: unloading %s", key)
                await provider.unload()

    def mark_running(self, key: str) -> None:
        self._running.add(key)

    def mark_idle(self, key: str) -> None:
        self._running.discard(key)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def list_categories(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for cat in CATEGORIES:
            try:
                mod = importlib.import_module(f"aideo_runtime.{cat}")
                providers = getattr(mod, "PROVIDERS", {})
                result[cat] = list(providers.keys())
            except Exception:
                result[cat] = []
        return result


_manager = ProviderManager()

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="aideo-runtime", version="2.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    # Pre-import categories so providers self-register
    import aideo_runtime.speech  # noqa: F401
    import aideo_runtime.chat  # noqa: F401
    import aideo_runtime.vision  # noqa: F401
    # video is lazy (torch import is heavy)
    asyncio.create_task(_manager.start_idle_sweeper())
    logger.info("aideo-runtime HTTP+SSE server started")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.post("/api/v1/{category}/{provider_name}")
async def run_provider(category: str, provider_name: str, request: Request) -> EventSourceResponse:
    """Run inference on a provider, streaming progress via SSE.

    Header ``X-Memory-Preempt: true`` unloads ALL other models first,
    giving this request exclusive GPU memory. Fails if any provider is
    currently running.
    """
    body = await request.json()
    preempt = request.headers.get("X-Memory-Preempt", "").lower() in ("1", "true", "yes")

    # Separate init kwargs from run kwargs
    init_keys = {"model_size_or_path", "device", "compute_type", "model_root"}
    init_kwargs = {k: body.pop(k) for k in init_keys if k in body and body.get(k) is not None}
    run_kwargs = body

    provider_key = f"{category}/{provider_name}"

    # Memory preemption: release all other models
    if preempt:
        try:
            await _manager.preempt_all(for_key=provider_key)
        except RuntimeError as exc:
            async def error_stream():
                yield {
                    "event": "error",
                    "data": ProgressStatus(
                        progress=100.0, message=str(exc),
                        result_data={"error": "preempt_failed", "detail": str(exc)},
                    ).model_dump_json(),
                }
            return EventSourceResponse(error_stream())

    provider = await _manager.get_provider(category, provider_name, **init_kwargs)

    provider.reset_cancel()

    async def event_stream():
        _manager.mark_running(provider_key)
        try:
            async for status in provider.run(**run_kwargs):
                yield {"event": "progress", "data": status.model_dump_json()}
        except asyncio.CancelledError:
            # Client disconnected — stop inference
            logger.info("Client disconnected, cancelling %s", provider_key)
            provider.cancel()
        except Exception as exc:
            logger.exception("Provider %s/%s failed", category, provider_name)
            yield {
                "event": "error",
                "data": ProgressStatus(
                    progress=100.0, message=str(exc), result_data={"error": str(exc)}
                ).model_dump_json(),
            }
        finally:
            _manager.mark_idle(provider_key)

    return EventSourceResponse(event_stream())


@app.get("/api/v1/{category}")
async def list_category_providers(category: str) -> dict:
    cats = _manager.list_categories()
    return {"category": category, "providers": cats.get(category, [])}


@app.get("/api/v1")
async def list_all_providers() -> dict:
    return {"categories": _manager.list_categories()}


@app.get("/health")
async def health() -> dict:
    cats = _manager.list_categories()
    return {"status": "ok", "service": "aideo-runtime", "categories": cats}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    host = os.environ.get("AIDEO_RUNTIME_HOST", "0.0.0.0")
    port = int(os.environ.get("AIDEO_RUNTIME_PORT", "9090"))
    uvicorn.run("aideo_runtime.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
