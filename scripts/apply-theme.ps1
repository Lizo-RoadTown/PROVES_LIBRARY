param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('spring', 'summer', 'fall', 'winter')]
    [string]$Theme = 'spring'
)

# Theme configurations
$themes = @{
    spring = @{
        primaryColor = '#E8F5E9'
        secondaryColor = '#FCE4EC'
        tertiaryColor = '#FFF9C4'
        primaryTextColor = '#2E7D32'
        secondaryTextColor = '#C2185B'
        tertiaryTextColor = '#F57F17'
        primaryBorderColor = '#66BB6A'
        secondaryBorderColor = '#F06292'
        tertiaryBorderColor = '#FDD835'
        lineColor = '#4CAF50'
        edgeLabelBackground = '#F1F8E9'
        nodeBorder = '#66BB6A'
        clusterBkg = '#FFF9C4'
        clusterBorder = '#FDD835'
        defaultLinkColor = '#4CAF50'
        titleColor = '#2E7D32'
        actorBkg = '#E8F5E9'
        actorBorder = '#66BB6A'
        actorTextColor = '#2E7D32'
        signalColor = '#4CAF50'
        labelBoxBkgColor = '#FCE4EC'
        stateBkg = '#E8F5E9'
        sectionBkgColor = '#FFF9C4'
        taskBorderColor = '#66BB6A'
        taskBkgColor = '#E8F5E9'
        activeTaskBkgColor = '#C8E6C9'
        gridColor = '#A5D6A7'
        doneTaskBkgColor = '#81C784'
        critBkgColor = '#F06292'
        todayLineColor = '#2E7D32'
    }
    summer = @{
        primaryColor = '#E1F5FE'
        secondaryColor = '#FFF9C4'
        tertiaryColor = '#FFE0B2'
        primaryTextColor = '#01579B'
        secondaryTextColor = '#F57F17'
        tertiaryTextColor = '#E65100'
        primaryBorderColor = '#29B6F6'
        secondaryBorderColor = '#FDD835'
        tertiaryBorderColor = '#FF9800'
        lineColor = '#0288D1'
        edgeLabelBackground = '#E1F5FE'
        nodeBorder = '#29B6F6'
        clusterBkg = '#FFE0B2'
        clusterBorder = '#FF9800'
        defaultLinkColor = '#0288D1'
        titleColor = '#01579B'
        actorBkg = '#E1F5FE'
        actorBorder = '#29B6F6'
        actorTextColor = '#01579B'
        signalColor = '#0288D1'
        labelBoxBkgColor = '#FFF9C4'
        stateBkg = '#E1F5FE'
        sectionBkgColor = '#FFE0B2'
        taskBorderColor = '#29B6F6'
        taskBkgColor = '#E1F5FE'
        activeTaskBkgColor = '#B3E5FC'
        gridColor = '#81D4FA'
        doneTaskBkgColor = '#4FC3F7'
        critBkgColor = '#FF9800'
        todayLineColor = '#01579B'
    }
    fall = @{
        primaryColor = '#FFF3E0'
        secondaryColor = '#F3E5F5'
        tertiaryColor = '#FFF8E1'
        primaryTextColor = '#E65100'
        secondaryTextColor = '#6A1B9A'
        tertiaryTextColor = '#F57F17'
        primaryBorderColor = '#FF9800'
        secondaryBorderColor = '#9C27B0'
        tertiaryBorderColor = '#FBC02D'
        lineColor = '#FF6F00'
        edgeLabelBackground = '#FFF3E0'
        nodeBorder = '#FF9800'
        clusterBkg = '#FFF8E1'
        clusterBorder = '#FBC02D'
        defaultLinkColor = '#FF6F00'
        titleColor = '#E65100'
        actorBkg = '#FFF3E0'
        actorBorder = '#FF9800'
        actorTextColor = '#E65100'
        signalColor = '#FF6F00'
        labelBoxBkgColor = '#F3E5F5'
        stateBkg = '#FFF3E0'
        sectionBkgColor = '#FFF8E1'
        taskBorderColor = '#FF9800'
        taskBkgColor = '#FFF3E0'
        activeTaskBkgColor = '#FFE0B2'
        gridColor = '#FFCC80'
        doneTaskBkgColor = '#FFB74D'
        critBkgColor = '#9C27B0'
        todayLineColor = '#E65100'
    }
    winter = @{
        primaryColor = '#E3F2FD'
        secondaryColor = '#ECEFF1'
        tertiaryColor = '#E1F5FE'
        primaryTextColor = '#01579B'
        secondaryTextColor = '#455A64'
        tertiaryTextColor = '#006064'
        primaryBorderColor = '#42A5F5'
        secondaryBorderColor = '#78909C'
        tertiaryBorderColor = '#26C6DA'
        lineColor = '#1976D2'
        edgeLabelBackground = '#E3F2FD'
        nodeBorder = '#42A5F5'
        clusterBkg = '#E1F5FE'
        clusterBorder = '#26C6DA'
        defaultLinkColor = '#1976D2'
        titleColor = '#01579B'
        actorBkg = '#E3F2FD'
        actorBorder = '#42A5F5'
        actorTextColor = '#01579B'
        signalColor = '#1976D2'
        labelBoxBkgColor = '#ECEFF1'
        stateBkg = '#E3F2FD'
        sectionBkgColor = '#E1F5FE'
        taskBorderColor = '#42A5F5'
        taskBkgColor = '#E3F2FD'
        activeTaskBkgColor = '#BBDEFB'
        gridColor = '#90CAF9'
        doneTaskBkgColor = '#64B5F6'
        critBkgColor = '#78909C'
        todayLineColor = '#01579B'
    }
}

$selectedTheme = $themes[$Theme]

Write-Host "Applying $Theme theme to all diagrams..." -ForegroundColor Cyan

# Get all diagram files except MERMAID_RULES.md and VALIDATION_REPORT.md
$diagramFiles = Get-ChildItem -Path "docs/diagrams/*.md" | Where-Object {
    $_.Name -ne "MERMAID_RULES.md" -and $_.Name -ne "VALIDATION_REPORT.md"
}

$updatedCount = 0

foreach ($file in $diagramFiles) {
    Write-Host "Processing $($file.Name)..." -ForegroundColor Gray

    $content = Get-Content $file.FullName -Raw -Encoding UTF8

    # Build the theme configuration block
    $themeConfig = @"
---
config:
  theme: base
  themeVariables:
    primaryColor: '$($selectedTheme.primaryColor)'
    secondaryColor: '$($selectedTheme.secondaryColor)'
    tertiaryColor: '$($selectedTheme.tertiaryColor)'
    primaryTextColor: '$($selectedTheme.primaryTextColor)'
    secondaryTextColor: '$($selectedTheme.secondaryTextColor)'
    tertiaryTextColor: '$($selectedTheme.tertiaryTextColor)'
    primaryBorderColor: '$($selectedTheme.primaryBorderColor)'
    secondaryBorderColor: '$($selectedTheme.secondaryBorderColor)'
    tertiaryBorderColor: '$($selectedTheme.tertiaryBorderColor)'
    lineColor: '$($selectedTheme.lineColor)'
    edgeLabelBackground: '$($selectedTheme.edgeLabelBackground)'
    nodeBorder: '$($selectedTheme.nodeBorder)'
    clusterBkg: '$($selectedTheme.clusterBkg)'
    clusterBorder: '$($selectedTheme.clusterBorder)'
    defaultLinkColor: '$($selectedTheme.defaultLinkColor)'
    titleColor: '$($selectedTheme.titleColor)'
    actorBkg: '$($selectedTheme.actorBkg)'
    actorBorder: '$($selectedTheme.actorBorder)'
    actorTextColor: '$($selectedTheme.actorTextColor)'
    signalColor: '$($selectedTheme.signalColor)'
    labelBoxBkgColor: '$($selectedTheme.labelBoxBkgColor)'
    stateBkg: '$($selectedTheme.stateBkg)'
    sectionBkgColor: '$($selectedTheme.sectionBkgColor)'
    taskBorderColor: '$($selectedTheme.taskBorderColor)'
    taskBkgColor: '$($selectedTheme.taskBkgColor)'
    activeTaskBkgColor: '$($selectedTheme.activeTaskBkgColor)'
    gridColor: '$($selectedTheme.gridColor)'
    doneTaskBkgColor: '$($selectedTheme.doneTaskBkgColor)'
    critBkgColor: '$($selectedTheme.critBkgColor)'
    todayLineColor: '$($selectedTheme.todayLineColor)'
  flowchart:
    curve: linear
---
"@

    # Replace existing frontmatter configs in mermaid blocks
    # Pattern matches: ```mermaid followed by optional --- config block ---
    $pattern = '```mermaid\r?\n(?:---\r?\n(?:(?!```)[\s\S])*?---\r?\n)?'
    $replacement = "``````mermaid`r`n$themeConfig`r`n"

    $newContent = $content -replace $pattern, $replacement

    if ($content -ne $newContent) {
        Set-Content -Path $file.FullName -Value $newContent -NoNewline -Encoding UTF8
        $updatedCount++
        Write-Host "  ✓ Updated" -ForegroundColor Green
    } else {
        Write-Host "  - No changes needed" -ForegroundColor Yellow
    }
}

Write-Host "`nTheme application complete!" -ForegroundColor Green
Write-Host "Updated $updatedCount of $($diagramFiles.Count) files with $Theme theme" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Review changes: git diff docs/diagrams/" -ForegroundColor Gray
Write-Host "2. Test diagrams: Open files in GitHub or Mermaid Live Editor" -ForegroundColor Gray
Write-Host "3. Commit changes: git add docs/diagrams/ && git commit -m 'Apply $Theme theme to all diagrams'" -ForegroundColor Gray
