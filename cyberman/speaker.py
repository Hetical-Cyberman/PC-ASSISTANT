from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cyberman.config import AppConfig

try:
    import pyttsx3
except Exception:  # pragma: no cover - optional dependency
    pyttsx3 = None


@dataclass
class Speaker:
    config: AppConfig

    def __post_init__(self) -> None:
        self._engine = None
        self._current_voice_gender = None
        if pyttsx3 is None:
            return

        self._initialize_engine()

    def _initialize_engine(self) -> None:
        if pyttsx3 is None:
            return

        try:
            self._engine = pyttsx3.init()
            self.refresh()
        except Exception:
            self._engine = None

    def _select_voice(self) -> None:
        if self._engine is None:
            return

        try:
            voices = self._engine.getProperty("voices")
            if not voices:
                return
            desired = self.config.voice_gender.lower()
            for voice in voices:
                label = f"{getattr(voice, 'name', '')} {getattr(voice, 'id', '')}".lower()
                if desired == "female" and "female" in label:
                    self._engine.setProperty("voice", voice.id)
                    return
                if desired == "male" and "male" in label:
                    self._engine.setProperty("voice", voice.id)
                    return
        except Exception:
            return

    def say(self, text: str) -> None:
        if self._engine is None:
            print(f"[speech disabled] {text}")
            return

        self._engine.say(text)
        self._engine.runAndWait()

    def refresh(self) -> None:
        if self._engine is None:
            return

        try:
            self._engine.setProperty("rate", self.config.speech_rate)
            if self._current_voice_gender != self.config.voice_gender.lower():
                self._select_voice()
                self._current_voice_gender = self.config.voice_gender.lower()
        except Exception:
            return
