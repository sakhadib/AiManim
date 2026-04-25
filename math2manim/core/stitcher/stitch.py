"""Stitch rendered scene videos into one output file."""

from __future__ import annotations

import subprocess
from pathlib import Path

from math2manim.core.utils.paths import ffmpeg_available


def _ffmpeg_concat_path(path: Path) -> str:
    resolved = path.resolve()
    return resolved.as_posix().replace("'", "'\\''")


def stitch_videos(scene_files: list[Path], output_file: Path, work_dir: Path) -> None:
    if not scene_files:
        raise ValueError("No scene files were provided for stitching")
    if not ffmpeg_available():
        raise RuntimeError("ffmpeg not found in PATH")

    list_file = work_dir / "concat_list.txt"
    lines = [f"file '{_ffmpeg_concat_path(path)}'" for path in scene_files]
    list_file.write_text("\n".join(lines), encoding="utf-8")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    resolved_output = output_file.resolve()
    command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file.resolve()),
        "-c",
        "copy",
        str(resolved_output),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    (work_dir / "ffmpeg_stdout.log").write_text(completed.stdout, encoding="utf-8")
    (work_dir / "ffmpeg_stderr.log").write_text(completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(f"ffmpeg stitch failed: {completed.stderr}")
