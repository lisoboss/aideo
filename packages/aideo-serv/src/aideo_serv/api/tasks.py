"""Task CRUD REST endpoints."""

import asyncio
import logging
from uuid import UUID

from aideo_serv.config import Settings
from aideo_serv.dependencies import get_inference_client, get_task_service
from aideo_serv.models.error import error_response
from aideo_serv.models.task import TaskCreate, TaskStatus
from aideo_serv.services.inference_client import TaskCallbacks
from aideo_serv.services.task_service import TaskService
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])

# ---- callback model (kept for backward compat / cloud inference) -----------


class CallbackPayload(BaseModel):
    """Payload received from the inference service via HTTP callback."""

    type: str  # progress | completed | error
    task_id: UUID
    data: dict


# ---- service-type resolution ----------------------------------------------


_SERVICE_FOR_TASK_TYPE: dict[str, str] = {
    "video_generation": "aideo-runtime",
    "speech_to_text": "aideo-runtime",
    "text_conversation": "aideo-runtime",
    "image_to_text": "aideo-runtime",
}


def _resolve_service(task_type: str | None) -> str:
    """Map a task_type to the inference service_type that handles it."""
    return _SERVICE_FOR_TASK_TYPE.get(task_type or "video_generation", "ltx2")


# ---- orchestration helper --------------------------------------------------


async def _submit_to_inference(
    task_id: UUID,
    prompt: str,
    params: dict | None,
    task_type: str = "video_generation",
    input_files: list[dict] | None = None,
    *,
    preempt: bool = False,
) -> None:
    """Transition task through RUNNING → GENERATING, dispatch via HTTP+SSE."""
    svc = get_task_service()
    client = get_inference_client()
    settings = Settings()

    try:
        svc.update_status(task_id, TaskStatus.RUNNING.value)
        svc.update_status(task_id, TaskStatus.GENERATING.value)

        payload = {
            "prompt": prompt,
            "params": params or {},
            "model_root": settings.model_root,
            "output_root": settings.output_root,
            "input_root": settings.input_root,
            "input_files": input_files or [],
            "task_id": str(task_id),
        }

        callbacks = TaskCallbacks(
            on_progress=lambda p, m: _on_progress(task_id, p, m),
            on_completed=lambda d: _on_completed(task_id, d),
            on_error=lambda m: _on_error(task_id, m),
        )

        await client.run(task_type, payload, callbacks, preempt=preempt)
    except Exception as exc:
        logger.exception("Failed to submit task %s to inference", task_id)
        svc.fail(task_id, str(exc))


async def _on_progress(task_id: UUID, progress: float, message: str) -> None:
    svc = get_task_service()
    try:
        svc.update_progress(task_id, progress, message)
    except ValueError:
        pass  # already terminal


async def _on_completed(task_id: UUID, result_data: dict) -> None:
    svc = get_task_service()
    try:
        svc.complete(task_id, "", result_data)
    except ValueError:
        pass


async def _on_error(task_id: UUID, message: str) -> None:
    svc = get_task_service()
    try:
        svc.fail(task_id, message)
    except ValueError:
        pass


# ---- REST endpoints ----------------------------------------------------


@tasks_router.post("", status_code=201)
async def create_task(
    payload: TaskCreate,
    svc: TaskService = Depends(get_task_service),
):
    """Submit a new generation task (video, speech-to-text, …)."""
    task = svc.create(
        prompt=payload.prompt,
        params=payload.params,
        task_type=payload.task_type,
        project_id=payload.project_id,
        output_node_id=payload.output_node_id,
        prompt_structured=payload.prompt_structured,
        input_files=payload.input_files,
    )
    asyncio.create_task(
        _submit_to_inference(
            task.id, task.prompt, task.params, task.task_type, task.input_files,
        )
    )
    return task


@tasks_router.get("")
async def list_tasks(
    status: str | None = Query(None),
    project_id: UUID | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    svc: TaskService = Depends(get_task_service),
):
    """List tasks with optional status/project_id filter and pagination."""
    return svc.list(status=status, project_id=project_id, offset=offset, limit=limit)


@tasks_router.get("/{task_id}")
async def get_task(
    task_id: UUID,
    svc: TaskService = Depends(get_task_service),
):
    """Get a single task by ID."""
    try:
        return svc.get(task_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "RESOURCE_NOT_FOUND", f"Task {task_id} not found"
            )[0],
        )


@tasks_router.delete("/{task_id}")
async def cancel_task(
    task_id: UUID,
    svc: TaskService = Depends(get_task_service),
):
    """Cancel a task. Forwards cancellation to inference service if generating."""
    try:
        task = svc.get(task_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "RESOURCE_NOT_FOUND", f"Task {task_id} not found"
            )[0],
        )

    # Runtime called via HTTP+SSE — cancel by client disconnect / timeout
    try:
        return svc.cancel(task_id)
    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=error_response("CONFLICT", str(e))[0],
        )
