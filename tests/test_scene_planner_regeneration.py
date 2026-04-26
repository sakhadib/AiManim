from math2manim.core.planner.scene_planner import ScenePlanner
from math2manim.providers.base import LLMProvider


class _RetryPlannerProvider(LLMProvider):
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, prompt: str, *, model: str | None = None, system_prompt: str | None = None) -> str:
        self.calls += 1
        if self.calls == 1:
            return "not json"
        return (
            '{"scenes":[{'
            '"id":1,"goal":"Intro","narration":"n1","duration_sec":4.0,'
            '"visual_elements":["axis"],"animation_count":2},'
            '{"id":2,"goal":"Step","narration":"n2","duration_sec":4.5,'
            '"visual_elements":["vector"],"animation_count":2},'
            '{"id":3,"goal":"Example","narration":"n3","duration_sec":5.0,'
            '"visual_elements":["matrix"],"animation_count":2}]}'
        )


def test_planner_regenerates_after_invalid_json() -> None:
    provider = _RetryPlannerProvider()
    planner = ScenePlanner(provider=provider, model="fake")

    plan = planner.plan("Explain eigen vectors", min_scenes=3, max_scenes=6, max_regeneration_attempts=3)

    assert len(plan.scenes) == 3
    assert provider.calls == 2


class _AlwaysBadPlannerProvider(LLMProvider):
    def generate(self, prompt: str, *, model: str | None = None, system_prompt: str | None = None) -> str:
        return "still not json"


def test_planner_fails_after_max_regeneration_attempts() -> None:
    planner = ScenePlanner(provider=_AlwaysBadPlannerProvider(), model="fake")

    try:
        planner.plan("Explain eigen vectors", min_scenes=2, max_scenes=4, max_regeneration_attempts=2)
    except RuntimeError as error:
        assert "Planner failed after regeneration attempts" in str(error)
        return

    assert False, "Expected RuntimeError after planner regeneration retries are exhausted"
