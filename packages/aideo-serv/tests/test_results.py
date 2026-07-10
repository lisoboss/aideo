"""Tests for result download and preview endpoints."""

import uuid


class TestDownloadEndpoint:
    def test_download_completed_task(self, client, task_service, tmp_path):
        task = task_service.create(prompt="download test")
        task_service.update_status(task.id, "running")
        task_service.update_status(task.id, "generating")
        video_path = tmp_path / "video.mp4"
        video_path.write_bytes(b"fake video content")
        task_service.complete(task.id, str(video_path))

        response = client.get(f"/api/v1/results/{task.id}/download")
        assert response.status_code == 200
        assert response.content == b"fake video content"

    def test_download_nonexistent_task(self, client):
        response = client.get(f"/api/v1/results/{uuid.uuid4()}/download")
        assert response.status_code == 404

    def test_download_incomplete_task(self, client, task_service):
        task = task_service.create(prompt="not done")
        response = client.get(f"/api/v1/results/{task.id}/download")
        assert response.status_code == 404


class TestPreviewEndpoint:
    def test_preview_returns_image(self, client, task_service, tmp_path):
        task = task_service.create(prompt="preview test")
        task_service.update_status(task.id, "running")
        task_service.update_status(task.id, "generating")
        preview_path = tmp_path / "0000.jpg"
        preview_path.write_bytes(b"fake jpeg content")
        task_service.add_preview(task.id, str(preview_path))

        video_path = tmp_path / "video.mp4"
        video_path.write_bytes(b"video")
        task_service.complete(task.id, str(video_path))

        response = client.get(f"/api/v1/results/{task.id}/preview/0000")
        assert response.status_code == 200
        assert response.content == b"fake jpeg content"

    def test_preview_not_found(self, client, task_service):
        task = task_service.create(prompt="no previews")
        task_service.update_status(task.id, "running")
        task_service.update_status(task.id, "generating")
        task_service.complete(task.id, "/nonexistent/video.mp4")
        response = client.get(f"/api/v1/results/{task.id}/preview/0000")
        assert response.status_code == 404
