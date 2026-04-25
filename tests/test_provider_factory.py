import pytest

from math2manim.providers.factory import get_provider, supported_providers
from math2manim.providers.gemini_provider import GeminiProvider
from math2manim.providers.openai_provider import OpenAIProvider
from math2manim.providers.openrouter_provider import OpenRouterProvider


def test_supported_providers() -> None:
    assert supported_providers() == ["openrouter", "openai", "gemini"]


def test_factory_openrouter() -> None:
    assert isinstance(get_provider("openrouter"), OpenRouterProvider)


def test_factory_openai() -> None:
    assert isinstance(get_provider("openai"), OpenAIProvider)


def test_factory_gemini() -> None:
    assert isinstance(get_provider("gemini"), GeminiProvider)


def test_factory_invalid_provider() -> None:
    with pytest.raises(ValueError):
        get_provider("unknown")
