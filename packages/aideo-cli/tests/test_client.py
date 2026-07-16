"""Tests for AideoClient — HTTP + WebSocket wrapper."""

import asyncio
import json
import uuid
from pathlib import Path

import pytest
from pytest_httpx import HTTPXMock


@pytest.fixture
def client(server_url):
    from aideo_cli.client import AideoClient

    return AideoClient(server=server_url)


def _task_json(task_id, prompt="test", status="queued", **overrides):
    return {
        "id": task_id,
        "prompt": prompt,
        "status": status,
        "progress": 0.0,
        "params": None,
        "created_at": "2026-06-27T00:00:00Z",
        "updated_at": "2026-06-27T00:00:00Z",
        "result_path": None,
        "result_url": None,
        "previews": [],
        "error_message": None,
        **overrides,
    }


class TestSubmit:
    def test_submit_returns_task(self, client, api_url, httpx_mock: HTTPXMock):
        tid = str(uuid.uuid4())
        httpx_mock.add_response(
            method="POST",
            url=f"{api_url}/tasks",
            status_code=201,
            json=_task_json(tid, prompt="a cat"),
        )
        task = asyncio.run(client.submit("a cat"))
        assert task["id"] == tid
        assert task["status"] == "queued"
        assert task["prompt"] == "a cat"

    def test_submit_with_params(self, client, api_url, httpx_mock: HTTPXMock):
        tid = str(uuid.uuid4())
        httpx_mock.add_response(
            method="POST",
            url=f"{api_url}/tasks",
            status_code=201,
            json=_task_json(tid, params={"duration": 5}),
        )
        task = asyncio.run(client.submit("test", params={"duration": 5}))
        assert task["params"] == {"duration": 5}


class TestList:
    def test_list_tasks(self, client, api_url, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            method="GET",
            url=f"{api_url}/tasks?offset=0&limit=20",
            status_code=200,
            json={"tasks": [], "total": 0, "offset": 0, "limit": 20},
        )
        result = asyncio.run(client.list_tasks())
        assert result["tasks"] == []

    def test_list_with_status_filter(self, client, api_url, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            method="GET",
            url=f"{api_url}/tasks?status=completed&offset=0&limit=10",
            status_code=200,
            json={"tasks": [], "total": 0, "offset": 0, "limit": 10},
        )
        result = asyncio.run(client.list_tasks(status="completed", limit=10))
        assert result["total"] == 0


class TestGetTask:
    def test_get_task(self, client, api_url, httpx_mock: HTTPXMock):
        tid = str(uuid.uuid4())
        httpx_mock.add_response(
            method="GET",
            url=f"{api_url}/tasks/{tid}",
            status_code=200,
            json=_task_json(tid, prompt="my task"),
        )
        task = asyncio.run(client.get_task(tid))
        assert task["id"] == tid
        assert task["prompt"] == "my task"


class TestCancel:
    def test_cancel_task(self, client, api_url, httpx_mock: HTTPXMock):
        tid = str(uuid.uuid4())
        httpx_mock.add_response(
            method="DELETE",
            url=f"{api_url}/tasks/{tid}",
            status_code=200,
            json=_task_json(tid, status="cancelled"),
        )
        task = asyncio.run(client.cancel_task(tid))
        assert task["status"] == "cancelled"


class TestDownload:
    def test_download_saves_file(
        self, client, api_url, httpx_mock: HTTPXMock, tmp_path
    ):
        tid = str(uuid.uuid4())
        httpx_mock.add_response(
            method="GET",
            url=f"{api_url}/results/{tid}/download",
            status_code=200,
            content=b"fake mp4 content",
        )
        output = tmp_path / "output.mp4"
        asyncio.run(client.download_result(tid, str(output)))
        assert output.read_bytes() == b"fake mp4 content"
