"""Stitch rendered scene videos into one output file."""

from __future__ import annotations

import subprocess
from pathlib import Path

from math2manim.core.utils.paths import ffmpeg_available


def stitch_videos(scene_files: list[Path], output_file: Path, work_dir: Path) -> None:
    if not scene_files:
        raise ValueError("No scene files were provided for stitching")
    if not ffmpeg_available():
        raise RuntimeError("ffmpeg not found in PATH")

    list_file = work_dir / "concat_list.txt"
    lines = [f"file '{path.as_posix()}'" for path in scene_files]
    list_file.write_text("\n".join(lines), encoding="utf-8")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-c",
        "copy",
        str(output_file),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"ffmpeg stitch failed: {completed.stderr}")
