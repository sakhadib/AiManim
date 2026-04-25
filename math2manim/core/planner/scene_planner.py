"""Scene planning from user prompts."""

from __future__ import annotations

import json
from pathlib import Path

from math2manim.providers.base import LLMProvider
from math2manim.schemas.scene import ScenePlan


def _extract_json(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = [line for line in stripped.splitlines() if not line.strip().startswith("```")]
        stripped = "\n".join(lines).strip()
    return stripped


class ScenePlanner:
    """Generate strict scene plans using an LLM provider."""

    def __init__(self, provider: LLMProvider, model: str | None = None, prompts_dir: Path | None = None) -> None:
        self.provider = provider
        self.model = model
        self.prompts_dir = prompts_dir or Path(__file__).resolve().parents[2] / "prompts"

    def _prompt_template(self) -> str:
        prompt_file = self.prompts_dir / "planner.txt"
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return "Create exactly two scenes in JSON format as {\"scenes\":[...]}."

    def plan(self, user_prompt: str) -> ScenePlan:
        template = self._prompt_template()
        prompt = (
            f"{template}\n\n"
            "User math prompt:\n"
            f"{user_prompt}\n\n"
            "Return strict JSON with top-level key 'scenes'."
        )
        response = self.provider.generate(prompt, model=self.model)
        payload = json.loads(_extract_json(response))
        return ScenePlan.model_validate(payload)
