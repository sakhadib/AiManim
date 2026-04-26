from pathlib import Path

import pytest

from math2manim.providers.base import LLMProvider
from math2manim.workflows import langgraph_flow


class FakeProvider(LLMProvider):
    def generate(self, prompt: str, *, model: str | None = None, system_prompt: str | None = None) -> str:
        return "{}"


def test_pipeline_voiceover_preflight_reports_missing_dependencies(monkeypatch) -> None:
    monkeypatch.setattr(langgraph_flow, "manim_available", lambda: True)
    monkeypatch.setattr(langgraph_flow, "ffmpeg_available", lambda: True)
    monkeypatch.setattr(langgraph_flow, "manim_voiceover_available", lambda provider: False)

    with pytest.raises(RuntimeError, match="Voiceover mode requires manim-voiceover"):
        langgraph_flow.run_pipeline(
            user_prompt="Explain circle",
            provider=FakeProvider(),
            model=None,
            output_file=Path("outputs/final.mp4"),
            max_retries=1,
            keep_scenes=False,
            enable_voiceover=True,
            voice_provider="gtts",
        )
