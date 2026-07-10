"""Tests for image edit / upscale providers (stub)."""

import pytest


class TestStubImageProvider:
    """Interface compliance + stub run behaviour (no model)."""

    @pytest.fixture
    def provider(self):
        from aideo_runtime.image.stub import StubImageProvider

        return StubImageProvider()

    def test_provider_name(self, provider):
        assert provider.provider_name == "stub@image.provider"

    def test_loaded_by_default(self, provider):
        # Stub has no model, so it's always "loaded".
        assert provider.is_loaded is True

    def test_inherits_image_provider(self, provider):
        from aideo_runtime.image.provider import ImageProvider

        assert isinstance(provider, ImageProvider)

    def test_inherits_base_provider(self, provider):
        from aideo_runtime.provider import BaseProvider

        assert isinstance(provider, BaseProvider)

    def test_registered_in_category(self):
        from aideo_runtime.image import PROVIDERS
        from aideo_runtime.image.stub import StubImageProvider

        assert PROVIDERS.get("stub@image.provider") is StubImageProvider

    def test_discoverable_by_prefix(self):
        # aideo-serv maps image_edit/image_upscale → ("image", "stub");
        # the server resolves "stub" via prefix match against "stub@image.provider".
        from aideo_runtime.image import PROVIDERS

        matches = [k for k in PROVIDERS if k.startswith("stub")]
        assert "stub@image.provider" in matches

    def test_run_is_async_generator(self, provider):
        gen = provider.run(params={"mode": "composite"})
        assert hasattr(gen, "__aiter__")

    @pytest.mark.asyncio
    async def test_edit_run_yields_progress_then_result(self, provider):
        events = []
        async for status in provider.run(
            prompt="A white robot",
            params={"mode": "replace_character", "base_image": "asset-1"},
            input_files=[
                {"path": "/tmp/base.jpg", "role": "base", "asset_id": "asset-1"}
            ],
            task_id="task-123",
        ):
            events.append(status)

        # progress event(s) then a terminal event with result_data
        assert len(events) >= 2
        assert events[0].result_data is None
        final = events[-1]
        assert final.progress == 100.0
        assert final.result_data is not None
        assert final.result_data["status"] == "not_implemented"
        assert final.result_data["operation"] == "edit (replace_character)"
        assert final.result_data["task_id"] == "task-123"

    @pytest.mark.asyncio
    async def test_upscale_run_reports_scale(self, provider):
        events = []
        async for status in provider.run(
            params={"scale": 4, "asset_id": "asset-9"},
            input_files=[
                {"path": "/tmp/src.jpg", "role": "source", "asset_id": "asset-9"}
            ],
            task_id="task-up",
        ):
            events.append(status)

        final = events[-1]
        assert final.result_data["operation"] == "upscale x4"

    @pytest.mark.asyncio
    async def test_cancel_stops_before_result(self, provider):
        provider.cancel()  # signal cancellation before running
        events = []
        async for status in provider.run(params={"mode": "inpainting"}):
            events.append(status)

        # Only the initial progress event; no terminal result_data.
        assert all(s.result_data is None for s in events)

    @pytest.mark.asyncio
    async def test_result_serializes_for_sse(self, provider):
        # server.py calls status.model_dump_json() on each yielded item.
        async for status in provider.run(params={"scale": 2}):
            assert isinstance(status.model_dump_json(), str)
