from math2manim.core.codegen.manim_codegen import ManimCodeGenerator
from math2manim.core.planner.scene_planner import ScenePlanner
from math2manim.providers.base import LLMProvider


class FakeProvider(LLMProvider):
    def generate(self, prompt: str, *, model: str | None = None, system_prompt: str | None = None) -> str:
        if "top-level key 'scenes'" in prompt:
            return (
                '{"scenes":[{'
                '"id":1,"goal":"Intro","narration":"n1","duration_sec":4.0,'
                '"visual_elements":["axes","point"],"animation_count":2},'
                '{"id":2,"goal":"Update","narration":"n2","duration_sec":4.5,'
                '"visual_elements":["line"],"animation_count":2}]}'
            )
        return "title = Text(\"Gradient Descent\")\nself.play(Write(title))\nself.wait(1)"


def test_planner_and_codegen_dry_run_smoke() -> None:
    provider = FakeProvider()
    planner = ScenePlanner(provider=provider, model="fake")
    codegen = ManimCodeGenerator(provider=provider, model="fake")

    plan = planner.plan("Explain gradient descent")
    assert len(plan.scenes) == 2

    for scene in plan.scenes:
        body = codegen.generate_construct_body(scene)
        assert "import " not in body.lower()
        assert "class " not in body.lower()
