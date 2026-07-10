"""Shared test fixtures for aideo-serv."""

import socket

import pytest
from fastapi.testclient import TestClient


class _StubInferenceClient:
    """No-op inference client — prevents side effects in unit tests."""

    async def health_check(self) -> bool:
        return True  # inference reachable → orchestration proceeds

    async def submit(self, *args, **kwargs) -> None:
        pass  # no-op


@pytest.fixture
def anyio_backend():
    """Use asyncio for pytest-asyncio."""
    return "asyncio"


@pytest.fixture
def task_service():
    """Create a fresh TaskService instance for each test."""
    from aideo_serv.services.task_service import TaskService

    return TaskService()


@pytest.fixture
def connection_manager():
    """Create a fresh ConnectionManager for each test."""
    from aideo_serv.services.connection_manager import ConnectionManager

    return ConnectionManager()


@pytest.fixture
def app(task_service, connection_manager):
    """Create a FastAPI app with test dependencies injected."""
    from aideo_serv.app import create_app
    from aideo_serv.dependencies import (
        get_connection_manager,
        get_inference_client,
        get_task_service,
        set_connection_manager,
        set_inference_client,
        set_task_service,
    )

    set_task_service(task_service)
    set_connection_manager(connection_manager)
    set_inference_client(_StubInferenceClient())

    app = create_app()
    app.dependency_overrides[get_task_service] = lambda: task_service
    app.dependency_overrides[get_connection_manager] = lambda: connection_manager
    app.dependency_overrides[get_inference_client] = lambda: _StubInferenceClient()
    return app


@pytest.fixture
def client(app):
    """FastAPI TestClient bound to the test app."""
    return TestClient(app)


@pytest.fixture
def unused_tcp_port():
    """Find an unused TCP port for testing."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
