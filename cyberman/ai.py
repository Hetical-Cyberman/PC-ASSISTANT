from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from cyberman.config import AppConfig


@dataclass
class AIResponse:
    ok: bool
    response: str
    provider: str
    detail: str | None = None


def build_system_prompt(config: AppConfig) -> str:
    return (
        f"You are {config.assistant_name}, a calm, concise Windows assistant inspired by JARVIS. "
        "Help with practical commands, short explanations, and clear next actions. "
        "Prefer brief answers unless the user asks for detail. "
        "If the user is asking for an OS action, help them understand what will happen."
    )


class ClaudeBackend:
    def __init__(self, config: AppConfig):
        self.config = config
        self._client = None
        self._ready_reason = None

        api_key = os.getenv("ANTHROPIC_API_KEY") or config.extra.get("anthropic_api_key")
        if not api_key:
            self._ready_reason = "Missing Anthropic API key."
            return

        try:
            from anthropic import Anthropic

            self._client = Anthropic(api_key=api_key)
        except Exception as exc:  # pragma: no cover - optional dependency
            self._ready_reason = f"Claude client unavailable: {exc}"

    @property
    def ready(self) -> bool:
        return self._client is not None

    @property
    def ready_reason(self) -> str | None:
        return self._ready_reason

    def chat(self, user_text: str) -> AIResponse:
        assert self._client is not None

        try:
            message = self._client.messages.create(
                model=self.config.claude_model,
                max_tokens=256,
                system=build_system_prompt(self.config),
                messages=[
                    {
                        "role": "user",
                        "content": user_text,
                    }
                ],
            )
            text = self._extract_text(message)
            if text:
                return AIResponse(True, text, "claude")
            return AIResponse(False, "Claude returned no text.", "claude")
        except Exception as exc:
            return AIResponse(False, f"Claude failed: {exc}", "claude", detail=str(exc))

    @staticmethod
    def _extract_text(message: Any) -> str:
        parts = getattr(message, "content", None) or []
        fragments: list[str] = []
        for part in parts:
            text = getattr(part, "text", None)
            if text:
                fragments.append(text)
        return "".join(fragments).strip()


class OllamaBackend:
    def __init__(self, config: AppConfig):
        self.config = config
        self._client = None
        self._ready_reason = None

        try:
            import ollama

            self._client = ollama
        except Exception as exc:  # pragma: no cover - optional dependency
            self._ready_reason = f"Ollama client unavailable: {exc}"

    @property
    def ready(self) -> bool:
        return self._client is not None

    @property
    def ready_reason(self) -> str | None:
        return self._ready_reason

    def chat(self, user_text: str) -> AIResponse:
        assert self._client is not None

        try:
            result = self._client.chat(
                model=self.config.ollama_model,
                messages=[
                    {
                        "role": "system",
                        "content": build_system_prompt(self.config),
                    },
                    {
                        "role": "user",
                        "content": user_text,
                    },
                ],
            )
            message = result.get("message", {})
            text = (message.get("content") or "").strip()
            if text:
                return AIResponse(True, text, "ollama")
            return AIResponse(False, "Ollama returned no text.", "ollama")
        except Exception as exc:
            return AIResponse(False, f"Ollama failed: {exc}", "ollama", detail=str(exc))
