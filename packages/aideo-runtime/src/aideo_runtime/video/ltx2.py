"""LTX-2 text-to-video provider via ltx-pipelines."""

import asyncio
import logging
import os
import time
from collections.abc import AsyncGenerator
from pathlib import Path

import torch

from aideo_runtime.video.provider import VideoProvider

logger = logging.getLogger(__name__)


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


class LTX2VideoProvider(VideoProvider):
    """LTX-2 text-to-video generation backed by the distilled ltx-pipelines."""

    provider_name = "ltx2"

    def __init__(
        self,
        distilled_checkpoint_path: str | None = None,
        gemma_root: str | None = None,
        spatial_upsampler_path: str | None = None,
        lora_path: str | None = None,
        lora_strength: float = 1.0,
        device: str | None = None,
        output_dir: str | None = None,
        input_root: str | None = None,
        offload_mode: str | None = None,
        quantization: str | None = None,
    ):
        self._distilled_checkpoint = distilled_checkpoint_path or _env(
            "LTX2_DISTILLED_CHECKPOINT_PATH",
            "/mnt/g/AI/models/LTX-2.3/ltx-2.3-22b-distilled-1.1.safetensors",
        )
        self._gemma_root = gemma_root or _env(
            "LTX2_GEMMA_ROOT",
            "/mnt/g/AI/models/gemma-3-12b-it-qat-q4_0-unquantized",
        )
        self._spatial_upsampler_path = spatial_upsampler_path or _env(
            "LTX2_SPATIAL_UPSAMPLER_PATH",
            "/mnt/g/AI/models/LTX-2.3/ltx-2.3-spatial-upscaler-x2-1.1.safetensors",
        )
        self._lora_path = lora_path or _env("LTX2_LORA_PATH", "")
        self._lora_strength = float(
            lora_strength if lora_strength != 1.0 else _env("LTX2_LORA_STRENGTH", "1.0")
        )
        self._device_str = device or _env("LTX2_DEVICE", "cuda")
        self._output_dir = Path(output_dir or _env("LTX2_OUTPUT_DIR", "./data"))
        self._input_root = Path(input_root or _env("LTX2_INPUT_ROOT", "./data/input"))
        self._offload_mode = offload_mode or _env("LTX2_OFFLOAD_MODE", "none")
        self._quantization = quantization or _env("LTX2_QUANTIZATION", "fp8-cast")
        self._pipeline = None
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def output_dir(self) -> Path:
        return self._output_dir

    def set_output_dir(self, path: str) -> None:
        self._output_dir = Path(path)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def set_input_root(self, path: str) -> None:
        self._input_root = Path(path)
        self._input_root.mkdir(parents=True, exist_ok=True)

    async def load(self) -> None:
        loop = asyncio.get_running_loop()

        def _build():
            from ltx_core.loader import (
                LoraPathStrengthAndSDOps,
                LTXV_LORA_COMFY_RENAMING_MAP,
            )
            from ltx_pipelines.distilled import DistilledPipeline
            from ltx_pipelines.utils.quantization_factory import QuantizationKind
            from ltx_pipelines.utils.types import OffloadMode

            mode = OffloadMode(self._offload_mode)
            q_policy = (
                QuantizationKind(self._quantization).to_policy(self._distilled_checkpoint)
                if self._quantization
                else None
            )
            loras: list = []
            if self._lora_path:
                loras.append(
                    LoraPathStrengthAndSDOps(
                        self._lora_path, self._lora_strength, LTXV_LORA_COMFY_RENAMING_MAP,
                    )
                )
            logger.info(
                "Building DistilledPipeline — checkpoint=%s gemma=%s upsampler=%s "
                "device=%s offload=%s quantization=%s",
                self._distilled_checkpoint, self._gemma_root, self._spatial_upsampler_path,
                self._device_str, mode.value, self._quantization or "none",
            )
            device = torch.device(self._device_str)
            return DistilledPipeline(
                distilled_checkpoint_path=self._distilled_checkpoint,
                gemma_root=self._gemma_root,
                spatial_upsampler_path=self._spatial_upsampler_path,
                loras=loras,
                device=device,
                quantization=q_policy,
                offload_mode=mode,
            )

        self._pipeline = await loop.run_in_executor(None, _build)
        self._loaded = True
        logger.info("DistilledPipeline built successfully")

    async def run(
        self,
        prompt: str,
        params: dict | None = None,
        task_id: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        if not self._loaded or self._pipeline is None:
            await self.load()

        params = params or {}
        loop = asyncio.get_running_loop()

        seed: int = params.get("seed", 42)
        height: int = params.get("height", 512)
        width: int = params.get("width", 768)
        num_frames: int = params.get("num_frames", 121)
        frame_rate: float = params.get("frame_rate", 24.0)
        enhance_prompt: bool = params.get("enhance_prompt", True)

        stage_1_seconds = max(60, num_frames * 17)
        stage_2_seconds = max(60, num_frames * 24)
        encode_seconds = 60

        yield {"progress": 5.0, "message": "Pipeline ready, starting stage 1/2..."}

        def _run():
            from ltx_core.model.video_vae import TilingConfig, get_video_chunks_number
            from ltx_pipelines.utils.constants import DISTILLED_SIGMAS, STAGE_2_DISTILLED_SIGMAS
            from ltx_pipelines.utils.media_io import encode_video

            tiling_config = TilingConfig.default()
            video_chunks_number = get_video_chunks_number(num_frames, tiling_config)

            video_iter, audio = self._pipeline(
                prompt=prompt, seed=seed, height=height, width=width,
                num_frames=num_frames, frame_rate=frame_rate, images=[],
                tiling_config=tiling_config, enhance_prompt=enhance_prompt,
                stage_1_sigmas=DISTILLED_SIGMAS, stage_2_sigmas=STAGE_2_DISTILLED_SIGMAS,
            )
            filename = f"{task_id}.mp4" if task_id else "video.mp4"
            output_path = str(self._output_dir / filename)
            encode_video(
                video=video_iter, fps=int(frame_rate), audio=audio,
                output_path=output_path, video_chunks_number=video_chunks_number,
            )
            return output_path

        task = loop.run_in_executor(None, _run)
        t0 = time.monotonic()

        while not task.done():
            elapsed = time.monotonic() - t0
            if elapsed < stage_1_seconds:
                pct, msg = 5.0 + (elapsed / stage_1_seconds) * 45.0, "Stage 1/2: denoising at low resolution..."
            elif elapsed < stage_1_seconds + stage_2_seconds:
                pct, msg = 50.0 + ((elapsed - stage_1_seconds) / stage_2_seconds) * 45.0, "Stage 2/2: upsampling and refining..."
            else:
                pct, msg = 95.0 + min(4.0, (elapsed - stage_1_seconds - stage_2_seconds) / encode_seconds * 4.0), "Encoding video..."
            yield {"progress": round(min(pct, 99.0), 1), "message": msg}
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=5)
            except TimeoutError:
                pass

        await task
        yield {"progress": 100.0, "message": "Generation complete"}
