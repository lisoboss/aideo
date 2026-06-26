"""Shared test fixtures for aideo-serv."""

import pytest
from fastapi.testclient import TestClient


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
        get_task_service,
        set_connection_manager,
        set_task_service,
    )

    set_task_service(task_service)
    set_connection_manager(connection_manager)

    app = create_app()
    app.dependency_overrides[get_task_service] = lambda: task_service
    app.dependency_overrides[get_connection_manager] = lambda: connection_manager
    return app


@pytest.fixture
def client(app):
    """FastAPI TestClient bound to the test app."""
    return TestClient(app)
