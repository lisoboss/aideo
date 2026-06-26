"""Tests for Task and WebSocket event Pydantic models."""

from datetime import datetime
from uuid import UUID

import pytest


class TestTaskCreate:
    """Validate TaskCreate input model."""

    def test_valid_minimal(self):
        """TaskCreate with only required fields."""
        from aideo_serv.models.task import TaskCreate

        t = TaskCreate(prompt="A cat walking in a garden")
        assert t.prompt == "A cat walking in a garden"
        assert t.params is None

    def test_prompt_too_short(self):
        """Empty prompt must be rejected."""
        from aideo_serv.models.task import TaskCreate

        with pytest.raises(ValueError):
            TaskCreate(prompt="")

    def test_prompt_too_long(self):
        """Prompt exceeding 4096 chars must be rejected."""
        from aideo_serv.models.task import TaskCreate

        with pytest.raises(ValueError):
            TaskCreate(prompt="x" * 4097)

    def test_prompt_exactly_4096_ok(self):
        """Prompt at exactly max length is valid."""
        from aideo_serv.models.task import TaskCreate

        t = TaskCreate(prompt="x" * 4096)
        assert len(t.prompt) == 4096

    def test_prompt_not_string(self):
        """Non-string prompt must be rejected."""
        from aideo_serv.models.task import TaskCreate

        with pytest.raises(ValueError):
            TaskCreate(prompt=123)  # type: ignore

    def test_params_optional(self):
        """TaskCreate without params is valid."""
        from aideo_serv.models.task import TaskCreate

        t = TaskCreate(prompt="test")
        assert t.params is None

    def test_params_accepts_dict(self):
        """TaskCreate with params dict."""
        from aideo_serv.models.task import TaskCreate

        t = TaskCreate(
            prompt="test",
            params={"duration": 5, "resolution": "1080p"},
        )
        assert t.params == {"duration": 5, "resolution": "1080p"}


class TestTask:
    """Validate the full Task model."""

    def test_defaults(self):
        """Task created from TaskCreate has correct defaults."""
        from aideo_serv.models.task import Task, TaskCreate, TaskStatus

        tc = TaskCreate(prompt="A sunset over mountains")
        task = Task(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            prompt=tc.prompt,
            params=tc.params,
            status=TaskStatus.QUEUED,
            progress=0.0,
            created_at=datetime(2026, 6, 26, 12, 0, 0),
            updated_at=datetime(2026, 6, 26, 12, 0, 0),
            previews=[],
        )
        assert task.status == TaskStatus.QUEUED
        assert task.progress == 0.0
        assert task.result_path is None
        assert task.result_url is None
        assert task.previews == []
        assert task.error_message is None

    def test_progress_range_valid(self):
        """Progress values within 0-100 are accepted."""
        from aideo_serv.models.task import Task, TaskStatus

        for val in [0.0, 50.0, 100.0]:
            task = Task(
                id=UUID("12345678-1234-5678-1234-567812345678"),
                prompt="test",
                status=TaskStatus.GENERATING,
                progress=val,
                created_at=datetime(2026, 6, 26, 12, 0, 0),
                updated_at=datetime(2026, 6, 26, 12, 0, 0),
                previews=[],
            )
            assert task.progress == val

    def test_progress_below_zero_rejected(self):
        """Progress below 0 must be rejected."""
        import datetime as dt

        from aideo_serv.models.task import Task, TaskStatus

        with pytest.raises(ValueError):
            Task(
                id=UUID("12345678-1234-5678-1234-567812345678"),
                prompt="test",
                status=TaskStatus.GENERATING,
                progress=-1.0,
                created_at=dt.datetime(2026, 6, 26, 12, 0, 0),
                updated_at=dt.datetime(2026, 6, 26, 12, 0, 0),
                previews=[],
            )

    def test_progress_above_hundred_rejected(self):
        """Progress above 100 must be rejected."""
        import datetime as dt

        from aideo_serv.models.task import Task, TaskStatus

        with pytest.raises(ValueError):
            Task(
                id=UUID("12345678-1234-5678-1234-567812345678"),
                prompt="test",
                status=TaskStatus.GENERATING,
                progress=100.1,
                created_at=dt.datetime(2026, 6, 26, 12, 0, 0),
                updated_at=dt.datetime(2026, 6, 26, 12, 0, 0),
                previews=[],
            )

    def test_id_is_uuid(self):
        """Task id must be a UUID."""
        from aideo_serv.models.task import Task, TaskStatus

        with pytest.raises(ValueError):
            Task(
                id="not-a-uuid",  # type: ignore
                prompt="test",
                status=TaskStatus.QUEUED,
                progress=0.0,
                created_at=datetime(2026, 6, 26, 12, 0, 0),
                updated_at=datetime(2026, 6, 26, 12, 0, 0),
                previews=[],
            )

    def test_error_message_on_failed(self):
        """Failed tasks can carry an error_message."""
        import datetime as dt

        from aideo_serv.models.task import Task, TaskStatus

        task = Task(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            prompt="test",
            status=TaskStatus.FAILED,
            progress=0.0,
            error_message="CUDA out of memory",
            created_at=dt.datetime(2026, 6, 26, 12, 0, 0),
            updated_at=dt.datetime(2026, 6, 26, 12, 0, 0),
            previews=[],
        )
        assert task.error_message == "CUDA out of memory"


class TestTaskStatus:
    """Validate the TaskStatus enum."""

    def test_all_statuses_present(self):
        """All six status values exist."""
        from aideo_serv.models.task import TaskStatus

        expected = {
            "queued",
            "running",
            "generating",
            "completed",
            "failed",
            "cancelled",
        }
        actual = {s.value for s in TaskStatus}
        assert actual == expected

    def test_status_is_string_enum(self):
        """TaskStatus values are strings."""
        from aideo_serv.models.task import TaskStatus

        assert TaskStatus.QUEUED == "queued"
        assert isinstance(TaskStatus.QUEUED.value, str)


class TestTaskListResponse:
    """Validate the TaskListResponse model."""

    def test_structure(self):
        from aideo_serv.models.task import Task, TaskListResponse, TaskStatus

        resp = TaskListResponse(
            tasks=[],
            total=0,
            offset=0,
            limit=20,
        )
        assert resp.tasks == []
        assert resp.total == 0
        assert resp.limit == 20

    def test_with_tasks(self):
        from aideo_serv.models.task import Task, TaskListResponse, TaskStatus

        task = Task(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            prompt="test",
            status=TaskStatus.COMPLETED,
            progress=100.0,
            created_at=datetime(2026, 6, 26, 12, 0, 0),
            updated_at=datetime(2026, 6, 26, 12, 0, 0),
            previews=[],
        )
        resp = TaskListResponse(tasks=[task], total=1, offset=0, limit=20)
        assert len(resp.tasks) == 1
        assert resp.total == 1


class TestWSEvent:
    """Validate the WebSocket event model."""

    def test_valid_event(self):
        from aideo_serv.models.events import WSEvent

        event = WSEvent(
            type="progress",
            task_id="550e8400-e29b-41d4-a716-446655440000",
            data={"progress": 50.0, "step": "denoising"},
        )
        assert event.type == "progress"
        assert event.task_id == "550e8400-e29b-41d4-a716-446655440000"
        assert event.data == {"progress": 50.0, "step": "denoising"}
        assert isinstance(event.timestamp, datetime)

    def test_type_is_required(self):
        """WSEvent without type fails validation."""
        from aideo_serv.models.events import WSEvent

        with pytest.raises(ValueError):
            WSEvent(
                task_id="550e8400-e29b-41d4-a716-446655440000",
                data={},
            )

    def test_task_id_is_required(self):
        """WSEvent without task_id fails validation."""
        from aideo_serv.models.events import WSEvent

        with pytest.raises(ValueError):
            WSEvent(
                type="progress",
                data={},
            )

    def test_timestamp_auto_generated(self):
        """Timestamp is auto-set if not provided."""
        from datetime import datetime, timezone

        from aideo_serv.models.events import WSEvent

        before = datetime.now(timezone.utc)
        event = WSEvent(
            type="status_change",
            task_id="550e8400-e29b-41d4-a716-446655440000",
            data={"status": "running"},
        )
        after = datetime.now(timezone.utc)
        assert before <= event.timestamp <= after

    def test_data_can_be_empty_dict(self):
        """data can be an empty dict."""
        from aideo_serv.models.events import WSEvent

        event = WSEvent(
            type="completed",
            task_id="550e8400-e29b-41d4-a716-446655440000",
            data={},
        )
        assert event.data == {}

    def test_data_must_be_dict(self):
        """data must be a dict, not a list or scalar."""
        from aideo_serv.models.events import WSEvent

        with pytest.raises(ValueError):
            WSEvent(
                type="completed",
                task_id="550e8400-e29b-41d4-a716-446655440000",
                data="not-a-dict",  # type: ignore
            )
