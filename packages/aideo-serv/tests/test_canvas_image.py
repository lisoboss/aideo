"""Integration tests for POST /canvas/edit-image and /canvas/upscale."""

import io
import uuid


def _upload_image(client, name: str = "base.jpg") -> str:
    """Upload a fake image asset and return its asset_id."""
    resp = client.post(
        "/api/v1/assets",
        files={"file": (name, io.BytesIO(b"fake-image-bytes"), "image/jpeg")},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


class TestEditImage:
    def test_edit_image_returns_201(self, client):
        base_id = _upload_image(client)
        resp = client.post(
            "/api/v1/canvas/edit-image",
            json={
                "mode": "replace_character",
                "base_image": base_id,
                "prompt_blocks": [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "character",
                        "content": "A white robot with red eyes",
                    },
                ],
                "mask_regions": [
                    {
                        "x": 0.2,
                        "y": 0.15,
                        "width": 0.3,
                        "height": 0.6,
                        "label": "character_A",
                    },
                ],
                "language": "zh",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "task_id" in data
        task = data["task"]
        assert task["status"] == "queued"
        assert task["task_type"] == "image_edit"
        assert task["input_files"][0]["asset_id"] == base_id
        assert task["input_files"][0]["role"] == "base"
        assert "A white robot" in task["prompt"]

    def test_edit_image_with_reference_assets(self, client):
        base_id = _upload_image(client, "base.jpg")
        ref_id = _upload_image(client, "ref.jpg")
        resp = client.post(
            "/api/v1/canvas/edit-image",
            json={
                "mode": "composite",
                "base_image": base_id,
                "reference_images": [ref_id],
            },
        )
        assert resp.status_code == 201
        task = resp.json()["task"]
        # base + 1 reference
        assert len(task["input_files"]) == 2
        roles = {f["role"] for f in task["input_files"]}
        assert roles == {"base", "reference"}
        # empty prompt_blocks → mode-derived default prompt
        assert task["prompt"] == "Image edit (composite)"

    def test_edit_image_with_project(self, client):
        proj = client.post("/api/v1/projects", json={"name": "Edit Project"})
        pid = proj.json()["id"]
        base_id = _upload_image(client)
        resp = client.post(
            "/api/v1/canvas/edit-image",
            json={"mode": "inpainting", "base_image": base_id, "project_id": pid},
        )
        assert resp.status_code == 201
        assert resp.json()["task"]["project_id"] == pid

    def test_edit_image_missing_base_asset_returns_404(self, client):
        resp = client.post(
            "/api/v1/canvas/edit-image",
            json={"mode": "composite", "base_image": str(uuid.uuid4())},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_edit_image_missing_reference_asset_returns_404(self, client):
        base_id = _upload_image(client)
        resp = client.post(
            "/api/v1/canvas/edit-image",
            json={
                "mode": "style_transfer",
                "base_image": base_id,
                "reference_images": [str(uuid.uuid4())],
            },
        )
        assert resp.status_code == 404

    def test_edit_image_nonexistent_project_returns_404(self, client):
        base_id = _upload_image(client)
        resp = client.post(
            "/api/v1/canvas/edit-image",
            json={
                "mode": "composite",
                "base_image": base_id,
                "project_id": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 404

    def test_edit_image_invalid_mode_returns_422(self, client):
        base_id = _upload_image(client)
        resp = client.post(
            "/api/v1/canvas/edit-image",
            json={"mode": "not_a_mode", "base_image": base_id},
        )
        assert resp.status_code == 422

    def test_edit_image_mask_region_out_of_range_returns_422(self, client):
        base_id = _upload_image(client)
        resp = client.post(
            "/api/v1/canvas/edit-image",
            json={
                "mode": "inpainting",
                "base_image": base_id,
                "mask_regions": [{"x": 1.5, "y": 0.1, "width": 0.2, "height": 0.2}],
            },
        )
        assert resp.status_code == 422


class TestUpscale:
    def test_upscale_returns_201(self, client):
        asset_id = _upload_image(client)
        resp = client.post(
            "/api/v1/canvas/upscale",
            json={"asset_id": asset_id, "scale": 4},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "task_id" in data
        task = data["task"]
        assert task["status"] == "queued"
        assert task["task_type"] == "image_upscale"
        assert task["params"]["scale"] == 4
        assert task["input_files"][0]["asset_id"] == asset_id

    def test_upscale_default_scale_is_2(self, client):
        asset_id = _upload_image(client)
        resp = client.post("/api/v1/canvas/upscale", json={"asset_id": asset_id})
        assert resp.status_code == 201
        assert resp.json()["task"]["params"]["scale"] == 2

    def test_upscale_missing_asset_returns_404(self, client):
        resp = client.post(
            "/api/v1/canvas/upscale",
            json={"asset_id": str(uuid.uuid4()), "scale": 2},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_upscale_invalid_scale_returns_422(self, client):
        asset_id = _upload_image(client)
        resp = client.post(
            "/api/v1/canvas/upscale",
            json={"asset_id": asset_id, "scale": 3},
        )
        assert resp.status_code == 422
