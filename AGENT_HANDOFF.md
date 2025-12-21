# Agent Handoff Document

**Last Updated:** 2024-12-20
**Current Phase:** Trial Mapping Complete, LangSmith Integration Complete
**Next Phase:** Test automated extraction, validate against manual analysis

---

## 🎯 Quick Context

You are working on the **PROVES Library** - an agentic knowledge base system for CubeSat mission safety. The system extracts dependencies from documentation to prevent "Team A changes something, Team B's system fails 2 weeks before launch" scenarios.

**Core Problem:** Hidden cross-system dependencies cause catastrophic mission failures.
**Our Solution:** LLM-powered dependency extraction + knowledge graph + continuous monitoring.

---

## 📍 Current State (What's Built)

### ✅ Completed

1. **Neon PostgreSQL Knowledge Graph** (cloud-hosted)
   - Schema: `kg_nodes`, `kg_relationships`, `library_entries`
   - ERV relationship types: depends_on, conflicts_with, enables, requires, mitigates, causes
   - pgvector for semantic search
   - Database utilities: [scripts/db_connector.py](scripts/db_connector.py), [scripts/graph_manager.py](scripts/graph_manager.py)

2. **Trial Dependency Mapping** (Manual Analysis)
   - Analyzed F´ I2C Driver (411 lines) + PROVES Kit Power Management (154 lines)
   - Found 45+ dependencies with line citations
   - Identified 4 critical cross-system dependencies (undocumented in either system!)
   - Full analysis: [trial_docs/COMPREHENSIVE_DEPENDENCY_MAP.md](trial_docs/COMPREHENSIVE_DEPENDENCY_MAP.md)

3. **GitHub Pages Visualization Site**
   - Live at: https://lizo-roadtown.github.io/PROVES_LIBRARY/
   - 5 interactive Mermaid diagram pages
   - Tactile theme with proper styling
   - Automated deployment via GitHub Actions

4. **LangSmith Tracing Integration** (NEW!)
   - Dependency extractor with full observability: [scripts/dependency_extractor.py](scripts/dependency_extractor.py)
   - All LLM calls traced (wrap_openai)
   - All extraction steps traced (@traceable decorators)
   - Documentation: [docs/LANGSMITH_INTEGRATION.md](docs/LANGSMITH_INTEGRATION.md)
   - Environment template: [.env.example](.env.example)

### ⚠️ Partially Complete

1. **Database Schema**
   - Enhanced schema designed (dependency_sources, knowledge_gaps, team_boundaries tables)
   - NOT YET IMPLEMENTED in Neon
   - Design docs: [docs/KNOWLEDGE_GRAPH_SCHEMA.md](docs/KNOWLEDGE_GRAPH_SCHEMA.md)

2. **MCP Server**
   - Skeleton exists in [mcp-server/](mcp-server/)
   - NOT YET FUNCTIONAL
   - Needs to connect to Neon database
   - Needs to expose dependency query tools

### ❌ Not Started

1. **Automated Dependency Extraction Test**
   - LangSmith tracing code is built
   - NOT YET RUN on trial documents
   - Need to compare automated vs manual extraction

2. **Risk Scanner**
   - Skeleton exists in [risk-scanner/](risk-scanner/)
   - NOT YET IMPLEMENTED

3. **Agentic Workflows**
   - Designed in [docs/AGENTIC_ARCHITECTURE.md](docs/AGENTIC_ARCHITECTURE.md)
   - NOT YET IMPLEMENTED

---

## 🏗️ Current Architecture

```
┌─────────────────────────────────────────────┐
│         PROVES Library (Current)            │
├─────────────────────────────────────────────┤
│                                             │
│  📄 Documentation Sources                   │
│     ├─ F´ (nasa/fprime)                    │
│     └─ PROVES Kit (BroncoSpace/PROVES)     │
│              ↓                              │
│  🤖 Dependency Extractor (NEW!)            │
│     ├─ GPT-4o-mini extraction              │
│     ├─ LangSmith tracing                   │
│     └─ scripts/dependency_extractor.py     │
│              ↓                              │
│  🗄️  Neon PostgreSQL (Cloud)               │
│     ├─ kg_nodes (components)               │
│     ├─ kg_relationships (ERV)              │
│     └─ library_entries (metadata)          │
│              ↓                              │
│  🌐 GitHub Pages (Visualization)           │
│     └─ https://lizo-roadtown.github.io/    │
│        PROVES_LIBRARY/                      │
│                                             │
│  📊 LangSmith (Observability)              │
│     └─ https://smith.langchain.com         │
│        (PROVES_Library project)             │
└─────────────────────────────────────────────┘
```

---

## 🔑 Key Files Reference

### Core Scripts

| File | Purpose | Status |
|------|---------|--------|
| [scripts/db_connector.py](scripts/db_connector.py) | Database connection pooling | ✅ Working |
| [scripts/graph_manager.py](scripts/graph_manager.py) | CRUD for nodes/relationships | ✅ Working |
| [scripts/dependency_extractor.py](scripts/dependency_extractor.py) | LLM dependency extraction | ✅ Built, not tested |

### Documentation

| File | Purpose | Up to Date? |
|------|---------|-------------|
| [README.md](README.md) | Project overview | ❌ Outdated (mentions Neo4j) |
| [GETTING_STARTED.md](GETTING_STARTED.md) | Setup guide | ❌ Outdated (mentions Neo4j) |
| [ROADMAP.md](ROADMAP.md) | Implementation roadmap | ✅ Current |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture | ⚠️ Partially outdated |
| [docs/AGENTIC_ARCHITECTURE.md](docs/AGENTIC_ARCHITECTURE.md) | Agent design | ✅ Current |
| [docs/KNOWLEDGE_GRAPH_SCHEMA.md](docs/KNOWLEDGE_GRAPH_SCHEMA.md) | Database schema | ✅ Current |
| [docs/LANGSMITH_INTEGRATION.md](docs/LANGSMITH_INTEGRATION.md) | Tracing guide | ✅ Current (NEW) |
| [trial_docs/COMPREHENSIVE_DEPENDENCY_MAP.md](trial_docs/COMPREHENSIVE_DEPENDENCY_MAP.md) | Trial analysis results | ✅ Current |

### Configuration

| File | Purpose |
|------|---------|
| [.env](.env) | Live credentials (NOT in git) |
| [.env.example](.env.example) | Template for environment variables |
| [requirements.txt](requirements.txt) | Python dependencies |

---

## 🚀 How to Run Things

### 1. Test Database Connection

```bash
cd c:/Users/LizO5/PROVES_LIBRARY
.venv/Scripts/activate
python scripts/db_connector.py
```

**Expected Output:**
```
✅ Connected to PostgreSQL: PostgreSQL 16.x...
📊 Database Statistics:
  kg_nodes: X rows
  kg_relationships: Y rows
  ...
```

### 2. Test Graph Manager

```bash
python scripts/graph_manager.py
```

**Expected Output:**
```
📊 Graph Statistics:
  Total nodes: X
  Total relationships: Y
  ...
```

### 3. Run Dependency Extraction (NOT YET TESTED)

```bash
# First, set up environment
cp .env.example .env
# Edit .env and add:
#   LANGSMITH_TRACING=true
#   LANGSMITH_API_KEY=lsv2_pt_...
#   OPENAI_API_KEY=sk-...

# Run extraction
python scripts/dependency_extractor.py trial_docs/fprime_i2c_driver_full.md
```

**Expected Output:**
```
Processing fprime_i2c_driver_full.md...

📊 Extraction Statistics:
  Total dependencies: ~25
  Criticality breakdown:
    HIGH: ~15
    MEDIUM: ~8
    LOW: ~2
  ...

✅ Full trace available in LangSmith UI
```

**View Trace:**
- Go to https://smith.langchain.com
- Select "PROVES_Library" project
- See full extraction pipeline with LLM prompts/responses

---

## 🎯 Next Steps (Priority Order)

### Immediate (Next Session)

1. **Test Automated Extraction**
   ```bash
   python scripts/dependency_extractor.py trial_docs/fprime_i2c_driver_full.md
   ```
   - Compare automated results to manual analysis
   - Check LangSmith traces for quality
   - Identify what dependencies were missed

2. **Refine Extraction Prompts**
   - Based on trace analysis, improve system prompt in dependency_extractor.py
   - Rerun and compare results
   - Iterate until quality matches manual analysis

3. **Extract from Both Trial Docs**
   ```bash
   python scripts/dependency_extractor.py trial_docs/fprime_i2c_driver_full.md
   python scripts/dependency_extractor.py trial_docs/proves_kit_power_mgmt_full.md
   ```
   - Get automated extraction for both documents
   - Run cross-document analysis
   - Compare to manual cross-system dependency findings

### Short-term (This Week)

4. **Insert Trial Data into Database**
   - Create script to load extracted dependencies into Neon
   - Store nodes (components) and relationships (dependencies)
   - Link to library_entries for source documentation

5. **Test Comprehensive Queries**
   - Implement query patterns from COMPREHENSIVE_DEPENDENCY_MAP.md
   - Test transitive dependency queries (recursive CTEs)
   - Test cross-document dependency detection
   - Validate cascade path finding

6. **Update Documentation**
   - Update README.md to reflect Neon (not Neo4j)
   - Update GETTING_STARTED.md with current setup steps
   - Add "Current Status" section to ARCHITECTURE.md

### Medium-term (Next 2 Weeks)

7. **Implement Enhanced Schema**
   - Add dependency_sources table
   - Add knowledge_gaps table
   - Add team_boundaries table
   - Migrate existing data

8. **Build MCP Server Integration**
   - Connect MCP server to Neon database
   - Expose dependency query tools
   - Test with Claude Desktop

9. **Scale to Full Corpus**
   - Process all F´ documentation
   - Process all PROVES Kit documentation
   - Build automated pipeline for continuous updates

---

## 🐛 Known Issues & Gotchas

1. **No Neo4j** - Original docs mention Neo4j, but we're using Neon PostgreSQL. Ignore Neo4j references.

2. **GitHub Pages Theme** - Had to use Tactile theme (not TeXt theme gem) because GitHub Pages doesn't support the gem version. Working now.

3. **LangSmith Not Tested** - The dependency_extractor.py is built but NOT YET RUN. First test will validate the approach.

4. **Requirements.txt Ordering** - langsmith was appended to end of file (line 41) instead of in AI/ML section. Works fine, but could be reorganized.

5. **Database Schema Not Enhanced** - Schema design is ready, but enhanced tables (dependency_sources, knowledge_gaps, team_boundaries) are NOT YET CREATED in Neon.

---

## 🔐 Environment Variables Required

```bash
# Neon Database
NEON_DATABASE_URL=postgresql://user:password@ep-xxx.neon.tech/proves_library

# LangSmith (for tracing)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=PROVES_Library
# LANGSMITH_WORKSPACE_ID=...  # Only if multiple workspaces

# OpenAI (for LLM calls)
OPENAI_API_KEY=sk-...

# GitHub (for doc fetching)
GITHUB_TOKEN=ghp_...
```

---

## 📚 Key Concepts to Understand

### ERV (Engineering Relationship Vocabulary)

6 relationship types for dependency tracking:
- **depends_on**: Runtime dependency (A needs B to function)
- **requires**: Build/config requirement (A needs B to build)
- **enables**: Makes something possible (A enables B)
- **conflicts_with**: Incompatible (A conflicts with B)
- **mitigates**: Reduces risk (A mitigates risk of B)
- **causes**: Leads to effect (A causes B)

### Knowledge Gaps

Dependencies that exist but aren't documented. Examples from trial:
- Timing specifications (how fast must I2C be?)
- Voltage requirements (what voltage for IMU?)
- Error recovery procedures (what if I2C fails?)
- Bus conflict resolution (what if two devices use same address?)

### Team Boundaries (FRAMES)

Organizational interfaces where knowledge is lost:
- F´ team ↔ PROVES Kit team (interface strength: 2/10 WEAK)
- Documentation doesn't cross team boundaries
- Graduation creates 90% knowledge loss

### Transitive Dependencies

Multi-hop dependency chains:
```
Application → DeviceManager → BusDriver → HardwareI2C → PowerSupply
```
13+ hops deep in trial mapping!

---

## 🆘 If Something Breaks

### Can't Connect to Database
```bash
# Test connection string
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('NEON_DATABASE_URL'))"

# Should output: postgresql://...
# If empty, check .env file exists and has NEON_DATABASE_URL
```

### LangSmith Not Tracing
```bash
# Check environment variables
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('TRACING:', os.getenv('LANGSMITH_TRACING')); print('API_KEY:', os.getenv('LANGSMITH_API_KEY')[:10] + '...' if os.getenv('LANGSMITH_API_KEY') else 'NOT SET')"

# Should output:
# TRACING: true
# API_KEY: lsv2_pt_...

# If not set, edit .env file
```

### GitHub Pages Not Updating
```bash
# Check workflow status
cd c:/Users/LizO5/PROVES_LIBRARY
gh run list --workflow=deploy-pages.yml --limit 1

# Should show "completed success"
# If failed, check error logs:
gh run view --log
```

---

## 🤝 Handoff Checklist

When another agent takes over, they should:

- [ ] Read this AGENT_HANDOFF.md file
- [ ] Test database connection (run db_connector.py)
- [ ] Review trial mapping results (trial_docs/COMPREHENSIVE_DEPENDENCY_MAP.md)
- [ ] Understand LangSmith tracing setup (docs/LANGSMITH_INTEGRATION.md)
- [ ] Check current todo list (ask user for latest status)
- [ ] Run dependency extractor test (scripts/dependency_extractor.py)
- [ ] Review LangSmith traces to assess extraction quality
- [ ] Proceed with next priority task from "Next Steps" section above

---

## 📞 Contact & Resources

- **GitHub Repo:** https://github.com/Lizo-RoadTown/PROVES_LIBRARY
- **GitHub Pages:** https://lizo-roadtown.github.io/PROVES_LIBRARY/
- **LangSmith Project:** https://smith.langchain.com (PROVES_Library project)
- **Neon Database:** https://console.neon.tech
- **User:** Elizabeth Osborn (eosborn@cpp.edu)

---

**Status as of 2024-12-20:**
- ✅ Trial mapping complete (manual)
- ✅ LangSmith integration complete (code written)
- ⏸️ Automated extraction ready to test
- 📋 Next: Test automated extraction and compare to manual analysis
