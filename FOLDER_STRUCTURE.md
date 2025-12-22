# PROVES Library - Folder Structure & Organization Best Practices

**Last Updated:** December 22, 2025
**Purpose:** Maintain clean, organized repository structure as the project evolves

---

## Repository Structure

```
PROVES_LIBRARY/
├── curator-agent/              # PRIMARY: Deep Agent system (LangGraph)
│   ├── src/curator/            # Agent implementation
│   │   ├── agent.py            # Main coordinator + HITL
│   │   └── subagents/          # Extractor, Validator, Storage
│   ├── run_with_approval.py    # CLI entry point
│   └── langgraph.json          # Deployment config
├── scripts/                    # Infrastructure utilities
│   ├── apply_schema.py         # Initialize knowledge graph schema
│   ├── setup_checkpointer.py   # Create LangGraph checkpoint tables
│   ├── db_connector.py         # PostgreSQL connection pooling
│   └── graph_manager.py        # Knowledge graph CRUD
├── docs/                       # Technical documentation
│   ├── ROADMAP.md              # Implementation roadmap
│   ├── AGENT_HANDOFF.md        # AI agent onboarding context
│   └── *.md                    # Architecture, schema docs
├── notebooks/                  # Jupyter notebooks
│   ├── 01_setup_and_explore.ipynb
│   └── 02_training_local_llm.ipynb
├── library/                    # Knowledge base entries
├── trial_docs/                 # Manual analysis results
├── tests/                      # Test suite (to be populated)
├── archive/                    # Superseded code and documentation
│   ├── legacy-agents/          # Old agent implementations
│   ├── curator-agent-old/      # Old curator scripts and docs
│   ├── design-docs/            # Unimplemented designs
│   ├── historical/             # Point-in-time logs
│   ├── old-configs/            # Deprecated configurations
│   └── outdated-docs/          # Superseded documentation
├── .env.example                # Environment template
├── requirements.txt            # Python dependencies (root)
├── README.md                   # Project overview (START HERE)
├── GETTING_STARTED.md          # Setup and onboarding
└── FOLDER_STRUCTURE.md         # This file
```

## What Goes Where?

### Root Level (Minimal - User Essentials Only)

**✅ KEEP IN ROOT:**
- `README.md` - Project overview (first thing users see)
- `GETTING_STARTED.md` - Quick start guide
- `FOLDER_STRUCTURE.md` - Organization guide
- `LICENSE` - License file (if you add one)
- `CONTRIBUTING.md` - Contribution guidelines (if you add one)
- `.env.example` - Environment template
- `requirements.txt` - Python dependencies
- `.gitignore`, `.gitattributes` - Git configuration

**❌ DON'T PUT IN ROOT:**
- Technical documentation → goes in `docs/`
- Historical logs → goes in `archive/historical/`
- Design documents → goes in `docs/` or `archive/design-docs/`
- Status updates → goes in `archive/historical/`
- Implementation plans → goes in `docs/`

**Rule of thumb:** If it's not something a new user needs immediately, it doesn't belong in root.

### docs/ (All Technical Documentation)

**✅ GOES IN docs/:**
- Architecture documents
- Integration guides (LangSmith, MCP, etc.)
- Database schema documentation
- Implementation roadmaps
- Agent onboarding docs
- Setup guides for specific features
- Design decision records

**Examples:**
- `docs/ROADMAP.md` - Implementation roadmap
- `docs/AGENT_HANDOFF.md` - AI agent context
- `docs/ARCHITECTURE.md` - System architecture
- `docs/KNOWLEDGE_GRAPH_SCHEMA.md` - Database schema

### archive/ (Historical & Superseded)

**archive/legacy-agents/** - Old implementations
- Superseded agent code
- Old standalone scripts

**archive/design-docs/** - Unimplemented designs
- MCP server design (not built)
- Risk scanner design (not built)

**archive/historical/** - Point-in-time records
- Setup logs from specific dates
- Status snapshots
- One-time event logs

**archive/old-configs/** - Deprecated configurations
- Old .env templates with outdated tech stack

---

## Directory Guidelines

### 1. curator-agent/ - Deep Agent System (PRIMARY)

**Purpose:** LangGraph-based Deep Agent system for automated dependency extraction

**Status:** ✅ Active Development

**Structure:**
```
curator-agent/
├── langgraph.json              # LangGraph deployment configuration
├── pyproject.toml              # Python package definition (uv/pip)
├── README.md                   # Deep Agent documentation
├── test_agent.py               # Test script
├── uv.lock                     # Dependency lock file
└── src/curator/
    ├── agent.py                # Main coordinator agent
    └── subagents/
        ├── extractor.py        # Extraction sub-agent
        ├── validator.py        # Validation sub-agent
        └── storage.py          # Storage sub-agent
```

**Best Practices:**
- This is the **main agent implementation** - all agent work goes here
- Follow LangGraph patterns (main agent + sub-agents as tools)
- Use Claude Sonnet 4.5 for consistency
- Keep comprehensive README with architecture diagrams
- Test scripts go in the root of curator-agent/

**When to Add Files Here:**
- New sub-agents
- Agent configuration changes
- Agent-specific tests
- LangGraph deployment configs

---

### 2. scripts/ - Infrastructure & Utilities

**Purpose:** Database management, documentation sync, and standalone utilities

**Status:** ✅ Active (infrastructure layer)

**Current Contents:**

**Database Layer (Keep):**
- `db_connector.py` - Database connection pooling for Neon PostgreSQL
- `graph_manager.py` - Knowledge graph CRUD operations
- `apply_schema.py` - Database initialization and schema application

**Documentation Sync (Keep):**
- `doc_sync_manager.py` - Documentation synchronization framework
- `github_doc_sync.py` - GitHub API documentation fetcher
- `library_indexer.py` - Markdown parser with YAML frontmatter

**Legacy Extraction (Review):**
- `dependency_extractor.py` - OpenAI-based extraction (consider migrating to Claude)

**Best Practices:**
- Only infrastructure and cross-cutting utilities go here
- No agent implementations (use curator-agent/ instead)
- Each script should be standalone and runnable
- Document usage in docstrings and README
- Prefer small, focused scripts over monoliths

**When to Add Files Here:**
- Database utilities
- Documentation sync tools
- Data migration scripts
- Schema management
- Indexing and search utilities

**When NOT to add files here:**
- Agent implementations → curator-agent/
- Documentation → docs/
- Tests → tests/

---

### 3. docs/ - Technical Documentation

**Purpose:** Architecture, design decisions, integration guides

**Status:** ✅ Active (requires updates)

**Current Contents:**
- `KNOWLEDGE_GRAPH_SCHEMA.md` - Database schema (Neon PostgreSQL + ERV)
- `LANGSMITH_INTEGRATION.md` - LangSmith tracing setup
- `ARCHITECTURE.md` - System architecture (needs update)
- `AGENTIC_ARCHITECTURE.md` - Agent architecture (needs update)

**Best Practices:**
- One file per major topic
- Keep docs synchronized with implementation
- Include diagrams where helpful (Mermaid, ASCII art)
- Link to relevant code with file paths
- Update docs when architecture changes

**Document Types:**
- **Architecture:** System design, component interaction
- **Integration:** Third-party service setup (LangSmith, Neon, etc.)
- **Schema:** Database structure, ERV ontology
- **Workflows:** Step-by-step process documentation

**When to Add Files Here:**
- New architectural patterns
- Integration guides for external services
- Design decision records (ADRs)
- Workflow documentation

**Naming Convention:**
- `UPPERCASE_WITH_UNDERSCORES.md` for major docs
- `lowercase-with-hyphens.md` for specific topics

---

### 4. library/ - Knowledge Base Entries

**Purpose:** Curated dependency knowledge organized by domain

**Status:** ⚠️ Minimal (only 1 example file)

**Planned Structure:**
```
library/
├── software/
│   ├── example-i2c-conflict.md
│   └── [more software components]
├── hardware/
│   └── [hardware components]
└── patterns/
    └── [design patterns]
```

**Entry Format (YAML Frontmatter + Markdown):**
```markdown
---
title: Component Name
type: software|hardware|pattern
tags: [tag1, tag2]
dependencies:
  - name: Dependency Name
    relationship: depends_on|requires|enables|conflicts_with|mitigates|causes
    criticality: HIGH|MEDIUM|LOW
---

# Component Name

## Description
...

## Dependencies
...
```

**Best Practices:**
- Use YAML frontmatter for structured metadata
- Organize by type: software/, hardware/, patterns/
- Follow ERV relationship types
- Include examples and context
- Cross-link related entries

**When to Add Files Here:**
- New component knowledge entries
- Manually curated dependencies
- Expert analysis results
- Pattern documentation

---

### 5. trial_docs/ - Manual Analysis & Trial Results

**Purpose:** Manual dependency mappings, trial extractions, research results

**Status:** ✅ Active (reference data)

**Current Contents:**
- `COMPREHENSIVE_DEPENDENCY_MAP.md` - Manual analysis of F' I2C driver
- Trial extraction results
- Manual mappings for validation

**Best Practices:**
- Keep manual analysis separate from automated extraction
- Use as ground truth for validation
- Document methodology used
- Include timestamps and context

**When to Add Files Here:**
- Manual dependency analysis
- Trial run results
- Validation datasets
- Research findings

---

### 6. notebooks/ - Jupyter Notebooks

**Purpose:** Exploratory data analysis, experimentation, prototyping

**Status:** ⚠️ Minimal (1 notebook)

**Best Practices:**
- Use for exploration, not production code
- Clear naming: `YYYY-MM-DD-descriptive-name.ipynb`
- Document purpose at top of notebook
- Extract production code to scripts/ or curator-agent/

**When to Add Files Here:**
- Data exploration
- Algorithm prototyping
- Visualization experiments
- One-off analysis

---

### 7. tests/ - Test Suite

**Purpose:** Unit, integration, and end-to-end tests

**Status:** ❌ Empty (needs implementation)

**Planned Structure:**
```
tests/
├── unit/
│   ├── test_graph_manager.py
│   ├── test_db_connector.py
│   └── curator_agent/
│       ├── test_extractor.py
│       ├── test_validator.py
│       └── test_storage.py
├── integration/
│   ├── test_database_operations.py
│   └── test_agent_workflow.py
└── e2e/
    └── test_full_extraction_pipeline.py
```

**Best Practices:**
- Mirror source structure in tests/
- Use pytest conventions
- Include fixtures in conftest.py
- Mock external services (LangSmith, database)
- Test both happy and error paths

**When to Add Files Here:**
- Unit tests for new modules
- Integration tests for workflows
- End-to-end tests for full pipelines
- Test fixtures and utilities

---

### 8. archive/ - Superseded & Outdated

**Purpose:** Preserve historical context without cluttering active codebase

**Status:** ✅ Active archive

**Structure:**
```
archive/
├── legacy-agents/          # Old agent implementations
│   ├── agents/             # Original agents/ directory
│   └── curator_agent.py    # Standalone curator (pre-LangGraph)
├── design-docs/            # Unimplemented designs
│   ├── mcp-server/         # MCP server design
│   └── risk-scanner/       # Risk scanner design
├── outdated-docs/          # Superseded documentation
└── old-configs/            # Deprecated configurations
    └── .env.template       # Old Neo4j template
```

**Best Practices:**
- Archive, don't delete (preserves history)
- Include README.md explaining why archived
- Organize by reason (legacy code, outdated docs, etc.)
- Reference current replacement in archive README

**When to Add Files Here:**
- Superseded implementations
- Outdated documentation
- Deprecated configurations
- Unimplemented design docs (for reference)

**See:** [archive/README.md](archive/README.md)

---

## File Naming Conventions

### Documentation
- **Major docs:** `UPPERCASE_WITH_UNDERSCORES.md` (e.g., `README.md`, `GETTING_STARTED.md`)
- **Specific topics:** `lowercase-with-hyphens.md` (e.g., `api-integration.md`)
- **Archive READMEs:** Always `README.md` in each directory

### Python Code
- **Modules:** `lowercase_with_underscores.py` (PEP 8)
- **Classes:** `PascalCase` (e.g., `GraphManager`, `DependencyExtractor`)
- **Functions:** `lowercase_with_underscores` (e.g., `get_node_by_name`)

### Notebooks
- **Format:** `YYYY-MM-DD-descriptive-name.ipynb`
- **Example:** `2024-12-21-dependency-analysis.ipynb`

### Tests
- **Pattern:** `test_<module_name>.py`
- **Example:** `test_graph_manager.py`

### Configuration
- **Active:** `.env.example` (template for users)
- **Actual:** `.env` (not in git, local secrets)
- **Lock files:** `<package-manager>.lock` (e.g., `uv.lock`, `package-lock.json`)

---

## Configuration Management

### Current Stack
- **Database:** Neon PostgreSQL (cloud) + pgvector
- **LLM:** Anthropic Claude Sonnet 4.5
- **Agent Framework:** LangGraph
- **Tracing:** LangSmith
- **Package Manager:** pip (root), uv (curator-agent/)

### Environment Variables

**Primary Template:** `.env.example`

**Required Variables:**
```bash
# Anthropic (Primary LLM)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Neon Database
DATABASE_URL=postgresql://...
PGVECTOR_ENABLED=true

# LangSmith (Tracing)
LANGSMITH_API_KEY=lsv2_sk_...
LANGSMITH_WORKSPACE_ID=...
LANGCHAIN_TRACING_V2=true

# Optional: OpenAI (for comparison)
OPENAI_API_KEY=sk-...
```

**Setup:**
1. Copy `.env.example` to `.env`
2. Fill in actual API keys
3. Never commit `.env` to git

---

## When to Update This Document

Update `FOLDER_STRUCTURE.md` when:
- ✅ Adding new top-level directories
- ✅ Changing repository structure
- ✅ Establishing new naming conventions
- ✅ Archiving major components
- ✅ Changing tech stack (database, LLM, framework)
- ✅ Adding new file type categories

Don't update for:
- ❌ Individual file additions (unless establishing new pattern)
- ❌ Minor doc tweaks
- ❌ Dependency updates

---

## Decision Log

### 2024-12-21: Initial Folder Structure Definition
- Archived old agents/ directory (superseded by curator-agent/)
- Archived mcp-server/ and risk-scanner/ (design-only, not implemented)
- Moved .env.template to archive (contains outdated Neo4j config)
- Established curator-agent/ as primary agent implementation
- Created archive/ structure with READMEs

### 2024-12-20: Deep Agent Migration
- Switched from standalone agents to LangGraph Deep Agent pattern
- Built curator-agent/ with main + 3 sub-agents
- Adopted Claude Sonnet 4.5 as primary LLM

### Previous
- Used Neo4j (switched to Neon PostgreSQL)
- Standalone agent scripts (switched to LangGraph)

---

## Quick Reference

**Where does this go?**

| What you're adding | Where it goes | Example |
|-------------------|---------------|---------|
| New sub-agent | `curator-agent/src/curator/subagents/` | `analyzer.py` |
| Database utility | `scripts/` | `migration_helper.py` |
| Architecture doc | `docs/` | `VECTOR_SEARCH.md` |
| Knowledge entry | `library/software/` | `uart-driver.md` |
| Manual analysis | `trial_docs/` | `manual-fprime-analysis.md` |
| Unit test | `tests/unit/` | `test_graph_manager.py` |
| Exploration | `notebooks/` | `2024-12-21-graph-analysis.ipynb` |
| Old code | `archive/legacy-agents/` | `old_extractor.py` |
| Design doc (not implemented) | `archive/design-docs/` | `proposed-feature/` |

---

**Maintained by:** Claude Code + Human Oversight
**Review Frequency:** After major structural changes
**Last Review:** December 21, 2024
