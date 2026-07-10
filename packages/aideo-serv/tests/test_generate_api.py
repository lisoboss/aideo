"""Integration tests for POST /generate endpoint."""

import uuid


class TestGenerateEndpoint:
    def test_generate_returns_201(self, client):
        block_id = str(uuid.uuid4())
        output_id = str(uuid.uuid4())
        response = client.post(
            "/api/v1/generate",
            json={
                "output_node_id": output_id,
                "output_content_type": "video",
                "blocks": [
                    {
                        "id": block_id,
                        "type": "scene",
                        "content": "A cyberpunk city at night",
                        "scene_tag": 0,
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "type": "character",
                        "content": "A samurai walking through rain",
                        "scene_tag": 0,
                    },
                ],
                "connections": [
                    {"source_id": block_id, "target_id": output_id},
                ],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "task_id" in data
        assert "task" in data
        task = data["task"]
        assert task["status"] == "queued"
        assert task["output_node_id"] == output_id
        assert task["prompt_structured"] is not None
        assert "A cyberpunk city" in task["prompt"]

    def test_generate_with_project(self, client):
        # Create project first
        proj = client.post("/api/v1/projects", json={"name": "Gen Project"})
        pid = proj.json()["id"]

        output_id = str(uuid.uuid4())
        response = client.post(
            "/api/v1/generate",
            json={
                "project_id": pid,
                "output_node_id": output_id,
                "output_content_type": "video",
                "blocks": [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "scene",
                        "content": "Test scene",
                        "scene_tag": 0,
                    },
                ],
                "connections": [],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["task"]["project_id"] == pid

    def test_generate_nonexistent_project_returns_404(self, client):
        response = client.post(
            "/api/v1/generate",
            json={
                "project_id": str(uuid.uuid4()),
                "output_node_id": str(uuid.uuid4()),
                "output_content_type": "video",
                "blocks": [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "scene",
                        "content": "Test",
                        "scene_tag": 0,
                    },
                ],
                "connections": [],
            },
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_generate_minimal(self, client):
        """Minimal valid request with just one block."""
        response = client.post(
            "/api/v1/generate",
            json={
                "output_node_id": str(uuid.uuid4()),
                "output_content_type": "image",
                "blocks": [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "custom",
                        "content": "A simple test prompt",
                    },
                ],
                "connections": [],
            },
        )
        assert response.status_code == 201
        assert response.json()["task"]["prompt"] == "Additional Notes: A simple test prompt"

    def test_generate_with_params(self, client):
        response = client.post(
            "/api/v1/generate",
            json={
                "output_node_id": str(uuid.uuid4()),
                "output_content_type": "video",
                "blocks": [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "scene",
                        "content": "Test scene",
                        "scene_tag": 0,
                    },
                ],
                "connections": [],
                "output_params": {
                    "duration": 10,
                    "resolution": "1080p",
                    "fps": 30,
                    "style": "anime",
                },
            },
        )
        assert response.status_code == 201
        task = response.json()["task"]
        assert task["params"]["duration"] == 10
        assert task["params"]["style"] == "anime"

    def test_generate_empty_blocks_rejected(self, client):
        response = client.post(
            "/api/v1/generate",
            json={
                "output_node_id": str(uuid.uuid4()),
                "output_content_type": "video",
                "blocks": [],
                "connections": [],
            },
        )
        assert response.status_code == 422

    def test_generate_missing_output_node_rejected(self, client):
        response = client.post(
            "/api/v1/generate",
            json={
                "output_content_type": "video",
                "blocks": [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "scene",
                        "content": "Test",
                    },
                ],
            },
        )
        assert response.status_code == 422
