param([Parameter(ValueFromRemainingArguments=$true)][string[]]$AgfArgs)
$ErrorActionPreference = 'Stop'
if (Get-Command python -ErrorAction SilentlyContinue) {
    & python (Join-Path $PSScriptRoot 'agf.py') @AgfArgs
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 (Join-Path $PSScriptRoot 'agf.py') @AgfArgs
} else {
    Write-Error 'Python 3.11 or newer is required. No installation was attempted.'
    exit 2
}
exit $LASTEXITCODE
