"""Structured error response models for aideo-serv v2."""

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Machine-readable error with optional details list."""

    code: str
    message: str
    details: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Standard error envelope — ``{"error": {...}}``."""

    error: ErrorDetail


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------


def error_response(
    code: str,
    message: str,
    details: list[str] | None = None,
    status_code: int = 400,
) -> tuple[dict, int]:
    """Build a FastAPI-compatible (content, status_code) error tuple.

    Usage::

        raise HTTPException(
            status_code=status_code,
            detail=error_response("RESOURCE_NOT_FOUND", "Project not found")[0],
        )

    Or simply::

        return JSONResponse(
            content=error_response("CONFLICT", "Task is terminal")[0],
            status_code=409,
        )
    """
    body = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            details=details or [],
        )
    )
    return body.model_dump(mode="json"), status_code
