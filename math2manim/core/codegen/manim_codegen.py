"""Constrained Manim code generation."""

from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
import inspect
from pathlib import Path
from textwrap import dedent
from typing import Callable

from math2manim.providers.base import LLMProvider
from math2manim.schemas.scene import Scene
from math2manim.templates.manim_template import build_scene_script

FORBIDDEN_CALLS = {"MathTex", "Tex"}
FORBIDDEN_ATTRIBUTES = {"add_coordinates", "get_axis_labels"}


def _strip_markdown_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = "\n".join(
            line for line in stripped.splitlines() if not line.strip().startswith("```")
        ).strip()
    return stripped


def _unparse_body(statements: list[ast.stmt]) -> str:
    return "\n".join(ast.unparse(statement) for statement in statements).strip()


def normalize_construct_body(text: str) -> str:
    """Convert common LLM responses into construct-body-only code."""

    body = inspect.cleandoc(_strip_markdown_fences(text)).strip()
    try:
        module = ast.parse(body)
    except SyntaxError:
        # Retry after removing any accidental leading indentation/newlines.
        retried = dedent(body.lstrip()).strip()
        try:
            module = ast.parse(retried)
            body = retried
        except SyntaxError:
            return body

    for node in module.body:
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == "construct":
                    return _unparse_body(child.body)

    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == "construct":
            return _unparse_body(node.body)

    filtered = [
        node
        for node in module.body
        if not isinstance(node, ast.Import | ast.ImportFrom | ast.ClassDef | ast.FunctionDef)
    ]
    if len(filtered) != len(module.body):
        return _unparse_body(filtered)

    return body


def validate_construct_body(construct_body: str) -> None:
    indented_body = "\n".join(f"    {line}" if line.strip() else line for line in construct_body.splitlines())
    try:
        module = ast.parse(f"def _generated_construct(self):\n{indented_body or '    pass'}\n")
    except SyntaxError as error:
        raise ValueError(f"Generated code is not valid Python: {error.msg}") from error

    for node in ast.walk(module):
        if isinstance(node, ast.Import | ast.ImportFrom):
            raise ValueError("Generated code includes imports; return only construct body statements")
        if isinstance(node, ast.ClassDef):
            raise ValueError("Generated code includes a class definition; return only construct body statements")
        if isinstance(node, ast.FunctionDef) and node.name != "_generated_construct":
            raise ValueError("Generated code includes a function definition; return only construct body statements")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                raise ValueError(f"Generated code uses {node.func.id}; use Text() instead")
            if isinstance(node.func, ast.Attribute) and node.func.attr in FORBIDDEN_ATTRIBUTES:
                raise ValueError(f"Generated code uses {node.func.attr}; create labels manually with Text()")


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
        base_prompt = (
            f"{template}\n\n"
            f"Scene goal: {scene.goal}\n"
            f"Narration: {scene.narration}\n"
            f"Duration (seconds): {scene.duration_sec}\n"
            f"Visual elements: {', '.join(scene.visual_elements)}\n"
            f"Max animations: {scene.animation_count}\n"
            "Return only Python lines for inside construct(self)."
        )
        prompt = base_prompt
        last_error: ValueError | None = None
        last_body = ""

        for _ in range(3):
            body = normalize_construct_body(self.provider.generate(prompt, model=self.model))
            try:
                validate_construct_body(body)
                return body
            except ValueError as error:
                last_error = error
                last_body = body
                prompt = (
                    f"{base_prompt}\n\n"
                    "Your previous response could not be used.\n"
                    f"Validation error: {error}\n\n"
                    "Previous response:\n"
                    f"{body}\n\n"
                    "Regenerate the complete construct body only. "
                    "Do not include imports, class definitions, def construct, MathTex, Tex, "
                    "add_coordinates(), or get_axis_labels()."
                )

        raise ValueError(f"Generated code is still invalid after retries: {last_error}\nLast body:\n{last_body}")

    def build_scene_source(self, scene: Scene, construct_body: str) -> tuple[str, str]:
        class_name = f"Scene{scene.id}"
        source = build_scene_script(class_name=class_name, construct_body=construct_body)
        return class_name, source


def generate_construct_bodies_parallel(
    *,
    codegen: ManimCodeGenerator,
    scenes: list[Scene],
    max_workers: int,
    progress: Callable[[str], None] | None = None,
    max_scene_generation_attempts: int = 2,
) -> dict[int, str]:
    """Generate initial construct bodies concurrently, keyed by scene id."""

    if not scenes:
        return {}

    workers = max(1, min(max_workers, len(scenes)))

    def generate_with_regeneration(scene: Scene) -> str:
        last_error: Exception | None = None
        for attempt in range(1, max_scene_generation_attempts + 1):
            try:
                return codegen.generate_construct_body(scene)
            except ValueError as error:
                last_error = error
                if progress and max_scene_generation_attempts > 1:
                    progress(
                        f"Scene {scene.id} codegen failed (attempt {attempt}/{max_scene_generation_attempts}); regenerating..."
                    )
        raise RuntimeError(
            f"Scene {scene.id} codegen failed after {max_scene_generation_attempts} regeneration attempt(s): {last_error}"
        )

    if workers == 1:
        bodies: dict[int, str] = {}
        for scene in scenes:
            if progress:
                progress(f"Generating Manim code for scene {scene.id}: {scene.goal}")
            bodies[scene.id] = generate_with_regeneration(scene)
        return bodies

    if progress:
        progress(f"Generating Manim code for {len(scenes)} scene(s) using {workers} worker(s)...")

    bodies = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(generate_with_regeneration, scene): scene
            for scene in scenes
        }
        for future in as_completed(futures):
            scene = futures[future]
            bodies[scene.id] = future.result()
            if progress:
                progress(f"Generated Manim code for scene {scene.id}: {scene.goal}")

    return bodies
