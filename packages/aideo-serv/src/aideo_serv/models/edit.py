"""Image edit / upscale request & response models (POST /canvas/edit-image, /upscale).

Mirrors the iPad ``EditImageRequest`` / ``UpscaleRequest`` and the documented
contract in ``docs/API.md``. Images are referenced by ``asset_id`` (uploaded via
``POST /assets``), never inlined as base64.
"""

from enum import StrEnum
from typing import Literal
from uuid import UUID

from aideo_serv.models.generate import PromptBlock
from aideo_serv.models.task import Task
from pydantic import BaseModel, Field


class ImageEditMode(StrEnum):
    """How the base image is edited."""

    COMPOSITE = "composite"  # 合图：把 reference 合成到 base 指定区域
    REPLACE_CHARACTER = "replace_character"  # 角色替换：替换 mask 区域内角色
    INPAINTING = "inpainting"  # 局部重绘：重绘 mask 区域
    STYLE_TRANSFER = "style_transfer"  # 风格迁移：把 reference 风格应用到 base


class MaskRegion(BaseModel):
    """A rectangular selection in relative (0.0–1.0) image coordinates."""

    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    width: float = Field(ge=0.0, le=1.0)
    height: float = Field(ge=0.0, le=1.0)
    label: str | None = None


class EditImageRequest(BaseModel):
    """AI image edit — composite / replace_character / inpainting / style_transfer."""

    project_id: UUID | None = None
    mode: ImageEditMode
    base_image: UUID  # asset_id of the base image
    reference_images: list[UUID] = Field(default_factory=list)  # asset_id[]
    mask_regions: list[MaskRegion] = Field(default_factory=list)
    prompt_blocks: list[PromptBlock] = Field(default_factory=list)
    language: str | None = None  # zh/en/ja/ko/auto
    ai_provider: str | None = None  # override default AI provider per-request


class EditImageResponse(BaseModel):
    """Returned after a successful /canvas/edit-image submission."""

    task_id: UUID
    task: Task


class UpscaleRequest(BaseModel):
    """Image super-resolution request."""

    asset_id: UUID  # source image asset_id
    scale: Literal[2, 4] = 2  # upscale factor


class UpscaleResponse(BaseModel):
    """Returned after a successful /canvas/upscale submission."""

    task_id: UUID
    task: Task
