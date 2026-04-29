$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Get-BasePython {
    foreach ($ver in @("Python312", "Python313", "Python311")) {
        $p = Join-Path $env:LocalAppData "Programs\Python\$ver\python.exe"
        if (Test-Path $p) {
            return $p
        }
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source
    if ($cmd -and $cmd -notmatch "WindowsApps") {
        return $cmd
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return "PY_LAUNCHER"
    }
    return $null
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    $base = Get-BasePython
    if (-not $base) {
        Write-Host "Kein Python gefunden. Bitte Python 3.11+ installieren (PATH oder winget)." -ForegroundColor Red
        exit 1
    }
    if ($base -eq "PY_LAUNCHER") {
        & py -3 -m venv .venv
    } else {
        & $base -m venv .venv
    }
}

& $venvPython -m pip install -q -r requirements.txt
& $venvPython app.py
