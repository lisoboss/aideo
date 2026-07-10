"""Main API router for aideo-serv."""

import logging

from aideo_serv.api.ai import ai_router
from aideo_serv.api.assets import assets_router
from aideo_serv.api.canvas_assist import canvas_router
from aideo_serv.api.generate import generate_router
from aideo_serv.api.projects import projects_router
from aideo_serv.api.results import results_router
from aideo_serv.api.tasks import CallbackPayload, tasks_router
from aideo_serv.api.ws import ws_router
from aideo_serv.dependencies import get_inference_manager, get_task_service
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")


@router.get("/health")
async def health():
    """Health check endpoint — v2 with version and services status."""
    mgr = get_inference_manager()
    inference_status = "connected" if mgr.is_any_connected() else "disconnected"
    return {
        "status": "ok",
        "version": "2.0.0",
        "services": {
            "inference": inference_status,
            "storage": "ok",
        },
    }


@router.post("/internal/callback", status_code=200)
async def inference_callback(payload: CallbackPayload):
    """Receive progress/completion/error/cancelled callbacks from the inference service."""
    svc = get_task_service()

    try:
        if payload.type == "progress":
            progress = float(payload.data.get("progress", 0))
            message = str(payload.data.get("message", ""))
            svc.update_progress(payload.task_id, progress, message)
        elif payload.type == "completed":
            result_path = payload.data.get("result_path", "")
            result_data = payload.data.get("result_data")
            svc.complete(payload.task_id, result_path, result_data)
        elif payload.type == "error":
            message = payload.data.get("message", "Unknown error")
            svc.fail(payload.task_id, message)
        elif payload.type == "cancelled":
            # Already handled locally by cancel_task endpoint;
            # this is the forwarded cancellation acknowledgement.
            pass
    except ValueError:
        # Task already in terminal state (e.g. cancelled locally before
        # the callback arrived) — ignore.
        logger.debug("Callback %s ignored for task %s", payload.type, payload.task_id)

    return {"status": "ok"}


router.include_router(tasks_router)
router.include_router(ws_router)
router.include_router(results_router)
router.include_router(projects_router)
router.include_router(assets_router)
router.include_router(generate_router)
router.include_router(canvas_router)
router.include_router(ai_router)
