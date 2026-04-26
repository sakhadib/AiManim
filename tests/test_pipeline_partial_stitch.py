from pathlib import Path

import pytest

from math2manim.core.renderer.render import RenderResult
from math2manim.providers.base import LLMProvider
from math2manim.schemas.scene import Scene, ScenePlan
from math2manim.workflows import langgraph_flow


class FakeProvider(LLMProvider):
    def generate(self, prompt: str, *, model: str | None = None, system_prompt: str | None = None) -> str:
        return "{}"


def _scene(scene_id: int) -> Scene:
    return Scene(
        id=scene_id,
        goal=f"Scene {scene_id}",
        narration="",
        duration_sec=4.0,
        visual_elements=["text"],
        animation_count=1,
    )


def test_pipeline_stitches_available_scenes_when_some_fail(monkeypatch, tmp_path) -> None:
    scenes = [_scene(1), _scene(2), _scene(3)]
    plan = ScenePlan(scenes=scenes)

    monkeypatch.setattr(langgraph_flow, "manim_available", lambda: True)
    monkeypatch.setattr(langgraph_flow, "ffmpeg_available", lambda: True)

    captured_scene_files: dict[str, list[Path]] = {}

    def fake_stitch(scene_files: list[Path], output_file: Path, work_dir: Path) -> None:
        captured_scene_files["files"] = scene_files
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("fake-video", encoding="utf-8")

    monkeypatch.setattr(langgraph_flow, "stitch_videos", fake_stitch)

    class _FakePlanner:
        def __init__(self, provider, model):
            pass

        def plan(self, *args, **kwargs):
            return plan

    monkeypatch.setattr(langgraph_flow, "ScenePlanner", _FakePlanner)

    def fake_codegen_parallel(**kwargs):
        return {1: "self.wait(1)", 2: "self.wait(1)", 3: "self.wait(1)"}

    monkeypatch.setattr(langgraph_flow, "generate_construct_bodies_parallel", fake_codegen_parallel)

    existing_video = tmp_path / "scene_1.mp4"
    existing_video.write_text("ok", encoding="utf-8")
    missing_video = tmp_path / "scene_3_missing.mp4"

    def fake_render_scene_with_retries(*, scene, **kwargs):
        if scene.id == 2:
            raise RuntimeError("render failed")
        if scene.id == 1:
            return RenderResult(
                scene=scene,
                class_name="Scene1",
                script_path=tmp_path / "scene_1.py",
                video_path=existing_video,
                attempts=1,
            )
        return RenderResult(
            scene=scene,
            class_name="Scene3",
            script_path=tmp_path / "scene_3.py",
            video_path=missing_video,
            attempts=1,
        )

    monkeypatch.setattr(langgraph_flow, "render_scene_with_retries", fake_render_scene_with_retries)

    output_file = tmp_path / "final.mp4"
    result = langgraph_flow.run_pipeline(
        user_prompt="Explain circle",
        provider=FakeProvider(),
        model=None,
        output_file=output_file,
        max_retries=1,
        keep_scenes=True,
        workspace_dir=tmp_path / "workspace",
    )

    assert result.final_video == output_file
    assert result.scene_videos == [existing_video]
    assert result.skipped_scene_ids == [2, 3]
    assert captured_scene_files["files"] == [existing_video]


def test_pipeline_errors_when_no_scene_videos_exist(monkeypatch, tmp_path) -> None:
    scenes = [_scene(1)]
    plan = ScenePlan(scenes=scenes)

    monkeypatch.setattr(langgraph_flow, "manim_available", lambda: True)
    monkeypatch.setattr(langgraph_flow, "ffmpeg_available", lambda: True)

    class _FakePlanner:
        def __init__(self, provider, model):
            pass

        def plan(self, *args, **kwargs):
            return plan

    monkeypatch.setattr(langgraph_flow, "ScenePlanner", _FakePlanner)
    monkeypatch.setattr(
        langgraph_flow,
        "generate_construct_bodies_parallel",
        lambda **kwargs: {1: "self.wait(1)"},
    )

    missing_video = tmp_path / "scene_1_missing.mp4"

    def fake_render_scene_with_retries(*, scene, **kwargs):
        return RenderResult(
            scene=scene,
            class_name="Scene1",
            script_path=tmp_path / "scene_1.py",
            video_path=missing_video,
            attempts=1,
        )

    monkeypatch.setattr(langgraph_flow, "render_scene_with_retries", fake_render_scene_with_retries)

    with pytest.raises(RuntimeError, match="No scenes rendered successfully"):
        langgraph_flow.run_pipeline(
            user_prompt="Explain circle",
            provider=FakeProvider(),
            model=None,
            output_file=tmp_path / "final.mp4",
            max_retries=1,
            keep_scenes=True,
            workspace_dir=tmp_path / "workspace",
        )
