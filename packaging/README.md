# Packaging Cyberman

This folder contains the starter build and installer files for a Windows release.

## Build the app

1. Create or activate the project virtual environment.
2. Run:

```powershell
.\packaging\build.ps1
```

That produces a Windows executable under `dist\Cyberman\`.

## Create the installer

After the build finishes, open `packaging\installer.iss` in Inno Setup and compile it.
The installer expects the built executable at:

```text
dist\Cyberman\Cyberman.exe
```

## Notes

- App settings and transcript history are stored under `%LOCALAPPDATA%\Cyberman`.
- If the old source-tree config exists, the app migrates it on first launch.
- Startup registration uses the frozen executable when packaged.
- Wake-word mode still depends on a valid Porcupine access key and keyword file.



- The EXE and installer use ssets\cyberman.ico, derived from the provided futuristic assistant image.
