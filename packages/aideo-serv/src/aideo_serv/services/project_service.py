"""Project CRUD service with in-memory storage."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from aideo_serv.models.project import (
    CanvasData,
    Project,
    ProjectCreate,
    ProjectListResponse,
    ProjectUpdate,
)


class ProjectService:
    """Manages project lifecycle with in-memory storage."""

    def __init__(self):
        self._projects: dict[UUID, Project] = {}

    def create(
        self,
        name: str = "Untitled Project",
        canvas_data: CanvasData | None = None,
        metadata: dict | None = None,
    ) -> Project:
        """Create a new project."""
        now = datetime.now(timezone.utc)
        project = Project(
            id=uuid4(),
            name=name,
            canvas_data=canvas_data or CanvasData(),
            metadata=metadata or {},
            task_count=0,
            created_at=now,
            updated_at=now,
        )
        self._projects[project.id] = project
        return project

    def get(self, project_id: UUID) -> Project:
        """Get a project by ID. Raises LookupError if not found."""
        if project_id not in self._projects:
            raise LookupError(f"Project {project_id} not found")
        return self._projects[project_id]

    def list(self, offset: int = 0, limit: int = 20) -> ProjectListResponse:
        """List projects with pagination, newest first."""
        projects = sorted(
            self._projects.values(),
            key=lambda p: p.created_at,
            reverse=True,
        )
        total = len(projects)
        page = projects[offset : offset + limit]
        return ProjectListResponse(items=page, total=total, offset=offset, limit=limit)

    def update(self, project_id: UUID, update: ProjectUpdate) -> Project:
        """Partially update a project. Only provided fields are changed."""
        project = self.get(project_id)
        if update.name is not None:
            project.name = update.name
        if update.canvas_data is not None:
            project.canvas_data = update.canvas_data
        if update.metadata is not None:
            project.metadata = update.metadata
        project.updated_at = datetime.now(timezone.utc)
        self._projects[project.id] = project
        return project

    def delete(self, project_id: UUID) -> None:
        """Delete a project. Raises LookupError if not found."""
        if project_id not in self._projects:
            raise LookupError(f"Project {project_id} not found")
        del self._projects[project_id]

    def increment_task_count(self, project_id: UUID) -> None:
        """Increment the task_count for a project (best-effort, no-op if missing)."""
        project = self._projects.get(project_id)
        if project is not None:
            project.task_count += 1
            project.updated_at = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_project_service: ProjectService | None = None


def get_project_service() -> ProjectService:
    """Return the global ProjectService singleton."""
    global _project_service
    if _project_service is None:
        _project_service = ProjectService()
    return _project_service


def set_project_service(svc: ProjectService) -> None:
    """Replace the global singleton (for testing)."""
    global _project_service
    _project_service = svc
