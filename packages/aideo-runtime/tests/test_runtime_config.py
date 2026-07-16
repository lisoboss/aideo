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
    monkeypatch.setenv("AIDEO_RUNTIME_DEBUG", "true")
    monkeypatch.setenv("AIDEO_RUNTIME_MODELS", "ignored-model")
    monkeypatch.setenv("AIDEO_RUNTIME_MODELS_DIR", "/tmp/models")
    monkeypatch.setenv("AIDEO_RUNTIME_INPUT_DIR", "/tmp/input")
    monkeypatch.setenv("AIDEO_RUNTIME_OUTPUT_DIR", "/tmp/output")

    settings = RuntimeSettings.from_env()

    assert settings.host == "0.0.0.0"
    assert settings.port == 9100
    assert settings.providers == ["demo", "xxx"]
    assert settings.debug is True
    assert settings.paths.models_dir.name == "models"


def test_settings_defaults_to_demo_and_rejects_empty_provider_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Settings should default to demo and reject blank explicit names."""
    monkeypatch.delenv("AIDEO_RUNTIME_PROVIDERS", raising=False)
    assert RuntimeSettings.from_env().providers == ["demo"]

    monkeypatch.setenv("AIDEO_RUNTIME_PROVIDERS", "demo,,xxx")
    with pytest.raises(ValueError, match="empty provider"):
        RuntimeSettings.from_env()


def test_settings_uses_legacy_model_root_when_the_new_name_is_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Existing Linux deployments should retain their configured model root."""
    monkeypatch.delenv("AIDEO_RUNTIME_MODELS_DIR", raising=False)
    monkeypatch.setenv("AIDEO_MODEL_ROOT", "/tmp/legacy-models")

    settings = RuntimeSettings.from_env()

    assert settings.paths.models_dir.name == "legacy-models"
