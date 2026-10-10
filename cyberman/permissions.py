from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import winreg
except Exception:  # pragma: no cover - Windows-only optional import
    winreg = None

from cyberman.paths import startup_target


STARTUP_VALUE_NAME = "Cyberman"
STARTUP_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
STARTUP_TASK_NAME = "Cyberman"


@dataclass
class StartupStatus:
    enabled: bool
    message: str


def _startup_command(script_path: Path) -> str:
    target = script_path.resolve()
    if target.suffix.lower() == ".exe":
        return subprocess.list2cmdline([str(target)])

    python_exe = Path(sys.executable).resolve()
    return subprocess.list2cmdline([str(python_exe), str(target)])


def startup_script_path() -> Path:
    return startup_target()


def _open_run_key(access: int):
    if winreg is None:
        raise FileNotFoundError("Windows registry unavailable")
    return winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_PATH, 0, access)


def _read_registry_startup_value() -> str | None:
    if winreg is None:
        return None
    try:
        with _open_run_key(winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, STARTUP_VALUE_NAME)
            return str(value)
    except FileNotFoundError:
        return None
    except OSError:
        return None


def _legacy_task_exists() -> bool:
    try:
        result = subprocess.run(
            ["schtasks", "/Query", "/TN", STARTUP_TASK_NAME],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0


def _remove_legacy_task() -> None:
    try:
        subprocess.run(
            ["schtasks", "/Delete", "/F", "/TN", STARTUP_TASK_NAME],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None
    except Exception:
        return None


def startup_status() -> StartupStatus:
    if winreg is None:
        return StartupStatus(_legacy_task_exists(), "Enabled" if _legacy_task_exists() else "Unavailable")
    registry_value = _read_registry_startup_value()
    if registry_value:
        return StartupStatus(True, "Enabled")
    if _legacy_task_exists():
        return StartupStatus(True, "Enabled (legacy task)")
    return StartupStatus(False, "Disabled")


def enable_startup(script_path: Path) -> StartupStatus:
    if winreg is None:
        return StartupStatus(False, "Unavailable")
    try:
        _remove_legacy_task()
        command = _startup_command(script_path)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_PATH) as key:
            winreg.SetValueEx(key, STARTUP_VALUE_NAME, 0, winreg.REG_SZ, command)
        return StartupStatus(True, "Enabled")
    except Exception as exc:
        return StartupStatus(False, str(exc) or "Could not enable startup")


def disable_startup() -> StartupStatus:
    if winreg is None:
        _remove_legacy_task()
        return StartupStatus(False, "Disabled")
    try:
        with _open_run_key(winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, STARTUP_VALUE_NAME)
            except FileNotFoundError:
                pass
    except FileNotFoundError:
        pass
    except Exception as exc:
        return StartupStatus(False, str(exc) or "Could not disable startup")

    _remove_legacy_task()
    return StartupStatus(False, "Disabled")
