from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
from typing import Callable

from cyberman.config import AppConfig


@dataclass
class SettingsPanel:
    parent: tk.Widget
    config: AppConfig
    on_save: Callable[[], None] | None = None

    def __post_init__(self) -> None:
        self.frame = ttk.Frame(self.parent, padding=12)

        self.assistant_name = tk.StringVar(value=self.config.assistant_name)
        self.voice_gender = tk.StringVar(value=self.config.voice_gender)
        self.speech_rate = tk.IntVar(value=self.config.speech_rate)
        self.wake_word = tk.StringVar(value=self.config.wake_word)
        self.language = tk.StringVar(value=self.config.language)
        self.ai_mode = tk.StringVar(value=self.config.ai_mode)
        self.claude_model = tk.StringVar(value=self.config.claude_model)
        self.ollama_model = tk.StringVar(value=self.config.ollama_model)
        self.default_browser = tk.StringVar(value=self.config.default_browser)
        self.porcupine_access_key = tk.StringVar(value=self.config.porcupine_access_key or "")
        self.porcupine_keyword_path = tk.StringVar(value=self.config.porcupine_keyword_path or "")
        self.porcupine_sensitivity = tk.DoubleVar(value=self.config.porcupine_sensitivity)

        self._build()

    def _build(self) -> None:
        self.frame.columnconfigure(1, weight=1)

        fields = [
            ("Assistant name", self.assistant_name),
            ("Voice gender", self.voice_gender),
            ("Speech rate", self.speech_rate),
            ("Wake word", self.wake_word),
            ("Language", self.language),
            ("AI mode", self.ai_mode),
            ("Claude model", self.claude_model),
            ("Ollama model", self.ollama_model),
            ("Default browser", self.default_browser),
            ("Porcupine access key", self.porcupine_access_key),
            ("Porcupine keyword path", self.porcupine_keyword_path),
            ("Porcupine sensitivity", self.porcupine_sensitivity),
        ]

        for row, (label, variable) in enumerate(fields):
            ttk.Label(self.frame, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
            if label in {"Voice gender", "AI mode"}:
                values = ["male", "female"] if label == "Voice gender" else ["auto", "online only", "offline only"]
                widget = ttk.Combobox(self.frame, textvariable=variable, values=values, state="readonly")
            elif label == "Speech rate":
                widget = ttk.Spinbox(self.frame, from_=80, to=260, textvariable=variable, width=12)
            elif label == "Porcupine sensitivity":
                widget = ttk.Scale(self.frame, from_=0.1, to=1.0, variable=variable)
            else:
                widget = ttk.Entry(self.frame, textvariable=variable)
            widget.grid(row=row, column=1, sticky="ew", pady=4)

        button_row = len(fields)
        actions = ttk.Frame(self.frame)
        actions.grid(row=button_row, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(actions, text="Save settings", command=self.save).pack(side="right")

    def save(self) -> None:
        self.apply_to_config()
        if self.on_save is not None:
            self.on_save()

    def apply_to_config(self) -> None:
        self.config.assistant_name = self.assistant_name.get().strip() or self.config.assistant_name
        self.config.voice_gender = self.voice_gender.get().strip() or self.config.voice_gender
        self.config.speech_rate = int(self.speech_rate.get())
        self.config.wake_word = self.wake_word.get().strip() or self.config.wake_word
        self.config.language = self.language.get().strip() or self.config.language
        self.config.ai_mode = self.ai_mode.get().strip() or self.config.ai_mode
        self.config.claude_model = self.claude_model.get().strip() or self.config.claude_model
        self.config.ollama_model = self.ollama_model.get().strip() or self.config.ollama_model
        self.config.default_browser = self.default_browser.get().strip() or self.config.default_browser
        self.config.porcupine_access_key = self.porcupine_access_key.get().strip() or None
        self.config.porcupine_keyword_path = self.porcupine_keyword_path.get().strip() or None
        self.config.porcupine_sensitivity = float(self.porcupine_sensitivity.get())

    def sync_from_config(self) -> None:
        self.assistant_name.set(self.config.assistant_name)
        self.voice_gender.set(self.config.voice_gender)
        self.speech_rate.set(self.config.speech_rate)
        self.wake_word.set(self.config.wake_word)
        self.language.set(self.config.language)
        self.ai_mode.set(self.config.ai_mode)
        self.claude_model.set(self.config.claude_model)
        self.ollama_model.set(self.config.ollama_model)
        self.default_browser.set(self.config.default_browser)
        self.porcupine_access_key.set(self.config.porcupine_access_key or "")
        self.porcupine_keyword_path.set(self.config.porcupine_keyword_path or "")
        self.porcupine_sensitivity.set(self.config.porcupine_sensitivity)
