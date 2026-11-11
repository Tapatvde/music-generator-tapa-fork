param([ValidateSet('Start','Stop','Status')][string]$Action = 'Start', [switch]$NoBrowser, [ValidateRange(1024,65535)][int]$Port=8766)
$ErrorActionPreference = 'Stop'
$forkRoot = Split-Path -Parent $PSScriptRoot
$forkPython = Join-Path $forkRoot '.venv\Scripts\python.exe'
$forkData = Join-Path $forkRoot 'data'
$forkStateFile = Join-Path $forkData 'fork-app-process.json'
$forkPort = $Port
New-Item -ItemType Directory -Force -Path (Join-Path $forkData 'tmp') | Out-Null
$env:TEMP = Join-Path $forkData 'tmp'
$env:TMP = $env:TEMP
$env:PYTHONUTF8 = '1'
$env:PYTHONNOUSERSITE = '1'
$env:PATH = (Join-Path $forkRoot 'engine\runtime\python') + [IO.Path]::PathSeparator + $env:PATH

function Get-ForkOwnedProcess {
    if (-not (Test-Path -LiteralPath $forkStateFile)) { return $null }
    $forkState = Get-Content -LiteralPath $forkStateFile -Raw | ConvertFrom-Json
    $forkProcess = Get-Process -Id $forkState.ProcessId -ErrorAction SilentlyContinue
    if (-not $forkProcess) { return $null }
    $forkInfo = Get-CimInstance Win32_Process -Filter "ProcessId=$($forkState.ProcessId)"
    if ($forkInfo.ExecutablePath -ne $forkPython -or $forkProcess.StartTime.ToUniversalTime().Ticks.ToString() -ne $forkState.StartTicks) { return $null }
    return $forkProcess
}

$forkOwned = Get-ForkOwnedProcess
if ($Action -eq 'Status') {
    if ($forkOwned) { Write-Output "Music Generator Fork läuft unter http://127.0.0.1:$forkPort" }
    else { Write-Output 'Music Generator Fork ist beendet.' }
    exit 0
}
if ($Action -eq 'Stop') {
    if ($forkOwned) { & taskkill.exe /PID $forkOwned.Id /T /F | Out-Null }
    Write-Output 'Music Generator Fork ist beendet.'
    exit 0
}
if (-not (Test-Path -LiteralPath $forkPython)) { throw 'Die App-Umgebung .venv fehlt.' }
if (-not $forkOwned) {
    if (Get-NetTCPConnection -State Listen -LocalPort $forkPort -ErrorAction SilentlyContinue) { throw "Port $forkPort ist belegt. Der vorhandene Dienst wurde nicht verändert." }
    $forkOwned = Start-Process -FilePath $forkPython -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port',"$forkPort") -WorkingDirectory $forkRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $forkData 'fork-app.out.log') -RedirectStandardError (Join-Path $forkData 'fork-app.err.log')
    [PSCustomObject]@{ProcessId=$forkOwned.Id;StartTicks=$forkOwned.StartTime.ToUniversalTime().Ticks.ToString()} | ConvertTo-Json | Set-Content -LiteralPath $forkStateFile -Encoding utf8
}
for ($forkAttempt=0; $forkAttempt -lt 240; $forkAttempt++) {
    $forkOwned.Refresh()
    if ($forkOwned.HasExited) { throw 'Die App wurde beim Start beendet. Siehe data\fork-app.err.log.' }
    try {
        $forkResponse = Invoke-WebRequest "http://127.0.0.1:$forkPort/api/voices" -UseBasicParsing -TimeoutSec 2
        if ($forkResponse.StatusCode -eq 200) {
            Write-Output "Music Generator Fork ist bereit: http://127.0.0.1:$forkPort"
            if (-not $NoBrowser) { Start-Process "http://127.0.0.1:$forkPort" }
            exit 0
        }
    } catch { }
    Start-Sleep -Milliseconds 500
}
throw 'Die App antwortet noch nicht. Siehe data\fork-app.err.log.'
