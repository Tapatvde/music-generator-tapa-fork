# Transparent online installer. Entry point: double-click Install.bat.
# Downloads are listed in downloads-manifest.json; Python packages in requirements/*.lock.
param([switch]$Yes,[ValidateSet('0.6B','1.7B','4B')][string]$LM='1.7B',
      [switch]$XL,[switch]$MusicOnly,[switch]$Alignment,[switch]$AcceptNonCommercialLicense,
      [switch]$NoStart,[switch]$PlanOnly,[switch]$SkipGpuCheck,[switch]$NoNetwork,
      [string]$AssetCache='', [string]$WheelCache='', [switch]$Cpu, [switch]$Auto)
$ErrorActionPreference='Stop'
if ($Cpu -and $Auto) { throw 'Choose either -Cpu or -Auto, not both.' }
. (Join-Path $PSScriptRoot 'scripts\installer-common.ps1')
. (Join-Path $PSScriptRoot 'scripts\configure-device.ps1')
Set-Location -LiteralPath $installRoot
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
$manifest=Get-Content -LiteralPath (Join-Path $installRoot 'downloads-manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
function Answer-Yes([string]$Question) { return (Read-Host ($Question+' [y/N]')) -match '^[jJyY]$' }
if (-not $PlanOnly -and -not $Yes) {
    Write-Host 'Music Generator - Tapa Fork: Windows / NVIDIA'
    Write-Host 'Install.bat installs inside this folder. No administrator rights or EXE setup package required.'
    Write-Host 'Choose language model: 1 = 0.6B (~0.7 GB), 2 = 1.7B (~2 GB), 3 = 4B (~4.5 GB).'
    $choice=Read-Host 'Choice [Enter = 2]'
    if ($choice -eq '1') { $LM='0.6B' } elseif ($choice -eq '3') { $LM='4B' }
    if (-not $XL) { $XL=Answer-Yes 'Add the XL sound model? (+5.3 GB; 16 GB GPU memory recommended)' }
    if (-not $MusicOnly) { $MusicOnly=-not (Answer-Yes 'Install voice conversion and your own voice training as well?') }
    if (-not $MusicOnly -and -not $Alignment) {
        $Alignment=Answer-Yes 'Optional automatic lyric/chorus alignment uses an NC model. Download for noncommercial use?'
        if ($Alignment) { $AcceptNonCommercialLicense=$true }
    }
}
if ($Alignment -and ($MusicOnly -or -not $AcceptNonCommercialLicense)) {
    throw 'Alignment requires RVC and explicit noncommercial acknowledgement. See docs\LIZENZEN.md.'
}
$modelNames=@('vae-BF16.gguf','Qwen3-Embedding-0.6B-Q8_0.gguf','acestep-v15-sft-Q8_0.gguf',"acestep-5Hz-lm-$LM-Q8_0.gguf")
if ($XL) { $modelNames+='acestep-v15-xl-sft-Q8_0.gguf' }
$models=@($manifest.models | Where-Object {
    ($_.group -eq 'ace' -and (Split-Path -Leaf $_.target) -in $modelNames) -or
    ($_.group -eq 'rvc' -and (-not $MusicOnly -or $_.id -in @('rvc-ffmpeg.exe','rvc-ffprobe.exe'))) -or ($_.group -eq 'alignment' -and $Alignment)
})
$assets=@($manifest.assets)
[long]$downloadBytes=0;foreach ($entry in @($assets)+@($models)) { $downloadBytes += [long]$entry.bytes }
$deviceChoice=Get-ForkLmDevice -Path (Join-Path $installRoot 'data\engine.conf') -Cpu:$Cpu -Auto:$Auto
$plan=[ordered]@{folder=$installRoot;language_model=$LM;language_model_device=$deviceChoice;sound_model=$(if($XL){'standard + XL'}else{'standard'});voice_training=(-not $MusicOnly);noncommercial_aligner=[bool]$Alignment;listed_download_GB=[math]::Round($downloadBytes/1e9,2);python_packages='Additional; see requirements/app.lock and rvc.lock';disk_recommendation_GB=$(if($MusicOnly){20}else{35})+[int]([bool]$XL)*6}
if ($PlanOnly) { $plan | ConvertTo-Json;exit 0 }
if (-not [Environment]::Is64BitOperatingSystem) { throw '64-bit Windows is required.' }
$packageInfo=Get-Content -LiteralPath (Join-Path $installRoot 'fork-info.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($packageInfo.package_status -ne 'public-source-preview') { throw 'This installer is only for the separate publication package.' }
if (Test-Path -LiteralPath (Join-Path $installRoot 'data\fork-app-process.json')) {
    $state=Get-Content -LiteralPath (Join-Path $installRoot 'data\fork-app-process.json') -Raw | ConvertFrom-Json
    $process=Get-CimInstance Win32_Process -Filter "ProcessId=$($state.ProcessId)" -ErrorAction SilentlyContinue
    if ($process.ExecutablePath -eq (Join-Path $installRoot '.venv\Scripts\python.exe')) { throw 'Stop this installation with Music Generator OFF.bat before running Install again.' }
}
$drive=[IO.DriveInfo]::new([IO.Path]::GetPathRoot($installRoot))
if ($drive.AvailableFreeSpace -lt [long]$plan.disk_recommendation_GB*1GB) { throw "Please provide at least $($plan.disk_recommendation_GB) GB of free space for downloads, packages and models." }
if (-not $SkipGpuCheck) {
    $gpuNames=@(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name)
    if (-not ($gpuNames -match 'NVIDIA')) { throw 'NVIDIA GPU/driver missing. No graphics driver is installed by this script.' }
    if (-not $MusicOnly -and ($gpuNames -match 'RTX\s*50')) { throw 'The RVC preview uses CUDA 11.8 and does not support RTX 50 voice training. Use -MusicOnly or see docs\INSTALLATION.md.' }
    Write-Host "GPU: $($gpuNames -join ', ')"
}
New-Item -ItemType Directory -Path (Join-Path $installRoot 'data') -Force | Out-Null
$env:PYTHONUTF8='1';$env:PYTHONNOUSERSITE='1'
$env:UV_CACHE_DIR=$(if($WheelCache){$WheelCache}else{Join-Path $installRoot 'engine\rvc-runtime\cache\uv'})
$env:UV_NO_PROGRESS='1'
if ($NoNetwork) { $env:UV_OFFLINE='1' }
$env:TEMP=Join-Path $installRoot 'data\tmp';$env:TMP=$env:TEMP
New-Item -ItemType Directory -Path $env:TEMP -Force | Out-Null
Start-Transcript -Path (Join-Path $installRoot 'data\installation.log') -Append | Out-Null
try {
    $plan | ConvertTo-Json | Write-Host
    Write-Host 'Checking source package...'
    $sourceManifest=Get-Content -LiteralPath (Join-Path $installRoot 'PACKAGE-CONTENTS.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($entry in $sourceManifest.files) {
        $path=Assert-InProgram (Join-Path $installRoot $entry.path)
        if (-not (Test-Path -LiteralPath $path) -or (Get-InstallHash $path) -ne $entry.sha256) { throw "Package file missing or modified: $($entry.path)" }
    }
    $uv=Join-Path $installRoot 'engine\tools\uv.exe'
    if (-not (Test-Path -LiteralPath $uv)) {
        $zip=Get-VerifiedAsset ($assets | Where-Object id -eq 'uv')
        Expand-VerifiedZip $zip (Join-Path $installRoot 'engine\uv-extract')
        New-Item -ItemType Directory -Path (Split-Path -Parent $uv) -Force | Out-Null
        $tool=Get-ChildItem -LiteralPath (Join-Path $installRoot 'engine\uv-extract') -Filter uv.exe -Recurse -File
        if (@($tool).Count -ne 1) { throw 'Unexpected uv archive structure.' }
        Copy-Item -LiteralPath $tool.FullName -Destination $uv
    }
    $uvEntry=$assets | Where-Object id -eq 'uv'
    if ((Get-InstallHash $uv) -ne $uvEntry.executable_sha256) { throw 'The local uv executable differs from the verified runtime. It was not executed.' }
    $python=Join-Path $installRoot 'engine\runtime\python\python.exe'
    if (-not (Test-Path -LiteralPath $python)) {
        $tar=Get-VerifiedAsset ($assets | Where-Object id -eq 'python')
        $destination=Join-Path $installRoot 'engine\runtime'
        New-Item -ItemType Directory -Path $destination -Force | Out-Null
        $members=& tar.exe -tf $tar
        if ($LASTEXITCODE -ne 0 -or @($members | Where-Object { $_ -notmatch '^python/' -or $_ -match '(^|/)\.\.(/|$)' }).Count) { throw 'Unsafe Python archive.' }
        Invoke-Checked 'tar.exe' @('-xf',$tar,'-C',$destination)
    }
    $pythonEntry=$assets | Where-Object id -eq 'python'
    if ((Get-InstallHash $python) -ne $pythonEntry.executable_sha256) { throw 'The local Python executable differs from the verified runtime. It was not executed.' }
    $env:PATH=(Split-Path -Parent $python)+[IO.Path]::PathSeparator+$env:PATH
    if (-not $SkipGpuCheck) { Invoke-Checked $python @((Join-Path $installRoot 'scripts\check-driver.py')) }
    # The original's pinned engine archive is checked before extraction and installed with rollback.
    $runtime=$assets | Where-Object id -eq 'ace-runtime'
    $ROOT=$installRoot; $DATA=Join-Path $installRoot 'data'; $ENGINE=Join-Path $installRoot 'engine\acestep.cpp'
    $ENGINE_WIN_REV=$runtime.revision; $ENGINE_WIN_URL=$runtime.url; $ENGINE_WIN_SHA256=$runtime.sha256
    function Port-Laeuft([int]$Number) { return [bool](Get-NetTCPConnection -State Listen -LocalPort $Number -ErrorAction SilentlyContinue) }
    function Download([string]$Url,[string]$Destination) {
        if ($Url -ne $runtime.url) { throw 'Unexpected native download source.' }
        Copy-Item -LiteralPath (Get-VerifiedAsset $runtime) -Destination $Destination
        return $true
    }
    . (Join-Path $installRoot 'scripts\install-ace-runtime.ps1')
    Install-AceRuntime
    foreach ($entry in $assets | Where-Object native_library -eq $true) {
        $archive=Get-VerifiedAsset $entry
        Invoke-Checked $python @((Join-Path $installRoot 'scripts\extract-native-libraries.py'),$archive,(Join-Path $installRoot 'engine\acestep.cpp\build\Release'),$entry.id)
    }
    $appPython=Join-Path $installRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $appPython)) { Invoke-Checked $uv @('venv','--python',$python,'--no-python-downloads',(Join-Path $installRoot '.venv')) }
    Invoke-Checked $uv @('pip','sync','--python',$appPython,'--require-hashes',(Join-Path $installRoot 'requirements\app.lock'))
    # Small RVC source/tools are shared by audio import and Deep Mode even without voice training.
    $rvc=Join-Path $installRoot 'engine\rvc'
        if (-not (Test-Path -LiteralPath (Join-Path $rvc '.source-revision.json'))) {
            if (Test-Path -LiteralPath $rvc) { throw 'Existing RVC folder has no verified source marker. It was not overwritten.' }
            $source=Get-VerifiedAsset ($assets | Where-Object id -eq 'rvc-source')
            $stage=Join-Path $installRoot ('engine\rvc-extract-'+[Guid]::NewGuid().ToString('N'))
            Expand-VerifiedZip $source $stage
            $folders=@(Get-ChildItem -LiteralPath $stage -Directory)
            if ($folders.Count -ne 1) { throw 'Unexpected RVC archive structure.' }
            Invoke-Checked $python @((Join-Path $installRoot 'scripts\apply-rvc-patch.py'),$folders[0].FullName,(Join-Path $installRoot 'scripts\rvc-customizations.patch'))
            Move-Item -LiteralPath $folders[0].FullName -Destination $rvc
        }
        Invoke-Checked $python @((Join-Path $installRoot 'scripts\check-rvc-source.py'),$rvc,(Join-Path $installRoot 'scripts\rvc-customizations.patch'))
        if (-not $MusicOnly) {
            $rvcPython=Join-Path $rvc '.venv\Scripts\python.exe'
            if (-not (Test-Path -LiteralPath $rvcPython)) { Invoke-Checked $uv @('venv','--python',$python,'--no-python-downloads',(Join-Path $rvc '.venv')) }
            Invoke-Checked $uv @('pip','sync','--python',$rvcPython,'--require-hashes',(Join-Path $installRoot 'requirements\rvc.lock'))
        }
    foreach ($entry in $models) {
        Install-VerifiedFile $entry
        if ($entry.id -eq 'rvc-mute.zip' -and -not (Test-Path -LiteralPath (Join-Path $installRoot 'engine\rvc\logs\mute\0_gt_wavs\mute40k.wav'))) {
            Invoke-Checked $python @((Join-Path $installRoot 'scripts\extract-mute.py'),(Join-Path $installRoot $entry.target),(Join-Path $installRoot 'engine\rvc\logs'))
        }
    }
    Write-ForkEngineConfig -Path (Join-Path $installRoot 'data\engine.conf') -LmFile "acestep-5Hz-lm-$LM-Q8_0.gguf" -Cpu:$Cpu -Auto:$Auto
    Invoke-Checked $appPython @((Join-Path $installRoot 'scripts\finish-install.py'),$(if($XL){'xl'}else{'standard'}))
    if (-not $MusicOnly) {
        . (Join-Path $installRoot 'scripts\rvc-environment.ps1')
        Invoke-Checked $rvcPython @((Join-Path $installRoot 'scripts\verify-runtime.py'))
    }
    Write-Host 'Installation complete. Start with Music Generator ON.bat.'
} finally { Stop-Transcript | Out-Null }
if (-not $NoStart) { & (Join-Path $installRoot 'scripts\fork-control.ps1') -Action Start }
