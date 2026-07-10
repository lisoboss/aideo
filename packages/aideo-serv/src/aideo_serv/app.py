"""FastAPI application factory."""

from contextlib import asynccontextmanager

from aideo_serv.api.router import router
from aideo_serv.dependencies import get_task_service
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    get_task_service()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="aideo-serv",
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Structured error handler — unwrap FastAPI's {"detail": ...} wrapper
    # so all error responses match the v2 API spec: {"error": {...}}
    # ------------------------------------------------------------------

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception):
        """Return 404 errors in structured format."""
        detail = getattr(exc, "detail", "Not found")
        if isinstance(detail, dict) and "error" in detail:
            return JSONResponse(status_code=404, content=detail)
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "RESOURCE_NOT_FOUND",
                    "message": str(detail) if isinstance(detail, str) else "Resource not found",
                    "details": [],
                }
            },
        )

    @app.exception_handler(409)
    async def conflict_handler(request: Request, exc: Exception):
        """Return 409 errors in structured format."""
        detail = getattr(exc, "detail", "Conflict")
        if isinstance(detail, dict) and "error" in detail:
            return JSONResponse(status_code=409, content=detail)
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": "CONFLICT",
                    "message": str(detail) if isinstance(detail, str) else "Conflict",
                    "details": [],
                }
            },
        )

    app.include_router(router)
    return app
