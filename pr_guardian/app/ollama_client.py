from __future__ import annotations

import json
import os
from typing import Any

import requests
from dotenv import load_dotenv


load_dotenv()


class OllamaClient:
    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int = 600,
    ):
        self.model = (
            model
            or os.getenv(
                "OLLAMA_MODEL",
                "qwen2.5-coder:7b",
            )
        )

        self.base_url = (
            base_url
            or os.getenv(
                "OLLAMA_URL",
                "http://127.0.0.1:11434",
            )
        ).rstrip("/")

        self.timeout = timeout

    def chat_json(
        self,
        system: str,
        prompt: str,
    ) -> dict[str, Any]:

        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "stream": False,
                "format": "json",
                "messages": [
                    {
                        "role": "system",
                        "content": system,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                "options": {
                    "temperature": 0,
                },
            },
            timeout=self.timeout,
        )

        if not response.ok:
            raise RuntimeError(
                f"Ollama request failed "
                f"({response.status_code}): "
                f"{response.text}"
            )

        try:
            data = response.json()
        except requests.JSONDecodeError as exc:
            raise RuntimeError(
                "Ollama returned invalid HTTP JSON."
            ) from exc

        message = data.get(
            "message",
            {},
        )

        content = message.get(
            "content",
            "",
        )

        if not content:
            raise RuntimeError(
                "Ollama returned an empty response."
            )

        try:
            result = json.loads(
                content
            )
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Ollama returned invalid model JSON: "
                f"{content}"
            ) from exc

        if not isinstance(
            result,
            dict,
        ):
            raise RuntimeError(
                "Ollama JSON response must be an object."
            )

        return result