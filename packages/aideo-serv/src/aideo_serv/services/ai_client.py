"""Unified AI client with multi-provider support.

Supports per-request provider selection so the iPad frontend can choose
which AI backend to use for each API call.

Configured providers (``AIDEO_AI_PROVIDERS`` env, JSON):
    [{"name":"openai","base_url":"https://api.openai.com/v1","api_key":"sk-...","model":"gpt-4o"}]

Or legacy flat config for a single provider:
    AIDEO_AI_PROVIDER=openai
    AIDEO_AI_BASE_URL=https://api.openai.com/v1
    AIDEO_AI_API_KEY=sk-...
    AIDEO_AI_MODEL=gpt-4o
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx

from aideo_serv.config import Settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Provider ABC
# ---------------------------------------------------------------------------


class AIProvider(ABC):
    """Abstract backend for LLM calls."""

    def __init__(self, name: str, model: str = ""):
        self.name = name
        self.model = model

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> str:
        ...

    @abstractmethod
    async def chat_json(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs,
    ) -> dict:
        ...

    def info(self) -> dict:
        """Return provider metadata for the frontend."""
        return {"name": self.name, "model": self.model}


# ---------------------------------------------------------------------------
# Stub provider
# ---------------------------------------------------------------------------


class StubProvider(AIProvider):
    """Mock responses for development without an API key."""

    def __init__(self):
        super().__init__(name="stub", model="mock")

    async def chat(self, messages, model=None, temperature=0.7, max_tokens=4096, **kwargs) -> str:
        user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
        return f"[Stub] Input: {user_msg[:200]}"

    async def chat_json(self, messages, model=None, temperature=0.3, max_tokens=4096, **kwargs) -> dict:
        return {"message": "Stub JSON response", "note": "Configure AIDEO_AI_PROVIDER for real AI"}


# ---------------------------------------------------------------------------
# OpenAI-compatible provider
# ---------------------------------------------------------------------------


class OpenAIProvider(AIProvider):
    """Calls any OpenAI-compatible ``/v1/chat/completions`` endpoint.

    Works with: OpenAI, Azure, vLLM, Ollama, LM Studio, Groq, DeepSeek, etc.
    """

    def __init__(self, name: str, base_url: str, api_key: str, model: str = "gpt-4o"):
        super().__init__(name=name, model=model)
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    @property
    def _endpoint(self) -> str:
        return f"{self._base_url}/chat/completions"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def chat(self, messages, model=None, temperature=0.7, max_tokens=4096, **kwargs) -> str:
        payload: dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        payload.update(kwargs)

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(self._endpoint, headers=self._headers(), json=payload)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def chat_json(self, messages, model=None, temperature=0.3, max_tokens=4096, **kwargs) -> dict:
        payload: dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        payload.update(kwargs)

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(self._endpoint, headers=self._headers(), json=payload)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())

    def info(self) -> dict:
        return {
            "name": self.name,
            "model": self.model,
            "base_url": self._base_url,
            "has_auth": bool(self._api_key),
        }


# ---------------------------------------------------------------------------
# Runtime provider
# ---------------------------------------------------------------------------


class RuntimeProvider(AIProvider):
    """Routes LLM requests to aideo-runtime."""

    def __init__(self):
        super().__init__(name="runtime", model="aideo-runtime")

    async def chat(self, messages, model=None, temperature=0.7, max_tokens=4096, **kwargs) -> str:
        from aideo_serv.dependencies import get_inference_manager

        mgr = get_inference_manager()
        user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
        if not mgr.is_connected("aideo-runtime"):
            return f"[Runtime: not connected] {user_msg[:200]}"
        return f"[Runtime: chat pending] {user_msg[:200]}"

    async def chat_json(self, messages, model=None, temperature=0.3, max_tokens=4096, **kwargs) -> dict:
        text = await self.chat(messages, model, temperature, max_tokens, **kwargs)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw_response": text}


# ---------------------------------------------------------------------------
# AIClient — multi-provider registry
# ---------------------------------------------------------------------------


class AIClient:
    """Holds all configured AI providers, supports per-request selection.

    Providers are configured via ``AIDEO_AI_PROVIDERS`` (JSON array) or
    the legacy flat ``AIDEO_AI_PROVIDER`` / ``AIDEO_AI_BASE_URL`` env vars.
    """

    def __init__(self, settings: Settings | None = None):
        self._settings = settings or Settings()
        self._providers: dict[str, AIProvider] = {}
        self._default_name: str = "stub"
        self._init_providers()

    def _init_providers(self) -> None:
        """Parse config and build provider instances."""
        s = self._settings

        # Always register stub as fallback
        stub = StubProvider()
        self._providers["stub"] = stub

        # --- Multi-provider JSON config (preferred) ---
        providers_json = s.ai_providers
        if providers_json:
            try:
                providers_list: list[dict] = json.loads(providers_json)
            except (json.JSONDecodeError, TypeError):
                providers_list = []

            for cfg in providers_list:
                name = cfg.get("name", "")
                provider_type = cfg.get("type", "openai")
                if not name:
                    continue

                if provider_type == "openai":
                    provider = OpenAIProvider(
                        name=name,
                        base_url=cfg.get("base_url", s.ai_base_url),
                        api_key=cfg.get("api_key", s.ai_api_key),
                        model=cfg.get("model", s.ai_model),
                    )
                elif provider_type == "runtime":
                    provider = RuntimeProvider()
                else:
                    continue

                self._providers[name] = provider
                logger.info("Registered AI provider: %s (%s)", name, provider_type)

            if providers_list:
                self._default_name = providers_list[0].get("name", "stub")
            return

        # --- Legacy single-provider config ---
        provider_type = s.ai_provider
        if provider_type == "runtime":
            provider = RuntimeProvider()
            self._providers["runtime"] = provider
            self._default_name = "runtime"
        elif provider_type not in ("", "stub") and s.ai_api_key:
            # Any other value (openai, deepseek, groq, ...) → OpenAI-compatible
            provider = OpenAIProvider(
                name=provider_type,
                base_url=s.ai_base_url,
                api_key=s.ai_api_key,
                model=s.ai_model,
            )
            self._providers[provider_type] = provider
            self._default_name = provider_type
        else:
            self._default_name = "stub"

    # ------------------------------------------------------------------
    # Provider access
    # ------------------------------------------------------------------

    @property
    def default_name(self) -> str:
        return self._default_name

    def get_provider(self, name: str | None = None) -> AIProvider:
        """Get a provider by name. Falls back to default if name is None or unknown."""
        if name is None:
            name = self._default_name
        provider = self._providers.get(name)
        if provider is None:
            logger.warning("Unknown provider '%s', falling back to %s", name, self._default_name)
            provider = self._providers.get(self._default_name, self._providers["stub"])
        return provider

    def list_providers(self) -> list[dict]:
        """Return metadata for all registered providers (for the frontend)."""
        return [
            {"name": p.name, "model": p.model, "is_default": (p.name == self._default_name)}
            for p in self._providers.values()
        ]

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    async def chat(
        self,
        messages: list[dict[str, str]],
        provider: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> str:
        return await self.get_provider(provider).chat(
            messages, model=model, temperature=temperature, max_tokens=max_tokens, **kwargs
        )

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        provider: str | None = None,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs,
    ) -> dict:
        return await self.get_provider(provider).chat_json(
            messages, model=model, temperature=temperature, max_tokens=max_tokens, **kwargs
        )


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_ai_client: AIClient | None = None


def get_ai_client() -> AIClient:
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client


def set_ai_client(client: AIClient) -> None:
    global _ai_client
    _ai_client = client
