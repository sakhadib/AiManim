"""Typer CLI for StruggleMath."""

from __future__ import annotations

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


def _prompt_provider() -> str:
    selected = typer.prompt("Select provider", default="openai").strip().lower()
    if selected not in supported_providers():
        raise typer.BadParameter(f"Provider must be one of: {', '.join(supported_providers())}")
    return selected


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
    dry_run: bool = typer.Option(False, help="Print plan/code and skip execution"),
) -> None:
    """Generate short Manim scenes from a math prompt."""

    selected_provider = provider.strip().lower() if provider else _prompt_provider()
    if selected_provider not in supported_providers():
        raise typer.BadParameter(f"Provider must be one of: {', '.join(supported_providers())}")

    _ensure_api_key(selected_provider)
    selected = get_provider(selected_provider)

    if dry_run:
        planner = ScenePlanner(provider=selected, model=model)
        codegen = ManimCodeGenerator(provider=selected, model=model)

        plan = planner.plan(prompt)
        typer.echo("=== Scene Plan ===")
        typer.echo(json.dumps(plan.model_dump(), indent=2))

        typer.echo("\n=== Generated construct() bodies ===")
        for scene in plan.scenes:
            typer.echo(f"\n# Scene {scene.id}: {scene.goal}")
            typer.echo(codegen.generate_construct_body(scene))
        return

    result = run_pipeline(
        user_prompt=prompt,
        provider=selected,
        model=model,
        output_file=out,
        max_retries=max_retries,
        keep_scenes=keep_scenes,
        quality="l",
    )
    typer.echo(f"Rendered {len(result.scene_videos)} scenes")
    typer.echo(f"Final video: {result.final_video}")


if __name__ == "__main__":
    app()
