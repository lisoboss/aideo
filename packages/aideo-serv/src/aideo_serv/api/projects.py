"""Project CRUD REST endpoints."""

import logging
from uuid import UUID

from aideo_serv.dependencies import (
    get_asset_service,
    get_project_service,
    get_task_service,
)
from aideo_serv.models.error import error_response
from aideo_serv.models.project import ProjectCreate, ProjectUpdate
from aideo_serv.services.asset_service import AssetService
from aideo_serv.services.project_service import ProjectService
from aideo_serv.services.task_service import TaskService
from fastapi import APIRouter, Depends, HTTPException, Query, Response

logger = logging.getLogger(__name__)
projects_router = APIRouter(prefix="/projects", tags=["projects"])


@projects_router.post("", status_code=201)
async def create_project(
    payload: ProjectCreate,
    svc: ProjectService = Depends(get_project_service),
):
    """Create a new canvas project."""
    project = svc.create(
        name=payload.name,
        canvas_data=payload.canvas_data,
        metadata=payload.metadata,
    )
    return project


@projects_router.get("")
async def list_projects(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    svc: ProjectService = Depends(get_project_service),
):
    """List projects with pagination."""
    return svc.list(offset=offset, limit=limit)


@projects_router.get("/{project_id}")
async def get_project(
    project_id: UUID,
    svc: ProjectService = Depends(get_project_service),
):
    """Get a single project by ID."""
    try:
        return svc.get(project_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "RESOURCE_NOT_FOUND", f"Project {project_id} not found"
            )[0],
        )


@projects_router.patch("/{project_id}")
async def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    svc: ProjectService = Depends(get_project_service),
):
    """Partially update a project (name, canvas_data, metadata)."""
    try:
        return svc.update(project_id, payload)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "RESOURCE_NOT_FOUND", f"Project {project_id} not found"
            )[0],
        )


@projects_router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    proj_svc: ProjectService = Depends(get_project_service),
    asset_svc: AssetService = Depends(get_asset_service),
    task_svc: TaskService = Depends(get_task_service),
):
    """Delete a project and its associated tasks + assets."""
    try:
        proj_svc.get(project_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "RESOURCE_NOT_FOUND", f"Project {project_id} not found"
            )[0],
        )

    # Cascade-delete tasks
    await task_svc.delete_by_project(project_id)
    # Cascade-delete assets
    await asset_svc.delete_by_project(project_id)
    # Delete project
    proj_svc.delete(project_id)
    return Response(status_code=204)


@projects_router.get("/{project_id}/tasks")
async def list_project_tasks(
    project_id: UUID,
    status: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    proj_svc: ProjectService = Depends(get_project_service),
    task_svc: TaskService = Depends(get_task_service),
):
    """List tasks belonging to a project."""
    try:
        proj_svc.get(project_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "RESOURCE_NOT_FOUND", f"Project {project_id} not found"
            )[0],
        )
    return task_svc.list_by_project(
        project_id=project_id, status=status, offset=offset, limit=limit
    )


@projects_router.get("/{project_id}/assets")
async def list_project_assets(
    project_id: UUID,
    media_type: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    proj_svc: ProjectService = Depends(get_project_service),
    asset_svc: AssetService = Depends(get_asset_service),
):
    """List assets belonging to a project."""
    try:
        proj_svc.get(project_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "RESOURCE_NOT_FOUND", f"Project {project_id} not found"
            )[0],
        )
    return asset_svc.list(project_id=project_id, media_type=media_type, offset=offset, limit=limit)
