"""Constrained Manim code generation."""

from __future__ import annotations

from pathlib import Path

from math2manim.providers.base import LLMProvider
from math2manim.schemas.scene import Scene
from math2manim.templates.manim_template import build_scene_script

FORBIDDEN_SNIPPETS = ["import ", "class ", "from ", "def construct"]


def validate_construct_body(construct_body: str) -> None:
    lowered = construct_body.lower()
    for forbidden in FORBIDDEN_SNIPPETS:
        if forbidden in lowered:
            raise ValueError(f"Generated code contains forbidden snippet: {forbidden.strip()}")


class ManimCodeGenerator:
    """Generate construct() body text with constraints."""

    def __init__(self, provider: LLMProvider, model: str | None = None, prompts_dir: Path | None = None) -> None:
        self.provider = provider
        self.model = model
        self.prompts_dir = prompts_dir or Path(__file__).resolve().parents[2] / "prompts"

    def _codegen_prompt(self) -> str:
        prompt_file = self.prompts_dir / "codegen.txt"
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return "Generate only code lines valid inside construct(self)."

    def generate_construct_body(self, scene: Scene) -> str:
        template = self._codegen_prompt()
        prompt = (
            f"{template}\n\n"
            f"Scene goal: {scene.goal}\n"
            f"Narration: {scene.narration}\n"
            f"Duration (seconds): {scene.duration_sec}\n"
            f"Visual elements: {', '.join(scene.visual_elements)}\n"
            f"Max animations: {scene.animation_count}\n"
            "Return only Python lines for inside construct(self)."
        )
        body = self.provider.generate(prompt, model=self.model).strip()
        if body.startswith("```"):
            body = "\n".join(
                line for line in body.splitlines() if not line.strip().startswith("```")
            ).strip()
        validate_construct_body(body)
        return body

    def build_scene_source(self, scene: Scene, construct_body: str) -> tuple[str, str]:
        class_name = f"Scene{scene.id}"
        source = build_scene_script(class_name=class_name, construct_body=construct_body)
        return class_name, source
