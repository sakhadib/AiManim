"""Provider abstractions for LLM backends."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Common LLM provider interface."""

    @abstractmethod
    def generate(self, prompt: str, *, model: str | None = None, system_prompt: str | None = None) -> str:
        """Generate completion text for a prompt."""
        raise NotImplementedError
