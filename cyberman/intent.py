from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from cyberman.config import AppConfig


@dataclass(frozen=True)
class CommandIntent:
    action: str
    args: tuple[str, ...] = ()
    source: str = "heuristic"


_SUPPORTED_ACTIONS = [
    "open_app",
    "close_app",
    "open_url",
    "help",
    "about",
    "volume_up",
    "volume_down",
    "volume_mute",
    "brightness_up",
    "brightness_down",
    "battery_status",
    "shutdown",
    "restart",
    "sleep",
    "voice_status",
    "copy_path",
    "move_path",
    "rename_path",
    "delete_path",
    "create_file",
    "read_file",
    "search_files",
    "list_files",
    "chat",
    "type_text",
    "type_text_in_app",
]


def infer_command_intent(
    text: str,
    config: AppConfig,
    claude_backend: Any,
    ollama_backend: Any,
) -> CommandIntent | None:
    heuristic = _heuristic_intent(text)
    if heuristic is not None:
        return heuristic

    return _ai_intent(text, config, claude_backend, ollama_backend)


def _heuristic_intent(text: str) -> CommandIntent | None:
    lower = text.strip().lower()
    if not lower:
        return None

    open_match = re.search(r"(?:open|open up|launch|start|run|bring up|show)\s+(.+)$", lower)
    if open_match:
        target = open_match.group(1).strip()
        if target.startswith(("http://", "https://", "www.")):
            return CommandIntent("open_url", (target,), "heuristic")
        return CommandIntent("open_app", (target,), "heuristic")

    close_match = re.search(r"(?:close|quit|exit|shut down|shut|terminate|kill|stop|end|force close)\s+(.+)$", lower)
    if close_match:
        return CommandIntent("close_app", (close_match.group(1).strip(),), "heuristic")

    if any(word in lower for word in ("brightness", "screen brightness", "display brightness")):
        if any(word in lower for word in ("down", "lower", "reduce", "decrease", "dim", "less", "dimmer")):
            return CommandIntent("brightness_down", (), "heuristic")
        if any(word in lower for word in ("up", "raise", "increase", "brighter", "more")):
            return CommandIntent("brightness_up", (), "heuristic")

    if any(word in lower for word in ("volume", "sound")):
        if any(word in lower for word in ("up", "raise", "increase", "louder")):
            return CommandIntent("volume_up", (), "heuristic")
        if any(word in lower for word in ("down", "lower", "reduce", "decrease", "quieter")):
            return CommandIntent("volume_down", (), "heuristic")
        if any(word in lower for word in ("mute", "silence")):
            return CommandIntent("volume_mute", (), "heuristic")

    if any(word in lower for word in ("battery", "power level", "charge")):
        return CommandIntent("battery_status", (), "heuristic")

    if any(word in lower for word in ("sleep", "suspend")):
        return CommandIntent("sleep", (), "heuristic")
    if any(word in lower for word in ("shutdown", "shut down", "power off")):
        return CommandIntent("shutdown", (), "heuristic")
    if any(word in lower for word in ("restart", "reboot", "start over")):
        return CommandIntent("restart", (), "heuristic")

    type_context_match = re.search(
        r"^(?:type|dictate|write|insert)(?:\s+text)?\s+(.+?)\s+(?:into|in|on|inside)\s+(?:the\s+)?(.+)$",
        text.strip(),
        flags=re.IGNORECASE,
    )
    if type_context_match:
        typed = type_context_match.group(1).strip()
        target = re.sub(
            r"^(?:the|a|an|my)\s+",
            "",
            type_context_match.group(2).strip(),
            flags=re.IGNORECASE,
        ).strip()
        if typed and target:
            return CommandIntent("type_text_in_app", (typed, target), "heuristic")

    type_match = re.search(r"^(?:type|dictate|write|insert)(?:\s+text)?\s+(.+)$", text.strip(), flags=re.IGNORECASE)
    if type_match:
        typed = type_match.group(1).strip()
        typed = re.sub(
            r"\s+(?:into|in|on|inside)\s+(?:the\s+)?(?:notepad|word|excel|chrome|edge|file manager|file explorer|explorer|document|sheet|spreadsheet|window|app|application)$",
            "",
            typed,
            flags=re.IGNORECASE,
        ).strip()
        if typed:
            return CommandIntent("type_text", (typed,), "heuristic")

    return None


def _ai_intent(
    text: str,
    config: AppConfig,
    claude_backend: Any,
    ollama_backend: Any,
) -> CommandIntent | None:
    mode = config.ai_mode.lower().strip()
    providers: list[tuple[str, Any]] = []

    if mode in {"auto", "online", "online only"}:
        providers.append(("claude", claude_backend))
    if mode in {"auto", "offline", "offline only"}:
        providers.append(("ollama", ollama_backend))

    prompt = _intent_prompt(text, config.assistant_name)
    for provider_name, provider in providers:
        if not getattr(provider, "ready", False):
            continue
        try:
            response = provider.chat(prompt)
        except Exception:
            continue
        if not getattr(response, "ok", False):
            continue
        intent = _parse_intent_response(getattr(response, "response", ""), provider_name)
        if intent is not None:
            return intent

    return None


def _intent_prompt(text: str, assistant_name: str) -> str:
    actions = ", ".join(_SUPPORTED_ACTIONS)
    return (
        f"You are a command interpreter for {assistant_name}. "
        "Translate the user's message into a single assistant intent. "
        "Return ONLY a JSON object with keys action and args. "
        f"Allowed actions: {actions}. "
        "Use action=chat if the message is not an OS command. "
        "Args must be an array of strings. "
        f"Message: {text!r}"
    )


def _parse_intent_response(raw: str, source: str) -> CommandIntent | None:
    candidate = raw.strip()
    if not candidate:
        return None
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        if candidate.startswith("json"):
            candidate = candidate[4:].strip()
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        payload = json.loads(candidate[start : end + 1])
    except Exception:
        return None

    action = str(payload.get("action", "chat")).strip() or "chat"
    args_raw = payload.get("args", [])
    if not isinstance(args_raw, list):
        args_raw = []
    args = tuple(str(item).strip() for item in args_raw if str(item).strip())
    return CommandIntent(action=action, args=args, source=source)


