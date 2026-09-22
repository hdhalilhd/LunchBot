# Botu Windows'ta calistirir.
#   powershell -ExecutionPolicy Bypass -File scripts\run.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "Sanal ortam yok, kuruluyor..." -ForegroundColor Yellow
    & "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv
    & $py -m pip install --upgrade pip
    & $py -m pip install -r requirements.txt
}

if (-not (Test-Path (Join-Path $root ".env"))) {
    Write-Host ".env dosyasi yok. .env.example dosyasini .env olarak kopyalayip doldur." -ForegroundColor Red
    exit 1
}

& $py bot.py
