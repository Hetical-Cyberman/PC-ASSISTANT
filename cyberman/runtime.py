from __future__ import annotations















from dataclasses import dataclass, field







from pathlib import Path







from queue import Empty, Queue







from time import sleep







from threading import Event, Lock, Thread







from typing import Any















from cyberman.brain import Brain, BrainResult







from cyberman.config import AppConfig







from cyberman.history import HistoryEntry, HistoryStore







from cyberman.executor import Executor







from cyberman.listener import ConsoleListener, Listener, create_listener, play_voice_cue







from cyberman.speaker import Speaker























@dataclass







class RuntimeEvent:







    kind: str







    message: str







    data: dict[str, Any] = field(default_factory=dict)























@dataclass







class AssistantRuntime:







    config: AppConfig







    history_path: Path | None = None







    listener: Listener | None = None















    def __post_init__(self) -> None:







        self.speaker = Speaker(self.config)







        self.executor = Executor(config=self.config)







        self.executor.confirm_callback = self.request_confirmation







        self.brain = Brain(config=self.config, executor=self.executor, status_provider=self._voice_status_text)







        self.listener = self.listener or create_listener(







            language=self.config.language,







            wake_word=self.config.wake_word,







            porcupine_access_key=self.config.porcupine_access_key,







            porcupine_keyword_path=self.config.porcupine_keyword_path,







            porcupine_sensitivity=self.config.porcupine_sensitivity,







        )







        self._history_store = HistoryStore(self.history_path) if self.history_path is not None else None







        self._command_queue: Queue[str | None] = Queue()







        self._event_queue: Queue[RuntimeEvent] = Queue()







        self._stop_event = Event()







        self._state_lock = Lock()







        self._confirmation_lock = Lock()







        self._confirmation_event = Event()







        self._confirmation_result: bool | None = None







        self._state = "idle"
        self._voice_idle_notified = False







        self._worker: Thread | None = None







        self._voice_thread: Thread | None = None







        self._history_entries: list[HistoryEntry] = self._history_store.load() if self._history_store else []















    @property







    def state(self) -> str:







        with self._state_lock:







            return self._state















    @property







    def input_mode(self) -> str:







        return getattr(self.listener, "mode_label", "console")















    @property







    def history_entries(self) -> list[HistoryEntry]:







        return list(self._history_entries)















    @property







    def voice_enabled(self) -> bool:







        return not isinstance(self.listener, ConsoleListener)

















    def voice_status(self) -> str:



        return self._voice_status_text()



    def start(self) -> None:







        if self._worker is None or not self._worker.is_alive():







            self._worker = Thread(target=self._process_loop, name="cyberman-worker", daemon=True)







            self._worker.start()















        if self.voice_enabled and (self._voice_thread is None or not self._voice_thread.is_alive()):







            self._voice_thread = Thread(target=self._voice_loop, name="cyberman-voice", daemon=True)







            self._voice_thread.start()















    def stop(self) -> None:







        self._stop_event.set()







        self._command_queue.put(None)







        self._close_listener()







        self._emit("status", "Shutting down.", {"state": "offline"})







        self._confirmation_event.set()















    def submit_text(self, text: str) -> None:







        cleaned = text.strip()







        if cleaned:







            self._command_queue.put(cleaned)















    def respond_confirmation(self, accepted: bool) -> None:







        with self._confirmation_lock:







            self._confirmation_result = accepted







        self._confirmation_event.set()















    def request_confirmation(self, prompt: str, timeout: float = 30.0) -> bool:







        with self._confirmation_lock:







            self._confirmation_result = None







        self._confirmation_event.clear()







        self._emit("confirm", prompt, {"prompt": prompt})







        if not self._confirmation_event.wait(timeout=timeout):







            self._emit("log", f"Confirmation timed out: {prompt}")







            return False







        with self._confirmation_lock:







            return bool(self._confirmation_result)















    def reconfigure(self, config: AppConfig) -> None:







        self._close_listener()







        self.config.assistant_name = config.assistant_name







        self.config.voice_gender = config.voice_gender







        self.config.speech_rate = config.speech_rate







        self.config.wake_word = config.wake_word







        self.config.language = config.language







        self.config.ai_mode = config.ai_mode







        self.config.claude_model = config.claude_model







        self.config.ollama_model = config.ollama_model







        self.config.default_browser = config.default_browser







        self.config.confirmed_delete = config.confirmed_delete







        self.config.porcupine_access_key = config.porcupine_access_key







        self.config.porcupine_keyword_path = config.porcupine_keyword_path







        self.config.porcupine_sensitivity = config.porcupine_sensitivity







        self.config.extra = dict(config.extra)







        self.speaker.refresh()







        self.listener = create_listener(







            language=self.config.language,







            wake_word=self.config.wake_word,







            porcupine_access_key=self.config.porcupine_access_key,







            porcupine_keyword_path=self.config.porcupine_keyword_path,







            porcupine_sensitivity=self.config.porcupine_sensitivity,







        )







        if not isinstance(self.listener, ConsoleListener) and (







            self._voice_thread is None or not self._voice_thread.is_alive()







        ):







            self._voice_thread = Thread(target=self._voice_loop, name="cyberman-voice", daemon=True)







            self._voice_thread.start()







        self._emit("status", "Runtime refreshed.", {"state": self._state})















    def _close_listener(self) -> None:







        listener = self.listener







        close = getattr(listener, "close", None)







        if callable(close):







            try:







                close()







            except Exception:







                pass















    def drain_events(self) -> list[RuntimeEvent]:







        events: list[RuntimeEvent] = []







        while True:







            try:







                events.append(self._event_queue.get_nowait())







            except Empty:







                break







        return events















    def _set_state(self, state: str) -> None:







        with self._state_lock:







            self._state = state







        self._emit("state", state, {"state": state})















    def _voice_status_text(self) -> str:



        listener = self.listener



        mode = getattr(listener, "mode_label", "console")



        ready_reason = getattr(listener, "ready_reason", None)



        ready = getattr(listener, "ready", None)







        if mode == "wake word":



            if ready:



                wake_word = getattr(self.config, "wake_word", "Cyberman")



                sensitivity = getattr(self.config, "porcupine_sensitivity", 0.55)



                return f"Wake word mode is ready for '{wake_word}' at sensitivity {sensitivity:.2f}."



            if ready_reason:



                return f"Wake word mode is not ready: {ready_reason}"



            return "Wake word mode is not ready."







        if mode == "microphone":



            if ready:



                return "Microphone mode is ready and listening without a wake word."



            if ready_reason:



                return f"Microphone mode is not ready: {ready_reason}"



            return "Microphone mode is not ready."







        return "Console mode is active. Voice input is not enabled."







    def _emit(self, kind: str, message: str, data: dict[str, Any] | None = None) -> None:







        if self._history_store is not None and kind != "state":







            speaker = data.get("speaker") if data else None







            if not speaker:







                if kind in {"user", "heard"}:







                    speaker = "You"







                elif kind == "assistant":







                    speaker = self.config.assistant_name







                else:







                    speaker = "System"







            entry = self._history_store.append(kind, str(speaker), message, data or {})







            self._history_entries.append(entry)







        self._event_queue.put(RuntimeEvent(kind=kind, message=message, data=data or {}))















    def _voice_loop(self) -> None:







        while not self._stop_event.is_set():







            if isinstance(self.listener, ConsoleListener):







                sleep(0.5)







                continue







            if getattr(self.listener, "_idle_armed", False):



                self._set_state("idle")



            else:



                self._set_state("listening")







            try:







                text = self.listener.listen_once() if self.listener is not None else None







            except Exception as exc:







                self._emit("error", f"Voice listener failed: {exc}")







                continue















            if text is None:



                if not self._voice_idle_notified:



                    self._set_state("idle")



                    play_voice_cue("idle")



                    self._emit("status", "No speech detected; returning to idle.")



                    self._voice_idle_notified = True



                continue















            self._voice_idle_notified = False



            self._emit("heard", text, {"source": "voice"})







            self._command_queue.put(text)















    def _process_loop(self) -> None:







        while not self._stop_event.is_set():







            try:







                text = self._command_queue.get(timeout=0.2)







            except Empty:







                continue















            if text is None:







                continue















            self.process_text(text)















    def process_text(self, text: str) -> BrainResult:







        if text.strip().lower() in {"quit", "exit"}:







            self._emit("user", text, {"source": "system"})







            self._set_state("offline")







            self.speaker.say("Powering down.")







            self._emit("assistant", "Powering down.", {"source": "system"})







            self.stop()







            return BrainResult(response="Powering down.")















        self._emit("user", text, {"source": "input"})







        self._set_state("thinking")







        result = self.brain.process(text)







        if result.preview_message:







            self._emit("preview", result.preview_message)







        if result.log_message:







            self._emit("log", result.log_message)







        if result.response:







            self._set_state("speaking")







            self._emit("assistant", result.response)







            self.speaker.say(result.response)







        self._set_state("idle")







        return result







