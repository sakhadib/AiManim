import os

from math2manim.core.utils import secrets


class _FakeKeyring:
    def __init__(self) -> None:
        self.store: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.store.get((service, username))

    def set_password(self, service: str, username: str, value: str) -> None:
        self.store[(service, username)] = value


def test_env_var_mapping() -> None:
    assert secrets.env_var_for_provider("openrouter") == "OPENROUTER_API_KEY"
    assert secrets.env_var_for_provider("openai") == "OPENAI_API_KEY"
    assert secrets.env_var_for_provider("gemini") == "GEMINI_API_KEY"


def test_get_api_key_uses_env_first(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setattr(secrets, "keyring", _FakeKeyring())
    assert secrets.get_api_key("openai") == "env-key"


def test_store_and_get_from_keyring(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    fake = _FakeKeyring()
    monkeypatch.setattr(secrets, "keyring", fake)

    saved = secrets.store_api_key("openai", "stored-key")
    assert saved is True
    assert secrets.get_api_key("openai") == "stored-key"


def test_get_api_key_uses_legacy_keyring_service(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    fake = _FakeKeyring()
    fake.set_password(secrets.LEGACY_SERVICE_NAME, "openai", "legacy-key")
    monkeypatch.setattr(secrets, "keyring", fake)

    assert secrets.get_api_key("openai") == "legacy-key"


def test_store_returns_false_without_keyring(monkeypatch) -> None:
    monkeypatch.setattr(secrets, "keyring", None)
    assert secrets.store_api_key("openai", "key") is False
