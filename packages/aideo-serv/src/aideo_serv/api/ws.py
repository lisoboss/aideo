"""WebSocket endpoints for real-time task progress and inference services."""

import logging
from pathlib import Path
from uuid import UUID, uuid4

from aideo_serv.config import Settings
from aideo_serv.dependencies import (
    get_connection_manager,
    get_inference_client,
    get_project_service,
    get_task_service,
)
from aideo_serv.models.events import WSEvent
from aideo_serv.models.task import TaskStatus
from aideo_serv.services.inference_client import TaskCallbacks
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
    client = get_inference_client()
    settings = Settings()

    try:
        while True:
            try:
                audio_bytes = await websocket.receive_bytes()
            except (WebSocketDisconnect, RuntimeError):
                break

            if not audio_bytes:
                continue

            temp_dir = Path(settings.output_root).resolve() / ".stream_tmp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_path = temp_dir / f"chunk_{uuid4().hex[:12]}.wav"
            temp_path.write_bytes(audio_bytes)

            task_id = None

            try:
                task = svc.create(
                    prompt=f"Stream transcription {temp_path.name}",
                    params={},
                    task_type="speech_to_text",
                    input_files=[{"path": str(temp_path), "type": "audio"}],
                )
                task_id = task.id

                await websocket.send_json({
                    "type": "status_change",
                    "data": {"status": "queued"},
                })

                svc.update_status(task_id, TaskStatus.RUNNING.value)
                svc.update_status(task_id, TaskStatus.GENERATING.value)

                await websocket.send_json({
                    "type": "progress",
                    "data": {"progress": 0.0, "message": "Transcribing..."},
                })

                # Call runtime via HTTP+SSE
                callbacks = TaskCallbacks(
                    on_progress=lambda p, m: _safe_send(websocket, {
                        "type": "progress", "data": {"progress": p, "message": m},
                    }),
                    on_completed=lambda d: _handle_stt_completed(task_id, d, websocket, svc),
                    on_error=lambda m: _safe_send(websocket, {
                        "type": "error", "task_id": str(task_id), "data": {"message": m},
                    }),
                )

                await client.run("speech_to_text", {
                    "audio_path": str(temp_path),
                    "params": task.params or {},
                    "task_id": str(task_id),
                }, callbacks)

            except Exception:
                logger.exception("Stream transcription failed for task %s", task_id)
                await _safe_send(websocket, {
                    "type": "error",
                    "data": {"message": "Internal server error during transcription"},
                })
            finally:
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


async def _handle_stt_completed(
    task_id: UUID, result_data: dict, websocket: WebSocket, svc,
) -> None:
    """Handle speech-to-text completion: complete task + send result to WS."""
    try:
        svc.complete(task_id, "", result_data)
        await websocket.send_json({
            "type": "result",
            "task_id": str(task_id),
            "data": result_data,
        })
    except (WebSocketDisconnect, RuntimeError, ValueError):
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
