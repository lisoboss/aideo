"""FastAPI dependency injection for aideo-serv."""

from aideo_serv.services.ai_client import (  # noqa: F401
    AIClient,
    get_ai_client,
    set_ai_client,
)
from aideo_serv.services.asset_service import (  # noqa: F401
    AssetService,
    get_asset_service,
    set_asset_service,
)
from aideo_serv.services.connection_manager import (  # noqa: F401
    get_connection_manager,
    set_connection_manager,
)
from aideo_serv.services.inference import InferenceClient
from aideo_serv.services.inference_manager import (  # noqa: F401
    get_inference_manager,
    set_inference_manager,
)
from aideo_serv.services.project_service import (  # noqa: F401
    ProjectService,
    get_project_service,
    set_project_service,
)
from aideo_serv.services.task_service import TaskService

_task_service: TaskService | None = None
_inference_client: InferenceClient | None = None


def get_task_service() -> TaskService:
    """Dependency: return the TaskService singleton."""
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service


def set_task_service(svc: TaskService) -> None:
    """Replace the global TaskService singleton (for testing)."""
    global _task_service
    _task_service = svc


def get_inference_client() -> InferenceClient:
    """Dependency: return the InferenceClient singleton."""
    global _inference_client
    if _inference_client is None:
        from aideo_serv.config import Settings

        settings = Settings()
        _inference_client = InferenceClient(base_url=settings.inference_url)
    return _inference_client


def set_inference_client(client: InferenceClient) -> None:
    """Replace the global InferenceClient singleton (for testing)."""
    global _inference_client
    _inference_client = client
