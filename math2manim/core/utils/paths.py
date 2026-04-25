"""Path and temporary workspace helpers."""

from __future__ import annotations

import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


@contextmanager
def temporary_workspace(prefix: str = "math2manim_") -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix=prefix) as tmp:
        yield Path(tmp)
