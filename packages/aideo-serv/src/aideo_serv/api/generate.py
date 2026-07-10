"""POST /generate — structured canvas submission endpoint."""

import asyncio
import logging
from uuid import UUID

from aideo_serv.config import Settings
from aideo_serv.dependencies import (
    get_ai_client,
    get_project_service,
    get_task_service,
)
from aideo_serv.models.error import error_response
from aideo_serv.models.generate import GenerateRequest, GenerateResponse
from aideo_serv.models.task import TaskStatus
from aideo_serv.services.ai_client import AIClient
from aideo_serv.services.prompt_serializer import serialize_prompt
from aideo_serv.services.project_service import ProjectService
from aideo_serv.services.task_service import TaskService
from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)
generate_router = APIRouter(tags=["generate"])

# System prompt for AI prompt enhancement
_ENHANCE_SYSTEM = """You are an expert prompt engineer for AI video generation.
Enhance the given prompt by adding visual details, lighting, camera direction,
and composition notes. Keep the original structure but enrich each section.
Preserve all section headers exactly as-is. Do NOT add new sections.
Return ONLY the enhanced prompt text, no explanations or markdown fences."""

# Language instruction for prompt enhancement
_ENHANCE_LANG = {
    "zh": "Write ALL enhanced content in Chinese (简体中文).",
    "en": "Write ALL enhanced content in English.",
    "ja": "Write ALL enhanced content in Japanese (日本語).",
    "ko": "Write ALL enhanced content in Korean (한국어).",
}
_ENHANCE_AUTO_LANG = "You MUST write the enhanced prompt in the same language as the input prompt. Detect the language from the prompt and use it for all enhanced content."

# Reuse the inference submission helper from tasks.py
from aideo_serv.api.tasks import _submit_to_inference


@generate_router.post("/generate", status_code=201)
async def generate(
    payload: GenerateRequest,
    task_svc: TaskService = Depends(get_task_service),
    proj_svc: ProjectService = Depends(get_project_service),
    ai: AIClient = Depends(get_ai_client),
):
    """Submit a structured canvas generation request.

    The server serializes PromptBlocks → flat prompt, optionally enhances
    it via the configured AI provider, creates a task, and submits to
    the inference service.
    """
    # Validate project exists if provided
    if payload.project_id is not None:
        try:
            proj_svc.get(payload.project_id)
        except LookupError:
            raise HTTPException(
                status_code=404,
                detail=error_response(
                    "RESOURCE_NOT_FOUND",
                    f"Project {payload.project_id} not found",
                )[0],
            )

    # Serialize prompt from structured blocks
    flat_prompt = serialize_prompt(payload.blocks, payload.connections)

    # Append AI enhance context
    if payload.ai_enhance_context:
        enhance_text = "\n".join(payload.ai_enhance_context)
        flat_prompt = f"{flat_prompt}\n\nAdditional Context:\n{enhance_text}"

    # Append upstream text results
    if payload.upstream_context:
        upstream_lines = []
        for u in payload.upstream_context:
            if u.text:
                upstream_lines.append(f"[Upstream {u.content_type}]: {u.text}")
        if upstream_lines:
            flat_prompt = f"{flat_prompt}\n\nUpstream Results:\n" + "\n".join(upstream_lines)

    # Optionally enhance prompt via AI (only when using a real provider)
    enhanced_prompt = flat_prompt
    effective_provider = payload.ai_provider or ai.default_name
    if effective_provider != "stub":
        # Build system prompt with language instruction (normalize zh-CN → zh)
        lang = payload.language[:2] if payload.language else None
        if lang and lang in _ENHANCE_LANG:
            enhance_system = f"{_ENHANCE_SYSTEM}\n\n{_ENHANCE_LANG[lang]}"
        else:
            enhance_system = f"{_ENHANCE_SYSTEM}\n\n{_ENHANCE_AUTO_LANG}"

        try:
            enhanced_prompt = await ai.chat(
                messages=[
                    {"role": "system", "content": enhance_system},
                    {"role": "user", "content": f"Enhance this prompt:\n\n{flat_prompt}"},
                ],
                provider=effective_provider,
                temperature=0.3,
                max_tokens=4096,
            )
            logger.info("AI prompt enhancement (%s): %d → %d chars",
                        effective_provider, len(flat_prompt), len(enhanced_prompt))
        except Exception:
            logger.exception("AI prompt enhancement failed, using raw prompt")
            enhanced_prompt = flat_prompt

    # Build GenerationParams dict
    params_dict = {}
    op = payload.output_params
    if op.duration is not None:
        params_dict["duration"] = op.duration
    if op.resolution is not None:
        params_dict["resolution"] = op.resolution
    if op.style is not None:
        params_dict["style"] = op.style
    if op.seed is not None:
        params_dict["seed"] = op.seed
    if op.fps is not None:
        params_dict["fps"] = op.fps
    if op.cfg_scale is not None:
        params_dict["cfg_scale"] = op.cfg_scale
    if op.steps is not None:
        params_dict["steps"] = op.steps

    # Build the prompt_structured snapshot
    prompt_structured = {
        "blocks": [b.model_dump(mode="json") for b in payload.blocks],
        "connections": [c.model_dump(mode="json") for c in payload.connections],
        "reference_assets": [r.model_dump(mode="json") for r in payload.reference_assets],
        "upstream_context": [u.model_dump(mode="json") for u in payload.upstream_context],
        "ai_enhance_context": payload.ai_enhance_context,
        "output_params": params_dict,
    }

    # Create task
    task_type = "video_generation" if payload.output_content_type == "video" else "text_conversation"
    task = task_svc.create(
        prompt=flat_prompt,
        params=params_dict or None,
        task_type=task_type,
        project_id=payload.project_id,
        output_node_id=payload.output_node_id,
        prompt_structured=prompt_structured,
    )

    # Increment project task_count
    if payload.project_id is not None:
        proj_svc.increment_task_count(payload.project_id)

    # Submit to inference (fire and forget)
    asyncio.create_task(
        _submit_to_inference(
            task.id, flat_prompt, params_dict or None, task_type
        )
    )

    return GenerateResponse(task_id=task.id, task=task)
