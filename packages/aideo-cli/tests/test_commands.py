"""Tests for aideo CLI commands via CliRunner."""

import uuid

import pytest
from typer.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def app():
    from aideo_cli.main import app

    return app


def _tid():
    return str(uuid.uuid4())


class TestSubmit:
    def test_submit_json_output(self, runner, app, httpx_mock):
        tid = _tid()
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8000/api/v1/tasks",
            status_code=201,
            json={
                "id": tid,
                "prompt": "a cat",
                "status": "queued",
                "progress": 0.0,
                "params": None,
                "created_at": "2026-06-27T00:00:00Z",
                "updated_at": "2026-06-27T00:00:00Z",
                "result_path": None,
                "result_url": None,
                "previews": [],
                "error_message": None,
            },
        )
        result = runner.invoke(app, ["submit", "a cat", "--format", "json"])
        assert result.exit_code == 0
        data = __import__("json").loads(result.stdout)
        assert data["prompt"] == "a cat"
        assert data["status"] == "queued"

    def test_submit_with_params(self, runner, app, httpx_mock):
        tid = _tid()
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8000/api/v1/tasks",
            status_code=201,
            json={
                "id": tid,
                "prompt": "test",
                "status": "queued",
                "progress": 0.0,
                "params": {"duration": 5},
                "created_at": "2026-06-27T00:00:00Z",
                "updated_at": "2026-06-27T00:00:00Z",
                "result_path": None,
                "result_url": None,
                "previews": [],
                "error_message": None,
            },
        )
        result = runner.invoke(
            app,
            ["submit", "test", "--param", "duration=5", "--format", "json"],
        )
        assert result.exit_code == 0


class TestList:
    def test_list_empty(self, runner, app, httpx_mock):
        httpx_mock.add_response(
            method="GET",
            url="http://localhost:8000/api/v1/tasks?offset=0&limit=20",
            status_code=200,
            json={"tasks": [], "total": 0, "offset": 0, "limit": 20},
        )
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

    def test_list_json_format(self, runner, app, httpx_mock):
        httpx_mock.add_response(
            method="GET",
            url="http://localhost:8000/api/v1/tasks?offset=0&limit=20",
            status_code=200,
            json={"tasks": [], "total": 0, "offset": 0, "limit": 20},
        )
        result = runner.invoke(app, ["list", "--format", "json"])
        assert result.exit_code == 0
        data = __import__("json").loads(result.stdout)
        assert data["tasks"] == []


class TestStatus:
    def test_status_json(self, runner, app, httpx_mock):
        tid = _tid()
        httpx_mock.add_response(
            method="GET",
            url=f"http://localhost:8000/api/v1/tasks/{tid}",
            status_code=200,
            json={
                "id": tid,
                "prompt": "test",
                "status": "running",
                "progress": 50.0,
                "params": None,
                "created_at": "2026-06-27T00:00:00Z",
                "updated_at": "2026-06-27T00:00:00Z",
                "result_path": None,
                "result_url": None,
                "previews": [],
                "error_message": None,
            },
        )
        result = runner.invoke(app, ["status", tid, "--format", "json"])
        assert result.exit_code == 0
        data = __import__("json").loads(result.stdout)
        assert data["progress"] == 50.0


class TestCancel:
    def test_cancel(self, runner, app, httpx_mock):
        tid = _tid()
        httpx_mock.add_response(
            method="DELETE",
            url=f"http://localhost:8000/api/v1/tasks/{tid}",
            status_code=200,
            json={
                "id": tid,
                "prompt": "test",
                "status": "cancelled",
                "progress": 0.0,
                "params": None,
                "created_at": "2026-06-27T00:00:00Z",
                "updated_at": "2026-06-27T00:00:00Z",
                "result_path": None,
                "result_url": None,
                "previews": [],
                "error_message": None,
            },
        )
        result = runner.invoke(app, ["cancel", tid])
        assert result.exit_code == 0


class TestDownload:
    def test_download(self, runner, app, httpx_mock, tmp_path):
        tid = _tid()
        httpx_mock.add_response(
            method="GET",
            url=f"http://localhost:8000/api/v1/results/{tid}/download",
            status_code=200,
            content=b"fake mp4",
        )
        output = tmp_path / "out.mp4"
        result = runner.invoke(app, ["download", tid, "--output", str(output)])
        assert result.exit_code == 0
        assert output.read_bytes() == b"fake mp4"
