param([Parameter(Mandatory)][string]$Source)
$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '../.venv/Scripts/python.exe'
if (Test-Path -LiteralPath $python) { & $python "$PSScriptRoot/install_models.py" $Source }
else { & uv run --no-project --python 3.11.15 "$PSScriptRoot/install_models.py" $Source }
exit $LASTEXITCODE
