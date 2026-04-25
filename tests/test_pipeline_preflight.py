from pathlib import Path

import pytest

from math2manim.providers.base import LLMProvider
from math2manim.workflows import langgraph_flow


class FakeProvider(LLMProvider):
    def generate(self, prompt: str, *, model: str | None = None, system_prompt: str | None = None) -> str:
        return "{}"


def test_pipeline_preflight_reports_missing_render_tools(monkeypatch) -> None:
    monkeypatch.setattr(langgraph_flow, "manim_available", lambda: False)
    monkeypatch.setattr(langgraph_flow, "ffmpeg_available", lambda: False)

    with pytest.raises(RuntimeError, match="Missing required render tool"):
        langgraph_flow.run_pipeline(
            user_prompt="Explain circle",
            provider=FakeProvider(),
            model=None,
            output_file=Path("outputs/final.mp4"),
            max_retries=1,
            keep_scenes=False,
        )
