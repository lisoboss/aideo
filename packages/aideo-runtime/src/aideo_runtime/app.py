"""FastAPI application factory for the Runtime service."""

from traceback import format_exception

from aideo_runtime.api import router
from aideo_runtime.backend.loader import load_provider
from aideo_runtime.config import RuntimeSettings
from aideo_runtime.registry import ModelRegistry
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def create_app(settings: RuntimeSettings | None = None) -> FastAPI:
    """Create an HTTP Runtime application from settings or environment."""
    runtime_settings = settings or RuntimeSettings.from_env()
    registry = ModelRegistry()
    for provider_name in runtime_settings.providers:
        provider = load_provider(provider_name)
        backend = provider.create_backend(runtime_settings.paths)
        for model in provider.models():
            registry.register(model, backend)
    app = FastAPI(
        title="Aideo Runtime",
        version="0.1.0",
    )
    app.state.registry = registry
    app.state.debug = runtime_settings.debug
    if runtime_settings.debug:
        app.add_exception_handler(Exception, _debug_exception_response)
    app.include_router(router)
    return app


async def _debug_exception_response(
    _: Request,
    error: Exception,
) -> JSONResponse:
    """Return an exception traceback for development-only Runtime debugging."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(error),
            "exception": type(error).__name__,
            "traceback": "".join(format_exception(error)),
        },
    )
