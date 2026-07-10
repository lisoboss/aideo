"""Image edit / upscale endpoints — POST /canvas/edit-image, /canvas/upscale.

These mirror the /generate flow: validate assets & project, serialize the
structured prompt, create a task, and dispatch to aideo-runtime via HTTP+SSE
(fire-and-forget). The client tracks progress over the project-level WebSocket.

Runtime providers for ``image_edit`` / ``image_upscale`` are registered in
``inference_client.TASK_TO_PROVIDER``; until aideo-runtime ships an ``image``
category, the dispatched task fails gracefully with a clear error.
"""

import asyncio
import logging
from uuid import UUID

from aideo_serv.api.tasks import _submit_to_inference
from aideo_serv.dependencies import (
    get_asset_service,
    get_project_service,
    get_task_service,
)
from aideo_serv.models.edit import (
    EditImageRequest,
    EditImageResponse,
    UpscaleRequest,
    UpscaleResponse,
)
from aideo_serv.models.error import error_response
from aideo_serv.services.asset_service import AssetService
from aideo_serv.services.project_service import ProjectService
from aideo_serv.services.prompt_serializer import serialize_prompt
from aideo_serv.services.task_service import TaskService
from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)
image_router = APIRouter(prefix="/canvas", tags=["canvas"])


def _resolve_asset(asset_svc: AssetService, asset_id: UUID, role: str) -> dict:
    """Validate an asset exists and return its input-file descriptor.

    Raises HTTPException(404) if the asset is unknown.
    """
    try:
        asset_svc.get(asset_id)
        path = asset_svc.get_file_path(asset_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail=error_response("RESOURCE_NOT_FOUND", f"Asset {asset_id} not found")[
                0
            ],
        )
    return {"path": str(path), "type": "image", "role": role, "asset_id": str(asset_id)}


@image_router.post("/edit-image", status_code=201)
async def edit_image(
    payload: EditImageRequest,
    task_svc: TaskService = Depends(get_task_service),
    proj_svc: ProjectService = Depends(get_project_service),
    asset_svc: AssetService = Depends(get_asset_service),
) -> EditImageResponse:
    """Submit an AI image edit.

    Modes: composite / replace_character / inpainting / style_transfer.
    """
    # Validate project exists if provided
    if payload.project_id is not None:
        try:
            proj_svc.get(payload.project_id)
        except LookupError:
            raise HTTPException(
                status_code=404,
                detail=error_response(
                    "RESOURCE_NOT_FOUND", f"Project {payload.project_id} not found"
                )[0],
            )

    # Validate & resolve base + reference assets
    input_files = [_resolve_asset(asset_svc, payload.base_image, "base")]
    for ref_id in payload.reference_images:
        input_files.append(_resolve_asset(asset_svc, ref_id, "reference"))

    # Serialize the structured prompt blocks (no connections for edit)
    prompt = serialize_prompt(payload.prompt_blocks, [])
    if not prompt:
        prompt = f"Image edit ({payload.mode.value})"

    params = {
        "mode": payload.mode.value,
        "base_image": str(payload.base_image),
        "reference_images": [str(a) for a in payload.reference_images],
        "mask_regions": [m.model_dump() for m in payload.mask_regions],
        "language": payload.language,
        "ai_provider": payload.ai_provider,
    }

    prompt_structured = {
        "mode": payload.mode.value,
        "base_image": str(payload.base_image),
        "reference_images": [str(a) for a in payload.reference_images],
        "mask_regions": [m.model_dump() for m in payload.mask_regions],
        "prompt_blocks": [b.model_dump(mode="json") for b in payload.prompt_blocks],
    }

    task = task_svc.create(
        prompt=prompt,
        params=params,
        task_type="image_edit",
        project_id=payload.project_id,
        prompt_structured=prompt_structured,
        input_files=input_files,
    )

    if payload.project_id is not None:
        proj_svc.increment_task_count(payload.project_id)

    asyncio.create_task(
        _submit_to_inference(task.id, prompt, params, "image_edit", input_files)
    )

    return EditImageResponse(task_id=task.id, task=task)


@image_router.post("/upscale", status_code=201)
async def upscale(
    payload: UpscaleRequest,
    task_svc: TaskService = Depends(get_task_service),
    asset_svc: AssetService = Depends(get_asset_service),
) -> UpscaleResponse:
    """Submit an image super-resolution task (2x / 4x)."""
    input_files = [_resolve_asset(asset_svc, payload.asset_id, "source")]

    params = {"scale": payload.scale, "asset_id": str(payload.asset_id)}
    prompt = f"Upscale {payload.scale}x"

    task = task_svc.create(
        prompt=prompt,
        params=params,
        task_type="image_upscale",
        prompt_structured=params,
        input_files=input_files,
    )

    asyncio.create_task(
        _submit_to_inference(task.id, prompt, params, "image_upscale", input_files)
    )

    return UpscaleResponse(task_id=task.id, task=task)
