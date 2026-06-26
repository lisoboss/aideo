"""Main API router for aideo-serv."""

from aideo_serv.api.results import results_router
from aideo_serv.api.tasks import tasks_router
from aideo_serv.api.ws import ws_router
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


router.include_router(tasks_router)
router.include_router(ws_router)
router.include_router(results_router)
