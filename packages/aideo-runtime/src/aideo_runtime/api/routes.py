"""FastAPI routes for the unified Runtime HTTP/SSE contract."""

import json
from collections.abc import AsyncIterator
from dataclasses import asdict
from traceback import format_exception
from typing import Any

from aideo_runtime.capabilities import Capability
from aideo_runtime.models import (
    BackendEvent,
    BackendRequest,
    BackendResponse,
    ErrorEvent,
    InferenceParameters,
)
from aideo_runtime.registry import ModelRegistry
from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse

router = APIRouter()


def _registry(request: Request) -> ModelRegistry:
    """Retrieve the configured registry from application state."""
    return request.app.state.registry


def _event_name(event: BackendEvent) -> str:
    """Map a normalized event class to its public SSE event name."""
    return type(event).__name__.removesuffix("Event").lower()


async def _sse(
    events: AsyncIterator[BackendEvent], *, debug: bool
) -> AsyncIterator[str]:
    """Encode normalized backend events as SSE frames."""
    try:
        async for event in events:
            encoded = json.dumps(jsonable_encoder(asdict(event)), separators=(",", ":"))
            yield f"event: {_event_name(event)}\ndata: {encoded}\n\n"
    except Exception as error:
        details = (
            {
                "exception": type(error).__name__,
                "traceback": "".join(format_exception(error)),
            }
            if debug
            else {}
        )
        event = ErrorEvent(
            str(error),
            code=type(error).__name__,
            details=details,
        )
        encoded = json.dumps(jsonable_encoder(asdict(event)), separators=(",", ":"))
        yield f"event: {_event_name(event)}\ndata: {encoded}\n\n"


@router.get("/health")
async def health(request: Request) -> dict[str, Any]:
    """Return Runtime health and registration count."""
    return {"status": "ok", "models": len(_registry(request).list_models())}


@router.get("/api/v1")
async def list_all_models(request: Request) -> dict[str, Any]:
    """List all registered models and their capabilities."""
    models = _registry(request).list_models()
    return {
        "models": [jsonable_encoder(asdict(model)) for model in models],
        "capabilities": sorted({model.capability.value for model in models}),
    }


@router.get("/api/v1/{capability}")
async def list_capability_models(
    capability: Capability, request: Request
) -> dict[str, Any]:
    """List models that serve one capability."""
    models = _registry(request).list_models(capability)
    return {
        "capability": capability.value,
        "models": [jsonable_encoder(asdict(model)) for model in models],
    }


@router.post("/api/v1/{capability}/{model}", response_model=None)
async def invoke(
    capability: Capability,
    model: str,
    payload: dict[str, Any],
    request: Request,
) -> JSONResponse | StreamingResponse:
    """Invoke one registered model, returning JSON or normalized SSE events."""
    if payload.get("capability") != capability.value or payload.get("model") != model:
        raise HTTPException(422, "Request capability and model must match the path")
    registry = _registry(request)
    try:
        info = registry.get_model(model)
    except KeyError as error:
        raise HTTPException(404, f"Unknown model: {model}") from error
    if info.capability is not capability:
        raise HTTPException(409, f"Model {model} does not support {capability.value}")
    input_data = payload.get("input")
    if not isinstance(input_data, dict):
        raise HTTPException(422, "Request input must be an object")
    raw_parameters = payload.get("parameters", {})
    if not isinstance(raw_parameters, dict):
        raise HTTPException(422, "Request parameters must be an object")
    try:
        parameters = InferenceParameters.from_dict(raw_parameters)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    if (
        parameters.max_output_tokens is not None
        and info.max_tokens is not None
        and parameters.max_output_tokens > info.max_tokens
    ):
        raise HTTPException(422, "max_output_tokens exceeds the model limit")
    backend_request = BackendRequest(
        capability=capability,
        model=model,
        input=input_data,
        parameters=parameters.to_dict(),
        stream=bool(payload.get("stream", False)),
    )
    backend = registry.get_backend(model)
    if not backend_request.stream:
        response: BackendResponse = await backend.invoke(backend_request)
        return JSONResponse(jsonable_encoder(asdict(response)))
    return StreamingResponse(
        _sse(backend.stream(backend_request), debug=request.app.state.debug),
        media_type="text/event-stream",
    )
