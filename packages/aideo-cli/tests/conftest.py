"""Shared fixtures for aideo-cli tests."""

import pytest


@pytest.fixture
def server_url():
    return "http://localhost:8000"


@pytest.fixture
def api_url(server_url):
    return f"{server_url}/api/v1"
