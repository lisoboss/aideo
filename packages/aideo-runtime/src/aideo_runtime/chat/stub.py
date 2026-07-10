"""Stub chat provider — placeholder for future LLM integration."""

import asyncio
import logging
from collections.abc import AsyncGenerator

from aideo_runtime.chat.provider import ChatProvider, register_provider

logger = logging.getLogger(__name__)


class StubChatProvider(ChatProvider):
    """Placeholder chat provider (llama.cpp / vLLM / ollama — not yet implemented)."""

    provider_name = "stub@chat.provider"

    @property
    def is_loaded(self) -> bool:
        return True

    async def load(self) -> None:
        logger.info("StubChatProvider — no model to load")

    async def run(
        self,
        messages: list[dict],
        params: dict | None = None,
        task_id: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        yield {"progress": 50.0, "message": "Chat stub: generating reply..."}
        await asyncio.sleep(0.5)
        yield {
            "progress": 100.0,
            "message": "Done",
            "result_data": {
                "reply": "LLM module not yet implemented.",
                "model": "stub",
            },
        }


# Register the stub provider so it can be used in the system.
register_provider(StubChatProvider)
