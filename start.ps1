param([int]$ApiPort=8000, [int]$UiPort=8501, [switch]$FullScan, [switch]$Offline)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    & ./.venv/Scripts/python.exe scripts/verify_models.py
    if ($LASTEXITCODE) { throw 'Model verification failed.' }
    if ($FullScan -and $Offline) { throw 'Choose either -FullScan or -Offline.' }
    $workerPort = if ($env:PHISH_FETCH_PORT) { [int]$env:PHISH_FETCH_PORT } else { 18731 }
    $workerUrl = "http://127.0.0.1:$workerPort"
    if ($FullScan) {
        & docker compose -f compose.fetcher.yaml up -d --build
        if ($LASTEXITCODE) { throw 'Failed to start the isolated Full Scan worker.' }
    }
    $env:PHISHSHIELD_FETCHER_URL = ''
    if (!$Offline) {
        $deadline = (Get-Date).AddSeconds(25)
        do {
            try {
                $status = Invoke-RestMethod "$workerUrl/health" -TimeoutSec 2
                if ($status.protocol -eq 'phishshield-static-v1' -and $status.confinement -eq 'active') {
                    $env:PHISHSHIELD_FETCHER_URL = $workerUrl
                }
            } catch {}
            if (!$FullScan -or $env:PHISHSHIELD_FETCHER_URL) { break }
            Start-Sleep -Milliseconds 350
        } while ((Get-Date) -lt $deadline)
        if ($FullScan -and !$env:PHISHSHIELD_FETCHER_URL) { throw 'Full Scan confinement check did not pass.' }
    }
    & ./.venv/Scripts/python.exe scripts/run_local.py --api-port $ApiPort --ui-port $UiPort
    if ($LASTEXITCODE) { throw 'Service failed. Check ports and service output.' }
} finally { Pop-Location }

