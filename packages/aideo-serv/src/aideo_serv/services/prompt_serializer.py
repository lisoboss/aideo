"""Server-side prompt serialization from structured canvas blocks."""

from aideo_serv.models.generate import BlockConnection, PromptBlock


def serialize_prompt(
    blocks: list[PromptBlock],
    connections: list[BlockConnection] | None = None,
) -> str:
    """Convert a sub-graph of PromptBlocks into a flat model prompt string.

    Strategy:
    1. Group blocks by ``scene_tag`` (None → ungrouped).
    2. Within each scene group, order by block type priority.
    3. Emit rich section headers per block type.
    4. Append AI enhance context and upstream text if provided (handled by caller).

    The output format is designed to be human-readable for the LLM while
    carrying all the structural information from the canvas.
    """
    if not blocks:
        return ""

    # ---- group by scene_tag ------------------------------------------------
    grouped: dict[int, list[PromptBlock]] = {}
    ungrouped: list[PromptBlock] = []

    for b in blocks:
        if b.scene_tag is not None:
            grouped.setdefault(b.scene_tag, []).append(b)
        else:
            ungrouped.append(b)

    # ---- type display order ------------------------------------------------
    _type_order: dict[str, int] = {
        "scene": 0,
        "character": 1,
        "action": 2,
        "camera": 3,
        "mood": 4,
        "style": 5,
        "custom": 6,
    }

    def _sort_key(b: PromptBlock) -> int:
        return _type_order.get(b.type.value, 99)

    # ---- type → rich header ------------------------------------------------
    _type_headers: dict[str, str] = {
        "scene": "Scene",
        "character": "Character",
        "action": "Action",
        "camera": "Camera Direction",
        "mood": "Atmosphere & Mood",
        "style": "Visual Style",
        "custom": "Additional Notes",
    }

    parts: list[str] = []

    # ---- emit scene groups -------------------------------------------------
    for tag in sorted(grouped.keys()):
        group = sorted(grouped[tag], key=_sort_key)
        parts.append(f"[Scene {tag + 1}]")
        for b in group:
            header = _type_headers.get(b.type.value, b.type.value.title())
            parts.append(f"{header}: {b.content}")
            # Append inline params if present
            param_str = _format_params(b.params)
            if param_str:
                parts.append(f"  ({param_str})")
        parts.append("")

    # ---- emit ungrouped blocks ---------------------------------------------
    if ungrouped:
        ungrouped.sort(key=_sort_key)
        for b in ungrouped:
            header = _type_headers.get(b.type.value, b.type.value.title())
            parts.append(f"{header}: {b.content}")
            param_str = _format_params(b.params)
            if param_str:
                parts.append(f"  ({param_str})")
        parts.append("")

    return "\n".join(parts).strip()


def _format_params(params) -> str:
    """Format GenerationParams as a compact inline string."""
    pieces = []
    if params.duration is not None:
        pieces.append(f"duration={params.duration}s")
    if params.resolution is not None:
        pieces.append(f"resolution={params.resolution}")
    if params.style is not None:
        pieces.append(f"style={params.style}")
    if params.seed is not None:
        pieces.append(f"seed={params.seed}")
    if params.fps is not None:
        pieces.append(f"fps={params.fps}")
    if params.cfg_scale is not None:
        pieces.append(f"cfg={params.cfg_scale}")
    if params.steps is not None:
        pieces.append(f"steps={params.steps}")
    return ", ".join(pieces) if pieces else ""
