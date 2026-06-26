"""Tests for the TaskService state machine and task lifecycle."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest


class TestCreateTask:
    def test_create_returns_task_with_queued_status(self, task_service):
        task = task_service.create(prompt="A cat walking")
        assert task.status == "queued"
        assert task.prompt == "A cat walking"
        assert task.progress == 0.0
        assert task.id is not None

    def test_create_with_params(self, task_service):
        task = task_service.create(prompt="test", params={"duration": 5})
        assert task.params == {"duration": 5}


class TestGetTask:
    def test_get_existing_task(self, task_service):
        created = task_service.create(prompt="test")
        fetched = task_service.get(created.id)
        assert fetched.id == created.id

    def test_get_nonexistent_task_raises(self, task_service):
        with pytest.raises(LookupError):
            task_service.get(uuid4())


class TestListTasks:
    def test_list_empty(self, task_service):
        result = task_service.list()
        assert result.tasks == []
        assert result.total == 0

    def test_list_returns_all_tasks(self, task_service):
        for i in range(5):
            task_service.create(prompt=f"task {i}")
        result = task_service.list()
        assert len(result.tasks) == 5
        assert result.total == 5

    def test_list_pagination(self, task_service):
        for i in range(10):
            task_service.create(prompt=f"task {i}")
        result = task_service.list(offset=0, limit=3)
        assert len(result.tasks) == 3
        assert result.total == 10

    def test_list_filter_by_status(self, task_service):
        t1 = task_service.create(prompt="queued one")
        t2 = task_service.create(prompt="running one")
        task_service.update_status(t2.id, "running")
        queued = task_service.list(status="queued")
        assert len(queued.tasks) == 1
        assert queued.tasks[0].id == t1.id


class TestCancelTask:
    def test_cancel_queued_task(self, task_service):
        task = task_service.create(prompt="test")
        cancelled = task_service.cancel(task.id)
        assert cancelled.status == "cancelled"

    def test_cancel_running_task(self, task_service):
        task = task_service.create(prompt="test")
        task_service.update_status(task.id, "running")
        cancelled = task_service.cancel(task.id)
        assert cancelled.status == "cancelled"

    def test_cannot_cancel_completed_task(self, task_service):
        task = task_service.create(prompt="test")
        task_service.update_status(task.id, "running")
        task_service.update_status(task.id, "generating")
        task_service.complete(task.id, "/data/video.mp4")
        with pytest.raises(ValueError, match="Cannot cancel"):
            task_service.cancel(task.id)


class TestStateMachine:
    def test_valid_transition_queued_to_running(self, task_service):
        task = task_service.create(prompt="test")
        updated = task_service.update_status(task.id, "running")
        assert updated.status == "running"

    def test_valid_transition_running_to_generating(self, task_service):
        task = task_service.create(prompt="test")
        task_service.update_status(task.id, "running")
        updated = task_service.update_status(task.id, "generating")
        assert updated.status == "generating"

    def test_invalid_transition_queued_to_generating(self, task_service):
        task = task_service.create(prompt="test")
        with pytest.raises(ValueError):
            task_service.update_status(task.id, "generating")

    def test_invalid_transition_completed_to_running(self, task_service):
        task = task_service.create(prompt="test")
        task_service.update_status(task.id, "running")
        task_service.update_status(task.id, "generating")
        task_service.complete(task.id, "/data/video.mp4")
        with pytest.raises(ValueError):
            task_service.update_status(task.id, "running")


class TestProgress:
    def test_update_progress_valid(self, task_service):
        task = task_service.create(prompt="test")
        task_service.update_status(task.id, "running")
        task_service.update_status(task.id, "generating")
        updated = task_service.update_progress(task.id, 50.0)
        assert updated.progress == 50.0

    def test_progress_below_zero(self, task_service):
        task = task_service.create(prompt="test")
        with pytest.raises(ValueError):
            task_service.update_progress(task.id, -1.0)

    def test_progress_above_hundred(self, task_service):
        task = task_service.create(prompt="test")
        with pytest.raises(ValueError):
            task_service.update_progress(task.id, 100.1)


class TestPreviews:
    def test_add_preview(self, task_service):
        task = task_service.create(prompt="test")
        task_service.add_preview(task.id, "http://example.com/preview/0000.jpg")
        fetched = task_service.get(task.id)
        assert len(fetched.previews) == 1

    def test_add_multiple_previews(self, task_service):
        task = task_service.create(prompt="test")
        task_service.add_preview(task.id, "http://example.com/p1.jpg")
        task_service.add_preview(task.id, "http://example.com/p2.jpg")
        task_service.add_preview(task.id, "http://example.com/p3.jpg")
        assert len(task_service.get(task.id).previews) == 3


class TestCompleteAndFail:
    def test_complete_sets_result_and_status(self, task_service):
        task = task_service.create(prompt="test")
        task_service.update_status(task.id, "running")
        task_service.update_status(task.id, "generating")
        completed = task_service.complete(task.id, "/data/video.mp4")
        assert completed.status == "completed"
        assert completed.result_path == "/data/video.mp4"
        assert completed.progress == 100.0

    def test_fail_sets_error_and_status(self, task_service):
        task = task_service.create(prompt="test")
        failed = task_service.fail(task.id, "CUDA out of memory")
        assert failed.status == "failed"
        assert failed.error_message == "CUDA out of memory"

    def test_cannot_complete_non_generating_task(self, task_service):
        task = task_service.create(prompt="test")
        with pytest.raises(ValueError):
            task_service.complete(task.id, "/data/video.mp4")
