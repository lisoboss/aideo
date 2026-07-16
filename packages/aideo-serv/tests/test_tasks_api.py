"""Integration tests for the task REST API endpoints."""

import uuid


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestCreateTaskEndpoint:
    def test_create_task_returns_201(self, client):
        response = client.post("/api/v1/tasks", json={"prompt": "A cat walking"})
        assert response.status_code == 201
        data = response.json()
        assert data["prompt"] == "A cat walking"
        assert data["status"] == "queued"
        assert "id" in data

    def test_create_task_empty_prompt_returns_422(self, client):
        response = client.post("/api/v1/tasks", json={"prompt": ""})
        assert response.status_code == 422

    def test_create_task_missing_prompt_returns_422(self, client):
        response = client.post("/api/v1/tasks", json={})
        assert response.status_code == 422

    def test_create_task_with_params(self, client):
        response = client.post(
            "/api/v1/tasks",
            json={"prompt": "test", "params": {"duration": 5}},
        )
        assert response.status_code == 201
        assert response.json()["params"] == {"duration": 5}


class TestListTasksEndpoint:
    def test_list_tasks_empty(self, client):
        response = client.get("/api/v1/tasks")
        assert response.status_code == 200
        assert response.json()["tasks"] == []

    def test_list_tasks_with_items(self, client):
        for i in range(3):
            client.post("/api/v1/tasks", json={"prompt": f"task {i}"})
        response = client.get("/api/v1/tasks")
        assert response.status_code == 200
        assert len(response.json()["tasks"]) == 3

    def test_list_tasks_with_status_filter(self, client):
        client.post("/api/v1/tasks", json={"prompt": "queued task"})
        response = client.get("/api/v1/tasks?status=queued")
        assert response.status_code == 200
        assert all(t["status"] == "queued" for t in response.json()["tasks"])


class TestGetTaskEndpoint:
    def test_get_existing_task(self, client):
        create_resp = client.post("/api/v1/tasks", json={"prompt": "find me"})
        task_id = create_resp.json()["id"]
        response = client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["prompt"] == "find me"

    def test_get_nonexistent_task_returns_404(self, client):
        response = client.get(f"/api/v1/tasks/{uuid.uuid4()}")
        assert response.status_code == 404


class TestCancelTaskEndpoint:
    def test_cancel_task(self, client, task_service):
        # Create directly via service to keep task in QUEUED state
        # (API endpoint triggers background inference submission which
        # races ahead and transitions the task past the cancellable states).
        task = task_service.create(prompt="cancel me")
        response = client.delete(f"/api/v1/tasks/{task.id}")
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    def test_cancel_nonexistent_task_returns_404(self, client):
        response = client.delete(f"/api/v1/tasks/{uuid.uuid4()}")
        assert response.status_code == 404
