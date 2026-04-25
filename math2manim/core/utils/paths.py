"""Path and temporary workspace helpers."""

from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def manim_available() -> bool:
    return importlib.util.find_spec("manim") is not None or shutil.which("manim") is not None


def manim_command() -> list[str]:
    if importlib.util.find_spec("manim") is not None:
        return [sys.executable, "-m", "manim"]
    if shutil.which("manim") is not None:
        return ["manim"]
    raise RuntimeError("manim not found. Install Manim or run with --dry-run to skip rendering.")


@contextmanager
def temporary_workspace(prefix: str = "math2manim_") -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix=prefix) as tmp:
        yield Path(tmp)
