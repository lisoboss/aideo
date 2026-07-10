"""AI provider discovery endpoint — lists available providers for the frontend."""

from aideo_serv.dependencies import get_ai_client
from aideo_serv.services.ai_client import AIClient
from fastapi import APIRouter, Depends

ai_router = APIRouter(prefix="/ai", tags=["ai"])


@ai_router.get("/providers")
async def list_providers(
    ai: AIClient = Depends(get_ai_client),
):
    """List available AI providers for the frontend to choose from.

    Returns metadata for each registered provider: name, model, is_default.
    The iPad client can present these as a picker and pass the chosen
    ``ai_provider`` name in generate / canvas assist requests.
    """
    return {
        "providers": ai.list_providers(),
        "default": ai.default_name,
    }
