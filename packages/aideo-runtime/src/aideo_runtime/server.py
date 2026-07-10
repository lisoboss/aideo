"""Aideo Runtime — aggregated local inference service.

On startup connects to aideo-serv's internal WebSocket, registers as
``"aideo-runtime"`` with multiple capabilities, and routes incoming
task_submit messages to the correct provider via a registry.

Architecture::

    server.py  (WebSocket client + FastAPI health)
        │
        ▼
    ProviderRegistry  (task_type → provider instance)
        │
        ├── video/ltx2.py          → LTX2VideoProvider
        ├── speech/faster_whisper.py → FasterWhisperProvider
        ├── chat/stub.py           → StubChatProvider
        └── vision/stub.py         → StubVisionProvider

Each provider implements the abstract base from its category
(video/base.py, speech/base.py, chat/base.py, vision/base.py).
"""

import asyncio
import json
import logging
import os
from collections.abc import AsyncGenerator
from pathlib import Path

import uvicorn
from fastapi import FastAPI

logger = logging.getLogger(__name__)


import websockets
from aideo_runtime import chat, speech, video, vision

# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------


class ProviderRegistry:
    """Maps task_type → provider instance."""

    def __init__(self) -> None:
        self._providers: dict[str, object] = {}

    def register(self, task_type: str, provider) -> None:
        self._providers[task_type] = provider
        logger.info("Provider registered: %s → %s", task_type, provider.provider_name)

    def get(self, task_type: str):
        return self._providers.get(task_type)

    @property
    def capabilities(self) -> list[str]:
        return list(self._providers.keys())


def _create_registry(
    model_root: str,
    output_root: str,
    input_root: str,
) -> ProviderRegistry:
    """Build the provider registry with concrete implementations."""
    from aideo_runtime.chat import get_provider as get_chat_provider
    from aideo_runtime.speech import get_provider as get_speech_provider
    from aideo_runtime.vision import get_provider as get_vision_provider

    registry = ProviderRegistry()

    # ---- speech-to-text ------------------------------------------------
    registry.register(
        "speech_to_text",
        FasterWhisperProvider(
            model_size_or_path=os.environ.get("WHISPER_MODEL", "large-v3"),
            device=os.environ.get("WHISPER_DEVICE", "cuda"),
            compute_type=os.environ.get("WHISPER_COMPUTE_TYPE", "float16"),
            model_root=model_root,
        ),
    )

    # ---- text conversation ---------------------------------------------
    registry.register("text_conversation", StubChatProvider())

    # ---- image-to-text -------------------------------------------------
    registry.register("image_to_text", StubVisionProvider())

    # ---- video generation (lazy — ltx2 depends on heavy imports) -----
    # Registered at first video task to avoid importing torch at startup.
    # The dispatch path checks for "video_generation" and loads on demand.

    return registry


# ---------------------------------------------------------------------------
# WebSocket client
# ---------------------------------------------------------------------------


class AideoWSClient:
    """Persistent WebSocket connection to aideo-serv."""

    def __init__(self, server_url: str = "ws://localhost:8000") -> None:
        self._server_url = server_url.rstrip("/")
        self._ws_url = f"{self._server_url}/api/v1/ws/internal/inference"
        self._ws = None
        self._running = False
        self._registry: ProviderRegistry | None = None

    def set_registry(self, registry: ProviderRegistry) -> None:
        self._registry = registry

    async def connect_and_serve(self) -> None:
        self._running = True
        backoff = 1.0

        while self._running:
            try:
                async with websockets.connect(self._ws_url) as ws:  # type: ignore[union-attr]
                    self._ws = ws
                    backoff = 1.0

                    await ws.send(
                        json.dumps(
                            {
                                "type": "register",
                                "service_type": "aideo-runtime",
                                "capabilities": (
                                    self._registry.capabilities
                                    if self._registry
                                    else []
                                ),
                                "version": "0.1.0",
                            }
                        )
                    )
                    ack = await asyncio.wait_for(ws.recv(), timeout=30.0)
                    logger.info("Registered with aideo-serv: %s", ack)

                    while self._running:
                        raw = await ws.recv()
                        if isinstance(raw, bytes):
                            raw = raw.decode()
                        msg = json.loads(raw)
                        asyncio.create_task(self._dispatch(msg))

            except asyncio.TimeoutError:
                logger.warning("Registration timed out, reconnecting in %ss", backoff)
            except Exception as exc:
                logger.warning(
                    "WebSocket disconnected (%s), reconnecting in %ss", exc, backoff
                )
            finally:
                self._ws = None

            if self._running:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30.0)

    async def shutdown(self) -> None:
        self._running = False
        if self._ws is not None:
            await self._ws.close()
            self._ws = None

    async def _ws_send(self, data: dict) -> None:
        if self._ws is not None:
            await self._ws.send(json.dumps(data))

    # ------------------------------------------------------------------
    # Task dispatch
    # ------------------------------------------------------------------

    async def _dispatch(self, msg: dict) -> None:
        msg_type = msg.get("type", "")
        task_id = msg.get("task_id", "")
        data = msg.get("data", {})

        if msg_type == "task_submit":
            task_type = msg.get("task_type", data.get("task_type", "video_generation"))
            await self._run_provider(task_id, task_type, data)
        elif msg_type == "task_cancel":
            logger.info("Cancel request for task %s", task_id)

    async def _run_provider(self, task_id: str, task_type: str, data: dict) -> None:
        """Execute a task through the registered provider."""
        # Lazy-load video provider on first use (heavy torch import)
        if (
            task_type == "video_generation"
            and self._registry
            and self._registry.get(task_type) is None
        ):
            from aideo_runtime.video.ltx2 import LTX2VideoProvider

            model_root = data.get("model_root", "") or os.environ.get(
                "AIDEO_MODEL_ROOT", "/mnt/g/AI/models"
            )
            output_root = data.get("output_root", "") or os.environ.get(
                "AIDEO_OUTPUT_ROOT", "./data/output"
            )
            input_root = data.get("input_root", "") or os.environ.get(
                "AIDEO_INPUT_ROOT", "./data/input"
            )
            params = data.get("params", {})

            provider = LTX2VideoProvider(
                distilled_checkpoint_path=str(
                    Path(model_root)
                    / "LTX-2.3"
                    / "ltx-2.3-22b-distilled-1.1.safetensors"
                ),
                gemma_root=str(
                    Path(model_root) / "gemma-3-12b-it-qat-q4_0-unquantized"
                ),
                spatial_upsampler_path=str(
                    Path(model_root)
                    / "LTX-2.3"
                    / "ltx-2.3-spatial-upscaler-x2-1.1.safetensors"
                ),
                lora_path=str(
                    Path(model_root)
                    / "LTX-2.3"
                    / "ltx-2.3-22b-distilled-lora-384-1.1.safetensors"
                ),
                lora_strength=float(params.pop("lora_strength", "1.0")),
                device=params.pop("device", None)
                or os.environ.get("LTX2_DEVICE", "cuda"),
                output_dir=output_root,
                input_root=input_root,
                offload_mode=params.pop("offload_mode", None)
                or os.environ.get("LTX2_OFFLOAD_MODE", "none"),
                quantization=params.pop("quantization", None)
                or os.environ.get("LTX2_QUANTIZATION", "fp8-cast"),
            )
            self._registry.register("video_generation", provider)

        provider = self._registry.get(task_type) if self._registry else None
        if provider is None:
            await self._ws_send(
                {
                    "type": "error",
                    "task_id": task_id,
                    "data": {"message": f"No provider for task_type: {task_type}"},
                }
            )
            return

        try:
            # Build kwargs from task_type-specific data fields
            kwargs = {"params": data.get("params", {}), "task_id": task_id}
            if task_type == "video_generation":
                kwargs["prompt"] = data.get("prompt", "")
            elif task_type == "speech_to_text":
                input_files = data.get("input_files", [])
                kwargs["audio_path"] = (
                    input_files[0]["path"]
                    if input_files
                    else data.get("params", {}).get("audio_path", "")
                )
                kwargs["language"] = data.get("params", {}).get("language")
            elif task_type == "text_conversation":
                kwargs["messages"] = data.get("params", {}).get("messages", [])
            elif task_type == "image_to_text":
                input_files = data.get("input_files", [])
                kwargs["image_path"] = input_files[0]["path"] if input_files else ""
                kwargs["prompt"] = data.get("prompt", "")

            async for event in provider.run(**kwargs):
                if "result_data" in event:
                    await self._ws_send(
                        {
                            "type": "completed",
                            "task_id": task_id,
                            "data": {
                                "result_path": event.get("result_path", ""),
                                "result_data": event["result_data"],
                            },
                        }
                    )
                else:
                    await self._ws_send(
                        {
                            "type": "progress",
                            "task_id": task_id,
                            "data": event,
                        }
                    )

        except asyncio.CancelledError:
            await self._ws_send(
                {
                    "type": "cancelled",
                    "task_id": task_id,
                    "data": {"message": "Cancelled"},
                }
            )
        except Exception as exc:
            logger.exception("Task %s failed", task_id)
            await self._ws_send(
                {"type": "error", "task_id": task_id, "data": {"message": str(exc)}}
            )


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

_ws_client: AideoWSClient | None = None


def _get_aideo_url() -> str:
    host = os.environ.get("AIDEO_SERVER_HOST", "localhost")
    port = os.environ.get("AIDEO_SERVER_PORT", "8000")
    return f"ws://{host}:{port}"


app = FastAPI(title="aideo-runtime", version="0.1.0")


@app.on_event("startup")
async def startup() -> None:
    global _ws_client
    server_url = os.environ.get("AIDEO_SERVER_URL", _get_aideo_url())

    model_root = os.environ.get("AIDEO_MODEL_ROOT", "/mnt/g/AI/models")
    output_root = os.environ.get("AIDEO_OUTPUT_ROOT", "./data/output")
    input_root = os.environ.get("AIDEO_INPUT_ROOT", "./data/input")

    registry = _create_registry(model_root, output_root, input_root)
    _ws_client = AideoWSClient(server_url=server_url)
    _ws_client.set_registry(registry)
    asyncio.create_task(_ws_client.connect_and_serve())
    logger.info("aideo-runtime started, connecting to aideo-serv at %s", server_url)


@app.on_event("shutdown")
async def shutdown() -> None:
    if _ws_client is not None:
        await _ws_client.shutdown()


@app.get("/health")
async def health() -> dict:
    connected = _ws_client is not None and _ws_client._ws is not None
    caps = (
        _ws_client._registry.capabilities if _ws_client and _ws_client._registry else []
    )
    return {
        "status": "ok" if connected else "connecting",
        "service": "aideo-runtime",
        "capabilities": caps,
    }


def main() -> None:
    host = os.environ.get("AIDEO_RUNTIME_HOST", "0.0.0.0")
    port = int(os.environ.get("AIDEO_RUNTIME_PORT", "9090"))
    uvicorn.run("aideo_runtime.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
