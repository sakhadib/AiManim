"""Typer CLI for AIManim."""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import sys

import typer

from math2manim.core.codegen.manim_codegen import ManimCodeGenerator, generate_construct_bodies_parallel
from math2manim.core.planner.scene_planner import ScenePlanner
from math2manim.core.utils.config import CONFIG_FILE, CLIConfig, load_config, save_config
from math2manim.core.utils.paths import ffmpeg_available, manim_available
from math2manim.core.utils.secrets import env_var_for_provider, get_api_key, store_api_key
from math2manim.providers.factory import get_provider, supported_providers
from math2manim.workflows.langgraph_flow import run_pipeline

app = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
)

ROOT_COMMANDS = {"generate", "setup", "providers", "config", "doctor"}


def _new_run_dir(base_dir: Path = Path("temp")) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = base_dir / timestamp
    suffix = 1
    while run_dir.exists():
        run_dir = base_dir / f"{timestamp}_{suffix}"
        suffix += 1
    return run_dir


def _normalize_cli_args(args: list[str]) -> list[str]:
    if args and args[0] not in ROOT_COMMANDS and not args[0].startswith("-"):
        return ["generate", *args]
    return args


def _validate_provider(provider: str) -> str:
    selected = provider.strip().lower()
    if selected not in supported_providers():
        raise typer.BadParameter(f"Provider must be one of: {', '.join(supported_providers())}")
    return selected


def _prompt_provider(default: str | None = None) -> str:
    selected = typer.prompt("Select provider", default=default or "openrouter").strip().lower()
    return _validate_provider(selected)


def _prompt_model(provider: str, default: str | None = None) -> str | None:
    default_text = default or ""
    value = typer.prompt(f"Model id for {provider}", default=default_text).strip()
    return value or None


def _resolve_provider(provider: str | None, config: CLIConfig, *, interactive: bool = True) -> str:
    if provider:
        return _validate_provider(provider)
    if config.default_provider:
        return _validate_provider(config.default_provider)
    if interactive:
        return _prompt_provider()
    raise typer.BadParameter("No provider configured. Run `math2manim setup` or pass --provider.")


def _resolve_model(provider: str, model: str | None, config: CLIConfig, *, interactive: bool = True) -> str | None:
    if model:
        return model.strip()
    configured = config.model_for(provider)
    if configured:
        return configured
    if interactive:
        return _prompt_model(provider)
    return None


def _validate_model(provider: str, model: str | None) -> None:
    if provider == "openrouter" and not model:
        raise typer.BadParameter("OpenRouter requires a model id. Run `aimanim setup` or pass --model.")


def _ensure_api_key(provider: str, *, prompt_if_missing: bool = True) -> bool:
    env_var = env_var_for_provider(provider)
    existing = get_api_key(provider)
    if existing:
        os.environ[env_var] = existing
        return True

    if not prompt_if_missing:
        return False

    typer.echo(f"No stored API key found for provider '{provider}'.")
    api_key = typer.prompt("Enter API key", hide_input=True, confirmation_prompt=True).strip()
    os.environ[env_var] = api_key

    if store_api_key(provider, api_key):
        typer.echo("API key saved in secure OS keyring.")
    else:
        typer.echo("Could not access secure keyring. Key will be used for this session only.")
    return True


def _run_generate(
    *,
    prompt: str,
    provider: str | None,
    model: str | None,
    out: Path | None,
    max_retries: int,
    keep_scenes: bool,
    temp_dir: Path | None,
    dry_run: bool,
    codegen_workers: int,
    min_scenes: int,
    max_scenes: int,
    target_total_duration_sec: int,
    non_interactive: bool = False,
) -> None:
    if max_scenes < min_scenes:
        raise typer.BadParameter("--max-scenes must be greater than or equal to --min-scenes")

    config = load_config()
    selected_provider = _resolve_provider(provider, config, interactive=not non_interactive)
    selected_model = _resolve_model(selected_provider, model, config, interactive=not non_interactive)
    _validate_model(selected_provider, selected_model)

    if not _ensure_api_key(selected_provider, prompt_if_missing=not non_interactive):
        env_var = env_var_for_provider(selected_provider)
        raise typer.BadParameter(f"Missing API key. Set {env_var} or run `math2manim setup`.")

    selected = get_provider(selected_provider)
    output_file = out or Path(config.output_dir) / "final.mp4"
    run_dir = _new_run_dir(temp_dir or Path(config.temp_dir))
    typer.echo(f"Provider: {selected_provider}")
    if selected_model:
        typer.echo(f"Model: {selected_model}")
    typer.echo(f"Run artifacts: {run_dir}")

    if dry_run:
        planner = ScenePlanner(provider=selected, model=selected_model)
        codegen = ManimCodeGenerator(provider=selected, model=selected_model)

        typer.echo("Planning scenes with AI...")
        plan = planner.plan(
            prompt,
            min_scenes=min_scenes,
            max_scenes=max_scenes,
            target_total_duration_sec=target_total_duration_sec,
            progress=typer.echo,
        )
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
        (run_dir / "plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")
        construct_bodies = generate_construct_bodies_parallel(
            codegen=codegen,
            scenes=plan.scenes,
            max_workers=codegen_workers,
            progress=typer.echo,
        )

        typer.echo("=== Scene Plan ===")
        typer.echo(json.dumps(plan.model_dump(), indent=2))

        typer.echo("\n=== Generated construct() bodies ===")
        for scene in plan.scenes:
            scene_dir = run_dir / "scenes" / f"scene_{scene.id:03d}"
            scene_dir.mkdir(parents=True, exist_ok=True)
            body = construct_bodies[scene.id]
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
        output_file=output_file,
        max_retries=max_retries,
        keep_scenes=keep_scenes,
        quality="l",
        workspace_dir=run_dir,
        progress=typer.echo,
        codegen_workers=codegen_workers,
        min_scenes=min_scenes,
        max_scenes=max_scenes,
        target_total_duration_sec=target_total_duration_sec,
    )
    typer.echo(f"Rendered {len(result.scene_videos)} scenes")
    if result.skipped_scene_ids:
        typer.echo(f"Skipped scenes: {result.skipped_scene_ids}")
    typer.echo(f"Final video: {result.final_video}")
    typer.echo(f"Run artifacts: {result.workspace}")


@app.callback()
def root() -> None:
    """AIManim CLI."""


@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Math prompt to animate."),
    provider: str | None = typer.Option(None, "--provider", "-p", help="LLM provider", case_sensitive=False),
    model: str | None = typer.Option(None, "--model", "-m", help="Model id for selected provider"),
    out: Path | None = typer.Option(None, "--out", "-o", help="Output video path"),
    max_retries: int = typer.Option(3, "--max-retries", min=1, max=3, help="Maximum repair retries per scene"),
    keep_scenes: bool = typer.Option(False, "--keep-scenes", help="Keep intermediate scene scripts and media"),
    temp_dir: Path | None = typer.Option(None, "--temp-dir", help="Directory for timestamped run artifacts"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print plan/code and skip execution"),
    codegen_workers: int = typer.Option(4, "--codegen-workers", min=1, max=16, help="Parallel workers for initial AI code generation"),
    min_scenes: int = typer.Option(6, "--min-scenes", min=1, max=60, help="Minimum planned scene count"),
    max_scenes: int = typer.Option(14, "--max-scenes", min=1, max=60, help="Maximum planned scene count"),
    target_total_duration_sec: int = typer.Option(60, "--target-total-seconds", min=5, max=900, help="Target overall video duration for planning"),
    non_interactive: bool = typer.Option(False, "--non-interactive", help="Fail instead of prompting for missing setup"),
) -> None:
    """Generate a Manim video from a math prompt."""

    _run_generate(
        prompt=prompt,
        provider=provider,
        model=model,
        out=out,
        max_retries=max_retries,
        keep_scenes=keep_scenes,
        temp_dir=temp_dir,
        dry_run=dry_run,
        codegen_workers=codegen_workers,
        min_scenes=min_scenes,
        max_scenes=max_scenes,
        target_total_duration_sec=target_total_duration_sec,
        non_interactive=non_interactive,
    )


@app.command()
def setup() -> None:
    """Configure default provider, model, and API key."""

    config = load_config()
    provider = _prompt_provider(config.default_provider)
    model = _prompt_model(provider, config.model_for(provider))
    _ensure_api_key(provider, prompt_if_missing=True)

    config.default_provider = provider
    config.set_model(provider, model)
    path = save_config(config)
    typer.echo(f"Saved config: {path}")


@app.command("providers")
def list_providers() -> None:
    """List supported providers and key status."""

    config = load_config()
    typer.echo("Supported providers:")
    for provider in supported_providers():
        default_marker = " (default)" if provider == config.default_provider else ""
        key_status = "configured" if get_api_key(provider) else "missing"
        model = config.model_for(provider) or "-"
        typer.echo(f"- {provider}{default_marker}: key={key_status}, model={model}, env={env_var_for_provider(provider)}")


@app.command("config")
def show_config() -> None:
    """Show current CLI configuration."""

    config = load_config()
    typer.echo(f"Config file: {CONFIG_FILE}")
    typer.echo(json.dumps(config.to_dict(), indent=2))


@app.command()
def doctor() -> None:
    """Check local render tools and provider setup."""

    config = load_config()
    checks = [
        ("Manim", manim_available()),
        ("FFmpeg", ffmpeg_available()),
    ]
    for name, ok in checks:
        typer.echo(f"{name}: {'ok' if ok else 'missing'}")

    if config.default_provider:
        provider = config.default_provider
        typer.echo(f"Default provider: {provider}")
        typer.echo(f"Default model: {config.model_for(provider) or '-'}")
        typer.echo(f"API key: {'configured' if get_api_key(provider) else 'missing'}")
    else:
        typer.echo("Default provider: not configured")

    if not all(ok for _, ok in checks):
        raise typer.Exit(code=1)


def cli() -> None:
    app(args=_normalize_cli_args(sys.argv[1:]))


if __name__ == "__main__":
    cli()
