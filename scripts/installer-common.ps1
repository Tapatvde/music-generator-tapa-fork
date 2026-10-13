$ErrorActionPreference='Stop'
$installRoot=Split-Path -Parent $PSScriptRoot
$installCache=Join-Path $installRoot 'engine\downloads'

function Get-InstallHash([string]$Path) {
    $stream=[IO.File]::OpenRead($Path);$hasher=[Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($hasher.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
    finally { $stream.Dispose();$hasher.Dispose() }
}

function Assert-InProgram([string]$Path) {
    $absolute=[IO.Path]::GetFullPath($Path)
    $prefix=[IO.Path]::GetFullPath($installRoot).TrimEnd('\')+'\'
    if (-not $absolute.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)) { throw "Path outside program folder: $Path" }
    return $absolute
}

function Get-VerifiedAsset($Entry) {
    $destination=Assert-InProgram (Join-Path $installCache ($Entry.sha256+'.bin'))
    New-Item -ItemType Directory -Path $installCache -Force | Out-Null
    if (Test-Path -LiteralPath $destination) {
        if ((Get-InstallHash $destination) -eq $Entry.sha256) { return $destination }
        throw "Existing cached asset has a wrong checksum: $($Entry.id). It was retained."
    }
    if ($AssetCache) {
        $candidate=Join-Path $AssetCache ($Entry.sha256+'.bin')
        if (Test-Path -LiteralPath $candidate) {
            if ((Get-InstallHash $candidate) -ne $Entry.sha256) { throw "External cache checksum mismatch: $($Entry.id)" }
            Copy-Item -LiteralPath $candidate -Destination $destination
            return $destination
        }
    }
    if ($NoNetwork) { throw "Verified asset missing in offline cache: $($Entry.id)" }
    Write-Host "Downloading $($Entry.id) ($([math]::Round([long]$Entry.bytes/1MB,1)) MB)"
    $part=$destination+'.part'
    if ((Test-Path -LiteralPath $part) -and (Get-InstallHash $part) -eq $Entry.sha256) {
        Move-Item -LiteralPath $part -Destination $destination
        return $destination
    }
    & curl.exe --location --fail --retry 3 --retry-delay 2 --continue-at - --progress-bar --output $part $Entry.url
    if ($LASTEXITCODE -in @(33,36)) {
        # Some pinned archive providers do not support HTTP Range. Retain the partial download.
        if (Test-Path -LiteralPath $part) { Move-Item -LiteralPath $part -Destination ($part+'.no-range-'+[Guid]::NewGuid().ToString('N')) }
        Write-Host 'The server cannot resume this file. Restarting its verified download.'
        & curl.exe --location --fail --retry 3 --retry-delay 2 --progress-bar --output $part $Entry.url
    }
    if ($LASTEXITCODE -ne 0) { throw "Download failed: $($Entry.id). Run Install.bat again to resume." }
    if ((Get-InstallHash $part) -ne $Entry.sha256) {
        $quarantine=$part+'.bad-'+[Guid]::NewGuid().ToString('N')
        Move-Item -LiteralPath $part -Destination $quarantine
        throw "Checksum mismatch: $($Entry.id). The file was retained for inspection. No unverified file was installed."
    }
    Move-Item -LiteralPath $part -Destination $destination
    return $destination
}

function Install-VerifiedFile($Entry) {
    $target=Assert-InProgram (Join-Path $installRoot $Entry.target)
    if (Test-Path -LiteralPath $target) {
        if ((Get-InstallHash $target) -eq $Entry.sha256) { Write-Host "Verified existing file: $($Entry.id)";return }
        throw "Existing file differs: $($Entry.target). It was not overwritten."
    }
    $asset=Get-VerifiedAsset $Entry
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath $asset -Destination ($target+'.verified')
    Move-Item -LiteralPath ($target+'.verified') -Destination $target
}

function Expand-VerifiedZip([string]$Archive,[string]$Destination) {
    $Destination=Assert-InProgram $Destination
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip=[IO.Compression.ZipFile]::OpenRead($Archive)
    try {
        foreach ($entry in $zip.Entries) {
            $name=$entry.FullName.Replace('/','\')
            $full=[IO.Path]::GetFullPath((Join-Path $Destination $name))
            if (-not $full.StartsWith($Destination.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe ZIP member.' }
            if (($entry.ExternalAttributes -shr 16 -band 0xF000) -eq 0xA000) { throw 'ZIP links are not supported.' }
        }
    } finally { $zip.Dispose() }
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    # Expand-Archive requires a .zip extension; the verified cache retains its hash name.
    $copy=Join-Path $installCache ([Guid]::NewGuid().ToString('N')+'.zip')
    Copy-Item -LiteralPath $Archive -Destination $copy
    Expand-Archive -LiteralPath $copy -DestinationPath $Destination
    Remove-Item -LiteralPath $copy
}

function Invoke-Checked([string]$Executable,[string[]]$Arguments) {
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "A setup command failed with exit code $LASTEXITCODE. See the transcript." }
}
