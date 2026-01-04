
[CmdletBinding()]
[System.Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidUsingWriteHost', '')]
param()

$file = "docs/architecture/AGENTIC_ARCHITECTURE.md"
$content = Get-Content $file -Raw -Encoding UTF8

# Define the new flowchart content
$newDiagram = @"
flowchart TB
    START(( )) --> Router

    Router -->|"Why brownouts?"| CascadeAnalyzer
    CascadeAnalyzer -->|Find power paths| GraphQuery
    GraphQuery -->|Extract evidence| EvidenceTracer
    EvidenceTracer -->|Get mitigation docs| VectorSearch
    VectorSearch -->|Combine results| Synthesizer
    Synthesizer -->|Return answer| END(( ))

    %% Notes represented as subgraphs or just side nodes connected with dotted lines
    %% Note right of CascadeAnalyzer
    NOTE_CA[/"Query graph for:<br/>RadioTX -> Power cascade paths"\]
    CascadeAnalyzer -.- NOTE_CA
    style NOTE_CA fill:#fff9c4,stroke:#fbc02d

    %% Note right of EvidenceTracer
    NOTE_ET[/"Trace evidence for:<br/>- Unknown edges<br/>- Assumed relationships"\]
    EvidenceTracer -.- NOTE_ET
    style NOTE_ET fill:#fff9c4,stroke:#fbc02d

    %% Note right of Synthesizer
    NOTE_SYN[/"Generate answer with:<br/>- Cascade diagram<br/>- Root cause analysis<br/>- Recommended fixes<br/>- Confidence score"\]
    Synthesizer -.- NOTE_SYN
    style NOTE_SYN fill:#fff9c4,stroke:#fbc02d
"@

# We need to find the block.
$pattern = "(?ms)```mermaid\s*stateDiagram-v2.*?(```)"

if ($content -match $pattern) {
    $replacement = '```mermaid' + "`r`n" + $newDiagram + "`r`n" + '```'
    $content = $content -replace $pattern, $replacement
    Write-Host "Converted stateDiagram-v2 to flowchart in AGENTIC_ARCHITECTURE.md"
} else {
    Write-Warning "Could not find stateDiagram-v2 block in AGENTIC_ARCHITECTURE.md"
}

Set-Content -Path $file -Value $content -Encoding UTF8
Write-Host "Done."
