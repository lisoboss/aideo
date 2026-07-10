"""WebSocket endpoints for real-time task progress and inference services."""

import logging
from pathlib import Path
from uuid import UUID, uuid4

from aideo_serv.config import Settings
from aideo_serv.dependencies import (
    get_connection_manager,
    get_inference_manager,
    get_task_service,
)
from aideo_serv.models.events import InferenceMessage, WSEvent
from aideo_serv.models.task import TaskStatus
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

ws_router = APIRouter(prefix="/ws", tags=["websocket"])


@ws_router.websocket("/tasks/{task_id}")
async def task_progress(websocket: WebSocket, task_id: UUID):
    """Stream task progress events to the client over WebSocket."""
    await websocket.accept()

    svc = get_task_service()
    try:
        task = svc.get(task_id)
    except LookupError:
        await websocket.close(code=4004, reason="Task not found")
        return

    manager = get_connection_manager()
    queue = manager.subscribe(task_id)

    _TERMINAL = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}

    try:
        await websocket.send_json(
            WSEvent(
                type="status_change",
                task_id=str(task_id),
                data={"status": task.status.value},
            ).model_dump(mode="json")
        )

        # If the task is already in a terminal state, send the relevant
        # final event and close — no more events will arrive on the queue.
        if task.status == TaskStatus.FAILED and task.error_message:
            await websocket.send_json(
                WSEvent(
                    type="error",
                    task_id=str(task_id),
                    data={"message": task.error_message},
                ).model_dump(mode="json")
            )
        elif task.status == TaskStatus.COMPLETED and task.result_url:
            await websocket.send_json(
                WSEvent(
                    type="completed",
                    task_id=str(task_id),
                    data={
                        "result_url": task.result_url,
                        "result_data": task.result_data,
                    },
                ).model_dump(mode="json")
            )

        if task.status in _TERMINAL:
            await websocket.close()
            return

        while True:
            event = await queue.get()
            if event is None:
                break
            await websocket.send_json(event)

    except WebSocketDisconnect:
        pass
    finally:
        manager.unsubscribe(task_id, queue)


# ---------------------------------------------------------------------------
# Internal WebSocket endpoint — inference services connect here
# ---------------------------------------------------------------------------


@ws_router.websocket("/internal/inference")
async def inference_service(websocket: WebSocket):
    """Internal WebSocket for local inference services (ltx2, whisper, …).

    Inference services connect at startup and register with their
    ``service_type`` and ``capabilities``.  aideo-serv then routes
    task_submit / task_cancel messages over this persistent channel.
    """
    mgr = get_inference_manager()
    await mgr.handle_connection(websocket)


# ---------------------------------------------------------------------------
# Streaming speech-to-text — "one audio → one text" over a persistent WS
# ---------------------------------------------------------------------------


@ws_router.websocket("/transcribe")
async def transcribe_stream(websocket: WebSocket):
    """Streaming speech-to-text WebSocket.

    Client sends binary audio frames (one utterance per frame), server
    replies with JSON progress/result events.  The connection stays open
    so the client can send multiple audio clips without reconnecting.

    Protocol
    --------
    **Client → Server** (binary frames)
        Raw audio bytes — PCM 16kHz 16-bit mono or WAV.

    **Server → Client** (JSON text frames)
        ``{"type": "status_change", "data": {"status": "queued"}}``
        ``{"type": "progress", "data": {"progress": 50.0, "message": "…"}}``
        ``{"type": "result", "data": {"full_text": "…", "segments": […], …}}``
        ``{"type": "error", "data": {"message": "…"}}``
    """
    await websocket.accept()

    svc = get_task_service()
    mgr = get_inference_manager()
    conn_mgr = get_connection_manager()
    settings = Settings()
    service_type = "aideo-runtime"

    try:
        while True:
            # ---- receive binary audio ---------------------------------
            try:
                audio_bytes = await websocket.receive_bytes()
            except WebSocketDisconnect:
                break

            if not audio_bytes:
                continue

            # ---- save to temp file ------------------------------------
            temp_dir = Path(settings.output_root) / ".stream_tmp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_path = temp_dir / f"chunk_{uuid4().hex[:12]}.wav"
            temp_path.write_bytes(audio_bytes)

            task_id = None
            queue = None

            try:
                # ---- create task --------------------------------------
                task = svc.create(
                    prompt=f"Stream transcription {temp_path.name}",
                    params={},
                    task_type="speech_to_text",
                    input_files=[{"path": str(temp_path), "type": "audio"}],
                )
                task_id = task.id

                # ---- subscribe BEFORE any events are broadcast ----------
                queue = conn_mgr.subscribe(task_id)

                # ---- submit to inference runtime -----------------------
                svc.update_status(task_id, TaskStatus.RUNNING.value)
                svc.update_status(task_id, TaskStatus.GENERATING.value)

                inference_msg = InferenceMessage(
                    type="task_submit",
                    task_id=str(task_id),
                    task_type="speech_to_text",
                    data={
                        "prompt": task.prompt,
                        "params": task.params or {},
                        "model_root": settings.model_root,
                        "output_root": settings.output_root,
                        "input_root": settings.input_root,
                        "input_files": task.input_files or [],
                    },
                )
                await mgr.send_to_service(service_type, inference_msg)

                # ---- wait for result via event queue -------------------
                while True:
                    event = await queue.get()
                    if event is None:
                        break
                    await websocket.send_json(event)

                    parsed = event if isinstance(event, dict) else {}
                    etype = parsed.get("type", "")
                    if etype in ("completed", "error"):
                        # Send a clean "result" / "error" event with full data
                        final_task = svc.get(task_id)
                        if etype == "completed" and final_task.result_data:
                            await websocket.send_json({
                                "type": "result",
                                "task_id": str(task_id),
                                "data": final_task.result_data,
                            })
                        elif etype == "error":
                            await websocket.send_json({
                                "type": "error",
                                "task_id": str(task_id),
                                "data": {
                                    "message": final_task.error_message or "Unknown error",
                                },
                            })
                        break

            except LookupError:
                await websocket.send_json({
                    "type": "error",
                    "data": {
                        "message": f"Inference service '{service_type}' is not connected",
                    },
                })
            except Exception:
                logger.exception("Stream transcription failed for task %s", task_id)
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Internal server error during transcription"},
                })
            finally:
                if queue is not None and task_id is not None:
                    conn_mgr.unsubscribe(task_id, queue)
                # Clean up temp file
                try:
                    temp_path.unlink(missing_ok=True)
                except Exception:
                    pass

    except WebSocketDisconnect:
        pass
