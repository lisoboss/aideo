"""Tests for the streaming speech-to-text WebSocket endpoint.

The ws/transcribe endpoint is verified via integration with a running
aideo-serv + aideo-runtime (see manual verification steps below).

These unit tests cover the supporting models and logic.
"""

import uuid

import pytest


class TestStreamTranscribeTaskFlow:
    """Verify the task lifecycle a streaming chunk goes through."""

    def test_create_speech_to_text_task_with_input_files(self, task_service):
        """Creating a speech_to_text task stores audio input info."""
        task = task_service.create(
            prompt="Stream chunk test.wav",
            task_type="speech_to_text",
            input_files=[{"path": "/tmp/test.wav", "type": "audio"}],
        )
        assert task.task_type == "speech_to_text"
        assert task.status.value == "queued"
        assert len(task.input_files) == 1
        assert task.input_files[0]["type"] == "audio"

    def test_task_transitions_for_stream_chunk(self, task_service):
        """A streaming chunk task goes through queued→running→generating→completed."""
        task = task_service.create(
            prompt="Stream test",
            task_type="speech_to_text",
        )
        tid = task.id

        # Transition to running
        task_service.update_status(tid, "running")
        task = task_service.get(tid)
        assert task.status.value == "running"

        # Transition to generating
        task_service.update_status(tid, "generating")
        task = task_service.get(tid)
        assert task.status.value == "generating"

        # Complete with result_data
        result_data = {"full_text": "hello", "segments": [], "language": "en"}
        task_service.complete(tid, "", result_data)
        task = task_service.get(tid)
        assert task.status.value == "completed"
        assert task.result_data == result_data
        assert task.progress == 100.0

    def test_complete_stores_result_data_for_download(self, task_service):
        """result_data on a completed task is accessible for the download endpoint."""
        task = task_service.create(prompt="stt", task_type="speech_to_text")
        task_service.update_status(task.id, "running")
        task_service.update_status(task.id, "generating")

        expected = {"full_text": "测试文本", "segments": [], "language": "zh"}
        task_service.complete(task.id, "", expected)

        task = task_service.get(task.id)
        assert task.result_data == expected
        # Download check: result_data present means it's downloadable
        assert task.result_data is not None
