"""LTX-2 model wrapper — stub implementation.

Replace with real LTX-2 model loading and inference when
the model is available. https://github.com/Lightricks/LTX-2
"""

import asyncio
from collections.abc import AsyncGenerator


class LTX2Model:
    """Stub LTX-2 text-to-video model.

    Generates placeholder video bytes with simulated progress.
    Replace with real model loading and CUDA inference.
    """

    def __init__(self):
        """Initialize model; call load() before generate()."""
        self._loaded = False

    async def load(self) -> None:
        """Load the model into memory (stub)."""
        await asyncio.sleep(0.01)
        self._loaded = True

    async def generate(
        self,
        prompt: str,
        params: dict | None = None,
    ) -> AsyncGenerator[float, None]:
        """Generate a video from a text prompt.

        Yields progress percentages (0.0 → 100.0) during generation.
        Final yield is 100.0, after which the video is ready.

        Stub: simulates 10 steps over ~2 seconds.
        """
        _ = params or {}
        if not self._loaded:
            await self.load()

        steps = 10
        for i in range(steps + 1):
            progress = (i / steps) * 100.0
            await asyncio.sleep(0.1)
            yield progress

    def get_video(self) -> bytes:
        """Return the generated video bytes (stub)."""
        return b"STUB_LTX2_VIDEO_DATA"
