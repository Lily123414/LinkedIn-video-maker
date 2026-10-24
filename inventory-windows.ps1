[CmdletBinding()]
param(
    [string]$Source = 'D:\Lily\Ankarsrum\Company Knowledge Hub',
    [string]$Output = '',
    [switch]$NoOpen
)
$ErrorActionPreference = 'Stop'
$writer = $null
$stream = $null
$mediaCount = 0
$issueCount = 0
$Columns = @('Name','Original path','Relative path','Original folder','File type','Extension','Size bytes','Modified UTC','Suggested category','Evidence','Review status','Review reason','Visual inspection','Scan status')
$Photos = @('.jpg','.jpeg','.png','.webp','.heic','.heif','.tif','.tiff','.bmp','.gif','.dng','.cr2','.cr3','.nef','.arw','.avif')
$Videos = @('.mp4','.mov','.m4v','.avi','.mkv','.mts','.m2ts','.wmv','.webm','.mpg','.mpeg','.3gp')
$Rules = [ordered]@{
    Design = @('design','cad','drawings','设计','图纸')
    Prototyping = @('prototype','prototypes','prototyping','试制','样机','原型')
    Lab = @('lab','laboratory','testing','test lab','实验室','测试','检测')
    Manufacturing = @('manufacturing','production','assembly','factory','生产','制造','装配','工厂')
}

function Assert-PlainAncestors([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    while ($null -ne $item) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Linked/reparse path is not supported: $($item.FullName)"
        }
        $item = $item.Parent
    }
}

function Write-Row($Row) {
    $values = foreach ($column in $Columns) {
        $value = [string]$Row[$column]
        if ($value -match '^\s*[=+@-]' -or $value -match '^[\t\r]') { $value = "'" + $value }
        '"' + $value.Replace('"','""') + '"'
    }
    $writer.WriteLine(($values -join ','))
}

function Get-Relative([string]$Path) {
    if ($Path -eq $sourcePath) { return '.' }
    return $Path.Substring($sourcePrefix.Length)
}

function Write-Issue([string]$Path, [string]$Reason) {
    Write-Row @{
        'Name' = [IO.Path]::GetFileName($Path)
        'Original path' = $Path
        'Relative path' = Get-Relative $Path
        'Original folder' = [IO.Path]::GetDirectoryName($Path)
        'File type' = 'Scan issue'
        'Suggested category' = 'To Review'
        'Review status' = 'Needs review'
        'Review reason' = $Reason
        'Visual inspection' = 'Not performed'
        'Scan status' = 'Skipped'
    }
    $script:issueCount++
}

function Get-Suggestion([string]$Relative) {
    $folder = [IO.Path]::GetDirectoryName($Relative)
    $hits = @()
    $evidence = @()
    foreach ($category in $Rules.Keys) {
        $matched = $false
        foreach ($keyword in $Rules[$category]) {
            if ($keyword -match '^[\x00-\x7f]+$') {
                $pattern = '(?<![a-z0-9])' + [regex]::Escape($keyword) + '(?![a-z0-9])'
            } else { $pattern = [regex]::Escape($keyword) }
            if ($folder -match $pattern) {
                $matched = $true
                $evidence += ($category + ': folder clue "' + $keyword + '"')
            }
        }
        if ($matched) { $hits += $category }
    }
    if ($hits.Count -eq 1) {
        return @{ Category=$hits[0]; Evidence=($evidence -join '; '); Reason='Folder context only; content has not been inspected. Confirm manually.' }
    }
    if ($hits.Count -gt 1) {
        return @{ Category='To Review'; Evidence=($evidence -join '; '); Reason='Conflicting category clues in folder names.' }
    }
    return @{ Category='To Review'; Evidence='No recognized category clues in relative folder names.'; Reason='Insufficient evidence. Filename alone is not used.' }
}

try {
    $sourceItem = Get-Item -LiteralPath $Source -Force
    if (-not $sourceItem.PSIsContainer) { throw 'Source must be a directory.' }
    Assert-PlainAncestors $sourceItem.FullName
    $sourcePath = $sourceItem.FullName
    $sourcePrefix = $sourcePath.TrimEnd([char[]]@('\','/')) + [IO.Path]::DirectorySeparatorChar
    if (-not $Output) {
        $reportFolder = Join-Path $env:USERPROFILE 'Downloads'
        $Output = Join-Path $reportFolder ('motor-media-inventory-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fffffff') + '.csv')
    }
    $outputPath = [IO.Path]::GetFullPath($Output)
    $outputParent = [IO.Path]::GetDirectoryName($outputPath)
    if (-not [IO.Directory]::Exists($outputParent)) { throw "Report folder does not exist: $outputParent" }
    Assert-PlainAncestors $outputParent
    if ($outputPath.Equals($sourcePath,[StringComparison]::OrdinalIgnoreCase) -or $outputPath.StartsWith($sourcePrefix,[StringComparison]::OrdinalIgnoreCase)) {
        throw 'The report must be saved outside the source folder.'
    }
    # CreateNew is atomic: never truncate or overwrite an existing file.
    $stream = [IO.File]::Open($outputPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    $writer = [IO.StreamWriter]::new($stream,[Text.UTF8Encoding]::new($true))
    $writer.WriteLine((($Columns | ForEach-Object { '"' + $_ + '"' }) -join ','))
    $folders = [Collections.Generic.Stack[string]]::new()
    $folders.Push($sourcePath)
    while ($folders.Count -gt 0) {
        $folder = $folders.Pop()
        try { $entries = [IO.Directory]::GetFileSystemEntries($folder); [Array]::Sort($entries) }
        catch { Write-Issue $folder ('Cannot list folder: ' + $_.Exception.Message); continue }
        foreach ($path in $entries) {
            try { $item = Get-Item -LiteralPath $path -Force }
            catch { Write-Issue $path ('Cannot inspect metadata: ' + $_.Exception.Message); continue }
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                Write-Issue $path 'Linked/reparse entry skipped; target/content not accessed.'
                continue
            }
            if ($item.PSIsContainer) { $folders.Push($path); continue }
            $extension = $item.Extension.ToLowerInvariant()
            if ($extension -notin $Photos -and $extension -notin $Videos) { continue }
            $relative = Get-Relative $path
            $suggestion = Get-Suggestion $relative
            $kind = if ($extension -in $Photos) { 'Photo' } else { 'Video' }
            Write-Row @{
                'Name'=$item.Name; 'Original path'=$path; 'Relative path'=$relative
                'Original folder'=$item.DirectoryName; 'File type'=$kind; 'Extension'=$extension
                'Size bytes'=$item.Length; 'Modified UTC'=$item.LastWriteTimeUtc.ToString('o')
                'Suggested category'=$suggestion.Category; 'Evidence'=$suggestion.Evidence
                'Review status'='Needs review'; 'Review reason'=$suggestion.Reason
                'Visual inspection'='Not performed'; 'Scan status'='Listed'
            }
            $mediaCount++
        }
    }
    $writer.Dispose(); $writer = $null; $stream = $null
    Write-Host "Media files listed: $mediaCount. Scan issues: $issueCount."
    Write-Host "New CSV: $outputPath"
    Write-Host 'Source files were not changed. Every category suggestion requires human review.'
    if ($issueCount -gt 0 -or $mediaCount -eq 0) {
        Write-Host 'Inventory may be incomplete. Check scan issues and the selected source folder.'
        exit 2
    }
    if (-not $NoOpen -and $env:OS -eq 'Windows_NT') { & explorer.exe "/select,`"$outputPath`"" }
    exit 0
} catch {
    Write-Host ('Inventory stopped: ' + $_.Exception.Message)
    Write-Host 'Source files were not modified. Preserve any partial CSV and use a new report name when retrying.'
    exit 1
} finally {
    if ($null -ne $writer) { $writer.Dispose() }
    elseif ($null -ne $stream) { $stream.Dispose() }
}
