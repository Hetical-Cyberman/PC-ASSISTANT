# CYBERMAN

Cyberman is a Windows-first assistant inspired by JARVIS: local wake/listen/speak support, online and offline brains, a Tkinter dashboard, and OS-level automation.

## Current State

This first scaffold gives us:

- a runnable command loop
- config loading and saving
- text-based command parsing
- basic file and app actions
- optional text-to-speech
- optional Whisper-backed microphone input with console fallback
- optional Claude and Ollama routing for non-rule commands
- a Tkinter dashboard with console, settings, and live status panels
- system tray support with minimize-to-tray behavior
- Windows startup registration through Task Scheduler
- confirmation prompts for destructive file actions

## Configuration

The assistant reads settings from `config/settings.json` when present.

Useful runtime values:

- `ai_mode`: `auto`, `online`, `online only`, `offline`, or `offline only`
- `claude_model`: Claude model name
- `ollama_model`: Ollama model name
- `porcupine_access_key`: Porcupine access key for wake-word mode
- `porcupine_keyword_path`: path to the custom Porcupine keyword file
- `porcupine_sensitivity`: wake-word sensitivity from `0.1` to `1.0`
- `CYBERMAN_CONSOLE=1`: force terminal mode instead of the dashboard

`ANTHROPIC_API_KEY` is also read from the environment for Claude access.

## Run

```bash
python main.py
```

## Next Steps

1. tune the wake-word loop on the target machine
2. expand the command grammar for richer file operations
3. harden Windows-specific controls like brightness and sleep across more hardware
4. add transcript search presets and saved filters in the dashboard
