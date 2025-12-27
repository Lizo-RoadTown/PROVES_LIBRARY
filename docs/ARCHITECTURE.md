# System Architecture

## Overview

The PROVES Library system consists of three main components that work together to create an automated knowledge capture and interrogation system.

## Components

### 1. Library (Knowledge Storage)

**Purpose:** Store knowledge entries as structured markdown files

**Location:** `/library/`

**Structure:**
```
library/
├── build/              # Assembly, hardware, testing knowledge
├── software/           # F Prime patterns, components, architecture
└── ops/                # Configurations, fixes, operational checklists
```

**Entry Schema:**
- YAML frontmatter with metadata
- Markdown body with detailed content
- Citations and source excerpts
- Artifact links (components, repos, docs, tests)

**Key Requirements:**
- All entries must have citations (no original knowledge claims)
- Artifact links must be verifiable
- No attribution to individuals (structure owns outcomes)
- Tags for searchability

**Curation Pipeline (Database):**
- Extractor writes candidates to `staging_extractions` with evidence + confidence
- Validator updates status and can request more evidence
- Storage promotes approved items into domain tables and core entities
- Schema is created by `scripts/setup_domain_tables.py`

### 2. MCP Server

**Purpose:** Make the library interrogatable through structured queries

**Location:** `/mcp-server/`

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#e3f2fd',
    'primaryTextColor': '#1a1a1a',
    'primaryBorderColor': '#1976d2',
    'secondaryColor': '#fff8e1',
    'secondaryBorderColor': '#f9a825',
    'tertiaryColor': '#f3e5f5',
    'tertiaryBorderColor': '#7b1fa2',
    'lineColor': '#546e7a',
    'textColor': '#1a1a1a',
    'fontFamily': 'system-ui, -apple-system, sans-serif',
    'fontSize': '14px'
  },
  'flowchart': {
    'curve': 'linear',
    'nodeSpacing': 40,
    'rankSpacing': 60,
    'padding': 15,
    'htmlLabels': true
  }
}}%%
flowchart TB
    subgraph Clients[MCP Clients]
        VSCode[VS Code Extension]
        Scanner[Risk Scanner]
        CLI[Command Line Tool]
        Builder[Builder Agent]
    end

    subgraph Server[MCP Server]
        MCP[FastMCP Tools]
        Registry[source_registry.yaml]
        Cache[Response Cache]
    end

    subgraph Storage[Data Layer]
        Graph[(Neon PostgreSQL + pgvector)]
        Library[(Library entries)]
    end

    VSCode -->|search, fetch| MCP
    Scanner -->|search, evidence| MCP
    CLI -->|list, fetch| MCP
    Builder -->|search patterns| MCP

    MCP --> Graph
    MCP --> Registry
    MCP --> Cache
    Graph --> Library

    style MCP fill:#4D96FF
    style Graph fill:#6BCB77
    style Library fill:#FFD93D
```

**Key Endpoints:**
- `search(query, filters)` - Semantic and keyword search
- `fetch(entry_id)` - Retrieve specific entry with full metadata
- `list(domain, tags)` - List entries by category
- `get_artifacts(entry_id)` - Fetch related artifacts

**Technology:**
- FastMCP server (Python)
- Neon PostgreSQL + pgvector
- `source_registry.yaml` for pre-mapped lookups
- MCP protocol implementation

**Why MCP?**
- Vendor-neutral protocol
- Works with any AI tool that supports MCP
- Structured queries vs dumping docs into context windows
- Creates "memory" for AI interactions

### 3. Risk Scanner

**Purpose:** Detect mission-critical risks in repos and capture knowledge

**Location:** `/risk-scanner/`

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#e3f2fd',
    'primaryTextColor': '#1a1a1a',
    'primaryBorderColor': '#1976d2',
    'secondaryColor': '#fff8e1',
    'secondaryBorderColor': '#f9a825',
    'tertiaryColor': '#f3e5f5',
    'tertiaryBorderColor': '#7b1fa2',
    'lineColor': '#546e7a',
    'textColor': '#1a1a1a',
    'fontFamily': 'system-ui, -apple-system, sans-serif',
    'fontSize': '14px'
  },
  'flowchart': {
    'curve': 'linear',
    'nodeSpacing': 40,
    'rankSpacing': 60,
    'padding': 15,
    'htmlLabels': true
  }
}}%%
flowchart TB
    subgraph Input[Scan Input]
        Repo[Repository Code]
        Config[Config Files]
        Tests[Test Files]
    end

    subgraph Scanner[Risk Scanner Engine]
        AST[AST Parser]
        ConfigAnalyzer[Config Analyzer]
        DepCheck[Dependency Checker]
        PatternMatcher[Pattern Matcher]
    end

    subgraph Patterns[Risk Patterns]
        Power[Power Patterns]
        Radio[Radio Patterns]
        Memory[Memory Patterns]
        Integration[Integration Patterns]
    end

    subgraph Output[Scan Output]
        Report[Risk Report]
        Alerts[Team Alerts]
        Capture[Knowledge Capture]
    end

    Repo --> AST
    Config --> ConfigAnalyzer
    Tests --> DepCheck

    AST --> PatternMatcher
    ConfigAnalyzer --> PatternMatcher
    DepCheck --> PatternMatcher

    Power --> PatternMatcher
    Radio --> PatternMatcher
    Memory --> PatternMatcher
    Integration --> PatternMatcher

    PatternMatcher --> Report
    Report --> Alerts
    Alerts -.Team Response.-> Capture

    style PatternMatcher fill:#FFD93D
    style Report fill:#FF6B6B
    style Capture fill:#6BCB77
```

**Workflow:**
1. Scan repository for known risk patterns
2. **PUSH:** Alert team with risk details + links to fixes
3. **PULL:** Capture team's context and resolution approach
4. Submit raw capture for review
5. Add approved entry to library

**Pattern Matching:**
- AST parsing for code patterns
- Config file analysis
- Dependency checking
- Test coverage analysis

**Risk Categories:**
- Power system issues
- Radio/communication timing
- I2C conflicts
- Memory management
- Component integration

**Output Format:**
```json
{
  "risk_id": "unique-id",
  "severity": "critical | high | medium | low",
  "category": "power | radio | memory | integration",
  "file_path": "/path/to/file",
  "line_number": 123,
  "pattern_matched": "pattern-name",
  "description": "What the risk is",
  "fix_link": "library/entry/id",
  "suggested_resolution": "How to fix it"
}
```

## Data Flow

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#e3f2fd',
    'primaryTextColor': '#1a1a1a',
    'primaryBorderColor': '#1976d2',
    'secondaryColor': '#fff8e1',
    'secondaryBorderColor': '#f9a825',
    'tertiaryColor': '#f3e5f5',
    'tertiaryBorderColor': '#7b1fa2',
    'lineColor': '#546e7a',
    'textColor': '#1a1a1a',
    'fontFamily': 'system-ui, -apple-system, sans-serif',
    'fontSize': '14px'
  },
  'flowchart': {
    'curve': 'linear',
    'nodeSpacing': 40,
    'rankSpacing': 60,
    'padding': 15,
    'htmlLabels': true
  }
}}%%
flowchart LR
    Team[University Team] --> Scanner[Risk Scanner]
    Scanner -->|PUSH: Alert| Team
    Team -->|PULL: Context| Scanner
    Scanner -->|Raw Capture| Library[Library Storage]
    Library -->|Index| MCP[MCP Server]
    MCP -->|Query Results| IDE[VS Code Extension]
    IDE --> Team
```

## Push/Pull Mechanism

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'actorBkg': '#e3f2fd',
    'actorBorder': '#1976d2',
    'actorTextColor': '#1a1a1a',
    'signalColor': '#546e7a',
    'signalTextColor': '#1a1a1a',
    'labelBoxBkgColor': '#fff8e1',
    'labelBoxBorderColor': '#f9a825',
    'loopTextColor': '#1a1a1a',
    'noteBkgColor': '#f3e5f5',
    'noteBorderColor': '#7b1fa2',
    'fontFamily': 'system-ui, -apple-system, sans-serif',
    'fontSize': '14px'
  },
  'sequence': {
    'mirrorActors': false,
    'messageAlign': 'center'
  }
}}%%
sequenceDiagram
    participant Team as University Team
    participant Repo as Team Repository
    participant Scanner as Risk Scanner
    participant MCP as MCP Server
    participant Library as Library Storage

    Note over Repo,Scanner: PUSH Phase - Value to Team
    Repo->>Scanner: Trigger scan (CI/manual)
    Scanner->>Scanner: Analyze code patterns
    Scanner->>MCP: Query: "Known fixes for I2C conflict?"
    MCP->>Scanner: Return: software-001 entry
    Scanner->>Team: ALERT: Risk detected + Fix link

    Note over Team,Scanner: PULL Phase - Value to Library
    Team->>Team: Review risk, implement fix
    Scanner->>Team: PROMPT: "How did you resolve it?"
    Team->>Scanner: CONTEXT: "Used TCA9548A, 2 weeks to CDR..."
    Scanner->>Library: Submit raw capture with context
    Library->>MCP: Re-index with new entry
    MCP-->>Scanner: Updated knowledge available

    Note over Team,Library: Mutual Value Exchange
```

### PUSH (Scanner → Team)
- Scanner detects risk
- Looks up fix in library via MCP
- Presents risk + fix link to team
- **Value to team:** Immediate risk mitigation

### PULL (Team → Scanner)
- Team provides context about their specific case
- Team describes how they resolved it (if different from suggestion)
- Scanner captures this as "raw lesson"
- **Value to library:** Enriched knowledge with real-world context

## Future: Agentic Systems

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#e3f2fd',
    'primaryTextColor': '#1a1a1a',
    'primaryBorderColor': '#1976d2',
    'secondaryColor': '#fff8e1',
    'secondaryBorderColor': '#f9a825',
    'tertiaryColor': '#f3e5f5',
    'tertiaryBorderColor': '#7b1fa2',
    'lineColor': '#546e7a',
    'textColor': '#1a1a1a',
    'fontFamily': 'system-ui, -apple-system, sans-serif',
    'fontSize': '14px'
  },
  'flowchart': {
    'curve': 'linear',
    'nodeSpacing': 40,
    'rankSpacing': 60,
    'padding': 15,
    'htmlLabels': true
  }
}}%%
flowchart TB
    subgraph Phase4[Phase 4 - Agentic Automation]
        Curator[Curator Agent<br/>LLM-powered normalization]
        Builder[Builder Agent<br/>Code generation]
    end

    subgraph Core[Core System]
        Scanner[Risk Scanner]
        Library[(Library Storage)]
        MCP[MCP Server]
    end

    subgraph Human[Human Oversight]
        Reviewer[Human Reviewer]
        Team[University Team]
    end

    Scanner -->|Raw Capture| Curator
    Curator -->|Extract citations| Curator
    Curator -->|Suggest tags| Curator
    Curator -->|Check duplicates| Curator
    Curator -->|Normalized Entry| Reviewer
    Reviewer -->|Approve/Reject| Library
    Reviewer -.Feedback.-> Curator

    MCP -->|Query patterns| Builder
    Team -->|Request component| Builder
    Builder -->|Generate FPP/C++| Builder
    Builder -->|Generate tests| Builder
    Builder -->|Validate code| Builder
    Builder -->|Generated code| Reviewer
    Reviewer -->|Approve| Team

    Library -->|Index| MCP

    style Curator fill:#E8AA42
    style Builder fill:#E8AA42
    style Reviewer fill:#95E1D3
    style Library fill:#6BCB77
```

### Curator Agent (Phase 4)
- Normalizes raw captures into entry format
- Maintains citation integrity
- Suggests tags and categorization
- Flags duplicate or conflicting entries

### Builder Agent (Phase 4)
- Generates F Prime components from patterns
- Creates test scaffolds
- Produces configuration templates
- Builds integration examples

## Security & Privacy

- No personal attribution in entries
- Citations are to public sources only
- No proprietary code or data
- Structure owns outcomes, not individuals

## Scalability

- Library grows through community contributions
- MCP server can be replicated/distributed
- Scanner can run locally or in CI/CD
- Embeddings can be pre-computed and cached
