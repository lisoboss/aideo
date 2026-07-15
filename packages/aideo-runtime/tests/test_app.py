"""HTTP and SSE contract tests for the Runtime service."""

from pathlib import Path

from aideo_runtime.app import create_app
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
