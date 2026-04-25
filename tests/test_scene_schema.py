from pydantic import ValidationError

from math2manim.schemas.scene import Scene, ScenePlan


def test_scene_duration_limit() -> None:
    try:
        Scene(
            id=1,
            goal="Too long",
            narration="",
            duration_sec=6,
            visual_elements=["x"],
            animation_count=1,
        )
    except ValidationError:
        return
    assert False, "Expected validation error for duration > 5"


def test_scene_plan_requires_two_scenes() -> None:
    one_scene = [
        Scene(
            id=1,
            goal="g",
            narration="n",
            duration_sec=3,
            visual_elements=["dot"],
            animation_count=1,
        )
    ]
    try:
        ScenePlan(scenes=one_scene)
    except ValidationError:
        return
    assert False, "Expected validation error for non-2 scene count"
