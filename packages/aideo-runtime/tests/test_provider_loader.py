"""Tests for dynamic Runtime provider loading."""

import pytest
from aideo_runtime.backend.loader import load_provider


def test_load_provider_returns_demo_contract() -> None:
    """A configured demo provider should expose models and a backend factory."""
    provider = load_provider("demo")

    assert provider.models()[0].id == "demo-chat"
    assert provider.create_backend().__class__.__name__ == "DemoBackend"


def test_load_local_providers_without_importing_gpu_dependencies() -> None:
    """LTX and ASR providers should remain discoverable before first inference."""
    assert load_provider("ltx2").models()[0].id == "ltx2"
    assert load_provider("faster_whisper2").models()[0].id == "faster-whisper2"


def test_load_provider_rejects_unknown_module() -> None:
    """Unknown provider names should produce an actionable configuration error."""
    with pytest.raises(ValueError, match="Unknown Runtime provider"):
        load_provider("does-not-exist")
