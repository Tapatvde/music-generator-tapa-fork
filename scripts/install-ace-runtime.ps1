# Install the upstream's pinned Windows release without touching models or foreign processes.
function Get-AceRuntimeHash([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
    finally { $stream.Dispose(); $sha.Dispose() }
}

function Assert-AceRuntimePath([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    $prefix = [IO.Path]::GetFullPath($ROOT).TrimEnd('\','/') + [IO.Path]::DirectorySeparatorChar
    if (-not $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw "Runtime path outside the fork: $full" }
    # Reparse points could redirect an otherwise contained path outside the project.
    $current = $full
    while ($current -and $current.Length -ge $prefix.Length) {
        if ((Test-Path -LiteralPath $current) -and ((Get-Item -LiteralPath $current -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Runtime path contains a reparse point: $current"
        }
        $current = Split-Path -Parent $current
    }
    return $full
}

function Install-AceRuntime {
    $ErrorActionPreference = 'Stop'
    $release = Assert-AceRuntimePath (Join-Path $ENGINE 'build\Release')
    $cache = Assert-AceRuntimePath (Join-Path $DATA "acestep-cpp-win64-$ENGINE_WIN_REV.zip")
    if (Port-Laeuft 8087) { throw 'The fork music server is busy on port 8087. Finish the running job before updating; no process was stopped.' }
    if (@(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -eq (Join-Path $release 'ace-server.exe') }).Count) {
        throw 'The installed music server is still running. No process was stopped.'
    }
    $version=Join-Path $release 'VERSION.txt'
    if (Test-Path -LiteralPath $version) {
        $record=@(Get-Content -LiteralPath $version -Encoding UTF8)
        $hashLines=@($record | Where-Object { $_ -match '^SHA256 ' })
        $intact=$record -contains "ZIP_SHA256=$ENGINE_WIN_SHA256"
        foreach ($line in $hashLines) {
            if ($line -notmatch '^SHA256 ([^/\\]+) ([0-9a-f]{64})$') { $intact=$false;break }
            $file=Join-Path $release $Matches[1];$expected=$Matches[2]
            if (-not (Test-Path -LiteralPath $file) -or (Get-AceRuntimeHash $file) -ne $expected) { $intact=$false;break }
        }
        if ($intact -and $hashLines.Count -gt 0 -and (Test-Path -LiteralPath (Join-Path $release 'ace-server.exe'))) {
            Write-Host "  Verified existing engine $ENGINE_WIN_REV"
            return
        }
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $cache) | Out-Null
    if ((Test-Path -LiteralPath $cache) -and (Get-AceRuntimeHash $cache) -ne $ENGINE_WIN_SHA256) {
        $bad = Assert-AceRuntimePath ($cache + '.bad-' + [Guid]::NewGuid().ToString('N'))
        Move-Item -LiteralPath $cache -Destination $bad
    }
    if (-not (Test-Path -LiteralPath $cache)) {
        if (-not (Download $ENGINE_WIN_URL "$cache.neu")) { throw 'Runtime download failed. Run the installer again to resume.' }
        if ((Get-AceRuntimeHash "$cache.neu") -ne $ENGINE_WIN_SHA256) {
            $bad = Assert-AceRuntimePath ($cache + '.bad-' + [Guid]::NewGuid().ToString('N'))
            Move-Item -LiteralPath "$cache.neu" -Destination $bad
            throw 'Runtime checksum mismatch; the installed version was not changed.'
        }
        Move-Item -LiteralPath "$cache.neu" -Destination $cache
    }
    $incoming = Assert-AceRuntimePath ($release + '.incoming-' + [Guid]::NewGuid().ToString('N'))
    $previous = Assert-AceRuntimePath ($release + '.previous-' + [Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $incoming | Out-Null
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [IO.Compression.ZipFile]::OpenRead($cache)
    try {
        foreach ($entry in $archive.Entries) {
            $target = [IO.Path]::GetFullPath((Join-Path $incoming $entry.FullName))
            if (-not $target.StartsWith($incoming + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe runtime archive path.' }
        }
    } finally { $archive.Dispose() }
    [IO.Compression.ZipFile]::ExtractToDirectory($cache, $incoming)
    if (-not (Test-Path -LiteralPath (Join-Path $incoming 'ace-server.exe'))) { throw 'ace-server.exe missing in verified runtime archive; installed version unchanged.' }
    # Retain additional app-local CUDA/MSVC dependencies that the archive does not provide.
    if (Test-Path -LiteralPath $release) {
        Get-ChildItem -LiteralPath $release -File -Filter '*.dll' | ForEach-Object {
            $target = Join-Path $incoming $_.Name
            if (-not (Test-Path -LiteralPath $target)) { Copy-Item -LiteralPath $_.FullName -Destination $target }
        }
    }
    $info = @("PREBUILT=$(Get-Date -Format s)", "ENGINE_REV=$ENGINE_WIN_REV", "SOURCE=$ENGINE_WIN_URL", "ZIP_SHA256=$ENGINE_WIN_SHA256")
    foreach ($file in (Get-ChildItem -LiteralPath $incoming -File | Where-Object { $_.Extension -in '.exe','.dll' } | Sort-Object Name)) {
        $info += "SHA256 $($file.Name) $(Get-AceRuntimeHash $file.FullName)"
    }
    $info | Set-Content -LiteralPath (Join-Path $incoming 'VERSION.txt') -Encoding UTF8
    $moved = $false
    try {
        if (Test-Path -LiteralPath $release) { Move-Item -LiteralPath $release -Destination $previous; $moved = $true }
        Move-Item -LiteralPath $incoming -Destination $release
    } catch {
        if ($moved -and -not (Test-Path -LiteralPath $release)) { Move-Item -LiteralPath $previous -Destination $release }
        throw
    }
    Write-Host "  Installed verified engine $ENGINE_WIN_REV; SHA-256 $ENGINE_WIN_SHA256"
    if ($moved) { Write-Host "  Previous runtime preserved in $previous" }
}
