"""Canvas Assist request/response models — structure, complete, inspire."""

from pydantic import BaseModel, Field

from aideo_serv.models.generate import BlockType, GenerationParams, PromptBlock


# ---------------------------------------------------------------------------
# POST /canvas/structure
# ---------------------------------------------------------------------------


class StructureRequest(BaseModel):
    """Free-text description → typed PromptBlocks."""

    description: str = Field(min_length=1, max_length=4096)
    ai_provider: str | None = None  # override default AI provider per-request


class StructureResponse(BaseModel):
    """Decomposed prompt cards ready to drop on canvas."""

    blocks: list[PromptBlock]


# ---------------------------------------------------------------------------
# POST /canvas/complete
# ---------------------------------------------------------------------------


class CompleteRequest(BaseModel):
    """Context + existing blocks → completion suggestions."""

    context: str = Field(min_length=1, max_length=4096)
    existing_blocks: list[PromptBlock] = Field(default_factory=list)
    mode: str = "completion"  # completion | suggestion
    ai_provider: str | None = None  # override default AI provider per-request


class CompleteSuggestion(BaseModel):
    """A group of blocks suggested to fill a gap or replace existing ones."""

    title: str
    blocks: list[PromptBlock]


class CompleteResponse(BaseModel):
    """List of completion/suggestion groups."""

    suggestions: list[CompleteSuggestion]


# ---------------------------------------------------------------------------
# POST /canvas/inspire
# ---------------------------------------------------------------------------


class InspireRequest(BaseModel):
    """Theme → inspiration templates with pre-filled blocks."""

    theme: str = Field(min_length=1, max_length=512)
    ai_provider: str | None = None  # override default AI provider per-request


class InspireTheme(BaseModel):
    """A single inspiration template."""

    title: str
    prompt: str
    style_hint: str
    tags: list[str] = Field(default_factory=list)
    blocks: list[PromptBlock]


class InspireResponse(BaseModel):
    """List of inspiration themes."""

    themes: list[InspireTheme]
