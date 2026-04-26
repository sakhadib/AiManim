"""Scene planning from user prompts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from pydantic import ValidationError

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

    def plan(
        self,
        user_prompt: str,
        *,
        min_scenes: int = 6,
        max_scenes: int = 14,
        target_total_duration_sec: int = 60,
        max_regeneration_attempts: int = 4,
        progress: Callable[[str], None] | None = None,
    ) -> ScenePlan:
        if min_scenes < 1:
            raise ValueError("min_scenes must be at least 1")
        if max_scenes < min_scenes:
            raise ValueError("max_scenes must be >= min_scenes")
        if target_total_duration_sec <= 0:
            raise ValueError("target_total_duration_sec must be > 0")
        if max_regeneration_attempts < 1:
            raise ValueError("max_regeneration_attempts must be at least 1")

        template = self._prompt_template()
        base_prompt = (
            f"{template}\n\n"
            "User math prompt:\n"
            f"{user_prompt}\n\n"
            "Planning constraints:\n"
            f"- Number of scenes must be between {min_scenes} and {max_scenes}.\n"
            f"- Target total duration should be about {target_total_duration_sec} seconds.\n"
            "- Use 4-5 second scenes to build step-by-step explanations.\n"
            "- Prefer more scenes for conceptual transitions and examples.\n\n"
            "Return strict JSON with top-level key 'scenes'."
        )
        prompt = base_prompt
        last_error = "unknown planning error"

        for attempt in range(1, max_regeneration_attempts + 1):
            if progress and attempt > 1:
                progress(f"Planner regeneration attempt {attempt}/{max_regeneration_attempts}...")

            try:
                response = self.provider.generate(prompt, model=self.model)
                payload = json.loads(_extract_json(response))
                plan = ScenePlan.model_validate(payload)
                scene_count = len(plan.scenes)
                if scene_count < min_scenes or scene_count > max_scenes:
                    raise ValueError(
                        f"Planner returned {scene_count} scenes, expected between {min_scenes} and {max_scenes}"
                    )
                return plan
            except (json.JSONDecodeError, ValidationError, ValueError) as error:
                last_error = str(error)
                prompt = (
                    f"{base_prompt}\n\n"
                    "Your previous output could not be used.\n"
                    f"Validation error: {last_error}\n\n"
                    "Regenerate complete JSON only with key 'scenes'.\n"
                    f"Ensure scene count is between {min_scenes} and {max_scenes}.\n"
                    "Do not include markdown, code fences, or commentary."
                )

        raise RuntimeError(
            "Planner failed after regeneration attempts. "
            f"Last planning error: {last_error}"
        )
