"""Tests for ProjectService CRUD operations."""

from uuid import uuid4

import pytest

from aideo_serv.models.project import CanvasData, CanvasViewport, ProjectUpdate


class TestCreateProject:
    def test_create_returns_project_with_defaults(self, project_service):
        project = project_service.create(name="Test Project")
        assert project.name == "Test Project"
        assert project.id is not None
        assert project.task_count == 0

    def test_create_with_canvas_data(self, project_service):
        canvas = CanvasData(viewport=CanvasViewport(center_x=100, center_y=200, scale=0.5))
        project = project_service.create(name="Canvas", canvas_data=canvas)
        assert project.canvas_data.viewport.center_x == 100
        assert project.canvas_data.viewport.scale == 0.5

    def test_create_with_metadata(self, project_service):
        project = project_service.create(
            name="Meta", metadata={"author": "test", "tags": ["a", "b"]}
        )
        assert project.metadata["author"] == "test"
        assert project.metadata["tags"] == ["a", "b"]


class TestGetProject:
    def test_get_existing(self, project_service):
        created = project_service.create(name="Get Me")
        fetched = project_service.get(created.id)
        assert fetched.id == created.id
        assert fetched.name == "Get Me"

    def test_get_nonexistent_raises(self, project_service):
        with pytest.raises(LookupError):
            project_service.get(uuid4())


class TestListProjects:
    def test_list_empty(self, project_service):
        result = project_service.list()
        assert result.items == []
        assert result.total == 0

    def test_list_returns_all(self, project_service):
        for i in range(3):
            project_service.create(name=f"Project {i}")
        result = project_service.list()
        assert len(result.items) == 3
        assert result.total == 3

    def test_list_pagination(self, project_service):
        for i in range(10):
            project_service.create(name=f"Project {i}")
        result = project_service.list(offset=0, limit=3)
        assert len(result.items) == 3
        assert result.total == 10


class TestUpdateProject:
    def test_update_name(self, project_service):
        project = project_service.create(name="Old Name")
        updated = project_service.update(project.id, ProjectUpdate(name="New Name"))
        assert updated.name == "New Name"

    def test_update_canvas_data(self, project_service):
        project = project_service.create(name="Canvas")
        new_canvas = CanvasData(viewport=CanvasViewport(center_x=500))
        updated = project_service.update(project.id, ProjectUpdate(canvas_data=new_canvas))
        assert updated.canvas_data.viewport.center_x == 500

    def test_update_metadata(self, project_service):
        project = project_service.create(name="Meta")
        updated = project_service.update(
            project.id, ProjectUpdate(metadata={"key": "value"})
        )
        assert updated.metadata == {"key": "value"}

    def test_update_nonexistent_raises(self, project_service):
        with pytest.raises(LookupError):
            project_service.update(uuid4(), ProjectUpdate(name="Nope"))


class TestDeleteProject:
    def test_delete_existing(self, project_service):
        project = project_service.create(name="Delete Me")
        project_service.delete(project.id)
        with pytest.raises(LookupError):
            project_service.get(project.id)

    def test_delete_nonexistent_raises(self, project_service):
        with pytest.raises(LookupError):
            project_service.delete(uuid4())


class TestTaskCount:
    def test_increment_task_count(self, project_service):
        project = project_service.create(name="Tasks")
        assert project.task_count == 0
        project_service.increment_task_count(project.id)
        assert project_service.get(project.id).task_count == 1
        project_service.increment_task_count(project.id)
        assert project_service.get(project.id).task_count == 2

    def test_increment_nonexistent_noop(self, project_service):
        # Should not raise
        project_service.increment_task_count(uuid4())
