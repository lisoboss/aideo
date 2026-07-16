"""Model-to-backend registry."""

from aideo_runtime.backend import Backend
from aideo_runtime.capabilities import Capability
from aideo_runtime.models import ModelInfo


class ModelRegistry:
    """Maps provider-neutral model identifiers to backend instances."""

    def __init__(self) -> None:
        """Initialize an empty model registry."""
        self._models: dict[str, ModelInfo] = {}
        self._backends: dict[str, Backend] = {}

    def register(self, model: ModelInfo, backend: Backend) -> None:
        """Register a model and the backend that serves it."""
        if model.id in self._models:
            raise ValueError(f"Model already registered: {model.id}")
        self._models[model.id] = model
        self._backends[model.id] = backend

    def get_backend(self, model_id: str) -> Backend:
        """Return the backend registered for a model identifier."""
        return self._backends[model_id]

    def get_model(self, model_id: str) -> ModelInfo:
        """Return registered metadata for a model identifier."""
        return self._models[model_id]

    def list_models(self, capability: Capability | None = None) -> list[ModelInfo]:
        """List registered models, optionally filtered by capability."""
        models = list(self._models.values())
        if capability is None:
            return models
        return [model for model in models if model.capability is capability]

    def unregister(self, model_id: str) -> ModelInfo:
        """Remove and return model metadata."""
        self._backends.pop(model_id)
        return self._models.pop(model_id)

    async def preempt_local_backends(self, model_id: str) -> list[str]:
        """Release loaded local backends other than the selected model backend.

        This explicit operation frees GPU memory for heavyweight local models.
        Online Provider backends and backends shared with ``model_id`` remain open.
        """
        selected_backend = self.get_backend(model_id)
        released: list[str] = []
        seen_backends: set[int] = set()
        for candidate_id, backend in self._backends.items():
            if backend is selected_backend or id(backend) in seen_backends:
                continue
            if self._models[candidate_id].online:
                continue
            closer = getattr(backend, "aclose", None)
            if closer is None:
                continue
            await closer()
            seen_backends.add(id(backend))
            released.append(candidate_id)
        return released
