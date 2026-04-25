"""Scene schema and validation contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class Scene(BaseModel):
    """Strict scene representation used across planning and rendering."""

    id: int = Field(ge=1)
    goal: str = Field(min_length=1)
    narration: str = Field(default="")
    duration_sec: float
    visual_elements: list[str]
    animation_count: int = Field(default=3, ge=0, le=3)

    @field_validator("duration_sec")
    @classmethod
    def max_duration(cls, value: float) -> float:
        if value > 5:
            raise ValueError("Scene duration exceeds 5 seconds")
        if value <= 0:
            raise ValueError("Scene duration must be greater than 0")
        return value

    @field_validator("visual_elements")
    @classmethod
    def max_visual_elements(cls, value: list[str]) -> list[str]:
        if len(value) > 4:
            raise ValueError("Scene has more than 4 visual elements")
        if not value:
            raise ValueError("Scene needs at least one visual element")
        return value


class ScenePlan(BaseModel):
    """Container for generated scenes."""

    scenes: list[Scene] = Field(min_length=1)

    @field_validator("scenes")
    @classmethod
    def enforce_unique_scene_ids(cls, value: list[Scene]) -> list[Scene]:
        ids = [scene.id for scene in value]
        if len(ids) != len(set(ids)):
            raise ValueError("Scene ids must be unique")
        return value
