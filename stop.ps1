param([int]$ApiPort=8000,[int]$UiPort=8501)
$dir=Join-Path $PSScriptRoot '.runtime'
if (Test-Path -LiteralPath $dir) {
    [IO.File]::WriteAllText((Join-Path $dir "$ApiPort-$UiPort.stop"),'stop')
}

