"""Tests for WebSocket real-time task progress endpoint."""

import uuid

import pytest


class TestWebSocketConnect:
    def _create(self, client, prompt="test ws"):
        resp = client.post("/api/v1/tasks", json={"prompt": prompt})
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_connect_to_existing_task(self, client):
        task_id = self._create(client)
        with client.websocket_connect(f"/api/v1/ws/tasks/{task_id}") as ws:
            data = ws.receive_json()
            assert data["type"] == "status_change"
            assert data["task_id"] == task_id

    def test_connect_nonexistent_task_closes(self, client):
        with pytest.raises(Exception):
            with client.websocket_connect(
                "/api/v1/ws/tasks/00000000-0000-0000-0000-000000000000"
            ) as ws:
                ws.receive_json()

    def test_receive_on_cancel(self, client):
        task_id = self._create(client, "cancel ws test")
        with client.websocket_connect(f"/api/v1/ws/tasks/{task_id}") as ws:
            ws.receive_json()
            client.delete(f"/api/v1/tasks/{task_id}")
            data = ws.receive_json()
            assert data["type"] == "status_change"
            assert data["data"]["status"] == "cancelled"

    def test_receive_on_fail(self, client, task_service):
        task_id = self._create(client, "fail ws test")
        with client.websocket_connect(f"/api/v1/ws/tasks/{task_id}") as ws:
            ws.receive_json()
            task_service.fail(uuid.UUID(task_id), "GPU out of memory")
            d1 = ws.receive_json()
            assert d1["type"] == "status_change"
            assert d1["data"]["status"] == "failed"
            d2 = ws.receive_json()
            assert d2["type"] == "error"
            assert "GPU out of memory" in d2["data"]["message"]

    def test_multiple_clients_same_task(self, client):
        task_id = self._create(client, "multi client")
        with client.websocket_connect(f"/api/v1/ws/tasks/{task_id}") as ws1:
            ws1.receive_json()
            with client.websocket_connect(f"/api/v1/ws/tasks/{task_id}") as ws2:
                ws2.receive_json()
                client.delete(f"/api/v1/tasks/{task_id}")
                d1 = ws1.receive_json()
                d2 = ws2.receive_json()
                assert d1["data"]["status"] == "cancelled"
                assert d2["data"]["status"] == "cancelled"
