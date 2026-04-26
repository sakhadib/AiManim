from math2manim.core.utils.config import CLIConfig, load_config, save_config


def test_config_round_trip(tmp_path) -> None:
    path = tmp_path / "config.json"
    config = CLIConfig(default_provider="openrouter")
    config.set_model("openrouter", "deepseek/deepseek-v4-flash")

    save_config(config, path)
    loaded = load_config(path)

    assert loaded.default_provider == "openrouter"
    assert loaded.model_for("openrouter") == "deepseek/deepseek-v4-flash"
    assert loaded.output_dir == "outputs"
    assert loaded.temp_dir == "temp"


def test_invalid_config_returns_defaults(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text("{not json", encoding="utf-8")

    loaded = load_config(path)

    assert loaded.default_provider is None
    assert loaded.models == {}
