"""Run Manim scene scripts and capture errors."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from math2manim.core.utils.paths import manim_command


@dataclass
class ExecutionResult:
    success: bool
    returncode: int
    stdout: str
    stderr: str


def execute_manim_script(
    script_path: Path,
    scene_name: str,
    *,
    quality: str = "l",
    media_dir: Path | None = None,
) -> ExecutionResult:
    command = [*manim_command(), "-q", quality, str(script_path), scene_name]
    if media_dir is not None:
        command.extend(["--media_dir", str(media_dir)])

    completed = subprocess.run(command, capture_output=True, text=True)
    return ExecutionResult(
        success=completed.returncode == 0,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
