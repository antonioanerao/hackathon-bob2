import os
import json

import requests
from dotenv import load_dotenv


load_dotenv()


class OllamaClient:
    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
    ):
        self.model = (
            model
            or os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
        )

        self.base_url = (
            base_url
            or os.getenv(
                "OLLAMA_URL",
                "http://127.0.0.1:11434"
            )
        ).rstrip("/")

    def chat_json(
        self,
        system: str,
        prompt: str,
    ):
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
            timeout=600,
        )

        response.raise_for_status()

        content = response.json()["message"]["content"]

        return json.loads(content)