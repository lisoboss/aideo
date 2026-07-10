"""Shared test fixtures for aideo-serv."""

import socket

import pytest
from fastapi.testclient import TestClient


class _StubInferenceClient:
    """No-op inference client — prevents side effects in unit tests."""

    async def health_check(self) -> bool:
        return True

    async def submit(self, *args, **kwargs) -> None:
        pass


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
def project_service():
    """Create a fresh ProjectService instance for each test."""
    from aideo_serv.services.project_service import ProjectService

    return ProjectService()


@pytest.fixture
def asset_service():
    """Create a fresh AssetService instance for each test (uses temp dir)."""
    import tempfile
    from aideo_serv.services.asset_service import AssetService

    with tempfile.TemporaryDirectory() as tmpdir:
        yield AssetService(base_dir=tmpdir)


@pytest.fixture
def connection_manager():
    """Create a fresh ConnectionManager for each test."""
    from aideo_serv.services.connection_manager import ConnectionManager

    return ConnectionManager()


@pytest.fixture
def ai_client():
    """Create a stub AIClient for testing."""
    from aideo_serv.config import Settings
    from aideo_serv.services.ai_client import AIClient

    settings = Settings(ai_provider="stub")
    return AIClient(settings=settings)


@pytest.fixture
def app(task_service, project_service, asset_service, connection_manager, ai_client):
    """Create a FastAPI app with test dependencies injected."""
    from aideo_serv.app import create_app
    from aideo_serv.dependencies import (
        get_ai_client,
        get_asset_service,
        get_connection_manager,
        get_inference_client,
        get_project_service,
        get_task_service,
        set_ai_client,
        set_asset_service,
        set_connection_manager,
        set_inference_client,
        set_project_service,
        set_task_service,
    )

    set_task_service(task_service)
    set_project_service(project_service)
    set_asset_service(asset_service)
    set_connection_manager(connection_manager)
    set_inference_client(_StubInferenceClient())
    set_ai_client(ai_client)

    app = create_app()
    app.dependency_overrides[get_task_service] = lambda: task_service
    app.dependency_overrides[get_project_service] = lambda: project_service
    app.dependency_overrides[get_asset_service] = lambda: asset_service
    app.dependency_overrides[get_connection_manager] = lambda: connection_manager
    app.dependency_overrides[get_inference_client] = lambda: _StubInferenceClient()
    app.dependency_overrides[get_ai_client] = lambda: ai_client
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
