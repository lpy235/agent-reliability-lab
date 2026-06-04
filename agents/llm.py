from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class LLMResponse:
    text: str
    tokens: dict[str, int]
    cost: float | None = None


class RuleBasedLLMClient:
    def complete(self, prompt: str) -> LLMResponse:
        question = self._extract_question(prompt)
        if re.search(r"\b(run|start|server|api)\b", question, flags=re.IGNORECASE) and "uvicorn" in prompt:
            text = "Run the API with `uvicorn app.main:app --reload`."
        elif re.search(r"\b(database|configure|config)\b", question, flags=re.IGNORECASE) and "DATABASE_URL" in prompt:
            text = "Set `DATABASE_URL` in the environment before starting the service."
        elif "DATABASE_URL" in prompt:
            text = "Set `DATABASE_URL` in the environment before starting the service."
        elif "uvicorn" in prompt:
            text = "Run the API with `uvicorn app.main:app --reload`."
        else:
            text = "I can answer based on the retrieved local documentation."

        prompt_tokens = len(prompt.split())
        completion_tokens = len(text.split())
        return LLMResponse(
            text=text,
            tokens={"prompt": prompt_tokens, "completion": completion_tokens, "total": prompt_tokens + completion_tokens},
        )

    def _extract_question(self, prompt: str) -> str:
        match = re.search(r"Question:\s*(.+?)(?:\n\n|\nContext:|$)", prompt, flags=re.DOTALL)
        return match.group(1).strip() if match else prompt


class OpenAICompatibleClient:
    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None, base_url: str | None = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAICompatibleClient")

    def complete(self, prompt: str) -> LLMResponse:
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0},
            timeout=30,
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResponse(
            text=text,
            tokens={
                "prompt": int(usage.get("prompt_tokens", 0)),
                "completion": int(usage.get("completion_tokens", 0)),
                "total": int(usage.get("total_tokens", 0)),
            },
            cost=None,
        )
