"""Canvas generation request/response models for POST /generate."""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from aideo_serv.models.task import Task


# ---------------------------------------------------------------------------
# Block types and prompt cards
# ---------------------------------------------------------------------------


class BlockType(StrEnum):
    """Seven prompt-card types matching the iPad PromptBlock.BlockType."""

    SCENE = "scene"
    CHARACTER = "character"
    ACTION = "action"
    STYLE = "style"
    CAMERA = "camera"
    MOOD = "mood"
    CUSTOM = "custom"


class GenerationParams(BaseModel):
    """Per-generation parameters — all optional, client sends only overrides."""

    duration: int | None = None
    resolution: str | None = None
    style: str | None = None
    seed: int | None = None
    fps: int | None = None
    cfg_scale: float | None = None
    steps: int | None = None


class PromptBlock(BaseModel):
    """A single prompt card from the canvas, 1:1 with iPad PromptBlock."""

    id: UUID
    type: BlockType
    content: str = Field(min_length=1, max_length=4096)
    scene_tag: int | None = None
    params: GenerationParams = Field(default_factory=GenerationParams)


class BlockConnection(BaseModel):
    """Directed edge between any two canvas nodes."""

    source_id: UUID
    target_id: UUID


# ---------------------------------------------------------------------------
# Reference assets and upstream context
# ---------------------------------------------------------------------------


class ReferenceAssetUsage(StrEnum):
    """How a reference asset is used in generation."""

    STYLE_REFERENCE = "style_reference"
    CHARACTER_REFERENCE = "character_reference"
    BACKGROUND = "background"
    MOTION_REFERENCE = "motion_reference"


class ReferenceAsset(BaseModel):
    """Reference to an already-uploaded asset (by asset_id, not base64)."""

    asset_id: UUID
    usage: ReferenceAssetUsage


class UpstreamResult(BaseModel):
    """Output from an upstream MediaOutputNode, fed as context."""

    node_id: UUID
    content_type: str  # video | image | text
    text: str | None = None
    asset_id: UUID | None = None


# ---------------------------------------------------------------------------
# Generate request / response
# ---------------------------------------------------------------------------


class GenerateRequest(BaseModel):
    """Structured canvas submission — server-side prompt serialization.

    Corresponds to the iPad's ``collectInputs()`` BFS trace-back result,
    but with asset references instead of inline base64 blobs.
    """

    project_id: UUID | None = None
    output_node_id: UUID
    output_content_type: str  # video | image | text
    blocks: list[PromptBlock] = Field(min_length=1)
    connections: list[BlockConnection] = Field(default_factory=list)
    reference_assets: list[ReferenceAsset] = Field(default_factory=list)
    upstream_context: list[UpstreamResult] = Field(default_factory=list)
    ai_enhance_context: list[str] = Field(default_factory=list)
    output_params: GenerationParams = Field(default_factory=GenerationParams)
    ai_provider: str | None = None  # override default AI provider per-request
    language: str | None = None  # zh/en/ja/ko/auto — AI response language


class GenerateResponse(BaseModel):
    """Returned after a successful /generate submission."""

    task_id: UUID
    task: Task
