$ErrorActionPreference = 'Stop'
$rvcProjectRoot = Split-Path -Parent $PSScriptRoot
$rvcRoot = Join-Path $rvcProjectRoot 'engine\rvc'
$rvcRuntime = Join-Path $rvcProjectRoot 'engine\rvc-runtime'
$rvcPython = Join-Path $rvcRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $rvcPython)) { throw 'Die lokale RVC-Umgebung fehlt.' }
$rvcCache = Join-Path $rvcRuntime 'cache'
$env:PYTHONNOUSERSITE = '1'
$env:PYTHONUTF8 = '1'
$env:HF_HOME = Join-Path $rvcCache 'huggingface'
$env:TORCH_HOME = Join-Path $rvcCache 'torch'
$env:XDG_CACHE_HOME = $rvcCache
$env:MPLCONFIGDIR = Join-Path $rvcCache 'matplotlib'
$env:NUMBA_CACHE_DIR = Join-Path $rvcCache 'numba'
$env:GRADIO_TEMP_DIR = Join-Path $rvcRuntime 'gradio-temp'
$env:TEMP = Join-Path $rvcRuntime 'tmp'
$env:TMP = $env:TEMP
$env:HF_HUB_DISABLE_TELEMETRY = '1'
$env:GRADIO_ANALYTICS_ENABLED = 'False'
$env:DO_NOT_TRACK = '1'
$env:PATH = $rvcRoot + [IO.Path]::PathSeparator + (Join-Path $rvcRoot '.venv\Scripts') + [IO.Path]::PathSeparator + $env:PATH
foreach ($rvcDirectory in @($env:TEMP, $env:MPLCONFIGDIR, $env:NUMBA_CACHE_DIR, $env:GRADIO_TEMP_DIR)) {
    New-Item -ItemType Directory -Path $rvcDirectory -Force | Out-Null
}
Set-Location -LiteralPath $rvcRoot
