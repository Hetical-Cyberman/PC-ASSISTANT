param(
    [string]$Name = "Cyberman",
    [switch]$OneFile = $true
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw "Virtual environment not found at $VenvPython. Create it first with: python -m venv .venv"
}

& $VenvPython -m pip install --upgrade pip pyinstaller

$Args = @(
    "main.py",
    "--name", $Name,
    "--noconfirm",
    "--clean",
    "--windowed",
    "--icon", (Join-Path $Root "assets\cyberman.ico"),
    "--distpath", (Join-Path $Root "dist\$Name"),
    "--workpath", (Join-Path $Root "build\$Name")
)

if ($OneFile) {
    $Args += "--onefile"
}

& $VenvPython -m PyInstaller @Args


