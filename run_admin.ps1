$ErrorActionPreference = "Stop"

$isAdmin = (
    [Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

$run = Join-Path $PSScriptRoot "run.ps1"

if (-not $isAdmin) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File",
        $run
    )
    exit 0
}

Set-Location $PSScriptRoot
& $run
