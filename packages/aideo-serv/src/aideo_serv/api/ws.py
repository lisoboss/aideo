"""WebSocket endpoints for real-time task progress and inference services."""

import logging
from pathlib import Path
from uuid import UUID, uuid4

from aideo_serv.config import Settings
from aideo_serv.dependencies import (
    get_connection_manager,
    get_inference_manager,
    get_project_service,
    get_task_service,
)
from aideo_serv.models.events import InferenceMessage, WSEvent
from aideo_serv.models.task import TaskStatus
from aideo_serv.services.task_service import _EVENT_DISCRIMINATOR
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

ws_router = APIRouter(prefix="/ws", tags=["websocket"])

_TERMINAL = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}


# ---------------------------------------------------------------------------
# Per-task WebSocket (v1 backward compat + typed v2 events)
# ---------------------------------------------------------------------------


@ws_router.websocket("/tasks/{task_id}")
async def task_progress(websocket: WebSocket, task_id: UUID):
    """Stream task progress events to the client over WebSocket.

    Events include both legacy ``{type, data}`` format and v2 typed
    ``event`` discriminator for forward compatibility.
    """
    await websocket.accept()

    svc = get_task_service()
    try:
        task = svc.get(task_id)
    except LookupError:
        await websocket.close(code=4004, reason="Task not found")
        return

    manager = get_connection_manager()
    queue = manager.subscribe(task_id)

    try:
        # Send current status on connect
        status_event = _build_typed_event(
            task, "status_change", {"status": task.status.value}
        )
        await websocket.send_json(status_event)

        # If already terminal, send final event and close
        if task.status == TaskStatus.FAILED and task.error_message:
            await websocket.send_json(
                _build_typed_event(task, "error", {"message": task.error_message})
            )
        elif task.status == TaskStatus.COMPLETED and task.result_url:
            await websocket.send_json(
                _build_typed_event(
                    task,
                    "completed",
                    {
                        "result_url": task.result_url,
                        "result_data": task.result_data,
                    },
                )
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
# Per-project WebSocket (v2 multiplexed)
# ---------------------------------------------------------------------------


@ws_router.websocket("/projects/{project_id}")
async def project_progress(websocket: WebSocket, project_id: UUID):
    """Multiplexed project-level WebSocket — single connection for all tasks.

    Connection lifecycle:
    1. Accept → send ``connected`` event with active-tasks snapshot
    2. Stream typed events for all task state changes in the project
    3. Connection stays open even after all tasks terminal (waiting for new)
    4. Close codes: 4004=project not found
    """
    await websocket.accept()

    proj_svc = get_project_service()
    try:
        proj_svc.get(project_id)
    except LookupError:
        await websocket.close(code=4004, reason="Project not found")
        return

    task_svc = get_task_service()
    conn_mgr = get_connection_manager()

    # Subscribe to project-level events
    queue = conn_mgr.subscribe_project(project_id)

    try:
        # ---- send connected event with active-tasks snapshot --------------
        active_tasks = task_svc.get_active_by_project(project_id)
        snapshot_tasks = []
        for t in active_tasks:
            snapshot_tasks.append({
                "task_id": str(t.id),
                "output_node_id": str(t.output_node_id) if t.output_node_id else None,
                "status": t.status.value,
                "progress": t.progress,
                "previews": t.previews,
            })

        connected_event = {
            "event": "connected",
            "project_id": str(project_id),
            "snapshot": {"active_tasks": snapshot_tasks},
        }
        await websocket.send_json(connected_event)

        # ---- stream events ------------------------------------------------
        while True:
            event = await queue.get()
            if event is None:
                break
            await websocket.send_json(event)

    except WebSocketDisconnect:
        pass
    finally:
        conn_mgr.unsubscribe_project(project_id, queue)


# ---------------------------------------------------------------------------
# Internal WebSocket — inference services connect here
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
            except (WebSocketDisconnect, RuntimeError):
                break

            if not audio_bytes:
                continue

            # ---- save to temp file (absolute path for runtime) ---------
            temp_dir = Path(settings.output_root).resolve() / ".stream_tmp"
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
                    try:
                        await websocket.send_json(event)
                    except (WebSocketDisconnect, RuntimeError):
                        break  # client disconnected, stop sending

                    parsed = event if isinstance(event, dict) else {}
                    etype = parsed.get("type", "")
                    if etype in ("completed", "error"):
                        try:
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
                        except (WebSocketDisconnect, RuntimeError):
                            pass
                        break

            except LookupError:
                await _safe_send(websocket, {
                    "type": "error",
                    "data": {
                        "message": f"Inference service '{service_type}' is not connected",
                    },
                })
            except Exception:
                logger.exception("Stream transcription failed for task %s", task_id)
                await _safe_send(websocket, {
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _safe_send(websocket: WebSocket, data: dict) -> None:
    """Send JSON over WS, silently drop if client already disconnected."""
    try:
        await websocket.send_json(data)
    except (WebSocketDisconnect, RuntimeError):
        pass


def _build_typed_event(task, event_type: str, data: dict) -> dict:
    """Build a v2 typed event dict from a task for WS broadcast.

    Includes both the legacy ``{type, data}`` format and v2 typed fields.
    """
    event_discriminator = _EVENT_DISCRIMINATOR.get(event_type, event_type)

    # Base legacy event
    legacy = WSEvent(
        type=event_type,
        task_id=str(task.id),
        data=data,
    )
    payload = legacy.model_dump(mode="json")

    # Add v2 typed fields
    payload["event"] = event_discriminator
    if task.output_node_id is not None:
        payload["output_node_id"] = str(task.output_node_id)

    if event_type == "status_change":
        payload["status"] = data.get("status")
    elif event_type == "progress":
        payload["progress"] = data.get("progress")
        payload["message"] = data.get("message", "")
    elif event_type == "preview":
        payload["frame_url"] = data.get("url")
    elif event_type == "completed":
        payload["result_url"] = data.get("result_url")
        payload["result_data"] = task.result_data
        payload["previews"] = task.previews
    elif event_type == "error":
        payload["error_message"] = data.get("message")

    return payload
