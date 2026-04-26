"""Persistent CLI configuration for AIManim."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CONFIG_DIR = Path.home() / ".aimanim"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class CLIConfig:
    default_provider: str | None = None
    models: dict[str, str] = field(default_factory=dict)
    output_dir: str = "outputs"
    temp_dir: str = "temp"

    def model_for(self, provider: str) -> str | None:
        return self.models.get(provider.strip().lower())

    def set_model(self, provider: str, model: str | None) -> None:
        normalized = provider.strip().lower()
        if model:
            self.models[normalized] = model.strip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "default_provider": self.default_provider,
            "models": self.models,
            "output_dir": self.output_dir,
            "temp_dir": self.temp_dir,
        }


def load_config(path: Path = CONFIG_FILE) -> CLIConfig:
    if not path.exists():
        return CLIConfig()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return CLIConfig()

    return CLIConfig(
        default_provider=data.get("default_provider"),
        models=dict(data.get("models", {})),
        output_dir=data.get("output_dir", "outputs"),
        temp_dir=data.get("temp_dir", "temp"),
    )


def save_config(config: CLIConfig, path: Path = CONFIG_FILE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")
    return path
