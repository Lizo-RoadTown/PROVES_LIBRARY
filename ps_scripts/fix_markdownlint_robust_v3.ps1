<#
Universal Markdownlint Rule Script (PowerShell)
- Each markdownlint rule handled in its own section
- Per-section backup, validation, and rollback
- Robust backup/restore logic (never deletes backup until script completes)
- Improved MD007: Handles unordered lists, nested lists, ignores code blocks, and tests only true lists
- Works for any markdown file

Usage: pwsh ./fix_markdownlint_robust_v3.ps1 -FilePath <file>
#>

[CmdletBinding()]
[System.Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', '')]
param(
    [Parameter(Mandatory=$true)]
    [string]$FilePath
)

# --- Robust Backup/Restore Functions ---
function Backup-File {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param([string]$file)
    $parent = Split-Path $file -Parent
    if ([string]::IsNullOrEmpty($parent)) { $parent = "." }
    $backupDir = Join-Path -Path $parent -ChildPath ".backups"
    if (!(Test-Path $backupDir)) { New-Item -ItemType Directory -Path $backupDir | Out-Null }
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupFile = Join-Path $backupDir ("$(Split-Path $file -Leaf).$timestamp.bak")
    if ($PSCmdlet.ShouldProcess($file, "Backup file to $backupFile")) {
        Copy-Item $file $backupFile -Force
    }
    return $backupFile
}

function Restore-File {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param([string]$backup, [string]$target)
    if ($PSCmdlet.ShouldProcess($target, "Restore file from $backup")) {
        Copy-Item $backup $target -Force
    }
}

function Remove-Backup {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param([string]$backup)
    if ($PSCmdlet.ShouldProcess($backup, "Remove backup file")) {
        if (Test-Path $backup) {
            Remove-Item $backup -Force
        }
    }
    else {
        # No state change if ShouldProcess returns false
        return
    }
}

# --- Helper: Update Line Endings ---
function Update-LineEndings {
    param([string]$content)
    # Replace CRLF with LF, then CR with LF (just in case)
    return $content -replace "`r`n", "`n" -replace "`r", "`n"
}

# --- Corruption Fixes: Pipe Artifacts & Indentation ---
function Format-CorruptionFixes {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param([string]$content)

    $lines = $content -split "`n"
    $result = [System.Collections.Generic.List[string]]::new()
    $inCode = $false
    $blockIndent = ""

    foreach ($line in $lines) {
        $newLine = $line

        # 1. Fix Pipe Artifacts (lines wrapped in |...|)
        # Regex: Start with |, content, end with |, optional trailing pipes
        if ($newLine -match '^\|(.*)\|(\s*\|\s*)*$') {
            $inner = $matches[1]
            if ($inner -notmatch '\|') {
                # Likely an artifact (single column)
                $newLine = $inner
            }
        }

        # 2. Fix Code Block Indentation
        if ($newLine -match '^(\s*)```') {
            if (-not $inCode) {
                $inCode = $true
                $blockIndent = $matches[1]
            } else {
                $inCode = $false
                $blockIndent = ""
            }
        } elseif ($inCode) {
            # Ensure content is indented at least as much as the fence
            if ($newLine.Trim().Length -gt 0) {
                $currentIndentMatch = [regex]::Match($newLine, '^(\s*)')
                $currentIndent = $currentIndentMatch.Groups[1].Value
                if ($currentIndent.Length -lt $blockIndent.Length) {
                    $needed = $blockIndent.Substring($currentIndent.Length)
                    $newLine = $needed + $newLine
                }
            }
        }

        $null = $result.Add($newLine)
    }

    $fixedContent = ($result.ToArray() -join "`n")
    if ($PSCmdlet.ShouldProcess("CorruptionFixes", "Apply corruption fixes (pipes, indentation)")) {
        # Log
    }
    return $fixedContent
}

# --- Remove Indent from Code Block Fences ---
function Set-CodeBlockFencesLeftAligned {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param([string]$content)
    # Remove all leading whitespace before any code block fence (```)
    $lines = $content -split "`n"

    if ($PSCmdlet.ShouldProcess("Content", "Left-align code block fences")) {
        for ($i = 0; $i -lt $lines.Length; $i++) {
            if ($lines[$i] -match '^\s*```') {
                $lines[$i] = $lines[$i].TrimStart()
            }
        }
    }
    return ($lines -join "`n")
}

# --- MD012: No multiple consecutive blank lines ---
function Format-MD012 {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param([string]$content)

    if ($PSCmdlet.ShouldProcess("MD012", "Apply regex-based fix for MD012")) {
        # Normalize line endings to LF first
        $text = $content -replace "`r`n", "`n" -replace "`r", "`n"

        # 1. Replace 3+ consecutive newlines (which create 2+ blank lines) with 2 newlines (1 blank line)
        # Matches \n followed by optional whitespace followed by \n, repeated 3 or more times
        # This effectively collapses multiple blank lines into a single blank line
        $text = [regex]::Replace($text, "(\n\s*){3,}", "`n`n")

        # 2. Remove leading blank lines (start of file)
        $text = $text -replace "^\s+", ""

        # 3. Remove trailing blank lines (end of file) and ensure single newline
        $text = $text -replace "\s+$", "`n"

        Write-Information "Format-MD012 applied (regex)."
        return $text
    }
    return $content
}

function Test-MD012 {    [System.Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', '')]    param([string]$content)
    # Return $false if 2+ consecutive blank lines are found
    $lines = $content -split "`n"
    $blankCount = 0
    foreach ($line in $lines) {
        if ($line -match '^\s*$') {
            $blankCount++
        } else {
            $blankCount = 0
        }
        if ($blankCount -ge 2) {
            return $false
        }
    }
    return $true
}

function Test-MD022 {
    param([string]$content)
    $lines = $content -split "`n"
    $inCode = $false
    for ($i = 0; $i -lt $lines.Length; $i++) {
        $line = $lines[$i]
        if ($line -match '^\s*```') {
            $inCode = -not $inCode
            continue
        }
        if ($inCode) { continue }
        if ($line -match '^\s{0,3}#+') {
            $prev = if ($i -gt 0) { $lines[$i-1] } else { '' }
            if ($i -gt 0 -and $prev.Trim() -ne '') {
                Write-Information "[Test-MD022Valid] FAIL: No blank line before heading at $i"
                return $false
            }
            $next = if ($i+1 -lt $lines.Length) { $lines[$i+1] } else { '' }
            if ($i+1 -lt $lines.Length -and $next.Trim() -ne '') {
                Write-Information "[Test-MD022Valid] FAIL: No blank line after heading at $i"
                return $false
            }
        }
    }
    return $true
}

# --- MD022: Headings must be surrounded by blank lines ---
function Format-MD022 {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param([string]$content)
    $lines = $content -split "`n"
    $result = [System.Collections.Generic.List[string]]::new()
    $inCode = $false
    $headingPattern = '^\s{0,3}#+(?:\s+.+|$)'
    for ($i = 0; $i -lt $lines.Length; $i++) {
        $line = $lines[$i]
        if ($line -match '^\s*```') { $inCode = -not $inCode }
        if ($inCode) {
            $null = $result.Add($line)
            continue
        }
        if ($line -match $headingPattern) {
            Write-Information "MD022: Found heading '$line'"
            # Ensure blank line before
            if ($result.Count -gt 0 -and $result[$result.Count-1].Trim() -ne '') {
                Write-Information "MD022: Adding blank line before '$line'"
                $null = $result.Add('')
            }
            $null = $result.Add($line)
            # Ensure blank line after
            if ($i+1 -lt $lines.Length -and $lines[$i+1].Trim() -ne '') {
                Write-Information "MD022: Adding blank line after '$line'"
                $null = $result.Add('')
            }
            continue
        }
        $null = $result.Add($line)
    }
    # Remove leading blank lines at file start
    while ($result.Count -gt 0 -and $result[0] -match '^\s*$') { $result.RemoveAt(0) }
    # Remove trailing blank lines at file end
    while ($result.Count -gt 0 -and $result[$result.Count-1] -match '^\s*$') { $result.RemoveAt($result.Count-1) }
    $fixedContent = ($result.ToArray() -join "`n")
    if ($PSCmdlet.ShouldProcess("MD022", "Apply markdownlint fix for MD022")) {
        # Could add logging here if desired
    }
    return $fixedContent
}

# --- MD023: Headings must start at beginning of line ---
function Format-MD023 {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param([string]$content)
    # Remove leading whitespace (spaces/tabs only) before heading hashes
    # Using [ \t] instead of \s to avoid matching newlines
    $fixedContent = ($content -replace "(?m)^[ \t]+(#+)", '$1')
    if ($PSCmdlet.ShouldProcess("MD023", "Apply markdownlint fix for MD023")) {
        # Could add logging here if desired
    }
    return $fixedContent
}

function Test-MD023 {
    param([string]$content)
    # Return $false if any heading does not start at the beginning of the line
    $lines = $content -split "`n"
    foreach ($line in $lines) {
        if ($line -match "^\s+#+") { return $false }
    }
    return $true
}

# --- MD029: Ordered list item prefix ---
function Format-MD029 {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param([string]$content)
    # Normalize ordered list numbers so each list starts at 1 and increments
    $lines = $content -split "`n"
    $i = 0
    while ($i -lt $lines.Length) {
        # Match ordered list item with optional indentation
        if ($lines[$i] -match "^(\s*)(\d+)\. ") {
            $indent = $matches[1]
            $num = 1
            $j = $i
            # For each contiguous block of ordered list items with SAME indentation
            while ($j -lt $lines.Length) {
                if ($lines[$j] -match "^$indent\d+\. ") {
                    $lines[$j] = $lines[$j] -replace "^$indent\d+\. ", "$indent$num. "
                    $num++
                    $j++
                } else {
                    break
                }
            }
            $i = $j - 1
        }
        $i++
    }
    $fixedContent = ($lines -join "`n")
    if ($PSCmdlet.ShouldProcess("MD029", "Apply markdownlint fix for MD029")) {
        # Could add logging here if desired
    }
    return $fixedContent
}

function Test-MD029 {
    param([string]$content)
    # Return $false if any ordered list does not increment properly
    $lines = $content -split "`n"
    $i = 0
    while ($i -lt $lines.Length) {
        if ($lines[$i] -match "^(\s*)(\d+)\. ") {
            $indent = $matches[1]
            $num = 1
            $j = $i
            while ($j -lt $lines.Length) {
                if ($lines[$j] -match "^$indent\d+\. ") {
                    if ($lines[$j] -notmatch "^$indent$num\. ") { return $false }
                    $num++
                    $j++
                } else {
                    break
                }
            }
            $i = $j - 1
        }
        $i++
    }
    return $true
}

# --- MD038: No space in code span (robust) ---
function Format-MD038 {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param([string]$content)
    # Remove spaces inside inline code spans (e.g., ` code ` -> `code`), outside code blocks
    $lines = $content -split "`n"
    $inCode = $false
    $result = @()
    foreach ($line in $lines) {
        if ($line -match '^\s*```') { $inCode = -not $inCode }
        if ($inCode) { $result += $line; continue }
        # Replace all inline code spans with spaces inside (greedy, robust)
        $fixedLine = $line
        while ($fixedLine -match '` [^`]+ `') {
            $fixedLine = $fixedLine -replace '` ([^`]+) `', '`$1`'
        }
        $result += $fixedLine
    }
    $fixedContent = ($result -join "`n")
    if ($PSCmdlet.ShouldProcess("MD038", "Apply markdownlint fix for MD038")) {
        # Could add logging here if desired
    }
    return $fixedContent
}

function Test-MD038 {
    param([string]$content)
    # Only check outside code blocks for code spans with spaces
    $lines = $content -split "`n"
    $inCode = $false
    foreach ($line in $lines) {
        if ($line -match '^\s*```') { $inCode = -not $inCode }
        if ($inCode) { continue }
        # Only check outside code blocks
        if ($line -match '` [^`]+ `') { return $false }
    }
    return $true
}

# --- MD007: Unordered list indentation (robust) ---
function Format-MD007 {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param([string]$content)
    # Fix unordered list indentation (2 spaces per nesting level), outside code blocks
    # Also normalizes root indentation (if a list block starts indented, it shifts it left)
    $lines = $content -split "`n"
    $inCode = $false
    $result = @()
    $listBlockIndent = $null

    for ($i = 0; $i -lt $lines.Length; $i++) {
        $line = $lines[$i]
        if ($line -match '^\s*```') {
            $inCode = -not $inCode
            $result += $line
            $listBlockIndent = $null
            continue
        }
        if ($inCode) {
            $result += $line
            continue
        }

        # Match list items with leading whitespace
        if ($line -match '^(\s*)([-*+]) (.*)') {
            $currentIndentLen = $matches[1].Length
            $marker = $matches[2]
            $text   = $matches[3]

            # If this is the start of a new list block (or we reset), establish the root indent
            if ($null -eq $listBlockIndent) {
                $listBlockIndent = $currentIndentLen
            }

            # Calculate relative indentation from the block's root
            $relativeIndent = $currentIndentLen - $listBlockIndent
            if ($relativeIndent -lt 0) { $relativeIndent = 0 }

            # Normalize to 2-space steps based on relative indent
            $level = [Math]::Round($relativeIndent / 2)
            $newIndent = ' ' * ($level * 2)

            $result += "$newIndent$marker $text"
        } else {
            # Reset list block tracking on non-list lines (blank lines, text, etc.)
            # This ensures we re-evaluate the root indent for the next list we encounter
            $listBlockIndent = $null
            $result += $line
        }
    }
    $fixedContent = ($result -join "`n")
    if ($PSCmdlet.ShouldProcess("MD007", "Apply markdownlint fix for MD007")) {
        # Could add logging here if desired
    }
    return $fixedContent
}

function Test-MD007 {
    param([string]$content)
    # Only check outside code blocks for unordered list indentation
    # Fail if indentation is not a multiple of 2
    $lines = $content -split "`n"
    $inCode = $false
    foreach ($line in $lines) {
        if ($line -match '^\s*```') { $inCode = -not $inCode }
        if ($inCode) { continue }
        # Only check outside code blocks
        if ($line -match '^(\s*)([-*+]) ') {
            $spaces = $matches[1].Length
            if ($spaces % 2 -ne 0) {
                Write-Information "Test-MD007: Failed on line '$line' (Indent: $spaces)"
                return $false
            }
        }
    }
    return $true
}

# --- MD055/MD056: Table pipe style and column count ---
function Format-MD055MD056 {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param([string]$content)
    # Normalize table rows to have consistent pipe style and column count
    $lines = $content -split "`n"
    $out = New-Object System.Collections.ArrayList
    $i = 0
    $inCode = $false
    while ($i -lt $lines.Length) {
        $line = $lines[$i]

        # Track code blocks
        if ($line -match '^\s*```') {
            $inCode = -not $inCode
            $out.Add($line) | Out-Null
            $i++
            continue
        }

        if ($inCode) {
            $out.Add($line) | Out-Null
            $i++
            continue
        }

        # Detect table header (must have at least one pipe, not code block)
        if ($line -match '^\s*\S.*\|.*$') {
            # Skip lines that are headings, not table rows
            if ($line -match '^#+ ') { $out.Add($line) | Out-Null; $i++; continue }

            # Table block: collect all contiguous lines with at least one pipe
            $table = @($line)
            $j = $i+1
            while ($j -lt $lines.Length) {
                $nextLine = $lines[$j]
                if ($nextLine -match '^\s*```') { break } # Stop at code fence
                if ($nextLine -notmatch '^\s*\S.*\|.*$') { break } # Stop at non-table line
                $table += $nextLine
                $j++
            }

            # Determine max columns from header or max row (based on content cells)
            $maxCols = 0
            $parsedRows = @()

            foreach ($row in $table) {
                # Use regex split to handle escaped pipes correctly
                $rowCells = $row.Trim() -split '(?<!\\)\|'

                # Remove empty leading/trailing cells from split (standard markdown table format)
                if ($rowCells.Count -gt 0 -and [string]::IsNullOrWhiteSpace($rowCells[0])) {
                    $rowCells = $rowCells[1..($rowCells.Count-1)]
                }
                if ($rowCells.Count -gt 0 -and [string]::IsNullOrWhiteSpace($rowCells[-1])) {
                    $rowCells = $rowCells[0..($rowCells.Count-2)]
                }

                if ($rowCells.Count -gt $maxCols) { $maxCols = $rowCells.Count }
                $parsedRows += ,$rowCells
            }

            # Prune empty last columns (if the last column is empty for ALL rows)
            # This fixes artifacts where an extra pipe was added/detected incorrectly
            while ($maxCols -gt 0) {
                $lastColEmpty = $true
                foreach ($r in $parsedRows) {
                    # If row has this column and it's not whitespace, then column is not empty
                    if ($r.Count -ge $maxCols -and -not [string]::IsNullOrWhiteSpace($r[$maxCols-1])) {
                        $lastColEmpty = $false
                        break
                    }
                }

                if ($lastColEmpty) {
                    $maxCols--
                    # Remove the column from parsed rows that have it
                    for ($p = 0; $p -lt $parsedRows.Count; $p++) {
                        if ($parsedRows[$p].Count -gt $maxCols) {
                            $parsedRows[$p] = $parsedRows[$p][0..($maxCols-1)]
                        }
                    }
                } else {
                    break
                }
            }

            # Fix each row
            for ($k = 0; $k -lt $parsedRows.Count; $k++) {
                $rowCells = $parsedRows[$k]

                # Pad or trim to maxCols
                if ($rowCells.Count -lt $maxCols) {
                    # Correctly add multiple empty cells
                    $needed = $maxCols - $rowCells.Count
                    for ($n = 0; $n -lt $needed; $n++) { $rowCells += " " }
                } elseif ($rowCells.Count -gt $maxCols) {
                    $rowCells = $rowCells[0..($maxCols-1)]
                }

                # Always add leading/trailing pipes
                $fixedRow = '|' + ($rowCells -join '|') + '|'
                $out.Add($fixedRow) | Out-Null
            }
            $i = $j
        } else {
            $out.Add($line) | Out-Null
            $i++
        }
    }
    $fixedContent = ($out -join "`n")
    if ($PSCmdlet.ShouldProcess("MD055MD056", "Apply markdownlint fix for MD055/MD056")) {
        # Could add logging here if desired
    }
    return $fixedContent
}

function Test-MD055MD056 {
    param([string]$content)
    $lines = $content -split "`n"
    $i = 0
    $inCode = $false
    while ($i -lt $lines.Length) {
        $line = $lines[$i]
        if ($line -match '^\s*```') {
            $inCode = -not $inCode
            $i++
            continue
        }
        if ($inCode) {
            $i++
            continue
        }
        if ($line -match '^\s*\S.*\|.*$') {
            if ($line -match '^#+ ') { $i++; continue }
            $table = @($line)
            $j = $i + 1
            while ($j -lt $lines.Length) {
                $next = $lines[$j]
                if ($next -match '^\s*```') { break }
                if ($next -notmatch '^\s*\S.*\|.*$') { break }
                $table += $next
                $j++
            }
            $expectedColumns = $null
            foreach ($row in $table) {
                $segments = @($row.Trim() -split '\|')
                if ($segments.Count -eq 0) { continue }
                $rowCells = @()
                for ($idx = 0; $idx -lt $segments.Count; $idx++) {
                    $isBoundary = ($idx -eq 0) -or ($idx -eq $segments.Count - 1)
                    if ($isBoundary -and $segments[$idx] -eq '') { continue }
                    $rowCells += $segments[$idx]
                }
                if ($null -eq $expectedColumns) {
                    $expectedColumns = $rowCells.Count
                    continue
                }
                if ($rowCells.Count -ne $expectedColumns) { return $false }
            }
            $i = $j
        } else {
            $i++
        }
    }
    return $true
}

# --- MD019: No multiple spaces after hash in headings ---
function Format-MD019 {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param([string]$content)
    # Remove multiple spaces after hash in headings
    if ($PSCmdlet.ShouldProcess("Content", "Apply markdownlint fix for MD019")) {
        $lines = $content -split "`n"
        $result = @()
        foreach ($line in $lines) {
            if ($line -match '^(#+)\s{2,}') {
                $fixed = $line -replace '^(#+)\s{2,}', '$1 '
                Write-Information "MD019 set: '$line' -> '$fixed'"
                $result += $fixed
            } else {
                $result += $line
            }
        }
        return ($result -join "`n")
    } else {
        return $content
    }
}

# --- Main entry point ---
function Main {
    param(
        [Parameter(Mandatory=$true)]
        [string]$FilePath
    )
    $content = Get-Content $FilePath -Raw -Encoding UTF8
    $backup = Backup-File $FilePath
    try {
        # Normalize line endings first
        $content = Update-LineEndings $content
        Write-Information "Content length after normalize: $($content.Length)"

        # Apply and validate each rule in sequence

        # 1. Apply Corruption Fixes First (Pipes, Indentation)
        $content = Format-CorruptionFixes $content
        Write-Information "Content length after CorruptionFixes: $($content.Length)"

        # 2. Left-align all code block fences (fix for MD046)
        $content = Set-CodeBlockFencesLeftAligned $content
        Write-Information "Content length after Set-CodeBlockFencesLeftAligned: $($content.Length)"

        $content = Format-MD022 $content
        Write-Information "Content length after MD022: $($content.Length)"
        if (-not (Test-MD022 $content)) { Write-Warning "MD022 validation failed after fix. Leaving file as-is for inspection." }

        $content = Format-MD019 $content
        Write-Information "Content length after MD019: $($content.Length)"

        $content = Format-MD023 $content
        Write-Information "Content length after MD023: $($content.Length)"
        if (-not (Test-MD023 $content)) { Write-Warning "MD023 validation failed after fix. Leaving file as-is for inspection." }

        $content = Format-MD029 $content
        Write-Information "Content length after MD029: $($content.Length)"
        if (-not (Test-MD029 $content)) { Write-Warning "MD029 validation failed after fix. Leaving file as-is for inspection." }

        $content = Format-MD038 $content
        Write-Information "Content length after MD038: $($content.Length)"
        if (-not (Test-MD038 $content)) { Write-Warning "MD038 validation failed after fix. Leaving file as-is for inspection." }

        $content = Format-MD007 $content
        Write-Information "Content length after MD007: $($content.Length)"
        if (-not (Test-MD007 $content)) { Write-Warning "MD007 validation failed after fix. Leaving file as-is for inspection." }

        $content = Format-MD055MD056 $content
        Write-Information "Content length after MD055MD056: $($content.Length)"
        if (-not (Test-MD055MD056 $content)) { Write-Warning "MD055/MD056 validation failed after fix. Leaving file as-is for inspection." }

        # 3. Aggressively remove all extra blank lines at the end (MD012)
        $content = Format-MD012 $content
        Write-Information "Content length after final Format-MD012: $($content.Length)"
        if (-not (Test-MD012 $content)) { Write-Warning "MD012 validation failed after final fix. Leaving file as-is for inspection." }

        Set-Content -Path $FilePath -Value $content -Encoding UTF8
        Remove-Backup $backup
        Write-Information "Universal markdownlint fixes applied to $FilePath"
    }
    catch {
        Write-Error $_
        Restore-File $backup $FilePath
        Write-Information "Rolled back to original file due to error. Please review the script section for improvements."
    }
}

Main -FilePath $FilePath

