"""LangGraph-based orchestration for the StruggleMath pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from math2manim.core.codegen.manim_codegen import ManimCodeGenerator
from math2manim.core.planner.scene_planner import ScenePlanner
from math2manim.core.renderer.render import render_scene_with_retries
from math2manim.core.repair.fixer import CodeFixer
from math2manim.core.stitcher.stitch import stitch_videos
from math2manim.core.utils.paths import temporary_workspace
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


def run_pipeline(
    *,
    user_prompt: str,
    provider: LLMProvider,
    model: str | None,
    output_file: Path,
    max_retries: int,
    keep_scenes: bool,
    quality: str = "l",
) -> PipelineResult:
    planner = ScenePlanner(provider=provider, model=model)
    codegen = ManimCodeGenerator(provider=provider, model=model)
    fixer = CodeFixer(provider=provider, model=model)

    plan = planner.plan(user_prompt)

    with temporary_workspace() as temp_dir:
        workspace = temp_dir if not keep_scenes else output_file.parent / "intermediate"
        workspace.mkdir(parents=True, exist_ok=True)

        media_dir = workspace / "media"
        scene_sources = workspace / "scenes"
        scene_videos: list[Path] = []

        for scene in plan.scenes:
            result = render_scene_with_retries(
                scene=scene,
                output_dir=scene_sources,
                media_dir=media_dir,
                codegen=codegen,
                fixer=fixer,
                max_retries=max_retries,
                quality=quality,
            )
            scene_videos.append(result.video_path)

        stitch_videos(scene_videos, output_file=output_file, work_dir=workspace)
        return PipelineResult(scene_videos=scene_videos, final_video=output_file)


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
