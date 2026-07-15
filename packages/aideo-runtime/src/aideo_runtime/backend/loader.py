"""Dynamic loader for configured Runtime provider modules."""

from importlib import import_module
from types import ModuleType

from aideo_runtime.backend.providers import RuntimeProvider


def load_provider(name: str) -> RuntimeProvider:
    """Load one provider module from ``backend.providers`` by name."""
    module_name = f"aideo_runtime.backend.providers.{name}"
    try:
        module = import_module(module_name)
    except ModuleNotFoundError as error:
        if error.name == module_name:
            raise ValueError(f"Unknown Runtime provider: {name}") from error
        raise
    return _provider_contract(name, module)


def _provider_contract(name: str, module: ModuleType) -> RuntimeProvider:
    """Validate and return a module's provider contract."""
    create_backend = getattr(module, "create_backend", None)
    models = getattr(module, "models", None)
    if not callable(create_backend) or not callable(models):
        raise ValueError(
            f"Runtime provider {name} must export create_backend() and models()"
        )
    return RuntimeProvider(create_backend=create_backend, models=models)
