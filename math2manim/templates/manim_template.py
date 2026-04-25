"""Template utilities for Manim scene files."""

from __future__ import annotations

from textwrap import indent


def build_scene_script(*, class_name: str, construct_body: str) -> str:
    body = indent(construct_body.strip() or "pass", " " * 8)
    return (
        "from manim import *\n\n"
        f"class {class_name}(Scene):\n"
        "    def construct(self):\n"
        f"{body}\n"
    )
