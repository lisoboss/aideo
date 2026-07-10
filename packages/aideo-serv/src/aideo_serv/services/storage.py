"""File storage abstraction for video results and previews."""

import os
from pathlib import Path

import aiofiles


class StorageService:
    """Manages local file storage for generated videos and preview images.

    Directory structure::
        {base_dir}/{task_id[:2]}/{task_id}/
            video.mp4
            preview/
                0000.jpg
                0001.jpg
                ...
    """

    def __init__(self, base_dir: str | Path = "./data"):
        """Initialize with the root storage directory."""
        self.base_dir = Path(base_dir)

    def _task_dir(self, task_id: str) -> Path:
        prefix = task_id[:2]
        return self.base_dir / prefix / task_id

    def _ensure_dir(self, path: Path) -> None:
        os.makedirs(path, exist_ok=True)

    async def save_video(self, task_id: str, content: bytes) -> Path:
        """Save generated video bytes and return the file path."""
        task_dir = self._task_dir(task_id)
        self._ensure_dir(task_dir)
        file_path = task_dir / "video.mp4"
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        return file_path

    async def save_preview(self, task_id: str, frame_no: int, content: bytes) -> Path:
        """Save a preview image frame and return the file path."""
        task_dir = self._task_dir(task_id)
        preview_dir = task_dir / "preview"
        self._ensure_dir(preview_dir)
        file_path = preview_dir / f"{frame_no:04d}.jpg"
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        return file_path

    def get_path(self, task_id: str) -> Path:
        """Return the task directory path."""
        return self._task_dir(task_id)

    def get_result_url(self, task_id: str) -> str:
        """Return the download URL for a task's video."""
        return f"/api/v1/results/{task_id}/download"

    def get_preview_url(self, task_id: str, frame_no: int) -> str:
        """Return the URL for a specific preview frame."""
        return f"/api/v1/results/{task_id}/preview/{frame_no:04d}"
