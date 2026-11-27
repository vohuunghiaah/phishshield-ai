param([int]$ApiPort=8000, [int]$UiPort=8501)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    & ./.venv/Scripts/python.exe scripts/verify_models.py
    if ($LASTEXITCODE) { throw 'Model verification failed.' }
    & ./.venv/Scripts/python.exe scripts/run_local.py --api-port $ApiPort --ui-port $UiPort
    if ($LASTEXITCODE) { throw 'Service failed. Check ports and service output.' }
} finally { Pop-Location }

