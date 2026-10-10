from __future__ import annotations

from dataclasses import dataclass
from threading import Thread
from typing import Callable

from cyberman.version import app_title

try:
    import pystray
    from PIL import Image, ImageDraw
except Exception:  # pragma: no cover - optional dependency
    pystray = None
    Image = None
    ImageDraw = None


@dataclass
class TrayController:
    title: str
    on_show: Callable[[], None]
    on_quit: Callable[[], None]

    def __post_init__(self) -> None:
        self.ready_reason = None
        self._icon = None
        self._thread: Thread | None = None

        if pystray is None or Image is None or ImageDraw is None:
            self.ready_reason = "Tray dependencies unavailable."
            return

        try:
            display = app_title(self.title)
            self._icon = pystray.Icon(display, self._build_image(), display, self._build_menu())
        except Exception as exc:  # pragma: no cover - optional dependency
            self.ready_reason = f"Tray unavailable: {exc}"
            self._icon = None

    @property
    def ready(self) -> bool:
        return self._icon is not None

    def start(self) -> None:
        if not self.ready:
            return
        if self._thread is not None and self._thread.is_alive():
            return
        self._thread = Thread(target=self._icon.run, name="cyberman-tray", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._icon is None:
            return
        try:
            self._icon.stop()
        except Exception:
            pass

    def set_title(self, title: str) -> None:
        self.title = title
        display = app_title(title)
        if self._icon is not None:
            try:
                self._icon.title = display
            except Exception:
                pass

    def _build_menu(self):
        return pystray.Menu(
            pystray.MenuItem("Open", self._menu_show, default=True),
            pystray.MenuItem("Quit", self._menu_quit),
        )

    def _menu_show(self, *_args) -> None:
        self.on_show()

    def _menu_quit(self, *_args) -> None:
        self.on_quit()

    def _build_image(self):
        image = Image.new("RGBA", (64, 64), (17, 24, 39, 255))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((8, 8, 56, 56), radius=12, fill=(37, 99, 235, 255))
        draw.text((20, 18), "C", fill="white")
        return image
