"""Dynamically loadable Runtime provider modules."""

from collections.abc import Callable
from dataclasses import dataclass

from aideo_runtime.backend.base import Backend
from aideo_runtime.models import ModelInfo

ProviderFactory = Callable[[], Backend]
ProviderModels = Callable[[], list[ModelInfo]]


@dataclass(frozen=True, slots=True)
class RuntimeProvider:
    """The required public contract for a dynamically loaded provider."""

    create_backend: ProviderFactory
    models: ProviderModels


__all__ = ["RuntimeProvider"]
