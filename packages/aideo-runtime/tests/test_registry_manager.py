"""Unit tests for model registry and backend management."""

from collections.abc import AsyncIterator

import pytest
from aideo_runtime.backend import BackendManager
from aideo_runtime.capabilities import Capability
from aideo_runtime.models import (
    BackendEvent,
    BackendRequest,
    BackendResponse,
    HealthStatus,
    ModelInfo,
)
from aideo_runtime.registry import ModelRegistry


class StubBackend:
    """A deterministic backend used by registry and manager tests."""

    def __init__(self, status: HealthStatus = HealthStatus.HEALTHY) -> None:
        """Set the health status returned by this backend."""
        self.status = status
        self.closed = 0

    async def invoke(self, request: BackendRequest) -> BackendResponse:
        """Return an empty successful response."""
        return BackendResponse(metadata={"model": request.model})

    async def stream(self, request: BackendRequest) -> AsyncIterator[BackendEvent]:
        """Provide an empty async event stream."""
        if False:
            yield

    async def health(self) -> HealthStatus:
        """Return the configured health result."""
        return self.status

    async def models(self) -> list[ModelInfo]:
        """Return no dynamically discovered models."""
        return []

    async def aclose(self) -> None:
        """Record one lifecycle release."""
        self.closed += 1


def test_registry_registers_lists_and_unregisters_models() -> None:
    """The registry should preserve model-to-backend mapping."""
    registry = ModelRegistry()
    backend = StubBackend()
    model = ModelInfo(
        id="gpt-5",
        provider="openai",
        capability=Capability.CHAT,
        online=True,
        context_length=128000,
    )

    registry.register(model, backend)

    assert registry.get_backend("gpt-5") is backend
    assert registry.list_models() == [model]
    assert registry.unregister("gpt-5") == model
    assert registry.list_models() == []


def test_registry_rejects_duplicate_model_ids() -> None:
    """Duplicate model IDs must not silently replace a configured backend."""
    registry = ModelRegistry()
    model = ModelInfo("flux", "comfyui", Capability.IMAGE, online=False)
    registry.register(model, StubBackend())

    with pytest.raises(ValueError, match="Model already registered: flux"):
        registry.register(model, StubBackend())


def test_registry_gets_and_filters_models_by_capability() -> None:
    """The registry should expose lookup and capability-filtered discovery."""
    registry = ModelRegistry()
    chat = ModelInfo("demo-chat", "demo", Capability.CHAT, online=False)
    image = ModelInfo("demo-image", "demo", Capability.IMAGE, online=False)
    backend = StubBackend()
    registry.register(chat, backend)
    registry.register(image, backend)

    assert registry.get_model("demo-chat") == chat
    assert registry.list_models(Capability.CHAT) == [chat]
    with pytest.raises(KeyError):
        registry.get_model("missing")


async def test_registry_preempts_other_local_backends() -> None:
    """Explicit preemption should release only local non-target backends."""
    registry = ModelRegistry()
    whisper = StubBackend()
    ltx = StubBackend()
    remote = StubBackend()
    registry.register(
        ModelInfo("whisper", "local", Capability.ASR, online=False), whisper
    )
    registry.register(ModelInfo("ltx2", "local", Capability.VIDEO, online=False), ltx)
    registry.register(
        ModelInfo("remote", "openai", Capability.CHAT, online=True), remote
    )

    released = await registry.preempt_local_backends("ltx2")

    assert released == ["whisper"]
    assert whisper.closed == 1
    assert ltx.closed == 0
    assert remote.closed == 0


async def test_manager_tracks_backend_health_and_lifecycle() -> None:
    """Health checks should update the backend state and unregister cleanly."""
    manager = BackendManager()
    healthy = StubBackend()
    unhealthy = StubBackend(HealthStatus.UNHEALTHY)
    manager.register("healthy", healthy, max_jobs=2)
    manager.register("unhealthy", unhealthy)

    statuses = await manager.check_all_health()

    assert statuses == {
        "healthy": HealthStatus.HEALTHY,
        "unhealthy": HealthStatus.UNHEALTHY,
    }
    assert manager.states["healthy"].healthy is True
    assert manager.states["healthy"].latency is not None
    assert manager.states["unhealthy"].healthy is False
    assert manager.unregister("healthy") is healthy
    with pytest.raises(KeyError):
        manager.get("healthy")
