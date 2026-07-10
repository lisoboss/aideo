"""Stub image provider — placeholder until a real edit / upscale model lands.

Proves the full ``aideo-serv → aideo-runtime → SSE`` path end-to-end without
a model. Replace with a real provider (e.g. diffusion inpainting for edit,
Real-ESRGAN for upscale) — keep the ``run()`` contract and yield
``ProgressStatus`` (never raw dicts, per the runtime coding rules).
"""

import asyncio
import logging
from collections.abc import AsyncGenerator

from aideo_runtime.image.provider import ImageProvider, register_provider
from aideo_runtime.provider import ProgressStatus

logger = logging.getLogger(__name__)


class StubImageProvider(ImageProvider):
    """Placeholder image edit / upscale provider (model not yet implemented)."""

    provider_name = "stub@image.provider"

    @property
    def is_loaded(self) -> bool:
        """Stub holds no model, so it is always ready."""
        return True

    async def load(self) -> None:
        """No-op — the stub has no model to load."""
        logger.info("StubImageProvider — no model to load")

    async def unload(self) -> None:
        """No-op — the stub has nothing to release."""
        logger.info("StubImageProvider — nothing to unload")

    async def run(
        self,
        prompt: str = "",
        params: dict | None = None,
        input_files: list[dict] | None = None,
        task_id: str | None = None,
        output_root: str | None = None,
        input_root: str | None = None,
        **kwargs,
    ) -> AsyncGenerator[ProgressStatus, None]:
        """Yield a progress event then a placeholder ``not_implemented`` result."""
        params = params or {}

        # Distinguish upscale from edit by the params shape aideo-serv sends.
        if "scale" in params:
            operation = f"upscale x{params.get('scale')}"
        else:
            operation = f"edit ({params.get('mode', 'unknown')})"

        yield ProgressStatus(
            progress=10.0,
            message=f"Image stub: {operation} — no model loaded",
        )

        if self.is_cancelled:
            return

        await asyncio.sleep(0.2)

        yield ProgressStatus(
            progress=100.0,
            message="Image module not yet implemented (stub)",
            result_data={
                "status": "not_implemented",
                "operation": operation,
                "model": "stub",
                "task_id": task_id,
            },
        )


# Register the stub so the `image` category resolves `/api/v1/image/stub`.
register_provider(StubImageProvider)
