
<#
.SYNOPSIS
    Validates and fixes Mermaid diagrams in Markdown files, then runs markdownlint fixes.
.DESCRIPTION
    Scans the repository for Markdown files containing Mermaid diagrams.
    Applies syntax fixes and the FALL theme to Mermaid blocks.
    Runs the robust markdownlint fixer (v3).
    Validates the results and logs errors.
.PARAMETER RootPath
    The root directory to scan. Defaults to current location.
.PARAMETER ExcludeDiagramsFolder
    If set, excludes the 'docs/diagrams' folder from processing.
.PARAMETER LintScriptPath
    Path to the fix_markdownlint_robust_v3.ps1 script.
#>
[CmdletBinding(SupportsShouldProcess=$true)]
[System.Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidUsingWriteHost', '')]
param(
    [string]$RootPath = ".",
    [switch]$ExcludeDiagramsFolder,
    [string]$LintScriptPath = "ps_scripts/fix_markdownlint_robust_v3.ps1"
)
$ErrorActionPreference = "Stop"
# --- Configuration ---
$FallThemeYaml = @"
config:
  theme: base
  fontSize: 16
  themeCSS: |
    .node rect, .cluster rect, .edgePath path { transition: filter 0.2s ease, stroke-width: 0.2s ease; }
    .node:hover rect, .cluster:hover rect, .edgePath:hover path { filter: drop-shadow(0 0 8px rgba(0,0,0,0.35)); stroke-width: 3px; }
    .edgeLabel rect { rx: 6px; ry: 6px; stroke-width: 1px; }
    .cluster-label { font-weight: 600; }
    .node .label, .nodeLabel, .node foreignObject div, .edgeLabel { font-size: 20px !important; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif !important; }
    .node.decision .label, .node polygon + .label { font-size: 18px !important; }
  themeVariables:
    primaryColor: '#FFF3E0'
    secondaryColor: '#F3E5F5'
    tertiaryColor: '#FFF8E1'
    primaryTextColor: '#5D4037'
    secondaryTextColor: '#4A148C'
    tertiaryTextColor: '#F57F17'
    primaryBorderColor: '#FF6F00'
    secondaryBorderColor: '#9C27B0'
    tertiaryBorderColor: '#FBC02D'
    background: '#FFF8E1'
    textColor: '#5D4037'
    lineColor: '#FF9800'
    fontFamily: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif'
    fontSize: '16px'
    nodeBorder: '#FF6F00'
    mainBkg: '#FFF3E0'
    clusterBkg: '#F3E5F5'
    clusterBorder: '#9C27B0'
    edgeLabelBackground: '#FFF8E1'
    actorBkg: '#FFF3E0'
    actorBorder: '#FF6F00'
    actorTextColor: '#5D4037'
    signalColor: '#FF9800'
    signalTextColor: '#5D4037'
    labelBoxBkgColor: '#F3E5F5'
    noteBkgColor: '#FFF8E1'
    noteTextColor: '#F57F17'
    noteBorderColor: '#FBC02D'
    pie1: '#FF6F00'
    pie2: '#9C27B0'
    pie3: '#FBC02D'
    pie4: '#FF9800'
    pie5: '#BA68C8'
    pie6: '#FFD54F'
    pie7: '#FFB74D'
    pie8: '#CE93D8'
    pie9: '#FFF176'
    pie10: '#FF8A65'
    pie11: '#F3E5F5'
    pie12: '#FFF8E1'
    sectionBkgColor: '#FFF8E1'
    altSectionBkgColor: '#FFF3E0'
    sectionBkgColor2: '#F3E5F5'
    taskBkgColor: '#FFB74D'
    taskBorderColor: '#FF6F00'
    activeTaskBkgColor: '#FF9800'
    activeTaskBorderColor: '#E65100'
    doneTaskBkgColor: '#FFCC80'
    doneTaskBorderColor: '#FF6F00'
    critBkgColor: '#CE93D8'
    critBorderColor: '#7B1FA2'
    taskTextColor: '#5D4037'
    taskTextOutsideColor: '#5D4037'
    taskTextLightColor: '#5D4037'
    taskTextDarkColor: '#FFFFFF'
    gridColor: '#FFCC80'
    todayLineColor: '#7B1FA2'
    classText: '#5D4037'
    fillType0: '#FFF3E0'
    fillType1: '#F3E5F5'
    fillType2: '#FFF8E1'
    fillType3: '#FFB74D'
    fillType4: '#CE93D8'
    fillType5: '#FFD54F'
    fillType6: '#FF8A65'
    fillType7: '#BA68C8'
    attributeBackgroundColorOdd: '#FFF8E1'
    attributeBackgroundColorEven: '#FFF3E0'
  gantt:
    fontSize: 16
    barHeight: 24
    barGap: 6
    topPadding: 50
    leftPadding: 75
    gridLineStartPadding: 35
    numberSectionStyles: 4
  flowchart:
    curve: 'linear'
    htmlLabels: false
    useMaxWidth: true
    padding: 25
    nodeSpacing: 60
    rankSpacing: 80
    diagramPadding: 8
  sequence:
    diagramMarginX: 50
    diagramMarginY: 10
    actorMargin: 50
    boxMargin: 10
    boxTextMargin: 5
    noteMargin: 10
"@
# --- Helper Functions ---
function Backup-File {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param([string]$file)
    $backupDir = Join-Path -Path (Split-Path $file -Parent) -ChildPath ".backups"
    if (!(Test-Path $backupDir)) { New-Item -ItemType Directory -Path $backupDir | Out-Null }
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupFile = Join-Path $backupDir ("$(Split-Path $file -Leaf).$timestamp.bak")
    Copy-Item $file $backupFile -Force
    return $backupFile
}

function Restore-File {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param([string]$backup, [string]$target)
    Copy-Item $backup $target -Force
}
function Remove-Backup {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param([string]$backup)
    if (Test-Path $backup) { Remove-Item $backup -Force }
}

function Repair-MermaidBlock {
    param([string]$blockContent)
    # 0. Cleanup: Remove trailing backslashes and whitespace from all lines
    # This fixes artifacts like '---\' or 'value: 10\'
    $lines = $blockContent -split "`n"
    $cleanLines = @()
    foreach ($line in $lines) {
        $cleanLines += $line.TrimEnd().TrimEnd('\')
    }
    $blockContent = $cleanLines -join "`n"
    # 1. Clean Slate: Remove ANY existing frontmatter (valid, broken, or messy)
    # Manual parsing to avoid regex pitfalls
    $trimmed = $blockContent.TrimStart()
    if ($trimmed.StartsWith('---')) {
        # Find the second '---'
        # We search from index 3 to skip the first '---'
        $second = $trimmed.IndexOf('---', 3)
        if ($second -gt 0) {
            # Remove everything up to second ---
            # Then trim any leading backslashes or whitespace from the remainder
            $blockContent = $trimmed.Substring($second + 3)
        }
    }
    # Remove any leftover leading backslashes or whitespace
    $blockContent = $blockContent.TrimStart().TrimStart('\').TrimStart()
    $blockContent = $blockContent.TrimStart().TrimStart('\').TrimStart()
    # 2. Prepend Fresh Frontmatter
    $blockContent = "---`n$FallThemeYaml`n---`n" + $blockContent
    # 3. Determine Diagram Type (for specific rules)
    $isSequence = $blockContent -match '(?m)^sequenceDiagram'
    # 3. Apply Syntax Fixes
    # Fix: Double colons :: -> space (except in URLs)
    # We do this carefully. Negative lookbehind for http/https is hard in regex,
    # so we'll split by lines and process non-url lines.
    $lines = $blockContent -split "`n"
    $fixedLines = @()
    foreach ($line in $lines) {
        if ($line -notmatch 'https?://') {
            $line = $line -replace '::', ' '
        }
        # Fix: Colons in subgraph labels: subgraph "Foo: Bar" -> subgraph "Foo Bar"
        if ($line -match 'subgraph\s+".*?:.*?"') {
            $line = $line -replace ':', ' '
        }
        # Fix: Unquoted forward slashes in node labels: [/path] -> ["/path"]
        # Pattern: [ followed by / followed by chars followed by ]
        # Avoid matching if already quoted ["..."]
        if ($line -match '\[/[^"\]]+\]') {
             $line = [regex]::Replace($line, '\[(/[^"\]]+)\]', '["$1"]')
        }
        # Fix: HTML tags (remove <br/> if not sequence, remove others always)
        if (-not $isSequence) {
            $line = $line -replace '<br\s*/?>', ' '
        }
        $line = $line -replace '<span>|</span>|<div>|</div>', ''
        $fixedLines += $line
    }
    $blockContent = $fixedLines -join "`n"
    return $blockContent
}
function Update-MermaidFile {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param(
        [string]$FilePath,
        [string]$LintScriptPath
    )
    if ($PSCmdlet.ShouldProcess($FilePath, "Update Mermaid diagrams and lint")) {
        Write-Host "Processing: $FilePath" -ForegroundColor Cyan
        $backup = Backup-File $FilePath
        try {
            $content = Get-Content $FilePath -Raw -Encoding UTF8
            # Regex to find mermaid blocks: ```mermaid ... ```
            # Using Matches and manual replacement to avoid ScriptBlock parser issues
            $mermaidMatches = [regex]::Matches($content, '(?ms)```mermaid(.*?)```')
            $newContent = $content
            # Process in reverse order to preserve indices
            for ($i = $mermaidMatches.Count - 1; $i -ge 0; $i--) {
                $m = $mermaidMatches[$i]
                $inner = $m.Groups[1].Value
                $fixedInner = Repair-MermaidBlock $inner
                $replacement = '```mermaid' + "`n" + $fixedInner + '```'
                $before = $newContent.Substring(0, $m.Index)
                $after = $newContent.Substring($m.Index + $m.Length)
                $newContent = $before + $replacement + $after
            }
            if ($newContent -ne $content) {
                # Use .NET file writing to ensure exact content preservation
                [System.IO.File]::WriteAllText($FilePath, $newContent, [System.Text.Encoding]::UTF8)
                Write-Host "Fixed." -ForegroundColor Green
            } else {
                Write-Host "No changes." -ForegroundColor Gray
            }
            # Run Lint Script
            if (Test-Path $LintScriptPath) {
                Write-Host "  -> Running Markdownlint fixer..." -ForegroundColor Cyan
                & $LintScriptPath -FilePath $FilePath | Out-Null
            } else {
                Write-Warning "Lint script not found at $LintScriptPath"
            }
            # Validation Scan
            $finalContent = Get-Content $FilePath -Raw -Encoding UTF8
            $errors = @()
            if ($finalContent -match '::' -and $finalContent -notmatch 'https?://') { $errors += "Double colons found" }
            if ($finalContent -match 'subgraph\s+".*?:.*?"') { $errors += "Colons in subgraph labels found" }
            if ($finalContent -match '\[/[^"\]]+\]') { $errors += "Unquoted forward slashes found" }
            if ($finalContent -match '<br\s*/?>' -and $finalContent -notmatch 'sequenceDiagram') { $errors += "HTML break tags found in non-sequence diagram" }
            if ($errors.Count -gt 0) {
                Write-Warning "  -> Validation Errors Found:"
                foreach ($err in $errors) { Write-Warning "     - $err" }
                # We do NOT restore backup here, as we want to keep partial fixes.
                # The user asked to "log them to be fixed by you the model later".
            } else {
                Write-Host "  -> Validation Passed." -ForegroundColor Green
                Remove-Backup $backup
            }
        } catch {
            Write-Error "Failed to process $FilePath : $_"
            Restore-File $backup $FilePath
        }
    }
}
# --- Main Execution ---
Write-Host "Starting Mermaid Fix & Lint Scan..." -ForegroundColor Magenta
# 1. Discovery
$files = Get-ChildItem -Path $RootPath -Recurse -Filter "*.md" | Where-Object {
    if ($ExcludeDiagramsFolder -and $_.FullName -like "*\docs\diagrams\*") { return $false }
    return $true
}
$mermaidFiles = @()
foreach ($file in $files) {
    if (Select-String -Path $file.FullName -Pattern "```mermaid" -Quiet) {
        $mermaidFiles += $file.FullName
    }
}
Write-Host "Found $($mermaidFiles.Count) files with Mermaid diagrams." -ForegroundColor Yellow
# 2. Processing
foreach ($file in $mermaidFiles) {
    Update-MermaidFile -FilePath $file -LintScriptPath $LintScriptPath
}
Write-Host "Scan and Fix Complete." -ForegroundColor Magenta
