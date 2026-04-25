"""Gemini provider implementation using Generative Language API."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from .base import LLMProvider


class GeminiProvider(LLMProvider):
    """Minimal Gemini generateContent client."""

    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def generate(self, prompt: str, *, model: str | None = None, system_prompt: str | None = None) -> str:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")

        selected_model = model or "gemini-1.5-flash"
        endpoint = self.endpoint.format(model=selected_model)
        url = f"{endpoint}?{urllib.parse.urlencode({'key': self.api_key})}"

        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"System instructions: {system_prompt}"}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": 0.2},
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini request failed: {details}") from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"Gemini network error: {error}") from error

        body = json.loads(raw)
        return body["candidates"][0]["content"]["parts"][0]["text"].strip()
