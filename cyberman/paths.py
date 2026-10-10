from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Cyberman"
LEGACY_CONFIG_DIR = Path("config")


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_data_dir() -> Path:
    base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
    if base:
        return Path(base) / APP_NAME
    return Path.home() / f".{APP_NAME.lower()}"


def config_path() -> Path:
    return app_data_dir() / "settings.json"


def history_path() -> Path:
    return app_data_dir() / "history.jsonl"


def legacy_config_path() -> Path:
    return LEGACY_CONFIG_DIR / "settings.json"


def legacy_history_path() -> Path:
    return LEGACY_CONFIG_DIR / "history.jsonl"


def migrate_legacy_data() -> None:
    target_dir = app_data_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    legacy_config = legacy_config_path()
    new_config = config_path()
    if legacy_config.exists() and not new_config.exists():
        try:
            new_config.write_bytes(legacy_config.read_bytes())
        except Exception:
            pass

    legacy_history = legacy_history_path()
    new_history = history_path()
    if legacy_history.exists() and not new_history.exists():
        try:
            new_history.write_bytes(legacy_history.read_bytes())
        except Exception:
            pass


def startup_target() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve()
    return Path(__file__).resolve().parents[1] / "main.py"
