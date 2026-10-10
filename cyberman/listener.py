from __future__ import annotations

import os
import struct
from dataclasses import dataclass
from typing import Protocol

try:
    import winsound
except Exception:  # pragma: no cover - Windows-only optional import
    winsound = None


class Listener(Protocol):
    mode_label: str
    ready_reason: str | None

    def listen_once(self) -> str | None:
        """Return the next command or ``None`` if nothing was captured."""


class ConsoleListener:
    mode_label = "console"
    ready_reason = None

    def listen_once(self) -> str | None:
        try:
            text = input("> ").strip()
        except EOFError:
            return "quit"
        return text or None

    def close(self) -> None:
        return None


def play_voice_cue(kind: str) -> None:
    if winsound is None:
        return
    try:
        if kind == "wake":
            winsound.MessageBeep(winsound.MB_OK)
        else:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        return


@dataclass
class SpeechRecognitionMicListener:
    language: str = "en"
    energy_threshold: int = 300
    phrase_time_limit: int = 8
    silence_timeout: int = 20
    transcription_backend: str = "auto"

    def __post_init__(self) -> None:
        self.mode_label = "microphone"
        self._recognizer = None
        self._microphone = None
        self.ready_reason = None
        self._idle_armed = False

        try:
            import speech_recognition as sr
        except Exception as exc:  # pragma: no cover - optional dependency
            self.ready_reason = f"SpeechRecognition unavailable: {exc}"
            return

        try:
            import pyaudio  # noqa: F401
        except Exception as exc:  # pragma: no cover - optional dependency
            self.ready_reason = f"PyAudio unavailable: {exc}"
            return

        try:
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = self.energy_threshold
            self._microphone = sr.Microphone()
        except Exception as exc:
            self.ready_reason = f"Microphone listener unavailable: {exc}"
            self._recognizer = None
            self._microphone = None

    @property
    def ready(self) -> bool:
        return self._recognizer is not None and self._microphone is not None

    def listen_once(self) -> str | None:
        if not self.ready:
            return None

        assert self._recognizer is not None
        assert self._microphone is not None

        import speech_recognition as sr

        wait_timeout = None if self._idle_armed else self.silence_timeout

        with self._microphone as source:
            try:
                audio = self._recognizer.listen(
                    source,
                    timeout=wait_timeout,
                    phrase_time_limit=self.phrase_time_limit,
                )
            except sr.WaitTimeoutError:
                self._idle_armed = True
                return None

        try:
            text = self._transcribe_audio(audio)
        except Exception as exc:
            print(f"[listener error] {exc}")
            return None

        if text:
            self._idle_armed = False
        return text

    def _transcribe_audio(self, audio) -> str | None:
        assert self._recognizer is not None

        import speech_recognition as sr

        backend = self.transcription_backend.lower().strip()
        attempts: list[str]
        if backend == "sphinx":
            attempts = ["sphinx"]
        elif backend == "google":
            attempts = ["google"]
        else:
            attempts = ["sphinx", "google"]

        for attempt in attempts:
            try:
                if attempt == "sphinx":
                    text = self._recognizer.recognize_sphinx(audio, language=self.language)
                else:
                    text = self._recognizer.recognize_google(audio, language=self.language)
                cleaned = (text or "").strip()
                if cleaned:
                    return cleaned
            except sr.UnknownValueError:
                continue
            except sr.RequestError:
                continue
            except Exception:
                continue

        return None

    def close(self) -> None:
        return None


@dataclass
class WakeWordMicListener:
    language: str = "en"
    wake_word: str = "Cyberman"
    porcupine_access_key: str | None = None
    porcupine_keyword_path: str | None = None
    sensitivity: float = 0.55
    phrase_time_limit: int = 8
    silence_timeout: int = 20
    energy_threshold: int = 300
    transcription_backend: str = "auto"

    def __post_init__(self) -> None:
        self.mode_label = "wake word"
        self.ready_reason = None
        self._porcupine = None
        self._pa = None
        self._stream = None
        self._recognizer = None
        self._microphone = None
        self._frame_length = None
        self._sample_rate = None

        access_key = self.porcupine_access_key or os.getenv("CYBERMAN_PORCUPINE_ACCESS_KEY")
        keyword_path = self.porcupine_keyword_path or os.getenv("CYBERMAN_PORCUPINE_KEYWORD_PATH")

        try:
            import pvporcupine
        except Exception as exc:  # pragma: no cover - optional dependency
            self.ready_reason = f"Porcupine unavailable: {exc}"
            return

        try:
            import pyaudio
            import speech_recognition as sr
        except Exception as exc:  # pragma: no cover - optional dependency
            self.ready_reason = f"Voice stack unavailable: {exc}"
            return

        if not access_key or not keyword_path:
            self.ready_reason = "Missing Porcupine access key or keyword path."
            return

        try:
            self._porcupine = pvporcupine.create(
                access_key=access_key,
                keyword_paths=[keyword_path],
                sensitivities=[self.sensitivity],
            )
            self._pa = pyaudio.PyAudio()
            self._frame_length = self._porcupine.frame_length
            self._sample_rate = self._porcupine.sample_rate
            self._stream = self._pa.open(
                rate=self._sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self._frame_length,
            )
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = self.energy_threshold
            self._microphone = sr.Microphone()
        except Exception as exc:
            self.ready_reason = f"Wake word listener unavailable: {exc}"
            self._cleanup()

    @property
    def ready(self) -> bool:
        return all(
            value is not None
            for value in (
                self._porcupine,
                self._pa,
                self._stream,
                self._recognizer,
                self._microphone,
            )
        )

    def listen_once(self) -> str | None:
        if not self.ready:
            return None

        assert self._porcupine is not None
        assert self._stream is not None

        try:
            print(f"Armed for {self.wake_word}...")
            while True:
                pcm = self._stream.read(self._porcupine.frame_length, exception_on_overflow=False)
                audio = struct.unpack_from(f"{self._porcupine.frame_length}h", pcm)
                result = self._porcupine.process(audio)
                if result >= 0:
                    print("Wake word detected.")
                    play_voice_cue("wake")
                    return self._capture_command()
        except KeyboardInterrupt:
            return "quit"
        except Exception as exc:
            print(f"[wake word error] {exc}")
            return None

    def _capture_command(self) -> str | None:
        assert self._recognizer is not None
        assert self._microphone is not None

        import speech_recognition as sr

        with self._microphone as source:
            try:
                audio = self._recognizer.listen(
                    source,
                    timeout=self.silence_timeout,
                    phrase_time_limit=self.phrase_time_limit,
                )
            except sr.WaitTimeoutError:
                self._idle_armed = True
                return None

        try:
            text = self._transcribe_audio(audio)
        except Exception as exc:
            print(f"[listener error] {exc}")
            return None

        if text:
            self._idle_armed = False
        return text

    def _transcribe_audio(self, audio) -> str | None:
        assert self._recognizer is not None

        import speech_recognition as sr

        backend = self.transcription_backend.lower().strip()
        attempts: list[str]
        if backend == "sphinx":
            attempts = ["sphinx"]
        elif backend == "google":
            attempts = ["google"]
        else:
            attempts = ["sphinx", "google"]

        for attempt in attempts:
            try:
                if attempt == "sphinx":
                    text = self._recognizer.recognize_sphinx(audio, language=self.language)
                else:
                    text = self._recognizer.recognize_google(audio, language=self.language)
                cleaned = (text or "").strip()
                if cleaned:
                    return cleaned
            except sr.UnknownValueError:
                continue
            except sr.RequestError:
                continue
            except Exception:
                continue

        return None

    def close(self) -> None:
        self._cleanup()

    def _cleanup(self) -> None:
        try:
            if self._stream is not None:
                self._stream.stop_stream()
                self._stream.close()
        except Exception:
            pass
        try:
            if self._pa is not None:
                self._pa.terminate()
        except Exception:
            pass
        self._stream = None
        self._pa = None


def create_listener(
    language: str = "en",
    wake_word: str = "Cyberman",
    porcupine_access_key: str | None = None,
    porcupine_keyword_path: str | None = None,
    porcupine_sensitivity: float = 0.55,
    transcription_backend: str = "auto",
) -> Listener:
    wake_listener = WakeWordMicListener(
        language=language,
        wake_word=wake_word,
        porcupine_access_key=porcupine_access_key,
        porcupine_keyword_path=porcupine_keyword_path,
        sensitivity=porcupine_sensitivity,
        transcription_backend=transcription_backend,
    )
    if wake_listener.ready:
        return wake_listener

    mic_listener = SpeechRecognitionMicListener(
        language=language,
        transcription_backend=transcription_backend,
    )
    if mic_listener.ready:
        if wake_listener.ready_reason:
            print(f"[wake word disabled] {wake_listener.ready_reason}")
        print("[wake word mode] Falling back to direct microphone input.")
        return mic_listener

    if mic_listener.ready_reason:
        print(f"[mic disabled] {mic_listener.ready_reason}")
    if wake_listener.ready_reason:
        print(f"[wake word disabled] {wake_listener.ready_reason}")
    print("[input mode] Falling back to console input.")
    return ConsoleListener()
