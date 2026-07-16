"""Tests for application settings configuration."""

import pytest


class TestSettingsDefaults:
    def test_default_host(self):
        from aideo_serv.config import Settings

        s = Settings()
        assert s.server_host == "0.0.0.0"

    def test_default_port(self):
        from aideo_serv.config import Settings

        s = Settings()
        assert s.server_port == 8000

    def test_default_storage_base_dir(self):
        from aideo_serv.config import Settings

        s = Settings()
        assert s.storage_base_dir == "./data"

    def test_default_runtime_url_is_set(self):
        from aideo_serv.config import Settings

        s = Settings()
        assert s.runtime_url.startswith("http")

    def test_default_cors_origins(self):
        from aideo_serv.config import Settings

        s = Settings()
        assert isinstance(s.cors_origins, list)


class TestSettingsFromEnv:
    def test_host_from_env(self, monkeypatch):
        from aideo_serv.config import Settings

        monkeypatch.setenv("AIDEO_SERVER_HOST", "127.0.0.1")
        s = Settings()
        assert s.server_host == "127.0.0.1"

    def test_port_from_env(self, monkeypatch):
        from aideo_serv.config import Settings

        monkeypatch.setenv("AIDEO_SERVER_PORT", "9000")
        s = Settings()
        assert s.server_port == 9000

    def test_runtime_url_from_env(self, monkeypatch):
        from aideo_serv.config import Settings

        monkeypatch.setenv("AIDEO_RUNTIME_URL", "http://gpu-box:9090")
        s = Settings()
        assert s.runtime_url == "http://gpu-box:9090"

    def test_storage_base_dir_from_env(self, monkeypatch):
        from aideo_serv.config import Settings

        monkeypatch.setenv("AIDEO_STORAGE_BASE_DIR", "/mnt/videos")
        s = Settings()
        assert s.storage_base_dir == "/mnt/videos"
