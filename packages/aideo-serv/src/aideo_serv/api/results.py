"""Result download and preview endpoints."""

from pathlib import Path
from uuid import UUID

from aideo_serv.dependencies import get_task_service
from aideo_serv.models.task import TaskStatus
from aideo_serv.services.task_service import TaskService
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse

results_router = APIRouter(prefix="/results", tags=["results"])


@results_router.get("/{task_id}/download")
async def download_result(
    task_id: UUID,
    svc: TaskService = Depends(get_task_service),
):
    """Download the generated video for a completed task."""
    try:
        task = svc.get(task_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Result not available")

    # Inline result data (e.g. speech-to-text transcription) — return as JSON
    if task.result_data:
        return JSONResponse(content=task.result_data)

    # File-based result (e.g. generated video)
    if not task.result_path:
        raise HTTPException(status_code=404, detail="Result not available")

    path = Path(task.result_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(path=path, media_type="video/mp4", filename=f"{task_id}.mp4")


@results_router.get("/{task_id}/preview/{frame}")
async def get_preview(
    task_id: UUID,
    frame: str,
    svc: TaskService = Depends(get_task_service),
):
    """Get a preview image frame for a task."""
    try:
        task = svc.get(task_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Task not found")

    for preview_url in task.previews:
        preview_path = Path(preview_url)
        if preview_path.exists() and preview_path.name.startswith(frame):
            return FileResponse(path=preview_path, media_type="image/jpeg")

    raise HTTPException(status_code=404, detail="Preview not found")
