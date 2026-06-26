"""WebSocket endpoint for real-time task progress."""

from uuid import UUID

from aideo_serv.dependencies import get_connection_manager, get_task_service
from aideo_serv.models.events import WSEvent
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

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

    try:
        await websocket.send_json(
            WSEvent(
                type="status_change",
                task_id=str(task_id),
                data={"status": task.status.value},
            ).model_dump(mode="json")
        )

        while True:
            event = await queue.get()
            if event is None:
                break
            await websocket.send_json(event)

    except WebSocketDisconnect:
        pass
    finally:
        manager.unsubscribe(task_id, queue)
