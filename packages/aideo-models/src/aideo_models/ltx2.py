"""Lazy LTX2 local video model without Runtime service dependencies."""

import asyncio
import os
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import Any

from aideo_models.models import VideoGenerationRequest


class LTX2Model:
    """Load and execute the LTX2 distilled video pipeline on demand."""

    def __init__(
        self,
        models_dir: Path,
        pipeline_factory: Callable[[], Any] | None = None,
        encoder: Callable[..., None] | None = None,
    ) -> None:
        """Configure the model directory and optional test collaborators."""
        self._models_dir = models_dir
        self._pipeline_factory = pipeline_factory
        self._encoder = encoder
        self._pipeline: Any | None = None

    async def generate(self, request: VideoGenerationRequest) -> Path:
        """Generate one video at the validated output path."""
        await self._load()
        pipeline = self._pipeline
        if pipeline is None:
            raise RuntimeError("LTX2 pipeline failed to initialize")
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._generate, pipeline, request)
        return request.output_path

    async def aclose(self) -> None:
        """Release the loaded pipeline."""
        self._pipeline = None

    async def _load(self) -> None:
        if self._pipeline is not None:
            return
        loop = asyncio.get_running_loop()
        self._pipeline = await loop.run_in_executor(None, self._build_pipeline)

    def _build_pipeline(self) -> Any:
        if self._pipeline_factory is not None:
            return self._pipeline_factory()
        torch_module = import_module("torch")
        loader_module = import_module("ltx_core.loader")
        distilled_module = import_module("ltx_pipelines.distilled")
        quantization_module = import_module("ltx_pipelines.utils.quantization_factory")
        types_module = import_module("ltx_pipelines.utils.types")
        lora_mapping = getattr(loader_module, "LTXV_LORA_COMFY_RENAMING_MAP")
        lora_path = getattr(loader_module, "LoraPathStrengthAndSDOps")
        distilled_pipeline = getattr(distilled_module, "DistilledPipeline")
        quantization_kind = getattr(quantization_module, "QuantizationKind")
        offload_mode = getattr(types_module, "OffloadMode")

        checkpoint = self._models_dir / os.environ["LTX2_DISTILLED_CHECKPOINT"]
        gemma = self._models_dir / os.environ["LTX2_GEMMA_ROOT"]
        upsampler = self._models_dir / os.environ["LTX2_SPATIAL_UPSAMPLER"]
        lora = os.environ.get("LTX2_LORA")
        loras = (
            [
                lora_path(
                    str(self._models_dir / lora),
                    float(os.environ.get("LTX2_LORA_STRENGTH", "1")),
                    lora_mapping,
                )
            ]
            if lora
            else []
        )
        quantization = os.environ.get("LTX2_QUANTIZATION", "fp8-cast")
        policy = (
            quantization_kind(quantization).to_policy(str(checkpoint))
            if quantization
            else None
        )
        return distilled_pipeline(
            distilled_checkpoint_path=str(checkpoint),
            gemma_root=str(gemma),
            spatial_upsampler_path=str(upsampler),
            loras=loras,
            device=torch_module.device(os.environ.get("LTX2_DEVICE", "cuda")),
            quantization=policy,
            offload_mode=offload_mode(os.environ.get("LTX2_OFFLOAD_MODE", "none")),
        )

    def _generate(self, pipeline: Any, request: VideoGenerationRequest) -> None:
        if self._encoder is not None:
            video, audio = pipeline(prompt=request.prompt)
            self._encoder(video, audio, output_path=str(request.output_path))
            return
        video_vae_module = import_module("ltx_core.model.video_vae")
        constants_module = import_module("ltx_pipelines.utils.constants")
        media_io_module = import_module("ltx_pipelines.utils.media_io")
        tiling_config = getattr(video_vae_module, "TilingConfig")
        chunks_count = getattr(video_vae_module, "get_video_chunks_number")
        stage_1_sigmas = getattr(constants_module, "DISTILLED_SIGMAS")
        stage_2_sigmas = getattr(constants_module, "STAGE_2_DISTILLED_SIGMAS")
        encode_video = getattr(media_io_module, "encode_video")
        tiling = tiling_config.default()
        video, audio = pipeline(
            prompt=request.prompt,
            seed=request.seed,
            height=request.height,
            width=request.width,
            num_frames=request.num_frames,
            frame_rate=request.frame_rate,
            images=[],
            tiling_config=tiling,
            enhance_prompt=request.enhance_prompt,
            stage_1_sigmas=stage_1_sigmas,
            stage_2_sigmas=stage_2_sigmas,
        )
        encode_video(
            video=video,
            fps=int(request.frame_rate),
            audio=audio,
            output_path=str(request.output_path),
            video_chunks_number=chunks_count(request.num_frames, tiling),
        )
