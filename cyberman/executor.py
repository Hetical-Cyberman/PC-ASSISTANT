from __future__ import annotations



import os
import re
import shutil

import subprocess

import time

import ctypes

import webbrowser

from dataclasses import dataclass

from pathlib import Path

from typing import Callable



from cyberman.config import AppConfig

try:
    import winreg
except Exception:  # pragma: no cover - Windows-only optional import
    winreg = None



try:

    import screen_brightness_control as sbc

except Exception:  # pragma: no cover - optional dependency

    sbc = None





@dataclass

class ExecutionResult:

    ok: bool

    message: str





@dataclass

class Executor:

    config: AppConfig

    confirm_callback: Callable[[str], bool] | None = None



    def _confirm(self, prompt: str) -> bool:

        if self.confirm_callback is None:

            return True

        try:

            return bool(self.confirm_callback(prompt))

        except Exception:

            return False



    def _app_command(self, app_name: str) -> str:
        app = re.sub(r'^(?:the|a|an|my)\s+', '', app_name.strip().lower())
        app = re.sub(r'\s+(?:app|application|program|software)$', '', app)
        known = {
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "edge": "msedge.exe",
            "microsoft edge": "msedge.exe",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "file": "explorer.exe",
            "file manager": "explorer.exe",
            "file browser": "explorer.exe",
            "files": "explorer.exe",
            "folder": "explorer.exe",
            "file explorer": "explorer.exe",
            "explorer": "explorer.exe",
            "windows explorer": "explorer.exe",
            "word": "WINWORD.EXE",
            "microsoft word": "WINWORD.EXE",
            "ms word": "WINWORD.EXE",
            "microsoft word": "WINWORD.EXE",
            "excel": "EXCEL.EXE",
            "microsoft excel": "EXCEL.EXE",
            "ms excel": "EXCEL.EXE",
            "microsoft excel": "EXCEL.EXE",
            "powerpoint": "POWERPNT.EXE",
            "microsoft powerpoint": "POWERPNT.EXE",
            "outlook": "OUTLOOK.EXE",
            "microsoft outlook": "OUTLOOK.EXE",
            "onenote": "ONENOTE.EXE",
            "microsoft onenote": "ONENOTE.EXE",
            "teams": "Teams.exe",
            "microsoft teams": "Teams.exe",
            "ms teams": "Teams.exe",
            "microsoft teams": "Teams.exe",
        }
        return self._resolve_app_path(known.get(app, app_name))

    def _resolve_app_path(self, command: str) -> str:
        candidate = command.strip().strip('"')
        if os.path.isabs(candidate) and Path(candidate).exists():
            return candidate

        exe_name = Path(candidate.split()[0]).name
        if winreg is not None and exe_name.lower().endswith('.exe'):
            app_paths = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe_name}"
            for hive in (getattr(winreg, 'HKEY_CURRENT_USER', None), getattr(winreg, 'HKEY_LOCAL_MACHINE', None)):
                if hive is None:
                    continue
                for flags in (0, getattr(winreg, 'KEY_WOW64_32KEY', 0), getattr(winreg, 'KEY_WOW64_64KEY', 0)):
                    try:
                        with winreg.OpenKey(hive, app_paths, 0, winreg.KEY_READ | flags) as key:
                            value, _ = winreg.QueryValueEx(key, None)
                            if value:
                                return str(value)
                    except Exception:
                        continue
        return candidate

    def open_app(self, app_name: str) -> ExecutionResult:
        command = self._app_command(app_name)
        try:
            if os.path.exists(command):
                subprocess.Popen([command], shell=False)
            else:
                subprocess.Popen(command, shell=True)
            return ExecutionResult(True, f"Opening {app_name}.")
        except Exception as exc:
            return ExecutionResult(False, f"Could not open {app_name}: {exc}")

    def close_app(self, app_name: str) -> ExecutionResult:
        try:
            if not self._confirm(f"Close {app_name} now?"):
                return ExecutionResult(False, f"Close cancelled for {app_name}.")
            command = self._app_command(app_name)
            image_name = Path(command.strip().strip('"')).name if os.path.isabs(command.strip().strip('"')) else Path(command.split()[0]).name
            if not image_name.lower().endswith('.exe'):
                image_name = f"{image_name}.exe"
            result = subprocess.run(["taskkill", "/f", "/im", image_name], capture_output=True, text=True)
            if result.returncode == 0:
                return ExecutionResult(True, f"Closed {app_name}.")
            detail = result.stderr.strip() or result.stdout.strip() or f"Could not close {app_name}."
            return ExecutionResult(False, detail)
        except Exception as exc:
            return ExecutionResult(False, f"Could not close {app_name}: {exc}")

    def open_url(self, url: str) -> ExecutionResult:

        try:

            webbrowser.open(url)

            return ExecutionResult(True, f"Opening {url}.")

        except Exception as exc:

            return ExecutionResult(False, f"Could not open {url}: {exc}")



    def copy_path(self, source: str, destination: str) -> ExecutionResult:

        try:

            src = Path(source).expanduser()

            dst = Path(destination).expanduser()

            if dst.exists() and not self._confirm(f"Overwrite existing destination '{dst}'?"):

                return ExecutionResult(False, f"Copy cancelled for {src} -> {dst}.")

            if src.is_dir():

                shutil.copytree(src, dst, dirs_exist_ok=True)

            else:

                if dst.is_dir():

                    shutil.copy2(src, dst / src.name)

                else:

                    shutil.copy2(src, dst)

            return ExecutionResult(True, f"Copied {src} to {dst}.")

        except Exception as exc:

            return ExecutionResult(False, f"Copy failed: {exc}")



    def move_path(self, source: str, destination: str) -> ExecutionResult:

        try:

            src = Path(source).expanduser()

            dst = Path(destination).expanduser()

            if dst.exists() and not self._confirm(f"Overwrite existing destination '{dst}'?"):

                return ExecutionResult(False, f"Move cancelled for {src} -> {dst}.")

            shutil.move(str(src), str(dst))

            return ExecutionResult(True, f"Moved {src} to {dst}.")

        except Exception as exc:

            return ExecutionResult(False, f"Move failed: {exc}")



    def rename_path(self, source: str, destination: str) -> ExecutionResult:

        try:

            src = Path(source).expanduser()

            dst = Path(destination).expanduser()

            if dst.exists() and not self._confirm(f"Replace existing path '{dst}'?"):

                return ExecutionResult(False, f"Rename cancelled for {src} -> {dst}.")

            src.rename(dst)

            return ExecutionResult(True, f"Renamed {src} to {dst}.")

        except Exception as exc:

            return ExecutionResult(False, f"Rename failed: {exc}")



    def delete_path(self, target: str) -> ExecutionResult:

        try:

            path = Path(target).expanduser()

            if not self._confirm(f"Delete '{path}' permanently?"):

                return ExecutionResult(False, f"Delete cancelled for {path}.")

            if path.is_dir():

                shutil.rmtree(path)

            else:

                path.unlink()

            return ExecutionResult(True, f"Deleted {path}.")

        except Exception as exc:

            return ExecutionResult(False, f"Delete failed: {exc}")



    def search_files(self, root: str, query: str) -> ExecutionResult:

        try:

            root_path = Path(root).expanduser()

            matches = []

            for path in root_path.rglob("*"):

                if query.lower() in path.name.lower():

                    matches.append(str(path))

                if len(matches) >= 10:

                    break

            if not matches:

                return ExecutionResult(True, f"No matches for {query}.")

            return ExecutionResult(True, "Matches: " + ", ".join(matches))

        except Exception as exc:

            return ExecutionResult(False, f"Search failed: {exc}")



    def list_files(self, root: str) -> ExecutionResult:

        try:

            root_path = Path(root).expanduser()

            if not root_path.exists():

                return ExecutionResult(False, f"{root_path} does not exist.")

            if not root_path.is_dir():

                return ExecutionResult(False, f"{root_path} is not a folder.")

            entries = sorted(path.name for path in root_path.iterdir())

            if not entries:

                return ExecutionResult(True, f"{root_path} is empty.")

            preview = ", ".join(entries[:20])

            if len(entries) > 20:

                preview += f" ... and {len(entries) - 20} more"

            return ExecutionResult(True, f"Contents of {root_path}: {preview}")

        except Exception as exc:

            return ExecutionResult(False, f"List files failed: {exc}")



    def create_folder(self, target: str) -> ExecutionResult:

        try:

            path = Path(target).expanduser()

            if path.exists():

                return ExecutionResult(True, f"{path} already exists.")

            path.mkdir(parents=True, exist_ok=False)

            return ExecutionResult(True, f"Created folder {path}.")

        except Exception as exc:

            return ExecutionResult(False, f"Create folder failed: {exc}")



    def create_file(self, target: str, content: str) -> ExecutionResult:

        try:

            path = Path(target).expanduser()

            if path.exists() and not self._confirm(f"Overwrite existing file '{path}'?"):

                return ExecutionResult(False, f"Create cancelled for {path}.")

            path.parent.mkdir(parents=True, exist_ok=True)

            path.write_text(content, encoding="utf-8")

            return ExecutionResult(True, f"Created {path}.")

        except Exception as exc:

            return ExecutionResult(False, f"Create failed: {exc}")



    def read_file(self, target: str, limit: int = 1200) -> ExecutionResult:

        try:

            path = Path(target).expanduser()

            content = path.read_text(encoding="utf-8")

            if not content.strip():

                return ExecutionResult(True, f"{path} is empty.")

            if len(content) > limit:

                return ExecutionResult(True, content[:limit].rstrip() + "...")

            return ExecutionResult(True, content)

        except Exception as exc:

            return ExecutionResult(False, f"Read failed: {exc}")


    def type_text(self, text: str) -> ExecutionResult:
        try:
            import keyboard

            keyboard.write(text)
            return ExecutionResult(True, f"Typed {len(text)} characters.")
        except Exception as exc:
            return ExecutionResult(False, f"Typing failed: {exc}")

    def type_text_into_app(self, text: str, app_name: str) -> ExecutionResult:
        open_result = self.open_app(app_name)
        if not open_result.ok:
            return open_result
        try:
            time.sleep(0.8)
            typed_result = self.type_text(text)
            if typed_result.ok:
                return ExecutionResult(True, f"Opened {app_name} and typed {len(text)} characters.")
            return typed_result
        except Exception as exc:
            return ExecutionResult(False, f"Typing into {app_name} failed: {exc}")



    def volume_up(self) -> ExecutionResult:

        return self._send_volume_key(0xAF, "Volume raised.")



    def volume_down(self) -> ExecutionResult:

        return self._send_volume_key(0xAE, "Volume lowered.")



    def volume_mute(self) -> ExecutionResult:

        return self._send_volume_key(0xAD, "Volume muted or unmuted.")



    def battery_status(self) -> ExecutionResult:

        try:

            class SYSTEM_POWER_STATUS(ctypes.Structure):

                _fields_ = [

                    ("ACLineStatus", ctypes.c_byte),

                    ("BatteryFlag", ctypes.c_byte),

                    ("BatteryLifePercent", ctypes.c_byte),

                    ("SystemStatusFlag", ctypes.c_byte),

                    ("BatteryLifeTime", ctypes.c_ulong),

                    ("BatteryFullLifeTime", ctypes.c_ulong),

                ]



            status = SYSTEM_POWER_STATUS()

            if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):  # type: ignore[attr-defined]

                return ExecutionResult(False, "Could not read battery status.")

            if status.BatteryLifePercent == 255:

                return ExecutionResult(True, "Battery status unavailable.")

            ac = "charging" if status.ACLineStatus == 1 else "on battery"

            return ExecutionResult(True, f"Battery at {status.BatteryLifePercent}% ({ac}).")

        except Exception as exc:

            return ExecutionResult(False, f"Battery status failed: {exc}")



    def brightness_up(self, step: int = 10) -> ExecutionResult:

        return self._set_brightness_relative(abs(step), "Brightness increased.")



    def brightness_down(self, step: int = 10) -> ExecutionResult:

        return self._set_brightness_relative(-abs(step), "Brightness decreased.")



    def shutdown(self) -> ExecutionResult:

        if not self._confirm("Shut down this computer now?"):

            return ExecutionResult(False, "Shutdown cancelled.")

        return self._run_simple_command(["shutdown", "/s", "/t", "0"], "Shutting down.")



    def restart(self) -> ExecutionResult:

        if not self._confirm("Restart this computer now?"):

            return ExecutionResult(False, "Restart cancelled.")

        return self._run_simple_command(["shutdown", "/r", "/t", "0"], "Restarting.")



    def sleep(self) -> ExecutionResult:

        if not self._confirm("Put this computer to sleep now?"):

            return ExecutionResult(False, "Sleep cancelled.")

        attempts = [
            ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
            ["shutdown", "/h"],
        ]
        last_error: str | None = None
        for command in attempts:
            result = self._run_simple_command(command, "Sleeping.")
            if result.ok:
                return result
            last_error = result.message
        return ExecutionResult(False, last_error or "Sleep failed.")



    def _send_volume_key(self, key_code: int, message: str) -> ExecutionResult:

        try:

            user32 = ctypes.windll.user32  # type: ignore[attr-defined]

            user32.keybd_event(key_code, 0, 0, 0)

            user32.keybd_event(key_code, 0, 2, 0)

            return ExecutionResult(True, message)

        except Exception as exc:

            return ExecutionResult(False, f"Volume control failed: {exc}")



    def _run_simple_command(self, command: list[str], message: str) -> ExecutionResult:

        try:

            subprocess.Popen(command, shell=False)

            return ExecutionResult(True, message)

        except Exception as exc:

            return ExecutionResult(False, f"{message[:-1]} failed: {exc}")



    def _set_brightness_relative(self, delta: int, message: str) -> ExecutionResult:

        try:

            if sbc is not None:

                current = self._get_brightness_level()

                if current is not None:

                    target = max(0, min(100, current + delta))

                    sbc.set_brightness(target)

                    return ExecutionResult(True, message)

            script = f"""

$brightness = Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness -ErrorAction SilentlyContinue

$methods = Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods -ErrorAction SilentlyContinue

if (-not $brightness -or -not $methods) {{

    exit 1

}}

$current = [int]$brightness.CurrentBrightness

$target = [Math]::Max(0, [Math]::Min(100, $current + {delta}))

foreach ($method in $methods) {{

    $method.WmiSetBrightness(1, $target) | Out-Null

}}

exit 0

"""

            result = subprocess.run(

                ["powershell", "-NoProfile", "-Command", script],

                capture_output=True,

                text=True,

            )

            if result.returncode != 0:

                detail = result.stderr.strip() or result.stdout.strip() or "Brightness controls not supported on this device."

                return ExecutionResult(False, f"Brightness control failed: {detail}")

            return ExecutionResult(True, message)

        except Exception as exc:

            return ExecutionResult(False, f"Brightness control failed: {exc}")



    def _get_brightness_level(self) -> int | None:

        if sbc is None:

            return None

        try:

            value = sbc.get_brightness()

            if isinstance(value, list) and value:

                return int(value[0])

            if isinstance(value, int):

                return int(value)

        except Exception:

            return None

        return None


from time

