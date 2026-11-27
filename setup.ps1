param([string]$ModelSource)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    Get-Command uv -ErrorAction Stop | Out-Null
    & uv sync --frozen --python 3.11.15 --extra demo
    if ($LASTEXITCODE) { throw 'Dependency setup failed.' }
    if ($ModelSource) {
        & ./.venv/Scripts/python.exe scripts/install_models.py $ModelSource
        if ($LASTEXITCODE) { throw 'Model installation failed.' }
    }
    & ./.venv/Scripts/python.exe scripts/verify_models.py
    if ($LASTEXITCODE) { throw 'Provide the approved ZIP or mounted research folder with -ModelSource.' }
    Write-Host 'Ready. Run .\start.ps1'
} finally { Pop-Location }

