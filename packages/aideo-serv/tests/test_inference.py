"""Tests for the LTX-2 inference service client."""

import asyncio
import uuid

import pytest
from pytest_httpx import HTTPXMock


@pytest.fixture
def inference_client():
    from aideo_serv.services.inference import InferenceClient

    return InferenceClient(base_url="http://inference:9090")


class TestSubmit:
    def test_submit_sends_correct_payload(
        self, inference_client, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(
            method="POST", url="http://inference:9090/generate", status_code=202
        )
        task_id = uuid.uuid4()
        asyncio.run(
            inference_client.submit(
                task_id=task_id,
                prompt="A cat walking",
                params={"duration": 5},
                callback_url="http://aideo-serv:8000/api/v1/internal/callback",
            )
        )
        assert len(httpx_mock.get_requests()) == 1
        body = httpx_mock.get_requests()[0].read().decode()
        import json

        data = json.loads(body)
        assert data["task_id"] == str(task_id)
        assert data["prompt"] == "A cat walking"

    def test_submit_handles_inference_unavailable(
        self, inference_client, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(
            method="POST", url="http://inference:9090/generate", status_code=503
        )
        with pytest.raises(Exception):
            asyncio.run(
                inference_client.submit(
                    task_id=uuid.uuid4(),
                    prompt="test",
                    callback_url="http://localhost/cb",
                )
            )


class TestHealthCheck:
    def test_health_check_ok(self, inference_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            method="GET",
            url="http://inference:9090/health",
            json={"status": "ok"},
            status_code=200,
        )
        result = asyncio.run(inference_client.health_check())
        assert result is True

    def test_health_check_fail(self, inference_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            method="GET", url="http://inference:9090/health", status_code=500
        )
        result = asyncio.run(inference_client.health_check())
        assert result is False
