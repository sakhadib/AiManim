"""Code repair module for failed scene execution."""

from __future__ import annotations

from pathlib import Path

from math2manim.core.codegen.manim_codegen import normalize_construct_body, validate_construct_body
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
        base_prompt = (
            f"{self._repair_prompt()}\n\n"
            "Error Message:\n"
            f"{error_message}\n\n"
            "Current code:\n"
            f"{construct_body}\n\n"
            f"Scene goal: {scene.goal}\n"
            "Return only corrected lines for construct(self)."
        )
        prompt = base_prompt
        last_error: ValueError | None = None
        last_body = ""

        for _ in range(3):
            fixed = normalize_construct_body(self.provider.generate(prompt, model=self.model))
            try:
                validate_construct_body(fixed)
                return fixed
            except ValueError as error:
                last_error = error
                last_body = fixed
                prompt = (
                    f"{base_prompt}\n\n"
                    "Your previous repair could not be used.\n"
                    f"Validation error: {error}\n\n"
                    "Previous repair:\n"
                    f"{fixed}\n\n"
                    "Return the complete corrected construct body only. "
                    "Do not include imports, class definitions, def construct, MathTex, Tex, "
                    "add_coordinates(), or get_axis_labels()."
                )

        raise ValueError(f"Repair code is still invalid after retries: {last_error}\nLast body:\n{last_body}")
