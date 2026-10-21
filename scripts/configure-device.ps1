# Preserve installer fallback and unrelated configuration when choosing the LM device.
function Get-ForkLmDevice([string]$Path,[switch]$Cpu,[switch]$Auto) {
    if ($Cpu -and $Auto) { throw 'Choose either -Cpu or -Auto, not both.' }
    if ($Cpu) { return 'cpu' }
    if ($Auto) { return 'auto' }
    if ((Test-Path -LiteralPath $Path) -and (Select-String -LiteralPath $Path -Pattern '^\s*LM_DEVICE=cpu\s*$' -Quiet)) { return 'cpu' }
    return 'auto'
}

function Write-ForkEngineConfig([string]$Path,[string]$LmFile,[switch]$Cpu,[switch]$Auto) {
    $device=Get-ForkLmDevice -Path $Path -Cpu:$Cpu -Auto:$Auto
    $oldLines=@()
    if (Test-Path -LiteralPath $Path) { $oldLines=@(Get-Content -LiteralPath $Path -Encoding UTF8) }
    $lines=@($oldLines | Where-Object { $_ -notmatch '^\s*(LM_DEVICE|LM_FILE)=' })
    if (-not @($lines | Where-Object { $_ -match '^\s*MODE=' }).Count) { $lines+='MODE=single' }
    if (-not @($lines | Where-Object { $_ -match '^\s*VAE_CHUNK=' }).Count) { $lines+='VAE_CHUNK=256' }
    $lines+="LM_FILE=$LmFile"
    if ($device -eq 'cpu') { $lines+='LM_DEVICE=cpu' }
    $parent=Split-Path -Parent $Path
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    $temporary=Join-Path $parent ('.engine-conf-'+[Guid]::NewGuid().ToString('N'))
    try {
        [IO.File]::WriteAllText($temporary,($lines -join "`r`n")+"`r`n",[Text.UTF8Encoding]::new($false))
        if (Test-Path -LiteralPath $Path) { [IO.File]::Replace($temporary,$Path,[NullString]::Value) }
        else { [IO.File]::Move($temporary,$Path) }
    } finally { if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary } }
}
