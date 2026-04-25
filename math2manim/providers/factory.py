"""Provider factory and registry."""

from __future__ import annotations

from .base import LLMProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider


def get_provider(name: str) -> LLMProvider:
    """Create a provider by user-facing name."""

    normalized = name.strip().lower()
    if normalized == "openai":
        return OpenAIProvider()
    if normalized == "gemini":
        return GeminiProvider()
    raise ValueError(f"Unsupported provider: {name}")


def supported_providers() -> list[str]:
    return ["openai", "gemini"]
