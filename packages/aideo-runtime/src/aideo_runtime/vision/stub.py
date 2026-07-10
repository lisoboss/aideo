"""Stub vision provider — placeholder for future VL model integration."""

import asyncio
import logging
from collections.abc import AsyncGenerator

from aideo_runtime.vision.provider import VisionProvider

logger = logging.getLogger(__name__)


class StubVisionProvider(VisionProvider):
    """Placeholder vision provider (LLaVA / Qwen-VL — not yet implemented)."""

    provider_name = "stub-vision"

    @property
    def is_loaded(self) -> bool:
        return True

    async def load(self) -> None:
        logger.info("StubVisionProvider — no model to load")

    async def run(
        self,
        image_path: str,
        prompt: str = "",
        params: dict | None = None,
        task_id: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        yield {"progress": 50.0, "message": "Vision stub: analyzing image..."}
        await asyncio.sleep(0.5)
        yield {
            "progress": 100.0,
            "message": "Done",
            "result_data": {"caption": "Vision module not yet implemented.", "model": "stub"},
        }
