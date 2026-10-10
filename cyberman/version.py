from __future__ import annotations

APP_NAME = "Cyberman"
APP_VERSION = "0.1.0"


def app_title(base_name: str | None = None) -> str:
    name = base_name.strip() if base_name else APP_NAME
    return f"{name} v{APP_VERSION}"
