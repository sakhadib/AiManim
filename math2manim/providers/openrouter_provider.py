"""OpenRouter provider implementation using the chat completions API."""

from __future__ import annotations

import json
import os
from typing import Any
import urllib.error
import urllib.request

from .base import LLMProvider


class OpenRouterProvider(LLMProvider):
    """Minimal OpenRouter chat completions client."""

    endpoint = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

    def generate(self, prompt: str, *, model: str | None = None, system_prompt: str | None = None) -> str:
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured")
        if not model:
            raise RuntimeError("OpenRouter requires a model id")

        payload: dict[str, object] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are a precise assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        data = json.dumps(payload).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        site_url = os.getenv("OPENROUTER_SITE_URL")
        app_name = os.getenv("OPENROUTER_APP_NAME")
        if site_url:
            headers["HTTP-Referer"] = site_url
        if app_name:
            headers["X-Title"] = app_name

        request = urllib.request.Request(
            self.endpoint,
            data=data,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenRouter request failed: {details}") from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"OpenRouter network error: {error}") from error

        body = json.loads(raw)
        return _message_text(body["choices"][0]["message"]["content"]).strip()


def _message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts)
    return str(content)
