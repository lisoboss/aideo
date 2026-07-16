"""HTTP and SSE contract tests for the Runtime service."""

import logging
from pathlib import Path

import pytest
from aideo_runtime.app import create_app
from aideo_runtime.backend.providers.demo import DemoBackend
from aideo_runtime.config import RuntimeSettings
from aideo_runtime.paths import PathSettings
from fastapi.testclient import TestClient


def make_client(tmp_path: Path) -> TestClient:
    """Create a configured Runtime application client."""
    return TestClient(
        create_app(
            RuntimeSettings(
                host="127.0.0.1",
                port=9090,
                providers=["demo"],
                paths=PathSettings(
                    tmp_path / "models",
                    tmp_path / "input",
                    tmp_path / "output",
                ),
            )
        )
    )


def test_runtime_discovery_and_health(tmp_path: Path) -> None:
    """Health and discovery endpoints should expose the registered demo model."""
    client = make_client(tmp_path)

    assert client.get("/health").json() == {"status": "ok", "models": 1}
    assert client.get("/api/v1/chat").json()["models"][0]["id"] == "demo-chat"
    assert client.get("/api/v1").json()["capabilities"] == ["chat"]


def test_runtime_invokes_json_and_sse_and_returns_contract_errors(
    tmp_path: Path,
) -> None:
    """The invoke endpoint should return response modes and stable errors."""
    client = make_client(tmp_path)
    payload = {
        "capability": "chat",
        "model": "demo-chat",
        "input": {"messages": []},
    }

    response = client.post("/api/v1/chat/demo-chat", json=payload)
    stream = client.post(
        "/api/v1/chat/demo-chat",
        json={
            **payload,
            "parameters": {"max_output_tokens": 128, "temperature": 0.7},
            "stream": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["outputs"][0]["text"] == "demo response"
    assert stream.headers["content-type"].startswith("text/event-stream")
    assert "event: delta" in stream.text
    assert "event: done" in stream.text
    assert (
        client.post(
            "/api/v1/chat/missing", json={**payload, "model": "missing"}
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/image/demo-chat", json={**payload, "capability": "image"}
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/v1/chat/demo-chat", json={**payload, "model": "other"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/chat/demo-chat",
            json={**payload, "parameters": {"max_output_tokens": 1025}},
        ).status_code
        == 422
    )


def test_debug_mode_returns_tracebacks_for_json_and_sse_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Debug mode should expose and log backend exceptions in both response modes."""

    async def fail(*_: object) -> object:
        """Raise a stable backend error for the debug contract."""
        raise RuntimeError("debug inference failure")

    async def fail_stream(*_: object) -> object:
        """Raise a stable streaming error for the debug contract."""
        if False:
            yield None
        raise RuntimeError("debug inference failure")

    monkeypatch.setattr(DemoBackend, "invoke", fail)
    monkeypatch.setattr(DemoBackend, "stream", fail_stream)
    caplog.set_level(logging.ERROR, logger="uvicorn.error")
    client = TestClient(
        create_app(
            RuntimeSettings(
                host="127.0.0.1",
                port=9090,
                providers=["demo"],
                debug=True,
                paths=PathSettings(
                    tmp_path / "models",
                    tmp_path / "input",
                    tmp_path / "output",
                ),
            )
        ),
        raise_server_exceptions=False,
    )
    payload = {
        "capability": "chat",
        "model": "demo-chat",
        "input": {"messages": []},
    }

    response = client.post("/api/v1/chat/demo-chat", json=payload)
    stream = client.post("/api/v1/chat/demo-chat", json={**payload, "stream": True})

    assert response.status_code == 500
    assert response.json()["traceback"]
    assert "debug inference failure" in stream.text
    assert "traceback" in stream.text
    assert "Inference request failed" in caplog.text
    assert "Inference stream failed" in caplog.text
