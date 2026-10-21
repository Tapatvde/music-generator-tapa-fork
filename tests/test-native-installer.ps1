# Tiny synthetic archives exercise the real installer helper; no GPU, network or user files.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$fixtures = Join-Path $projectRoot ('data\validation\runtime-update-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $fixtures | Out-Null
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
. (Join-Path $projectRoot 'scripts\install-ace-runtime.ps1')
$script:busy = $false
$script:failSwap = $false
$script:downloads = 0
function Port-Laeuft([int]$Port) { return $script:busy }
function Get-CimInstance { return @() }
function Download([string]$Url, [string]$Target) { $script:downloads++; Copy-Item -LiteralPath $script:fixtureZip -Destination $Target; return $true }
function Move-Item([string]$LiteralPath, [string]$Destination) {
    if ($script:failSwap -and $LiteralPath -match '\.incoming-') { throw 'Simulated directory rename failure' }
    Microsoft.PowerShell.Management\Move-Item -LiteralPath $LiteralPath -Destination $Destination
}
function Setup-Fixture([string]$Name, [string]$Entry='ace-server.exe') {
    $script:ROOT = Join-Path $fixtures $Name
    $script:ENGINE = Join-Path $ROOT 'engine\acestep.cpp'
    $script:DATA = Join-Path $ROOT 'data'
    $script:ENGINE_WIN_REV = 'fixture'
    $script:ENGINE_WIN_URL = 'https://invalid.example/never-contacted.zip'
    $release = Join-Path $ENGINE 'build\Release'
    New-Item -ItemType Directory -Force -Path $release, $DATA, (Join-Path $ENGINE 'models') | Out-Null
    [IO.File]::WriteAllText((Join-Path $release 'ace-server.exe'), 'old runtime')
    [IO.File]::WriteAllText((Join-Path $release 'extra-cuda.dll'), 'local dependency')
    [IO.File]::WriteAllText((Join-Path $ENGINE 'models\private.gguf'), 'model unchanged')
    [IO.File]::WriteAllText((Join-Path $DATA 'private.wav'), 'recording unchanged')
    $script:fixtureZip = Join-Path $ROOT 'fixture.zip'
    $zip = [IO.Compression.ZipFile]::Open($script:fixtureZip, [IO.Compression.ZipArchiveMode]::Create)
    try {
        $entryFile = $zip.CreateEntry($Entry)
        $writer = New-Object IO.StreamWriter($entryFile.Open())
        try { $writer.Write('new runtime') } finally { $writer.Dispose() }
    } finally { $zip.Dispose() }
    $script:ENGINE_WIN_SHA256 = Get-AceRuntimeHash $script:fixtureZip
    $script:downloads = 0
    return $release
}
function Assert-Old([string]$Release) {
    if ([IO.File]::ReadAllText((Join-Path $Release 'ace-server.exe')) -ne 'old runtime') { throw 'Old runtime was damaged' }
}
function Must-Reject([scriptblock]$Action) {
    $rejected = $false
    try { & $Action } catch { $rejected = $true }
    if (-not $rejected) { throw 'Unsafe input accepted' }
}

$release = Setup-Fixture 'success'
Install-AceRuntime
if ([IO.File]::ReadAllText((Join-Path $release 'ace-server.exe')) -ne 'new runtime') { throw 'New runtime missing' }
if ([IO.File]::ReadAllText((Join-Path $release 'extra-cuda.dll')) -ne 'local dependency') { throw 'Extra dependency lost' }
$previous = @(Get-ChildItem -LiteralPath (Split-Path -Parent $release) -Directory -Filter 'Release.previous-*')
if ($previous.Count -ne 1) { throw 'Recoverable old runtime missing' }
Assert-Old $previous[0].FullName
if ([IO.File]::ReadAllText((Join-Path $ENGINE 'models\private.gguf')) -ne 'model unchanged') { throw 'Model changed' }
if ([IO.File]::ReadAllText((Join-Path $DATA 'private.wav')) -ne 'recording unchanged') { throw 'Recording changed' }
if (-not (Select-String -LiteralPath (Join-Path $release 'VERSION.txt') -Pattern '^ENGINE_REV=fixture$')) { throw 'Runtime provenance missing' }

# Reinstalling an intact pinned runtime reuses it without another backup/download.
Install-AceRuntime
if (@(Get-ChildItem -LiteralPath (Split-Path -Parent $release) -Directory -Filter 'Release.previous-*').Count -ne 1 -or $script:downloads -ne 1) { throw 'Verified runtime was not reused.' }

$release = Setup-Fixture 'busy'
$script:busy = $true
Must-Reject { Install-AceRuntime }
$script:busy = $false
Assert-Old $release
if ($script:downloads) { throw 'Busy server still caused a download' }

$release = Setup-Fixture 'checksum'
$script:ENGINE_WIN_SHA256 = '0' * 64
Must-Reject { Install-AceRuntime }
Assert-Old $release
if (@(Get-ChildItem -LiteralPath $DATA -Filter '*.bad-*').Count -ne 1) { throw 'Rejected download not preserved' }

$release = Setup-Fixture 'traversal' '../outside.exe'
Must-Reject { Install-AceRuntime }
Assert-Old $release
if (Test-Path -LiteralPath (Join-Path $ENGINE 'build\outside.exe')) { throw 'ZIP path escaped staging' }

$release = Setup-Fixture 'missing-server' 'not-the-server.txt'
Must-Reject { Install-AceRuntime }
Assert-Old $release

$release = Setup-Fixture 'rollback'
$script:failSwap = $true
Must-Reject { Install-AceRuntime }
$script:failSwap = $false
Assert-Old $release

$release = Setup-Fixture 'outside'
$script:ENGINE = Split-Path -Parent $fixtures
Must-Reject { Install-AceRuntime }
Assert-Old $release

'PASS: pinned runtime installation/reuse, retained DLLs/models/recordings, backup, busy-port refusal, hash and ZIP checks, rollback and containment.'
