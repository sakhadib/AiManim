"""LangGraph-based orchestration for the StruggleMath pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from math2manim.core.codegen.manim_codegen import ManimCodeGenerator
from math2manim.core.planner.scene_planner import ScenePlanner
from math2manim.core.renderer.render import render_scene_with_retries
from math2manim.core.repair.fixer import CodeFixer
from math2manim.core.stitcher.stitch import stitch_videos
from math2manim.core.utils.paths import ffmpeg_available, manim_available, temporary_workspace
from math2manim.providers.base import LLMProvider

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover
    END = "END"
    START = "START"
    StateGraph = None


@dataclass
class PipelineResult:
    scene_videos: list[Path]
    final_video: Path | None
    workspace: Path


def run_pipeline(
    *,
    user_prompt: str,
    provider: LLMProvider,
    model: str | None,
    output_file: Path,
    max_retries: int,
    keep_scenes: bool,
    quality: str = "l",
    workspace_dir: Path | None = None,
    progress: Callable[[str], None] | None = None,
) -> PipelineResult:
    def report(message: str) -> None:
        if progress:
            progress(message)

    if workspace_dir is None and keep_scenes:
        workspace_dir = output_file.parent / "intermediate"

    workspace_context = temporary_workspace() if workspace_dir is None else None
    if workspace_context is None:
        workspace = workspace_dir
        workspace.mkdir(parents=True, exist_ok=True)
        cleanup = None
    else:
        cleanup = workspace_context
        workspace = cleanup.__enter__()

    try:
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "prompt.txt").write_text(user_prompt, encoding="utf-8")

        report("Checking render tools...")
        missing_tools = []
        if not manim_available():
            missing_tools.append("manim")
        if not ffmpeg_available():
            missing_tools.append("ffmpeg")
        if missing_tools:
            tools = ", ".join(missing_tools)
            raise RuntimeError(f"Missing required render tool(s): {tools}. Install them or run with --dry-run.")

        planner = ScenePlanner(provider=provider, model=model)
        codegen = ManimCodeGenerator(provider=provider, model=model)
        fixer = CodeFixer(provider=provider, model=model)

        report("Planning scenes with AI...")
        plan = planner.plan(user_prompt)
        report(f"Planned {len(plan.scenes)} scene(s).")

        media_dir = workspace / "media"
        scene_sources = workspace / "scenes"
        scene_videos: list[Path] = []

        (workspace / "plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")

        for scene in plan.scenes:
            result = render_scene_with_retries(
                scene=scene,
                output_dir=scene_sources,
                media_dir=media_dir,
                codegen=codegen,
                fixer=fixer,
                max_retries=max_retries,
                quality=quality,
                progress=report,
            )
            scene_videos.append(result.video_path)

        report("Stitching scene videos with FFmpeg...")
        stitch_videos(scene_videos, output_file=output_file, work_dir=workspace)
        report(f"Final video written to {output_file}")
        return PipelineResult(scene_videos=scene_videos, final_video=output_file, workspace=workspace)
    finally:
        if cleanup is not None:
            cleanup.__exit__(None, None, None)


def build_graph() -> object | None:
    """Build graph skeleton for future stateful extensions."""

    if StateGraph is None:
        return None

    graph = StateGraph(dict)

    def passthrough(state: dict) -> dict:
        return state

    graph.add_node("parse_prompt", passthrough)
    graph.add_node("generate_scene_plan", passthrough)
    graph.add_node("validate_plan", passthrough)
    graph.add_edge(START, "parse_prompt")
    graph.add_edge("parse_prompt", "generate_scene_plan")
    graph.add_edge("generate_scene_plan", "validate_plan")
    graph.add_edge("validate_plan", END)
    return graph.compile()
