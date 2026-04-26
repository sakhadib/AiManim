"""Scene render orchestration with retry/repair loop."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from math2manim.core.codegen.manim_codegen import ManimCodeGenerator
from math2manim.core.executor.runner import execute_manim_script
from math2manim.core.repair.fixer import CodeFixer
from math2manim.schemas.scene import Scene

QUALITY_FOLDERS = {
    "l": "480p15",
    "m": "720p30",
    "h": "1080p60",
}


@dataclass
class RenderResult:
    scene: Scene
    class_name: str
    script_path: Path
    video_path: Path
    attempts: int


NON_REPAIRABLE_ERROR_SNIPPETS = [
    "Application Control policy has blocked this file",
    "DLL load failed",
    "No module named manim",
    "No module named 'manim'",
    "No module named av",
    "No module named 'av'",
]


def _is_non_repairable_environment_error(stderr: str) -> bool:
    return any(snippet in stderr for snippet in NON_REPAIRABLE_ERROR_SNIPPETS)


def render_scene_with_retries(
    *,
    scene: Scene,
    output_dir: Path,
    media_dir: Path,
    codegen: ManimCodeGenerator,
    fixer: CodeFixer,
    max_retries: int = 3,
    quality: str = "l",
    progress: Callable[[str], None] | None = None,
    initial_construct_body: str | None = None,
) -> RenderResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    media_dir.mkdir(parents=True, exist_ok=True)

    if initial_construct_body is None and progress:
        progress(f"Generating Manim code for scene {scene.id}: {scene.goal}")
    construct_body = initial_construct_body or codegen.generate_construct_body(scene)
    scene_dir = output_dir / f"scene_{scene.id:03d}"
    scene_dir.mkdir(parents=True, exist_ok=True)
    (scene_dir / "scene.json").write_text(scene.model_dump_json(indent=2), encoding="utf-8")
    (scene_dir / "construct_initial.py").write_text(construct_body, encoding="utf-8")
    attempts = 0

    while attempts < max_retries:
        attempts += 1
        if progress:
            progress(f"Rendering scene {scene.id}, attempt {attempts}/{max_retries}: {scene.goal}")

        class_name, source = codegen.build_scene_source(scene, construct_body)
        attempt_dir = scene_dir / f"attempt_{attempts}"
        attempt_dir.mkdir(parents=True, exist_ok=True)
        script_path = attempt_dir / f"scene_{scene.id}.py"
        (attempt_dir / "construct_body.py").write_text(construct_body, encoding="utf-8")
        script_path.write_text(source, encoding="utf-8")

        result = execute_manim_script(script_path, class_name, quality=quality, media_dir=media_dir)
        (attempt_dir / "stdout.log").write_text(result.stdout, encoding="utf-8")
        (attempt_dir / "stderr.log").write_text(result.stderr, encoding="utf-8")

        if result.success:
            if progress:
                progress(f"Scene {scene.id} rendered successfully.")
            folder = QUALITY_FOLDERS.get(quality, "480p15")
            video_path = media_dir / "videos" / script_path.stem / folder / f"{class_name}.mp4"
            return RenderResult(
                scene=scene,
                class_name=class_name,
                script_path=script_path,
                video_path=video_path,
                attempts=attempts,
            )

        if _is_non_repairable_environment_error(result.stderr):
            raise RuntimeError(
                f"Scene {scene.id} failed because the render environment is not ready. "
                "This cannot be fixed by changing generated Manim code.\n"
                f"Last stderr:\n{result.stderr}"
            )

        if attempts >= max_retries:
            raise RuntimeError(
                f"Scene {scene.id} failed after {attempts} attempts. Last stderr:\n{result.stderr}"
            )

        if progress:
            progress(f"Scene {scene.id} failed; asking AI to repair the Manim code.")
        construct_body = fixer.fix(scene=scene, construct_body=construct_body, error_message=result.stderr)
        (scene_dir / f"repair_{attempts}.py").write_text(construct_body, encoding="utf-8")

    raise RuntimeError("Unexpected retry loop termination")
