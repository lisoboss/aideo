"""Integration tests for Project REST API endpoints."""

import uuid


class TestHealthEndpoint:
    def test_health_returns_v2_format(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "2.0.0"
        assert "services" in data
        assert "inference" in data["services"]
        assert "storage" in data["services"]


class TestCreateProject:
    def test_create_returns_201(self, client):
        response = client.post("/api/v1/projects", json={"name": "My Project"})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Project"
        assert "id" in data
        assert data["task_count"] == 0

    def test_create_with_default_name(self, client):
        response = client.post("/api/v1/projects", json={})
        assert response.status_code == 201
        assert response.json()["name"] == "Untitled Project"

    def test_create_with_canvas_data(self, client):
        response = client.post(
            "/api/v1/projects",
            json={
                "name": "Canvas",
                "canvas_data": {
                    "viewport": {"center_x": 100.0, "center_y": 200.0, "scale": 0.5}
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["canvas_data"]["viewport"]["center_x"] == 100.0


class TestListProjects:
    def test_list_empty(self, client):
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    def test_list_with_items(self, client):
        for i in range(3):
            client.post("/api/v1/projects", json={"name": f"Project {i}"})
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 3

    def test_list_pagination(self, client):
        for i in range(10):
            client.post("/api/v1/projects", json={"name": f"Project {i}"})
        response = client.get("/api/v1/projects?offset=0&limit=3")
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 10


class TestGetProject:
    def test_get_existing(self, client):
        create = client.post("/api/v1/projects", json={"name": "Find Me"})
        pid = create.json()["id"]
        response = client.get(f"/api/v1/projects/{pid}")
        assert response.status_code == 200
        assert response.json()["name"] == "Find Me"

    def test_get_nonexistent_returns_404(self, client):
        response = client.get(f"/api/v1/projects/{uuid.uuid4()}")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


class TestUpdateProject:
    def test_patch_name(self, client):
        create = client.post("/api/v1/projects", json={"name": "Old"})
        pid = create.json()["id"]
        response = client.patch(f"/api/v1/projects/{pid}", json={"name": "New"})
        assert response.status_code == 200
        assert response.json()["name"] == "New"

    def test_patch_metadata(self, client):
        create = client.post("/api/v1/projects", json={"name": "Meta"})
        pid = create.json()["id"]
        response = client.patch(
            f"/api/v1/projects/{pid}",
            json={"metadata": {"author": "me"}},
        )
        assert response.status_code == 200
        assert response.json()["metadata"]["author"] == "me"

    def test_patch_nonexistent_returns_404(self, client):
        response = client.patch(
            f"/api/v1/projects/{uuid.uuid4()}",
            json={"name": "Nope"},
        )
        assert response.status_code == 404


class TestDeleteProject:
    def test_delete_returns_204(self, client):
        create = client.post("/api/v1/projects", json={"name": "Delete Me"})
        pid = create.json()["id"]
        response = client.delete(f"/api/v1/projects/{pid}")
        assert response.status_code == 204

    def test_delete_nonexistent_returns_404(self, client):
        response = client.delete(f"/api/v1/projects/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_get_after_delete_returns_404(self, client):
        create = client.post("/api/v1/projects", json={"name": "Gone"})
        pid = create.json()["id"]
        client.delete(f"/api/v1/projects/{pid}")
        response = client.get(f"/api/v1/projects/{pid}")
        assert response.status_code == 404


class TestProjectTasks:
    def test_list_tasks_empty(self, client):
        create = client.post("/api/v1/projects", json={"name": "No Tasks"})
        pid = create.json()["id"]
        response = client.get(f"/api/v1/projects/{pid}/tasks")
        assert response.status_code == 200
        assert response.json()["tasks"] == []

    def test_list_project_tasks(self, client, task_service):
        create = client.post("/api/v1/projects", json={"name": "With Tasks"})
        pid = uuid.UUID(create.json()["id"])
        # Create tasks under this project
        task_service.create(prompt="task 1", project_id=pid)
        task_service.create(prompt="task 2", project_id=pid)
        task_service.create(prompt="task 3")  # no project_id
        response = client.get(f"/api/v1/projects/{pid}/tasks")
        assert response.status_code == 200
        assert len(response.json()["tasks"]) == 2

    def test_list_tasks_nonexistent_project_returns_404(self, client):
        response = client.get(f"/api/v1/projects/{uuid.uuid4()}/tasks")
        assert response.status_code == 404


class TestProjectAssets:
    def test_list_assets_empty(self, client):
        create = client.post("/api/v1/projects", json={"name": "No Assets"})
        pid = create.json()["id"]
        response = client.get(f"/api/v1/projects/{pid}/assets")
        assert response.status_code == 200
        assert response.json()["items"] == []

    def test_list_assets_nonexistent_project_returns_404(self, client):
        response = client.get(f"/api/v1/projects/{uuid.uuid4()}/assets")
        assert response.status_code == 404
