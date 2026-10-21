# Real configuration writes, isolated from any existing installation.
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
. (Join-Path $projectRoot 'scripts\configure-device.ps1')
$fixture=Join-Path $projectRoot ('data\tests\device-'+[Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $fixture -Force | Out-Null
$path=Join-Path $fixture 'engine.conf'
Write-ForkEngineConfig -Path $path -LmFile 'example.gguf' -Cpu
if ((Get-ForkLmDevice $path) -ne 'cpu') { throw 'CPU was not written to the real configuration file.' }
Add-Content -LiteralPath $path -Value 'OTHER=retained'
(Get-Content -LiteralPath $path) -replace '^MODE=single$','MODE=split' | Set-Content -LiteralPath $path
Write-ForkEngineConfig -Path $path -LmFile 'second.gguf'
if ((Get-ForkLmDevice $path) -ne 'cpu') { throw 'Stored CPU preference lost.' }
Write-ForkEngineConfig -Path $path -LmFile 'second.gguf' -Auto
if ((Get-ForkLmDevice $path) -ne 'auto') { throw 'Automatic choice not restored.' }
if (-not (Select-String -LiteralPath $path -Pattern '^MODE=split$' -Quiet)) { throw 'Installer fallback lost.' }
if (-not (Select-String -LiteralPath $path -Pattern '^OTHER=retained$' -Quiet)) { throw 'Unrelated setting lost.' }
if (-not (Select-String -LiteralPath $path -Pattern '^LM_FILE=second.gguf$' -Quiet)) { throw 'Selected language model not saved.' }
$before=[IO.File]::ReadAllText($path)
$rejected=$false
try { Write-ForkEngineConfig -Path $path -LmFile 'never.gguf' -Cpu -Auto } catch { $rejected=$true }
if (-not $rejected -or [IO.File]::ReadAllText($path) -ne $before) { throw 'Conflicting choices changed the file.' }
if (@(Get-ChildItem -LiteralPath $fixture -File).Count -ne 1) { throw 'Unexpected configuration files.' }
$raw=& "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File (Join-Path $projectRoot 'Install.ps1') -PlanOnly -Yes -LM 4B -XL -Cpu
if ($LASTEXITCODE -ne 0 -or (($raw -join "`n") | ConvertFrom-Json).language_model_device -ne 'cpu') { throw 'Installer plan did not accept CPU and XL.' }
'PASS: real CPU/Auto configuration writes; retained preferences, fallback and unrelated keys; conflict rejection; correct target path; CPU/XL plan.'
