"""Task orchestration service with lifecycle state machine."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from aideo_serv.models.events import WSEvent
from aideo_serv.models.task import (
    Task,
    TaskListResponse,
    TaskStatus,
)
from aideo_serv.services.connection_manager import get_connection_manager

_VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.QUEUED: {TaskStatus.RUNNING, TaskStatus.CANCELLED, TaskStatus.FAILED},
    TaskStatus.RUNNING: {
        TaskStatus.GENERATING,
        TaskStatus.CANCELLED,
        TaskStatus.FAILED,
    },
    TaskStatus.GENERATING: {
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
    },
}

_TERMINAL: set[TaskStatus] = {
    TaskStatus.COMPLETED,
    TaskStatus.FAILED,
    TaskStatus.CANCELLED,
}

# Map legacy event types to v2 typed event discriminators
_EVENT_DISCRIMINATOR: dict[str, str] = {
    "status_change": "task.status",
    "progress": "task.progress",
    "preview": "task.preview",
    "completed": "task.completed",
    "error": "task.failed",
    "cancelled": "task.cancelled",
}


class TaskService:
    """Manages video generation task lifecycle with in-memory storage."""

    def __init__(self):
        """Initialize with empty in-memory task store."""
        self._tasks: dict[UUID, Task] = {}

    def create(
        self,
        prompt: str,
        params: dict[str, Any] | None = None,
        task_type: str = "video_generation",
        project_id: UUID | None = None,
        output_node_id: UUID | None = None,
        prompt_structured: dict | None = None,
        input_files: list[dict] | None = None,
    ) -> Task:
        """Create a new task in QUEUED state."""
        now = datetime.now(timezone.utc)
        task = Task(
            id=uuid4(),
            prompt=prompt,
            params=params,
            task_type=task_type,
            project_id=project_id,
            output_node_id=output_node_id,
            prompt_structured=prompt_structured,
            input_files=input_files,
            status=TaskStatus.QUEUED,
            progress=0.0,
            created_at=now,
            updated_at=now,
            previews=[],
        )
        self._tasks[task.id] = task
        self._broadcast(task.id, "status_change", {"status": task.status.value})
        return task

    def get(self, task_id: UUID) -> Task:
        """Get a task by ID. Raises LookupError if not found."""
        if task_id not in self._tasks:
            raise LookupError(f"Task {task_id} not found")
        return self._tasks[task_id]

    def list(
        self,
        status: str | None = None,
        project_id: UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> TaskListResponse:
        """List tasks with optional status/project_id filter and pagination."""
        tasks = list(self._tasks.values())
        if status is not None:
            tasks = [t for t in tasks if t.status.value == status]
        if project_id is not None:
            tasks = [t for t in tasks if t.project_id == project_id]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        total = len(tasks)
        page = tasks[offset : offset + limit]
        return TaskListResponse(tasks=page, total=total, offset=offset, limit=limit)

    def list_by_project(
        self,
        project_id: UUID,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> TaskListResponse:
        """List tasks for a specific project."""
        return self.list(status=status, project_id=project_id, offset=offset, limit=limit)

    def get_active_by_project(self, project_id: UUID) -> list[Task]:
        """Return all non-terminal tasks for a project (for WS snapshot)."""
        return [
            t for t in self._tasks.values()
            if t.project_id == project_id and t.status not in _TERMINAL
        ]

    async def delete_by_project(self, project_id: UUID) -> int:
        """Delete all tasks belonging to a project. Returns count deleted."""
        to_delete = [
            tid for tid, t in self._tasks.items() if t.project_id == project_id
        ]
        for tid in to_delete:
            del self._tasks[tid]
        return len(to_delete)

    def cancel(self, task_id: UUID) -> Task:
        """Cancel a task (queued or running only)."""
        task = self.get(task_id)
        if task.status in _TERMINAL:
            raise ValueError(f"Cannot cancel task in {task.status.value} state")
        return self._transition(task, TaskStatus.CANCELLED)

    def update_status(self, task_id: UUID, new_status: str) -> Task:
        """Update task status with state machine validation."""
        task = self.get(task_id)
        status = TaskStatus(new_status)
        return self._transition(task, status)

    def update_progress(
        self, task_id: UUID, progress: float, message: str = ""
    ) -> Task:
        """Update generation progress (0.0–100.0) with optional stage message."""
        if not (0.0 <= progress <= 100.0):
            raise ValueError(f"Progress must be 0-100, got {progress}")
        task = self.get(task_id)
        task.progress = progress
        task.updated_at = datetime.now(timezone.utc)
        self._tasks[task.id] = task
        self._broadcast(
            task.id, "progress", {"progress": progress, "message": message}
        )
        return task

    def add_preview(self, task_id: UUID, preview_url: str) -> Task:
        """Append a preview image URL to the task."""
        task = self.get(task_id)
        task.previews.append(preview_url)
        task.updated_at = datetime.now(timezone.utc)
        self._tasks[task.id] = task
        self._broadcast(task.id, "preview", {"url": preview_url})
        return task

    def complete(self, task_id: UUID, result_path: str, result_data: dict | None = None) -> Task:
        """Mark a task as completed with the result video path and optional inline data.

        Inline ``result_data`` is used by providers (e.g. whisper) that return
        results directly rather than writing files to disk.
        """
        task = self.get(task_id)
        if task.status != TaskStatus.GENERATING:
            raise ValueError(
                f"Cannot complete task in {task.status.value} state, "
                f"expected generating"
            )
        task = self._transition(task, TaskStatus.COMPLETED)
        task.result_path = result_path
        task.result_url = f"/api/v1/results/{task.id}/download"
        task.result_data = result_data
        task.progress = 100.0
        task.updated_at = datetime.now(timezone.utc)
        self._tasks[task.id] = task
        self._broadcast(task.id, "completed", {"result_url": task.result_url})
        return task

    def fail(self, task_id: UUID, error_message: str) -> Task:
        """Mark a task as failed with an error message."""
        task = self.get(task_id)
        if task.status in _TERMINAL:
            raise ValueError(f"Cannot fail task in terminal state {task.status.value}")
        task = self._transition(task, TaskStatus.FAILED)
        task.error_message = error_message
        task.updated_at = datetime.now(timezone.utc)
        self._tasks[task.id] = task
        self._broadcast(task.id, "error", {"message": error_message})
        return task

    def _transition(self, task: Task, to_status: TaskStatus) -> Task:
        valid_targets = _VALID_TRANSITIONS.get(task.status, set())
        if to_status not in valid_targets:
            raise ValueError(
                f"Invalid transition: {task.status.value} → {to_status.value}"
            )
        task.status = to_status
        task.updated_at = datetime.now(timezone.utc)
        self._broadcast(task.id, "status_change", {"status": to_status.value})
        return task

    def _broadcast(self, task_id: UUID, event_type: str, data: dict) -> None:
        """Push a WebSocket event with both legacy and v2 typed formats.

        Events are broadcast to:
        1. Per-task queues (WS /ws/tasks/{id})
        2. Per-project queues (WS /ws/projects/{id}), if task has a project_id
        """
        task = self._tasks.get(task_id)

        # Build legacy event (v1 backward compat)
        legacy_event = WSEvent(
            type=event_type,
            task_id=str(task_id),
            data=data,
        )
        payload = legacy_event.model_dump(mode="json")

        # Add v2 typed discriminator fields
        event_discriminator = _EVENT_DISCRIMINATOR.get(event_type, event_type)
        payload["event"] = event_discriminator

        if task is not None:
            if task.output_node_id is not None:
                payload["output_node_id"] = str(task.output_node_id)

        # Add type-specific fields for v2 clients
        if event_type == "status_change":
            payload["status"] = data.get("status")
        elif event_type == "progress":
            payload["progress"] = data.get("progress")
            payload["message"] = data.get("message", "")
        elif event_type == "preview":
            payload["frame_url"] = data.get("url")
        elif event_type == "completed":
            payload["result_url"] = data.get("result_url")
            if task is not None:
                payload["result_data"] = task.result_data
                payload["previews"] = task.previews
        elif event_type == "error":
            payload["error_message"] = data.get("message")

        # Broadcast to per-task queues
        manager = get_connection_manager()
        manager.broadcast(task_id, payload)

        # Broadcast to per-project queue if task belongs to a project
        if task is not None and task.project_id is not None:
            manager.broadcast_project(task.project_id, payload)

        if event_type in ("completed", "error", "cancelled"):
            manager.close_task(task_id)
