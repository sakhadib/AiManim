"""OpenAI provider implementation using HTTP API."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    """Minimal OpenAI chat completions client."""

    endpoint = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def generate(self, prompt: str, *, model: str | None = None, system_prompt: str | None = None) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        payload: dict[str, object] = {
            "model": model or "gpt-4.1-mini",
            "messages": [
                {"role": "system", "content": system_prompt or "You are a precise assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI request failed: {details}") from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"OpenAI network error: {error}") from error

        body = json.loads(raw)
        return body["choices"][0]["message"]["content"].strip()
