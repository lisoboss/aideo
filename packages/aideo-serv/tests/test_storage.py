"""Tests for the StorageService file storage abstraction."""

import asyncio
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_base_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def storage(tmp_base_dir):
    from aideo_serv.services.storage import StorageService

    return StorageService(base_dir=tmp_base_dir)


class TestDirectoryStructure:
    def test_task_dir_created_on_save_video(self, storage, tmp_base_dir):
        task_id = "ab12345678901234567890123456789012"
        path = asyncio.run(storage.save_video(task_id, b"fake video"))
        assert path.exists()
        assert path.parent.name == task_id

    def test_preview_dir_created(self, storage, tmp_base_dir):
        task_id = "ab12345678901234567890123456789012"
        path = asyncio.run(storage.save_preview(task_id, 0, b"fake jpeg"))
        assert path.exists()
        assert path.parent.name == "preview"
        assert path.name == "0000.jpg"

    def test_preview_frame_number_padded(self, storage):
        task_id = "ab12345678901234567890123456789012"
        path = asyncio.run(storage.save_preview(task_id, 42, b"x"))
        assert path.name == "0042.jpg"


class TestPathGeneration:
    def test_get_path(self, storage, tmp_base_dir):
        task_id = "ffabcdef123456789012345678901234"
        path = storage.get_path(task_id)
        expected = tmp_base_dir / task_id[:2] / task_id
        assert path == expected

    def test_get_result_url(self, storage):
        task_id = "ab12345678901234567890123456789012"
        url = storage.get_result_url(task_id)
        assert "/api/v1/results/" in url
        assert task_id in url
        assert url.endswith("/download")

    def test_get_preview_url(self, storage):
        task_id = "ab12345678901234567890123456789012"
        url = storage.get_preview_url(task_id, 5)
        assert "/api/v1/results/" in url
        assert task_id in url
        assert "/preview/0005" in url


class TestConcurrentWrites:
    def test_concurrent_save_video(self, storage):
        task_ids = [f"{i:032x}" for i in range(5)]

        async def save_all():
            tasks = [
                storage.save_video(tid, f"video_{i}".encode())
                for i, tid in enumerate(task_ids)
            ]
            return await asyncio.gather(*tasks)

        paths = asyncio.run(save_all())
        assert all(p.exists() for p in paths)

    def test_concurrent_previews(self, storage):
        task_id = "cc" + "0" * 30

        async def save_previews():
            tasks = [
                storage.save_preview(task_id, i, f"frame_{i}".encode())
                for i in range(10)
            ]
            return await asyncio.gather(*tasks)

        paths = asyncio.run(save_previews())
        assert all(p.exists() for p in paths)
        assert len(paths) == 10
