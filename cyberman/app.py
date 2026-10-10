from __future__ import annotations

import os
import sys

from cyberman.paths import config_path, history_path, migrate_legacy_data
from cyberman.permissions import enable_startup, startup_script_path, startup_status
from cyberman.runtime import AssistantRuntime
from cyberman.config import AppConfig, load_config, save_config
from cyberman.version import app_title


def _print_banner(config: AppConfig) -> None:
    print("=" * 60)
    print(f"{app_title(config.assistant_name)} online")
    print(f"Mode: {config.ai_mode} | Wake word: {config.wake_word}")
    print("Say the wake word, then speak a command.")
    print("=" * 60)


def _ensure_startup_enabled() -> None:
    if not getattr(sys, "frozen", False):
        return
    status = startup_status()
    if status.enabled:
        return
    result = enable_startup(startup_script_path())
    if result.enabled:
        print("[startup] Enabled app auto-start at logon.")
    else:
        print(f"[startup] {result.message}")

def main() -> int:
    migrate_legacy_data()
    config_file = config_path()
    config = load_config(config_file)
    history_file = history_path()

    if os.getenv("CYBERMAN_CONSOLE", "").strip().lower() not in {"1", "true", "yes"}:
        try:
            from cyberman.gui.dashboard import launch_dashboard

            return launch_dashboard(config, config_file)
        except Exception as exc:
            print(f"[dashboard unavailable] {exc}")
            print("[console mode] Falling back to terminal assistant.")

    runtime = AssistantRuntime(config, history_path=history_file)
    listener = runtime.listener

    def _console_confirm(prompt: str) -> bool:
        while True:
            try:
                answer = input(f"{prompt} [y/n]: ").strip().lower()
            except EOFError:
                return False
            if answer in {"y", "yes"}:
                return True
            if answer in {"n", "no"}:
                return False

    runtime.executor.confirm_callback = _console_confirm

    _print_banner(config)
    print(f"Input mode: {listener.mode_label}")

    try:
        while True:
            text = listener.listen_once()
            if text is None:
                continue

            print("Thinking...")
            result = runtime.process_text(text)
            for event in runtime.drain_events():
                if event.kind == "user":
                    print(f"You: {event.message}")
                elif event.kind == "preview":
                    print(f"Preview: {event.message}")
                elif event.kind == "log":
                    print(event.message)
                elif event.kind == "assistant":
                    print(f"{config.assistant_name}: {event.message}")
                elif event.kind == "status":
                    print(event.message)
                elif event.kind == "error":
                    print(f"Error: {event.message}")
                elif event.kind == "heard":
                    print(f"Heard: {event.message}")

            if text.strip().lower() in {"quit", "exit"} or result.response == "Powering down.":
                break
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        save_config(config, config_file)

    return 0

