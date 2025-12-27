# Implementation Tasks

This document breaks down the work needed to build the PROVES Library system.

## Implementation Phases Overview

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
    P1[Phase 1<br/>Foundation]
    P2[Phase 2<br/>Core Functionality]
    P3[Phase 3<br/>Integration]
    P4[Phase 4<br/>Agentic Systems]

    P1 -->|Complete| P2
    P2 -->|MCP + Scanner Ready| P3
    P3 -->|Production System| P4

    style P1 fill:#6BCB77
    style P2 fill:#FFD93D
    style P3 fill:#4D96FF
    style P4 fill:#E8AA42
```

## Phase Dependencies

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
    subgraph Phase1[Phase 1 - Foundation]
        P1A[Library Structure]
        P1B[Documentation]
        P1C[Entry Schema]
    end

    subgraph Phase2[Phase 2 - Core]
        P2A[MCP Server]
        P2B[Risk Scanner]
        P2C[Library Indexing]
    end

    subgraph Phase3[Phase 3 - Integration]
        P3A[VS Code Extension]
        P3B[Push/Pull Workflow]
        P3C[Review Process]
    end

    subgraph Phase4[Phase 4 - Agents]
        P4A[Curator Agent]
        P4B[Builder Agent]
    end

    P1A --> P1C
    P1C --> P2A
    P1C --> P2B
    P1A --> P2C

    P2A --> P3A
    P2B --> P3B
    P2A --> P3B
    P2C --> P2A

    P3A --> P4A
    P3B --> P4A
    P2A --> P4B
    P2C --> P4B

    style P1A fill:#90EE90
    style P1B fill:#90EE90
    style P1C fill:#90EE90
```

## Phase 1: Foundation ✓

### Library Structure
- [x] Create directory structure
- [ ] Define entry schema (YAML frontmatter spec)
- [ ] Create example entries for each domain
- [ ] Document citation requirements
- [ ] Create entry validation script

### Documentation
- [x] README with project overview
- [x] Architecture documentation
- [ ] Contributing guidelines
- [ ] Entry submission process
- [ ] Code of conduct

## Phase 2: Core Functionality

### MCP Server

**Goal:** Make library interrogatable through MCP protocol

**Tasks:**
1. [ ] Set up Python project structure
   - [ ] FastAPI application
   - [ ] Requirements.txt with dependencies
   - [ ] Config management

2. [ ] Implement library indexer
   - [ ] Parse markdown files with frontmatter
   - [ ] Extract metadata to SQLite
   - [ ] Build full-text search index
   - [ ] Generate embeddings for semantic search

3. [ ] Implement MCP endpoints
   - [ ] `search` - Query library with filters
   - [ ] `fetch` - Get specific entry
   - [ ] `list` - Browse by category/tags
   - [ ] `get_artifacts` - Retrieve linked artifacts

4. [ ] Add caching layer
   - [ ] Cache search results
   - [ ] Cache embeddings
   - [ ] Invalidate on library updates

**Dependencies:**
- FastAPI
- Pydantic (data validation)
- SQLite3
- sentence-transformers (embeddings)
- PyYAML (frontmatter parsing)

**Estimated Effort:** 2-3 weeks

### Risk Scanner

**Goal:** Detect risks and capture knowledge through push/pull loop

**Tasks:**
1. [ ] Set up Python project structure
   - [ ] CLI interface
   - [ ] Requirements.txt
   - [ ] Pattern storage format

2. [ ] Implement pattern matching engine
   - [ ] AST parser for Python code
   - [ ] Config file analyzer (YAML, JSON, TOML)
   - [ ] Dependency checker
   - [ ] Test coverage analyzer

3. [ ] Create initial risk patterns
   - [ ] Power system patterns (I2C conflicts, voltage issues)
   - [ ] Radio timing patterns
   - [ ] Memory management patterns
   - [ ] Component integration patterns

4. [ ] Implement push mechanism
   - [ ] Generate risk report with severity
   - [ ] Link to library fixes via MCP query
   - [ ] Format user-friendly output

5. [ ] Implement pull mechanism
   - [ ] Capture user context (CLI prompts)
   - [ ] Capture resolution approach
   - [ ] Generate raw entry draft
   - [ ] Submit for review

**Dependencies:**
- ast (Python standard library)
- PyYAML
- MCP client library
- Rich (CLI formatting)

**Estimated Effort:** 3-4 weeks

## Phase 3: Integration

### VS Code Extension

**Goal:** Provide IDE integration for library queries and risk scans

**Tasks:**
1. [ ] Set up TypeScript project
   - [ ] Extension manifest
   - [ ] MCP client integration
   - [ ] UI components

2. [ ] Implement core features
   - [ ] Search library command palette
   - [ ] Inline risk warnings
   - [ ] Fix suggestion hover
   - [ ] Submit lesson command

3. [ ] Add UX polish
   - [ ] Keyboard shortcuts
   - [ ] Status bar integration
   - [ ] Settings panel

**Dependencies:**
- VS Code Extension API
- MCP client (TypeScript)

**Estimated Effort:** 2-3 weeks

### Workflow Integration

**Tasks:**
1. [ ] Daily scan workflow
   - [ ] CLI command: `proves-scan --daily`
   - [ ] Output format for CI/CD
   - [ ] GitHub Actions example

2. [ ] Review process
   - [ ] Submission queue (GitHub Issues?)
   - [ ] Review checklist
   - [ ] Approval workflow

3. [ ] Library update automation
   - [ ] Auto-rebuild MCP index on merge
   - [ ] Embedding regeneration
   - [ ] Cache invalidation

**Estimated Effort:** 1-2 weeks

## Phase 4: Agentic Systems (Future)

### Curator Agent

**Goal:** Automate entry normalization and quality control

**Tasks:**
1. [ ] Design agent architecture
   - [ ] LLM selection (Claude, GPT-4, local)
   - [ ] Prompt engineering for normalization
   - [ ] Quality scoring system

2. [ ] Implement core functions
   - [ ] Parse raw captures
   - [ ] Extract citations
   - [ ] Generate frontmatter
   - [ ] Suggest tags
   - [ ] Detect duplicates

3. [ ] Human-in-the-loop review
   - [ ] Present normalized entry for approval
   - [ ] Track feedback for prompt refinement
   - [ ] Learn from rejections

**Estimated Effort:** 4-6 weeks

### Builder Agent

**Goal:** Generate code/components from library patterns

**Tasks:**
1. [ ] Design generation pipeline
   - [ ] Pattern → Component mapping
   - [ ] Template system
   - [ ] Validation/testing

2. [ ] Implement generators
   - [ ] F Prime component generator
   - [ ] Test scaffold generator
   - [ ] Config template generator

3. [ ] Integration with scanner
   - [ ] Suggest generated fixes
   - [ ] Auto-apply with approval
   - [ ] Track success rate

**Estimated Effort:** 6-8 weeks

## Immediate Next Steps

1. **Define entry schema** (docs/ENTRY_SCHEMA.md)
2. **Create 3-5 example entries** (one per domain)
3. **Set up MCP server skeleton**
4. **Set up risk scanner skeleton**
5. **Write contributing guidelines**

## Success Metrics

- Library growth rate (entries per month)
- Risk detection accuracy
- Fix adoption rate
- User engagement (scans run, queries made)
- Cross-university participation
