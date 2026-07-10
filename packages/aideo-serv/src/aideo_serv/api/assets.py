"""Asset upload / download / delete REST endpoints."""

from uuid import UUID

from aideo_serv.dependencies import get_asset_service
from aideo_serv.models.error import error_response
from aideo_serv.services.asset_service import AssetService
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse

assets_router = APIRouter(prefix="/assets", tags=["assets"])


@assets_router.post("", status_code=201)
async def upload_asset(
    file: UploadFile = File(...),
    project_id: UUID | None = Form(None),
    media_type: str | None = Form(None),
    svc: AssetService = Depends(get_asset_service),
):
    """Upload a reference file (image, video, audio). Max 50 MB."""
    try:
        asset = await svc.upload(file=file, project_id=project_id, media_type=media_type)
        return asset
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=error_response("VALIDATION_ERROR", str(e))[0],
        )


@assets_router.get("/{asset_id}")
async def get_asset(
    asset_id: UUID,
    svc: AssetService = Depends(get_asset_service),
):
    """Get asset metadata by ID."""
    try:
        return svc.get(asset_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "RESOURCE_NOT_FOUND", f"Asset {asset_id} not found"
            )[0],
        )


@assets_router.get("/{asset_id}/download")
async def download_asset(
    asset_id: UUID,
    svc: AssetService = Depends(get_asset_service),
):
    """Download an asset's file binary."""
    try:
        file_path = svc.get_file_path(asset_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "RESOURCE_NOT_FOUND", f"Asset {asset_id} not found"
            )[0],
        )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=error_response("RESOURCE_NOT_FOUND", "File not found on disk")[0],
        )

    asset = svc.get(asset_id)
    return FileResponse(
        path=str(file_path),
        media_type=asset.content_type,
        filename=asset.filename,
    )


@assets_router.delete("/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: UUID,
    svc: AssetService = Depends(get_asset_service),
):
    """Delete an asset and its file."""
    try:
        svc.delete(asset_id)
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "RESOURCE_NOT_FOUND", f"Asset {asset_id} not found"
            )[0],
        )
    return Response(status_code=204)
