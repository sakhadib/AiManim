from math2manim.cli.main import _normalize_cli_args


def test_direct_prompt_rewrites_to_generate() -> None:
    assert _normalize_cli_args(["Explain circles"]) == ["generate", "Explain circles"]


def test_subcommand_is_not_rewritten() -> None:
    assert _normalize_cli_args(["setup"]) == ["setup"]


def test_options_are_not_rewritten() -> None:
    assert _normalize_cli_args(["--help"]) == ["--help"]
