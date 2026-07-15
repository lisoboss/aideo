"""Dynamically loadable Runtime provider modules."""

from collections.abc import Callable
from dataclasses import dataclass

from aideo_runtime.backend.base import Backend
from aideo_runtime.models import ModelInfo

ProviderFactory = Callable[..., Backend]
ProviderModels = Callable[[], list[ModelInfo]]


@dataclass(frozen=True, slots=True)
class RuntimeProvider:
    """The required public contract for a dynamically loaded provider.

    Provider factories receive the shared :class:`PathSettings` instance from
    the Runtime application. They must defer heavyweight optional imports until
    their Backend is first used so discovery remains available without a GPU.
    """

    create_backend: ProviderFactory
    models: ProviderModels


__all__ = ["RuntimeProvider"]
