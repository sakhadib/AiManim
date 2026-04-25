"""Code repair module for failed scene execution."""

from __future__ import annotations

from pathlib import Path

from math2manim.core.codegen.manim_codegen import validate_construct_body
from math2manim.providers.base import LLMProvider
from math2manim.schemas.scene import Scene


class CodeFixer:
    """Ask LLM for minimal fixes based on runtime/syntax errors."""

    def __init__(self, provider: LLMProvider, model: str | None = None, prompts_dir: Path | None = None) -> None:
        self.provider = provider
        self.model = model
        self.prompts_dir = prompts_dir or Path(__file__).resolve().parents[2] / "prompts"

    def _repair_prompt(self) -> str:
        prompt_file = self.prompts_dir / "repair.txt"
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return "Fix only the error and return construct body lines only."

    def fix(self, *, scene: Scene, construct_body: str, error_message: str) -> str:
        prompt = (
            f"{self._repair_prompt()}\n\n"
            "Error Message:\n"
            f"{error_message}\n\n"
            "Current code:\n"
            f"{construct_body}\n\n"
            f"Scene goal: {scene.goal}\n"
            "Return only corrected lines for construct(self)."
        )
        fixed = self.provider.generate(prompt, model=self.model).strip()
        if fixed.startswith("```"):
            fixed = "\n".join(
                line for line in fixed.splitlines() if not line.strip().startswith("```")
            ).strip()
        validate_construct_body(fixed)
        return fixed
