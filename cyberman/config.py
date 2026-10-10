from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AppConfig:
    assistant_name: str = "Cyberman"
    voice_gender: str = "male"
    speech_rate: int = 180
    wake_word: str = "Cyberman"
    language: str = "en"
    ai_mode: str = "auto"
    claude_model: str = "claude-sonnet-4"
    ollama_model: str = "llama3"
    default_browser: str = "chrome"
    confirmed_delete: bool = False
    porcupine_access_key: str | None = None
    porcupine_keyword_path: str | None = None
    porcupine_sensitivity: float = 0.55
    extra: dict[str, Any] = field(default_factory=dict)


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        return AppConfig()

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    known_fields = {
        "assistant_name",
        "voice_gender",
        "speech_rate",
        "wake_word",
        "language",
        "ai_mode",
        "claude_model",
        "ollama_model",
        "default_browser",
        "confirmed_delete",
        "porcupine_access_key",
        "porcupine_keyword_path",
        "porcupine_sensitivity",
    }
    config_kwargs = {key: data[key] for key in known_fields if key in data}
    extra = {key: value for key, value in data.items() if key not in known_fields}
    return AppConfig(**config_kwargs, extra=extra)


def save_config(config: AppConfig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "assistant_name": config.assistant_name,
        "voice_gender": config.voice_gender,
        "speech_rate": config.speech_rate,
        "wake_word": config.wake_word,
        "language": config.language,
        "ai_mode": config.ai_mode,
        "claude_model": config.claude_model,
        "ollama_model": config.ollama_model,
        "default_browser": config.default_browser,
        "confirmed_delete": config.confirmed_delete,
        "porcupine_access_key": config.porcupine_access_key,
        "porcupine_keyword_path": config.porcupine_keyword_path,
        "porcupine_sensitivity": config.porcupine_sensitivity,
        **config.extra,
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
