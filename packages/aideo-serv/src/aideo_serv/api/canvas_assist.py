"""Canvas Assist endpoints — LLM-powered via unified AI client.

When ``AIDEO_AI_PROVIDER=openai`` (with valid API key), uses real LLM.
When ``AIDEO_AI_PROVIDER=stub`` (default), falls back to mock responses.
When ``AIDEO_AI_PROVIDER=runtime``, routes to aideo-runtime chat capability.
"""

import json
import logging
from uuid import uuid4

from aideo_serv.dependencies import get_ai_client
from aideo_serv.models.assist import (
    CompleteRequest,
    CompleteResponse,
    CompleteSuggestion,
    InspireRequest,
    InspireResponse,
    InspireTheme,
    StructureRequest,
    StructureResponse,
)
from aideo_serv.models.generate import BlockType, GenerationParams, PromptBlock
from aideo_serv.services.ai_client import AIClient
from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)
canvas_router = APIRouter(prefix="/canvas", tags=["canvas"])

# ---------------------------------------------------------------------------
# Prompt templates for structured LLM calls
# ---------------------------------------------------------------------------

# Language instruction map — appended to system prompts
_LANG_MAP = {
    "zh": "ALL responses MUST be in Chinese (简体中文). Block content, titles, and descriptions must be in Chinese.",
    "en": "ALL responses MUST be in English.",
    "ja": "ALL responses MUST be in Japanese (日本語). Block content, titles, and descriptions must be in Japanese.",
    "ko": "ALL responses MUST be in Korean (한국어). Block content, titles, and descriptions must be in Korean.",
}
_AUTO_LANG_INSTRUCTION = "You MUST respond in the same language as the user's input. Detect the language from their description and use it for ALL block content, titles, and descriptions."


def _make_system(base_prompt: str, language: str | None) -> str:
    """Append language instruction. 'auto'/None → AI auto-detects from input."""
    if language and language != "auto" and language in _LANG_MAP:
        return f"{base_prompt}\n\n{_LANG_MAP[language]}"
    # auto or unset → let AI detect
    return f"{base_prompt}\n\n{_AUTO_LANG_INSTRUCTION}"


STRUCTURE_SYSTEM = """You are an expert prompt engineer for AI video generation.
Decompose the user's description into typed PromptBlocks.

Available block types: scene, character, action, camera, mood, style, custom

Rules:
- scene: the environment/location/setting — always include one
- character: who is in the scene (skip if none described)
- action: what is happening / movement
- camera: shot direction, angle, movement
- mood: emotional tone, atmosphere
- style: visual aesthetic, art direction
- custom: anything else

Return ONLY valid JSON. Do NOT include markdown fences or commentary.
Format: {"blocks": [{"type": "scene", "content": "..."}, ...]}

Example:
Input: "A lone knight rides through a misty forest at dawn"
Output: {"blocks": [{"type": "scene", "content": "Misty forest at dawn, tall ancient trees, soft golden light filtering through fog"}, {"type": "character", "content": "Lone knight in weathered silver armor, dark cloak, riding a black stallion"}, {"type": "action", "content": "Riding slowly through the forest, mist swirling around the horse's legs"}, {"type": "camera", "content": "Wide tracking shot, low angle following the knight"}, {"type": "mood", "content": "Mysterious, somber, heroic"}, {"type": "style", "content": "Cinematic fantasy, atmospheric lighting"}]}"""


COMPLETE_SYSTEM = """You are an expert prompt engineer for AI video generation.
Given existing prompt blocks, suggest complementary blocks to enrich the scene.

Return ONLY valid JSON. Do NOT include markdown fences or commentary.
Format: {"suggestions": [{"title": "Short description", "blocks": [{"type": "...", "content": "..."}]}]}

Suggest 1-3 groups of blocks. Each group should add missing dimensions (camera, mood, style, action, character)."""


INSPIRE_SYSTEM = """You are a creative director for AI video generation.
Given a theme, generate 2 inspiring scene templates with pre-filled blocks.

Return ONLY valid JSON. Do NOT include markdown fences or commentary.
Format: {"themes": [{"title": "...", "prompt": "...", "style_hint": "...", "tags": [...], "blocks": [{"type": "...", "content": "..."}]}]}

Each theme should have 2-4 blocks (scene + style + camera/mood). Use diverse perspectives."""


# ---------------------------------------------------------------------------
# Stub fallback (used when AI returns unparseable response)
# ---------------------------------------------------------------------------


def _stub_structure(description: str) -> list[PromptBlock]:
    """Fallback stub for /canvas/structure."""
    description_lower = description.lower()
    blocks: list[PromptBlock] = []

    has_character = any(w in description_lower for w in [
        "samurai", "warrior", "princess", "king", "queen", "robot",
        "character", "man", "woman", "person", "girl", "boy",
        "knight", "mage", "wizard", "hero",
    ])
    has_action = any(w in description_lower for w in [
        "walking", "running", "standing", "fighting", "sitting",
        "flying", "swimming", "dancing", "riding", "holding",
    ])

    blocks.append(PromptBlock(
        id=uuid4(), type=BlockType.SCENE,
        content=f"{description.strip()} — wide establishing shot",
    ))
    if has_character:
        blocks.append(PromptBlock(
            id=uuid4(), type=BlockType.CHARACTER,
            content="Detailed character design with distinctive silhouette and costume",
        ))
    if has_action:
        blocks.append(PromptBlock(
            id=uuid4(), type=BlockType.ACTION,
            content="Dynamic motion with clear posing and weight",
        ))
    blocks.append(PromptBlock(
        id=uuid4(), type=BlockType.STYLE,
        content="Cinematic lighting, high detail, professional composition",
        params=GenerationParams(style="cinematic"),
    ))
    blocks.append(PromptBlock(
        id=uuid4(), type=BlockType.MOOD,
        content="Atmospheric and immersive",
    ))
    return blocks


def _stub_complete(context: str) -> list[CompleteSuggestion]:
    """Fallback stub for /canvas/complete."""
    return [
        CompleteSuggestion(
            title="Add visual style direction",
            blocks=[
                PromptBlock(id=uuid4(), type=BlockType.STYLE,
                    content="Cinematic lighting with dramatic shadows, film grain, 35mm lens",
                    params=GenerationParams(style="cinematic")),
                PromptBlock(id=uuid4(), type=BlockType.MOOD,
                    content="Epic and grand, sense of wonder and scale"),
            ],
        ),
        CompleteSuggestion(
            title="Add camera direction",
            blocks=[
                PromptBlock(id=uuid4(), type=BlockType.CAMERA,
                    content="Slow dolly-in from wide to medium shot, shallow depth of field"),
            ],
        ),
    ]


def _stub_inspire(theme: str) -> list[InspireTheme]:
    """Fallback stub for /canvas/inspire."""
    return [
        InspireTheme(
            title=f"{theme.title()} — Grand Vista",
            prompt=f"A breathtaking panoramic view of {theme}, with dramatic lighting and rich atmospheric details",
            style_hint="Epic scale, sweeping camera movement, golden hour lighting",
            tags=["epic", "landscape", "cinematic"],
            blocks=[
                PromptBlock(id=uuid4(), type=BlockType.SCENE, scene_tag=0,
                    content=f"Grand panoramic view of {theme}, dramatic wide shot"),
                PromptBlock(id=uuid4(), type=BlockType.STYLE,
                    content="Epic cinematic, sweeping scale, golden hour",
                    params=GenerationParams(style="cinematic")),
                PromptBlock(id=uuid4(), type=BlockType.CAMERA, scene_tag=0,
                    content="Slow crane up from low angle to reveal full vista"),
            ],
        ),
        InspireTheme(
            title=f"{theme.title()} — Intimate Detail",
            prompt=f"Close-up details of {theme}, revealing textures, colors, and hidden beauty in the small moments",
            style_hint="Macro detail, shallow depth of field, soft bokeh",
            tags=["intimate", "detail", "atmospheric"],
            blocks=[
                PromptBlock(id=uuid4(), type=BlockType.SCENE, scene_tag=0,
                    content=f"Intimate close-up details within {theme}, macro perspective"),
                PromptBlock(id=uuid4(), type=BlockType.STYLE,
                    content="Shallow depth of field, soft bokeh, warm tones",
                    params=GenerationParams(style="realistic")),
                PromptBlock(id=uuid4(), type=BlockType.MOOD, scene_tag=0,
                    content="Peaceful, contemplative, intimate"),
            ],
        ),
    ]


# ---------------------------------------------------------------------------
# Parsing helpers — convert AI JSON blocks to typed PromptBlocks
# ---------------------------------------------------------------------------


def _parse_ai_blocks(raw_blocks: list[dict]) -> list[PromptBlock]:
    """Convert raw AI JSON block dicts to validated PromptBlock models."""
    blocks: list[PromptBlock] = []
    valid_types = {bt.value for bt in BlockType}
    for b in raw_blocks:
        block_type = b.get("type", "custom")
        if block_type not in valid_types:
            block_type = "custom"
        # Parse params if present
        params_dict = b.get("params", {})
        params = GenerationParams(
            duration=params_dict.get("duration"),
            resolution=params_dict.get("resolution"),
            style=params_dict.get("style"),
            seed=params_dict.get("seed"),
            fps=params_dict.get("fps"),
            cfg_scale=params_dict.get("cfg_scale"),
            steps=params_dict.get("steps"),
        )
        blocks.append(PromptBlock(
            id=uuid4(),
            type=BlockType(block_type),
            content=str(b.get("content", "")),
            scene_tag=b.get("scene_tag"),
            params=params,
        ))
    return blocks


# ---------------------------------------------------------------------------
# POST /canvas/structure
# ---------------------------------------------------------------------------


@canvas_router.post("/structure")
async def structure(
    request: StructureRequest,
    ai: AIClient = Depends(get_ai_client),
) -> StructureResponse:
    """Decompose a free-text description into typed PromptBlocks.

    Uses the configured AI provider when available, falls back to
    rule-based stub when the provider returns unparseable output.
    """
    try:
        result = await ai.chat_json(
            messages=[
                {"role": "system", "content": _make_system(STRUCTURE_SYSTEM, request.language)},
                {"role": "user", "content": request.description},
            ],
            provider=request.ai_provider,
            temperature=0.3,
            max_tokens=2048,
        )
        raw_blocks = result.get("blocks", [])
        if raw_blocks:
            blocks = _parse_ai_blocks(raw_blocks)
            logger.info("AI structure returned %d blocks", len(blocks))
            return StructureResponse(blocks=blocks)
    except Exception:
        logger.exception("AI structure failed, using stub fallback")

    # Fallback to stub
    blocks = _stub_structure(request.description)
    return StructureResponse(blocks=blocks)


# ---------------------------------------------------------------------------
# POST /canvas/complete
# ---------------------------------------------------------------------------


@canvas_router.post("/complete")
async def complete(
    request: CompleteRequest,
    ai: AIClient = Depends(get_ai_client),
) -> CompleteResponse:
    """Suggest missing block types or alternative content.

    Uses the configured AI provider when available, falls back to
    rule-based stub when the provider returns unparseable output.
    """
    # Build context message
    existing_info = ""
    if request.existing_blocks:
        existing_info = "\nExisting blocks:\n" + "\n".join(
            f"- [{b.type.value}] {b.content}" for b in request.existing_blocks
        )

    user_msg = f"Context: {request.context}\nMode: {request.mode}{existing_info}"

    try:
        result = await ai.chat_json(
            messages=[
                {"role": "system", "content": _make_system(COMPLETE_SYSTEM, request.language)},
                {"role": "user", "content": user_msg},
            ],
            provider=request.ai_provider,
            temperature=0.5,
            max_tokens=2048,
        )
        raw_suggestions = result.get("suggestions", [])
        if raw_suggestions:
            suggestions: list[CompleteSuggestion] = []
            for s in raw_suggestions:
                suggestions.append(CompleteSuggestion(
                    title=str(s.get("title", "Suggestion")),
                    blocks=_parse_ai_blocks(s.get("blocks", [])),
                ))
            logger.info("AI complete returned %d suggestions", len(suggestions))
            return CompleteResponse(suggestions=suggestions)
    except Exception:
        logger.exception("AI complete failed, using stub fallback")

    # Fallback to stub
    suggestions = _stub_complete(request.context)
    return CompleteResponse(suggestions=suggestions)


# ---------------------------------------------------------------------------
# POST /canvas/inspire
# ---------------------------------------------------------------------------


@canvas_router.post("/inspire")
async def inspire(
    request: InspireRequest,
    ai: AIClient = Depends(get_ai_client),
) -> InspireResponse:
    """Generate inspiration templates from a theme.

    Uses the configured AI provider when available, falls back to
    rule-based stub when the provider returns unparseable output.
    """
    try:
        result = await ai.chat_json(
            messages=[
                {"role": "system", "content": _make_system(INSPIRE_SYSTEM, request.language)},
                {"role": "user", "content": f"Theme: {request.theme}"},
            ],
            provider=request.ai_provider,
            temperature=0.7,
            max_tokens=2048,
        )
        raw_themes = result.get("themes", [])
        if raw_themes:
            themes: list[InspireTheme] = []
            for t in raw_themes:
                themes.append(InspireTheme(
                    title=str(t.get("title", "Theme")),
                    prompt=str(t.get("prompt", "")),
                    style_hint=str(t.get("style_hint", "")),
                    tags=[str(tag) for tag in t.get("tags", [])],
                    blocks=_parse_ai_blocks(t.get("blocks", [])),
                ))
            logger.info("AI inspire returned %d themes", len(themes))
            return InspireResponse(themes=themes)
    except Exception:
        logger.exception("AI inspire failed, using stub fallback")

    # Fallback to stub
    themes = _stub_inspire(request.theme)
    return InspireResponse(themes=themes)
