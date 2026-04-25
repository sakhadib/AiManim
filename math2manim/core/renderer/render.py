"""Scene render orchestration with retry/repair loop."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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


def render_scene_with_retries(
    *,
    scene: Scene,
    output_dir: Path,
    media_dir: Path,
    codegen: ManimCodeGenerator,
    fixer: CodeFixer,
    max_retries: int = 3,
    quality: str = "l",
) -> RenderResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    media_dir.mkdir(parents=True, exist_ok=True)

    construct_body = codegen.generate_construct_body(scene)
    attempts = 0

    while attempts < max_retries:
        attempts += 1
        class_name, source = codegen.build_scene_source(scene, construct_body)
        script_path = output_dir / f"scene_{scene.id}.py"
        script_path.write_text(source, encoding="utf-8")

        result = execute_manim_script(script_path, class_name, quality=quality, media_dir=media_dir)
        if result.success:
            folder = QUALITY_FOLDERS.get(quality, "480p15")
            video_path = media_dir / "videos" / script_path.stem / folder / f"{class_name}.mp4"
            return RenderResult(
                scene=scene,
                class_name=class_name,
                script_path=script_path,
                video_path=video_path,
                attempts=attempts,
            )

        if attempts >= max_retries:
            raise RuntimeError(
                f"Scene {scene.id} failed after {attempts} attempts. Last stderr:\n{result.stderr}"
            )

        construct_body = fixer.fix(scene=scene, construct_body=construct_body, error_message=result.stderr)

    raise RuntimeError("Unexpected retry loop termination")
