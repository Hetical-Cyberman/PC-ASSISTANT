from __future__ import annotations















import csv







import json







from dataclasses import dataclass







from datetime import datetime, timezone







from pathlib import Path







import tkinter as tk







from tkinter import filedialog







from tkinter import messagebox







from tkinter import ttk







from tkinter.scrolledtext import ScrolledText















from cyberman.config import AppConfig, load_config, save_config







from cyberman.history import HistoryEntry, HistoryStore







from cyberman.permissions import disable_startup as disable_startup_task







from cyberman.permissions import enable_startup as enable_startup_task







from cyberman.permissions import startup_status







from cyberman.runtime import AssistantRuntime







from cyberman.gui.settings_panel import SettingsPanel







from cyberman.tray import TrayController
from cyberman.version import app_title, APP_VERSION























STATE_COLORS = {







    "idle": "#6b7280",







    "listening": "#16a34a",







    "thinking": "#2563eb",







    "speaking": "#f59e0b",







    "offline": "#9ca3af",







}























@dataclass







class Dashboard:







    root: tk.Tk







    config: AppConfig







    config_path: Path















    def __post_init__(self) -> None:







        self.history_path = self.config_path.with_name("history.jsonl")







        self.runtime = AssistantRuntime(self.config, history_path=self.history_path)







        self._history_rows: list[HistoryEntry] = []







        self._history_presets: list[str] = self._load_history_presets()







        self.runtime.start()







        self.tray = TrayController(







            title=self.config.assistant_name,







            on_show=self.show_window,







            on_quit=self.quit_app,







        )







        self.tray.start()







        self._build_theme()







        self._build_layout()







        self._load_history_into_view()







        self._poll_events()







        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)















    def _build_theme(self) -> None:







        self.root.title(app_title(self.config.assistant_name))







        self.root.geometry("1100x720")







        self.root.minsize(920, 620)







        style = ttk.Style(self.root)







        try:







            style.theme_use("vista")







        except Exception:







            pass















    def _build_layout(self) -> None:







        self.root.columnconfigure(0, weight=1)







        self.root.rowconfigure(1, weight=1)















        header = ttk.Frame(self.root, padding=(16, 14, 16, 10))







        header.grid(row=0, column=0, sticky="ew")







        header.columnconfigure(0, weight=1)















        title = ttk.Label(header, text=self.config.assistant_name, font=("Segoe UI", 20, "bold"))







        title.grid(row=0, column=0, sticky="w")
        subtitle = ttk.Label(header, text=f"Version {APP_VERSION} - Windows assistant", foreground="#6b7280")
        subtitle.grid(row=1, column=0, sticky="w", pady=(2, 0))















        self.status_value = tk.StringVar(value="idle")







        self.mode_value = tk.StringVar(value=f"Input mode: {self.runtime.input_mode}")







        self.startup_value = tk.StringVar(value=f"Startup: {startup_status().message}")







        self.voice_status_value = tk.StringVar(value=self.runtime.voice_status())

        status_row = ttk.Frame(header)







        status_row.grid(row=1, column=0, sticky="ew", pady=(8, 0))







        ttk.Label(status_row, textvariable=self.mode_value).pack(side="left")







        ttk.Label(status_row, text="|").pack(side="left", padx=8)







        ttk.Label(status_row, text="Status:").pack(side="left")







        self.status_chip = tk.Label(status_row, textvariable=self.status_value, padx=8, pady=2, bg="#111827", fg="white")







        self.status_chip.pack(side="left", padx=(6, 0))















        body = ttk.Frame(self.root, padding=(16, 0, 16, 16))







        body.grid(row=1, column=0, sticky="nsew")







        body.columnconfigure(0, weight=2)







        body.columnconfigure(1, weight=1)







        body.rowconfigure(0, weight=1)















        notebook = ttk.Notebook(body)







        notebook.grid(row=0, column=0, sticky="nsew", padx=(0, 12))















        console_tab = ttk.Frame(notebook, padding=12)







        settings_tab = ttk.Frame(notebook, padding=12)







        help_tab = ttk.Frame(notebook, padding=12)







        notebook.add(console_tab, text="Console")







        notebook.add(settings_tab, text="Settings")







        notebook.add(help_tab, text="Help")







        console_tab.columnconfigure(0, weight=1)







        console_tab.rowconfigure(2, weight=1)







        help_tab.columnconfigure(0, weight=1)







        help_tab.rowconfigure(1, weight=1)















        search_row = ttk.Frame(console_tab)







        search_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))







        search_row.columnconfigure(1, weight=1)







        ttk.Label(search_row, text="Search").grid(row=0, column=0, sticky="w")







        self.search_var = tk.StringVar(value="")







        search_entry = ttk.Entry(search_row, textvariable=self.search_var)







        search_entry.grid(row=0, column=1, sticky="ew", padx=(8, 8))







        search_entry.bind("<Return>", lambda _: self.apply_history_filter())







        ttk.Button(search_row, text="Apply", command=self.apply_history_filter).grid(row=0, column=2)







        ttk.Button(search_row, text="Clear", command=self.clear_history_filter).grid(row=0, column=3, padx=(8, 0))















        preset_row = ttk.Frame(console_tab)







        preset_row.grid(row=1, column=0, sticky="ew", pady=(0, 10))







        preset_row.columnconfigure(1, weight=1)







        ttk.Label(preset_row, text="Saved filters").grid(row=0, column=0, sticky="w")







        self.preset_var = tk.StringVar(value=self._history_presets[0] if self._history_presets else "")







        self.preset_choice = ttk.Combobox(







            preset_row,







            textvariable=self.preset_var,







            values=self._history_presets,







            state="readonly",







        )







        self.preset_choice.grid(row=0, column=1, sticky="ew", padx=(8, 8))







        ttk.Button(preset_row, text="Load", command=self.load_history_preset).grid(row=0, column=2)







        ttk.Button(preset_row, text="Save current", command=self.save_history_preset).grid(row=0, column=3, padx=(8, 0))







        ttk.Button(preset_row, text="Delete", command=self.delete_history_preset).grid(row=0, column=4, padx=(8, 0))















        self.history = ScrolledText(console_tab, wrap="word", height=20, state="disabled")







        self.history.grid(row=2, column=0, sticky="nsew")















        input_row = ttk.Frame(console_tab)







        input_row.grid(row=3, column=0, sticky="ew", pady=(10, 0))







        input_row.columnconfigure(0, weight=1)







        self.command_var = tk.StringVar()







        self.command_entry = ttk.Entry(input_row, textvariable=self.command_var)







        self.command_entry.grid(row=0, column=0, sticky="ew")







        self.command_entry.bind("<Return>", lambda _: self.send_command())







        ttk.Button(input_row, text="Send", command=self.send_command).grid(row=0, column=1, padx=(8, 0))







        ttk.Button(input_row, text="Clear", command=self.clear_history).grid(row=0, column=2, padx=(8, 0))















        settings_tab.columnconfigure(0, weight=1)







        self.settings_panel = SettingsPanel(settings_tab, self.config, on_save=self.save_settings)







        self.settings_panel.frame.grid(row=0, column=0, sticky="nsew")















        help_intro = ttk.LabelFrame(help_tab, text="About", padding=12)







        help_intro.grid(row=0, column=0, sticky="ew")







        help_intro.columnconfigure(0, weight=1)







        ttk.Label(







            help_intro,







            text=(







                f"{self.config.assistant_name} is a Windows assistant with voice input, AI routing, "







                "safe file actions, and desktop controls."







            ),







            justify="left",







            wraplength=560,







        ).grid(row=0, column=0, sticky="w")















        help_commands = ttk.LabelFrame(help_tab, text="Supported Commands", padding=12)







        help_commands.grid(row=1, column=0, sticky="nsew", pady=(12, 0))







        help_commands.columnconfigure(0, weight=1)







        help_commands.rowconfigure(0, weight=1)







        commands_text = ScrolledText(help_commands, wrap="word", height=18, state="normal")







        commands_text.grid(row=0, column=0, sticky="nsew")







        commands_text.insert(







            "end",







            "\n".join(







                [







                    "help",







                    "about",







                    "open chrome",







                    "open https://example.com",







                    "copy notes.txt to Downloads",







                    "move notes.txt to Documents",







                    "rename old.txt to new.txt",







                    "delete notes.txt",







                    "create file notes.txt with hello world",







                    "read file notes.txt aloud",







                    "search report in Downloads",







                    "volume up / volume down / mute",







                    "brightness up / brightness down",







                    "battery status",







                    "shutdown / restart / sleep",







                ]







            ),







        )







        commands_text.configure(state="disabled")















        sidebar = ttk.Frame(body)







        sidebar.grid(row=0, column=1, sticky="nsew")







        sidebar.columnconfigure(0, weight=1)















        summary = ttk.LabelFrame(sidebar, text="Assistant", padding=12)







        summary.grid(row=0, column=0, sticky="ew")







        summary.columnconfigure(0, weight=1)







        self.input_mode_label = ttk.Label(summary, text=f"Mode: {self.runtime.input_mode}")







        self.input_mode_label.grid(row=0, column=0, sticky="w")







        ttk.Label(summary, text="Voice loop:").grid(row=1, column=0, sticky="w", pady=(8, 0))







        self.voice_label = ttk.Label(summary, text="enabled" if self.runtime.voice_enabled else "manual")







        self.voice_label.grid(row=2, column=0, sticky="w")







        ttk.Label(summary, textvariable=self.startup_value).grid(row=3, column=0, sticky="w", pady=(8, 0))















        ttk.Label(summary, text="Voice health:").grid(row=4, column=0, sticky="w", pady=(8, 0))

        ttk.Label(summary, textvariable=self.voice_status_value, wraplength=260, justify="left").grid(row=5, column=0, sticky="w")

        controls = ttk.LabelFrame(sidebar, text="Controls", padding=12)







        controls.grid(row=1, column=0, sticky="ew", pady=(12, 0))







        controls.columnconfigure(0, weight=1)







        ttk.Button(controls, text="Save config", command=self.save_settings).grid(row=0, column=0, sticky="ew")







        ttk.Button(controls, text="Reload config", command=self.reload_settings).grid(row=1, column=0, sticky="ew", pady=(8, 0))







        ttk.Button(controls, text="Export text", command=self.export_history_text).grid(row=2, column=0, sticky="ew", pady=(8, 0))







        ttk.Button(controls, text="Export JSON", command=self.export_history_json).grid(row=3, column=0, sticky="ew", pady=(8, 0))







        ttk.Button(controls, text="Export CSV", command=self.export_history_csv).grid(row=4, column=0, sticky="ew", pady=(8, 0))







        ttk.Button(controls, text="Refresh voice status", command=self.refresh_voice_status).grid(row=5, column=0, sticky="ew", pady=(8, 0))

        ttk.Button(controls, text="Enable startup", command=self.enable_startup).grid(row=5, column=0, sticky="ew", pady=(8, 0))







        ttk.Button(controls, text="Disable startup", command=self.disable_startup).grid(row=6, column=0, sticky="ew", pady=(8, 0))







        ttk.Button(controls, text="Quit app", command=self.quit_app).grid(row=7, column=0, sticky="ew", pady=(8, 0))















        note = ttk.LabelFrame(sidebar, text="Notes", padding=12)







        note.grid(row=2, column=0, sticky="nsew", pady=(12, 0))







        note.columnconfigure(0, weight=1)







        ttk.Label(







            note,







            text="Voice commands go through the background runtime.\nIf the audio stack is missing, use the console tab.",







            justify="left",







        ).grid(row=0, column=0, sticky="w")















        self._append_line("System", f"{self.config.assistant_name} is ready.")







        self._append_line("System", f"Input mode: {self.runtime.input_mode}")







        self.command_entry.focus_set()















    def send_command(self) -> None:







        text = self.command_var.get().strip()







        if not text:







            return







        self.command_var.set("")







        self._append_line("You", text)







        self.runtime.submit_text(text)















    def save_settings(self) -> None:







        self.settings_panel.apply_to_config()







        self.runtime.reconfigure(self.config)







        self.runtime.speaker.refresh()







        save_config(self.config, self.config_path)







        self.root.title(app_title(self.config.assistant_name))







        self.tray.set_title(self.config.assistant_name)







        self.input_mode_label.configure(text=f"Mode: {self.runtime.input_mode}")







        self.mode_value.set(f"Input mode: {self.runtime.input_mode}")







        self.voice_label.configure(text="enabled" if self.runtime.voice_enabled else "manual")







        self.startup_value.set(f"Startup: {startup_status().message}")







        self._append_line("System", "Settings saved.")















    def reload_settings(self) -> None:







        loaded = load_config(self.config_path)







        self.config = loaded







        self.settings_panel.config = loaded







        self.settings_panel.sync_from_config()







        self.runtime.reconfigure(self.config)







        self.root.title(app_title(self.config.assistant_name))







        self.tray.set_title(self.config.assistant_name)







        self.input_mode_label.configure(text=f"Mode: {self.runtime.input_mode}")







        self.mode_value.set(f"Input mode: {self.runtime.input_mode}")







        self.voice_label.configure(text="enabled" if self.runtime.voice_enabled else "manual")







        self.startup_value.set(f"Startup: {startup_status().message}")







        self._append_line("System", "Settings reloaded from disk.")















    def clear_history(self) -> None:







        self._history_rows.clear()







        self._render_history()

















    def refresh_voice_status(self) -> None:

        status = self.runtime.voice_status()

        self.voice_status_value.set(status)

        self._append_line("System", status)

    def _load_history_into_view(self) -> None:







        self._history_rows = list(self.runtime.history_entries)







        self._render_history()















    def apply_history_filter(self) -> None:







        self._render_history()















    def clear_history_filter(self) -> None:







        self.search_var.set("")







        self._render_history()















    def _load_history_presets(self) -> list[str]:







        raw = self.config.extra.get("history_search_presets", [])







        if not isinstance(raw, list):







            return []







        presets: list[str] = []







        for item in raw:







            preset = str(item).strip()







            if preset and preset not in presets:







                presets.append(preset)







        return presets[:10]















    def _save_history_presets(self) -> None:







        self.config.extra["history_search_presets"] = list(self._history_presets)







        save_config(self.config, self.config_path)















    def _refresh_preset_choices(self, selected: str | None = None) -> None:







        self.preset_choice.configure(values=self._history_presets)







        if selected is not None:







            self.preset_var.set(selected)







        elif self._history_presets:







            current = self.preset_var.get().strip()







            if current not in self._history_presets:







                self.preset_var.set(self._history_presets[0])







        else:







            self.preset_var.set("")















    def load_history_preset(self) -> None:







        preset = self.preset_var.get().strip()







        if not preset:







            return







        self.search_var.set(preset)







        self._render_history()















    def save_history_preset(self) -> None:







        preset = self.search_var.get().strip()







        if not preset:







            self._append_line("System", "Type a search first, then save it as a preset.")







            return







        if preset in self._history_presets:







            self._history_presets.remove(preset)







        self._history_presets.insert(0, preset)







        self._history_presets = self._history_presets[:10]







        self._refresh_preset_choices(selected=preset)







        self._save_history_presets()







        self._append_line("System", f"Saved filter: {preset}")















    def delete_history_preset(self) -> None:







        preset = self.preset_var.get().strip()







        if not preset:







            return







        if preset in self._history_presets:







            self._history_presets.remove(preset)







            self._refresh_preset_choices()







            self._save_history_presets()







            self._append_line("System", f"Removed filter: {preset}")















    def _render_history(self) -> None:







        query = self.search_var.get().strip()







        lowered = query.lower()







        self.history.configure(state="normal")







        self.history.delete("1.0", "end")







        for entry in self._history_rows:







            if lowered and not HistoryStore.matches(entry, lowered):







                continue







            timestamp = self._short_timestamp(entry.timestamp)







            prefix = f"[{timestamp}] " if timestamp else ""







            self.history.insert("end", f"{prefix}{entry.speaker}: {entry.message}\n")







        self.history.see("end")







        self.history.configure(state="disabled")















    @staticmethod







    def _short_timestamp(timestamp: str) -> str:







        if not timestamp:







            return ""







        return timestamp.replace("T", " ", 1).replace("+00:00", " UTC")















    def export_history_text(self) -> None:







        path = filedialog.asksaveasfilename(







            parent=self.root,







            title="Export history as text",







            defaultextension=".txt",







            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],







            initialfile=f"{self.config.assistant_name.lower()}-history.txt",







        )







        if not path:







            return







        text = self.history.get("1.0", "end").strip()







        Path(path).write_text(text + "\n", encoding="utf-8")







        self._append_line("System", f"History exported to {path}.")















    def export_history_json(self) -> None:







        path = filedialog.asksaveasfilename(







            parent=self.root,







            title="Export history as JSON",







            defaultextension=".json",







            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],







            initialfile=f"{self.config.assistant_name.lower()}-history.json",







        )







        if not path:







            return







        payload = [







            {







                "timestamp": entry.timestamp,







                "kind": entry.kind,







                "speaker": entry.speaker,







                "message": entry.message,







                "data": entry.data,







            }







            for entry in self.runtime.history_entries







        ]







        Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")







        self._append_line("System", f"History exported to {path}.")















    def export_history_csv(self) -> None:







        path = filedialog.asksaveasfilename(







            parent=self.root,







            title="Export history as CSV",







            defaultextension=".csv",







            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],







            initialfile=f"{self.config.assistant_name.lower()}-history.csv",







        )







        if not path:







            return







        with Path(path).open("w", encoding="utf-8", newline="") as handle:







            writer = csv.DictWriter(handle, fieldnames=["timestamp", "kind", "speaker", "message", "data"])







            writer.writeheader()







            for entry in self.runtime.history_entries:







                writer.writerow(







                    {







                        "timestamp": entry.timestamp,







                        "kind": entry.kind,







                        "speaker": entry.speaker,







                        "message": entry.message,







                        "data": json.dumps(entry.data, ensure_ascii=False),







                    }







                )







        self._append_line("System", f"History exported to {path}.")















    def _append_line(self, speaker: str, text: str) -> None:







        self._history_rows.append(







            HistoryEntry(







                timestamp=datetime.now(timezone.utc).isoformat(),







                kind="log",







                speaker=speaker,







                message=text,







                data={},







            )







        )







        self._render_history()















    def _set_status(self, state: str) -> None:







        self.status_value.set(state)







        color = STATE_COLORS.get(state, "#6b7280")







        self.status_chip.configure(foreground=color)















    def _poll_events(self) -> None:







        for event in self.runtime.drain_events():







            if event.kind == "state":







                self._set_status(event.data.get("state", event.message))







            elif event.kind == "user":







                self._append_line("You", event.message)







            elif event.kind == "assistant":







                self._append_line(self.config.assistant_name, event.message)







            elif event.kind == "log":







                self._append_line("Log", event.message)







            elif event.kind == "heard":







                self._append_line("Heard", event.message)







            elif event.kind == "error":







                self._append_line("Error", event.message)







            elif event.kind == "confirm":







                self._handle_confirmation(event.message)







            elif event.kind == "preview":







                self._append_line("Preview", event.message)







            elif event.kind == "status":







                self._append_line("System", event.message)







                self._set_status(event.data.get("state", "offline"))







            else:







                self._append_line("System", event.message)















        if not self.runtime._stop_event.is_set():







            self.root.after(100, self._poll_events)















    def hide_window(self) -> None:







        if self.tray.ready:







            self.root.withdraw()







            self._append_line("System", "Cyberman is running in the tray.")







            return







        self.quit_app()















    def show_window(self) -> None:







        self.root.after(0, self._show_window_ui)















    def _show_window_ui(self) -> None:







        self.root.deiconify()







        self.root.lift()







        self.root.focus_force()















    def quit_app(self) -> None:







        self.runtime.stop()







        self.tray.stop()







        save_config(self.config, self.config_path)







        self.root.after(100, self.root.destroy)















    def _handle_confirmation(self, prompt: str) -> None:







        accepted = messagebox.askyesno("Confirm action", prompt)







        self.runtime.respond_confirmation(accepted)















    def enable_startup(self) -> None:







        startup_path = Path(sys.executable).resolve() if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2] / "main.py"
        result = enable_startup_task(startup_path)







        self.startup_value.set(f"Startup: {result.message}")







        self._append_line("System", result.message)















    def disable_startup(self) -> None:







        result = disable_startup_task()







        self.startup_value.set(f"Startup: {result.message}")







        self._append_line("System", result.message)























def launch_dashboard(config: AppConfig, config_path: Path) -> int:







    root = tk.Tk()







    Dashboard(root=root, config=config, config_path=config_path)







    root.mainloop()







    return 0







