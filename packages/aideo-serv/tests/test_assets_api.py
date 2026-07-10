"""Integration tests for Asset REST API endpoints."""

import io
import uuid


class TestUploadAsset:
    def test_upload_returns_201(self, client):
        response = client.post(
            "/api/v1/assets",
            files={"file": ("test.jpg", io.BytesIO(b"fake-image-data"), "image/jpeg")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.jpg"
        assert data["content_type"] == "image/jpeg"
        assert data["media_type"] == "image"
        assert data["size"] == 15
        assert "id" in data
        assert "url" in data

    def test_upload_with_project_id(self, client):
        # Create a project first
        proj = client.post("/api/v1/projects", json={"name": "Assets Project"})
        pid = proj.json()["id"]

        response = client.post(
            "/api/v1/assets",
            files={"file": ("ref.jpg", io.BytesIO(b"image-bytes"), "image/jpeg")},
            data={"project_id": pid},
        )
        assert response.status_code == 201
        assert response.json()["project_id"] == pid

    def test_upload_with_explicit_media_type(self, client):
        response = client.post(
            "/api/v1/assets",
            files={"file": ("audio.wav", io.BytesIO(b"audio-data"), "audio/wav")},
            data={"media_type": "audio"},
        )
        assert response.status_code == 201
        assert response.json()["media_type"] == "audio"

    def test_upload_without_content_type_defaults_to_image(self, client):
        response = client.post(
            "/api/v1/assets",
            files={"file": ("unknown.bin", io.BytesIO(b"binary"), "application/octet-stream")},
        )
        assert response.status_code == 201
        assert response.json()["media_type"] == "other"


class TestGetAsset:
    def test_get_metadata(self, client):
        upload = client.post(
            "/api/v1/assets",
            files={"file": ("meta.jpg", io.BytesIO(b"metadata"), "image/jpeg")},
        )
        aid = upload.json()["id"]
        response = client.get(f"/api/v1/assets/{aid}")
        assert response.status_code == 200
        assert response.json()["filename"] == "meta.jpg"

    def test_get_nonexistent_returns_404(self, client):
        response = client.get(f"/api/v1/assets/{uuid.uuid4()}")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


class TestDownloadAsset:
    def test_download_returns_file(self, client):
        content = b"hello world image data"
        upload = client.post(
            "/api/v1/assets",
            files={"file": ("download.jpg", io.BytesIO(content), "image/jpeg")},
        )
        aid = upload.json()["id"]
        response = client.get(f"/api/v1/assets/{aid}/download")
        assert response.status_code == 200
        assert response.content == content

    def test_download_nonexistent_returns_404(self, client):
        response = client.get(f"/api/v1/assets/{uuid.uuid4()}/download")
        assert response.status_code == 404


class TestDeleteAsset:
    def test_delete_returns_204(self, client):
        upload = client.post(
            "/api/v1/assets",
            files={"file": ("del.jpg", io.BytesIO(b"delete me"), "image/jpeg")},
        )
        aid = upload.json()["id"]
        response = client.delete(f"/api/v1/assets/{aid}")
        assert response.status_code == 204

    def test_delete_nonexistent_returns_404(self, client):
        response = client.delete(f"/api/v1/assets/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_get_after_delete_returns_404(self, client):
        upload = client.post(
            "/api/v1/assets",
            files={"file": ("gone.jpg", io.BytesIO(b"gone"), "image/jpeg")},
        )
        aid = upload.json()["id"]
        client.delete(f"/api/v1/assets/{aid}")
        response = client.get(f"/api/v1/assets/{aid}")
        assert response.status_code == 404
