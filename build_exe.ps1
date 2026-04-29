$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Venv fehlt. Starte zuerst run.ps1 (oder erstelle .venv)." -ForegroundColor Yellow
    exit 1
}

& $venvPython -m pip install -q -r requirements.txt
& $venvPython -m PyInstaller --onefile --noconsole --name "ClickMoveDown" app.py

Write-Host ""
Write-Host "Fertig. EXE: dist\ClickMoveDown.exe" -ForegroundColor Green
