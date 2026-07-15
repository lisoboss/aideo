"""Tests for environment-backed Runtime settings."""

import pytest
from aideo_runtime.config import RuntimeSettings


def test_settings_parse_provider_list_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Settings should parse host, port, and provider names."""
    monkeypatch.setenv("AIDEO_RUNTIME_HOST", "0.0.0.0")
    monkeypatch.setenv("AIDEO_RUNTIME_PORT", "9100")
    monkeypatch.setenv("AIDEO_RUNTIME_PROVIDERS", "demo, xxx")
    monkeypatch.setenv("AIDEO_RUNTIME_MODELS", "ignored-model")

    settings = RuntimeSettings.from_env()

    assert settings.host == "0.0.0.0"
    assert settings.port == 9100
    assert settings.providers == ["demo", "xxx"]


def test_settings_defaults_to_demo_and_rejects_empty_provider_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Settings should default to demo and reject blank explicit names."""
    monkeypatch.delenv("AIDEO_RUNTIME_PROVIDERS", raising=False)
    assert RuntimeSettings.from_env().providers == ["demo"]

    monkeypatch.setenv("AIDEO_RUNTIME_PROVIDERS", "demo,,xxx")
    with pytest.raises(ValueError, match="empty provider"):
        RuntimeSettings.from_env()
