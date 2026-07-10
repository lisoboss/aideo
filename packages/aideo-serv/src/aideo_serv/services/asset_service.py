"""Asset upload / download / delete service."""

import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import aiofiles
from aideo_serv.config import Settings
from aideo_serv.models.asset import Asset, AssetListResponse
from fastapi import UploadFile


class AssetService:
    """Manages uploaded reference files (images, video, audio).

    File layout::

        {asset_base_dir}/{asset_id[:2]}/{asset_id}/{original_filename}
    """

    MAX_ASSET_SIZE = 50 * 1024 * 1024  # 50 MB

    def __init__(self, base_dir: str | Path | None = None):
        settings = Settings()
        self._base_dir = Path(base_dir or settings.asset_base_dir)
        self._assets: dict[UUID, Asset] = {}

    # ------------------------------------------------------------------
    # Storage helpers
    # ------------------------------------------------------------------

    def _asset_dir(self, asset_id: UUID) -> Path:
        prefix = str(asset_id)[:2]
        return self._base_dir / prefix / str(asset_id)

    def _ensure_dir(self, path: Path) -> None:
        os.makedirs(path, exist_ok=True)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def upload(
        self,
        file: UploadFile,
        project_id: UUID | None = None,
        media_type: str | None = None,
    ) -> Asset:
        """Save an uploaded file to disk and return its Asset metadata."""
        if file.filename is None:
            raise ValueError("Filename is required")

        # Read content (capped at MAX_ASSET_SIZE)
        content = await file.read()
        if len(content) > self.MAX_ASSET_SIZE:
            raise ValueError(
                f"File size {len(content)} exceeds maximum {self.MAX_ASSET_SIZE} bytes"
            )

        asset_id = uuid4()
        asset_dir = self._asset_dir(asset_id)
        self._ensure_dir(asset_dir)

        file_path = asset_dir / file.filename
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        # Auto-detect media_type from MIME if not provided
        if media_type is None:
            if file.content_type:
                ct = file.content_type.lower()
                if ct.startswith("image/"):
                    media_type = "image"
                elif ct.startswith("video/"):
                    media_type = "video"
                elif ct.startswith("audio/"):
                    media_type = "audio"
                else:
                    media_type = "other"
            else:
                media_type = "image"

        now = datetime.now(timezone.utc)
        asset = Asset(
            id=asset_id,
            project_id=project_id,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            size=len(content),
            media_type=media_type,
            uploaded_at=now,
            url=f"/api/v1/assets/{asset_id}/download",
            metadata={},
        )
        self._assets[asset.id] = asset
        return asset

    def get(self, asset_id: UUID) -> Asset:
        """Get asset metadata by ID. Raises LookupError if not found."""
        if asset_id not in self._assets:
            raise LookupError(f"Asset {asset_id} not found")
        return self._assets[asset_id]

    def list(
        self,
        project_id: UUID | None = None,
        media_type: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> AssetListResponse:
        """List assets with optional project and media_type filters."""
        assets = list(self._assets.values())
        if project_id is not None:
            assets = [a for a in assets if a.project_id == project_id]
        if media_type is not None:
            assets = [a for a in assets if a.media_type == media_type]
        assets.sort(key=lambda a: a.uploaded_at, reverse=True)
        total = len(assets)
        page = assets[offset : offset + limit]
        return AssetListResponse(items=page, total=total, offset=offset, limit=limit)

    def get_file_path(self, asset_id: UUID) -> Path:
        """Return the on-disk path for an asset's file."""
        asset = self.get(asset_id)
        return self._asset_dir(asset_id) / asset.filename

    def delete(self, asset_id: UUID) -> None:
        """Delete an asset and its file from disk."""
        asset = self.get(asset_id)
        file_path = self._asset_dir(asset_id) / asset.filename
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass
        # Clean up empty directories
        try:
            asset_dir = self._asset_dir(asset_id)
            preview_dir = asset_dir.parent
            asset_dir.rmdir()  # only if empty
            # try removing the 2-char prefix dir too
            preview_dir.rmdir()
        except Exception:
            pass
        del self._assets[asset_id]

    async def delete_by_project(self, project_id: UUID) -> int:
        """Delete all assets belonging to a project. Returns count deleted."""
        to_delete = [
            aid for aid, a in self._assets.items() if a.project_id == project_id
        ]
        for aid in to_delete:
            self.delete(aid)
        return len(to_delete)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_asset_service: AssetService | None = None


def get_asset_service() -> AssetService:
    """Return the global AssetService singleton."""
    global _asset_service
    if _asset_service is None:
        _asset_service = AssetService()
    return _asset_service


def set_asset_service(svc: AssetService) -> None:
    """Replace the global singleton (for testing)."""
    global _asset_service
    _asset_service = svc
