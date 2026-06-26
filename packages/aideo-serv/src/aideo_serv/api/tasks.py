"""Task CRUD REST endpoints."""

from uuid import UUID

from aideo_serv.dependencies import get_task_service
from aideo_serv.models.task import TaskCreate
from aideo_serv.services.task_service import TaskService
from fastapi import APIRouter, Depends, HTTPException, Query

tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


@tasks_router.post("", status_code=201)
async def create_task(
    payload: TaskCreate,
    svc: TaskService = Depends(get_task_service),
):
    """Submit a new video generation task."""
    task = svc.create(prompt=payload.prompt, params=payload.params)
    return task


@tasks_router.get("")
async def list_tasks(
    status: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    svc: TaskService = Depends(get_task_service),
):
    """List tasks with optional status filter and pagination."""
    return svc.list(status=status, offset=offset, limit=limit)


@tasks_router.get("/{task_id}")
async def get_task(
    task_id: UUID,
    svc: TaskService = Depends(get_task_service),
):
    """Get a single task by ID."""
    try:
        return svc.get(task_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Task not found")


@tasks_router.delete("/{task_id}")
async def cancel_task(
    task_id: UUID,
    svc: TaskService = Depends(get_task_service),
):
    """Cancel a task."""
    try:
        return svc.cancel(task_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Task not found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
