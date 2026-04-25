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


def test_scene_plan_allows_variable_scene_count() -> None:
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
    plan = ScenePlan(scenes=one_scene)
    assert len(plan.scenes) == 1


def test_scene_plan_rejects_duplicate_ids() -> None:
    scenes = [
        Scene(
            id=1,
            goal="g",
            narration="n",
            duration_sec=3,
            visual_elements=["dot"],
            animation_count=1,
        ),
        Scene(
            id=1,
            goal="g2",
            narration="n2",
            duration_sec=3,
            visual_elements=["line"],
            animation_count=1,
        ),
    ]
    try:
        ScenePlan(scenes=scenes)
    except ValidationError:
        return
    assert False, "Expected validation error for duplicate scene ids"
