"""Secure API key retrieval and storage helpers."""

from __future__ import annotations

import os
from typing import Final

SERVICE_NAME: Final[str] = "strugglemath"

try:
    import keyring
except ImportError:  # pragma: no cover
    keyring = None


def env_var_for_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized == "openai":
        return "OPENAI_API_KEY"
    if normalized == "gemini":
        return "GEMINI_API_KEY"
    raise ValueError(f"Unsupported provider: {provider}")


def get_api_key(provider: str) -> str | None:
    env_var = env_var_for_provider(provider)
    env_value = os.getenv(env_var)
    if env_value:
        return env_value

    if keyring is None:
        return None

    try:
        return keyring.get_password(SERVICE_NAME, provider.strip().lower())
    except Exception:
        return None


def store_api_key(provider: str, api_key: str) -> bool:
    if keyring is None:
        return False

    try:
        keyring.set_password(SERVICE_NAME, provider.strip().lower(), api_key)
        return True
    except Exception:
        return False
