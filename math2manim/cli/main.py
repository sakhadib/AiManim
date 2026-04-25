"""Typer CLI for StruggleMath."""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path

import typer

from math2manim.core.codegen.manim_codegen import ManimCodeGenerator
from math2manim.core.planner.scene_planner import ScenePlanner
from math2manim.core.utils.secrets import env_var_for_provider, get_api_key, store_api_key
from math2manim.providers.factory import get_provider, supported_providers
from math2manim.workflows.langgraph_flow import run_pipeline

app = typer.Typer(add_completion=False)


def _new_run_dir(base_dir: Path = Path("temp")) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = base_dir / timestamp
    suffix = 1
    while run_dir.exists():
        run_dir = base_dir / f"{timestamp}_{suffix}"
        suffix += 1
    return run_dir


def _prompt_provider() -> str:
    selected = typer.prompt("Select provider", default="openrouter").strip().lower()
    if selected not in supported_providers():
        raise typer.BadParameter(f"Provider must be one of: {', '.join(supported_providers())}")
    return selected


def _prompt_model(provider: str) -> str | None:
    if provider != "openrouter":
        return None
    return typer.prompt("OpenRouter model id").strip()


def _ensure_api_key(provider: str) -> None:
    env_var = env_var_for_provider(provider)
    existing = get_api_key(provider)
    if existing:
        os.environ[env_var] = existing
        return

    typer.echo(f"No stored API key found for provider '{provider}'.")
    api_key = typer.prompt("Enter API key", hide_input=True, confirmation_prompt=True).strip()
    os.environ[env_var] = api_key

    if store_api_key(provider, api_key):
        typer.echo("API key saved in secure OS keyring.")
    else:
        typer.echo("Could not access secure keyring. Key will be used for this session only.")


@app.command()
def main(
    prompt: str = typer.Argument(..., help="Math prompt to animate."),
    provider: str | None = typer.Option(None, help="LLM provider", case_sensitive=False),
    model: str | None = typer.Option(None, help="Model name for selected provider"),
    out: Path = typer.Option(Path("outputs/final.mp4"), help="Output video path"),
    max_retries: int = typer.Option(3, min=1, max=3, help="Maximum repair retries per scene"),
    keep_scenes: bool = typer.Option(False, help="Keep intermediate scene scripts and media"),
    temp_dir: Path = typer.Option(Path("temp"), help="Directory for timestamped run artifacts"),
    dry_run: bool = typer.Option(False, help="Print plan/code and skip execution"),
) -> None:
    """Generate short Manim scenes from a math prompt."""

    selected_provider = provider.strip().lower() if provider else _prompt_provider()
    if selected_provider not in supported_providers():
        raise typer.BadParameter(f"Provider must be one of: {', '.join(supported_providers())}")
    selected_model = model or _prompt_model(selected_provider)

    _ensure_api_key(selected_provider)
    selected = get_provider(selected_provider)
    run_dir = _new_run_dir(temp_dir)
    typer.echo(f"Run artifacts: {run_dir}")

    if dry_run:
        planner = ScenePlanner(provider=selected, model=selected_model)
        codegen = ManimCodeGenerator(provider=selected, model=selected_model)

        typer.echo("Planning scenes with AI...")
        plan = planner.plan(prompt)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
        (run_dir / "plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")

        typer.echo("=== Scene Plan ===")
        typer.echo(json.dumps(plan.model_dump(), indent=2))

        typer.echo("\n=== Generated construct() bodies ===")
        for scene in plan.scenes:
            scene_dir = run_dir / "scenes" / f"scene_{scene.id:03d}"
            scene_dir.mkdir(parents=True, exist_ok=True)
            typer.echo(f"Generating Manim code for scene {scene.id}: {scene.goal}")
            body = codegen.generate_construct_body(scene)
            class_name, source = codegen.build_scene_source(scene, body)
            (scene_dir / "scene.json").write_text(scene.model_dump_json(indent=2), encoding="utf-8")
            (scene_dir / "construct_body.py").write_text(body, encoding="utf-8")
            (scene_dir / f"{class_name}.py").write_text(source, encoding="utf-8")
            typer.echo(f"\n# Scene {scene.id}: {scene.goal}")
            typer.echo(body)
        return

    result = run_pipeline(
        user_prompt=prompt,
        provider=selected,
        model=selected_model,
        output_file=out,
        max_retries=max_retries,
        keep_scenes=keep_scenes,
        quality="l",
        workspace_dir=run_dir,
        progress=typer.echo,
    )
    typer.echo(f"Rendered {len(result.scene_videos)} scenes")
    typer.echo(f"Final video: {result.final_video}")
    typer.echo(f"Run artifacts: {result.workspace}")


if __name__ == "__main__":
    app()
