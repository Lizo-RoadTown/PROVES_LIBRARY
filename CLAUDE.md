# PROVES Library - Claude Code Context

> **This file is auto-loaded at session start. Read it. Don't invent.**

## What This Project Is

PROVES Library is an **agentic knowledge capture system** that extracts **couplings** (not just components) from engineering artifacts to build a resilience graph for space mission teams.

**Core principle:** "Agents provide context. Humans establish truth."

---

## The FRAMES Methodology

**Framework for Resilience Assessment in Modular Engineering Systems**

Agents extract COUPLINGS, not generic knowledge. Every extraction must answer:

| Question | What It Means |
|----------|---------------|
| **What flows?** | Data, power, commands, thermal, mechanical |
| **What breaks if it stops?** | Downstream dependencies |
| **What maintains it?** | Procedures, monitoring, redundancy |
| **Coupling strength?** | Critical / Important / Minor |

**Extraction rule:** If you can't answer 2 of 4 questions with evidence, don't extract.

---

## 4 Epistemic Dimensions (Required Metadata)

Every extraction carries these dimensions:

| Dimension | Meaning | Example Values |
|-----------|---------|----------------|
| **Contact** | How close to the source? | Direct observation → Documented → Inferred |
| **Directionality** | One-way or bidirectional? | Unidirectional / Bidirectional / Unknown |
| **Temporality** | Time-dependent? | Static / Dynamic / Triggered |
| **Formalizability** | How structured? | Formal spec / Semi-formal / Tacit |

---

## 3-Agent Pipeline

```
Extractor (Claude Sonnet) → Validator (Claude Haiku) → Storage (Claude Haiku)
```

| Agent | Responsibility | Key Tools |
|-------|----------------|-----------|
| **Extractor** | Parse source, identify couplings, classify early | `fetch_webpage`, extraction prompts |
| **Validator** | Check epistemic completeness, verify lineage | `verify_evidence_lineage`, `validate_epistemic_structure` |
| **Storage** | Persist with full metadata, maintain graph | `store_extraction()` (50+ params) |

**Contracts documented at:** `.deepagents/AGENT_CONTRACTS.md`

---

## V3 Canon Rules (Don't Repeat Old Mistakes)

| Rule | Why |
|------|-----|
| Classification happens early (Extractor responsibility) | Late classification caused pipeline confusion |
| Per-type defaults, not global defaults | Different entity types have different requirements |
| Staging must not filter - capture everything | Premature filtering lost valuable data |
| Per-extraction validation, not batch-level | Batch validation hid individual failures |
| Stateless agents | Database connection timeouts killed stateful runs |
| Human review before truth promotion | Agents are fallible; humans verify |

**Full canon at:** `canon/CANON.md`

---

## Before You Create Something New

**STOP. Check these first:**

| If you need... | Look at... |
|----------------|------------|
| Agent pattern/contract | `.deepagents/AGENT_CONTRACTS.md` |
| What agents extract | `canon/ONTOLOGY.md` (couplings, 4 questions) |
| Design principles | `canon/CANON.md` (V3 rules) |
| Epistemic theory | `canon/KNOWLEDGE_FRAMEWORK.md` |
| Database schema | `supabase/migrations/` (latest migration) |
| Workflow patterns | `.deepagents/workflows/COMPARISON.md` |
| Deep Agents patterns | `.deepagents/DEEP_AGENTS_ANALYSIS.md` |

---

## Repository Structure

### Core Folders (Read These)

| Folder | Purpose | Key Files |
|--------|---------|-----------|
| `canon/` | Design principles, ontology | `CANON.md`, `ONTOLOGY.md`, `KNOWLEDGE_FRAMEWORK.md` |
| `.deepagents/` | Agent contracts, roadmaps | `AGENT_CONTRACTS.md`, `IMPLEMENTATION_ROADMAP.md` |
| `supabase/` | Database migrations | `migrate.ps1` (single migration command) |
| `production/core/` | Domain models, repositories | Python code for entities |
| `curation_dashboard/` | React dashboard | Vite + React + Supabase |

### Active Work Areas

| Folder | What's There |
|--------|--------------|
| `.deepagents/standards/` | XTCE, SysML, PyG vocabulary studies |
| `supabase/migrations/` | SQL migration files |

### Low Priority (Rarely Used)

| Folder | Why |
|--------|-----|
| `ps_scripts/` | Mermaid/markdown fixing scripts (rarely needed) |
| `testing_data/` | Historical diagram experiments |

---

## Supabase Access (I Forget This)

**Project:** `guigtpwxlqwueylbbcpx`

### Running Migrations (AUTOMATED - No Manual Steps!)

```powershell
cd supabase
.\migrate.ps1 031     # Runs directly against database via Python
.\migrate.ps1 032     # Same for next migration
.\migrate.ps1 -List   # See all available migrations
.\migrate.ps1 -DryRun 031  # Preview without executing
```

**How it works:**
- Script reads `DATABASE_URL` from `.env` file
- Strips `pgbouncer` parameter (psycopg2 doesn't understand it)
- Executes SQL directly using Python + psycopg2
- **No clipboard. No browser. Fully automated.**

**Requirements:**
- `.env` file with `DATABASE_URL=postgresql://...`
- Python venv with psycopg2: `.venv\Scripts\python.exe`

### Direct Links (For Manual Access)

| Link | Purpose |
|------|---------|
| [SQL Editor](https://supabase.com/dashboard/project/guigtpwxlqwueylbbcpx/sql/new) | Run SQL directly |
| [Table Editor](https://supabase.com/dashboard/project/guigtpwxlqwueylbbcpx/editor) | Browse/edit data |
| [Dashboard](https://supabase.com/dashboard/project/guigtpwxlqwueylbbcpx) | Main dashboard |

---

## Curation Dashboard (Separate Repo!)

**The dashboard is a SEPARATE GitHub repo deployed via Vercel.**

| What | Where |
|------|-------|
| **Local folder** | `curation_dashboard/` (has its own `.git`) |
| **GitHub repo** | https://github.com/Lizo-RoadTown/proves-curation-dashboard |
| **Deployed at** | Vercel (auto-deploys on push to main) |

**To update the dashboard:**
```powershell
cd curation_dashboard
npm run dev              # Local development
git add . && git commit -m "message"
git push origin main     # Triggers Vercel deploy
```

**Don't confuse this with the parent PROVES_LIBRARY repo!**

---

## MCP Tools (I Have Live Access)

I have Docker-based MCP tools for live information. Use `mcp__MCP_DOCKER__` prefix.

| Tool | Purpose |
|------|---------|
| `mcp-find` | Search for available MCP servers |
| `mcp-add` | Add an MCP server to session |
| `get-library-docs` | Fetch up-to-date library documentation (Context7) |
| `resolve-library-id` | Find library ID for documentation |
| `fetch` | Fetch web pages as markdown |
| `browser_*` | Browser automation (Playwright) |
| `hf_doc_search` | Search Hugging Face documentation |
| `model_search` | Find ML models on Hugging Face |
| `run_js_ephemeral` | Run JavaScript in isolated container |

**To get current docs for a library:**
```
1. mcp__MCP_DOCKER__resolve-library-id (e.g., "langgraph")
2. mcp__MCP_DOCKER__get-library-docs with the resolved ID
```

**Don't invent API patterns - fetch current docs!**

---

## Building Agents (Documentation Lives Here)

**Don't invent agent patterns. Read these first:**

| Document | What It Covers |
|----------|----------------|
| `.deepagents/AGENT_CONTRACTS.md` | 3-agent pipeline, tool signatures, input/output contracts |
| `.deepagents/workflows/COMPARISON.md` | Sequential vs Agentic vs Deep Agents RAG |
| `.deepagents/DEEP_AGENTS_ANALYSIS.md` | Gaps in current patterns, TODO-based planning |
| `canon/ONTOLOGY.md` | What to extract (couplings), 4 mandatory questions |

**LangGraph patterns:** Use MCP to fetch current docs:
```
mcp__MCP_DOCKER__resolve-library-id("langgraph")
mcp__MCP_DOCKER__get-library-docs(...)
```

**Existing agent code lives in:** `curator-agent/` and `production/`

---

## What NOT To Do

1. **Don't invent agent patterns** - they're documented
2. **Don't extract "knowledge" generically** - extract couplings
3. **Don't skip epistemic metadata** - the 4 dimensions are required
4. **Don't batch validate** - per-extraction validation
5. **Don't filter in staging** - capture everything, filter later
6. **Don't forget human review** - agents provide context, humans verify

---

## Refresh Memory

If context seems stale, read these in order:
1. `canon/CANON.md` (10 min) - design principles
2. `canon/ONTOLOGY.md` (5 min) - what we extract
3. `.deepagents/AGENT_CONTRACTS.md` (5 min) - how agents work

---

## Current State (Auto-Generated)

> Last refreshed: 2026-01-18 10:59

### Git Status
- **Branch:** main
- **Uncommitted changes:** 23 files
- **Recent commits:**
  - f3227bf Add PROVES university teams and migrations
  - 2b4c52a Fix graph nodes timestamp type mismatch (migration 028)
  - 1cda4f4 Add organization and graph API migrations (022-027)

### Implementation Phase
- **Current:** Naming and Standards Alignment (Week 3)
- **Roadmap:** .deepagents/IMPLEMENTATION_ROADMAP.md

### Database
- **Latest migration:** 20260115191105_teams_and_batch_claims.sql
- **Run migrations:** cd supabase && .\migrate.ps1

### Recent Session Work
- SESSION_SUMMARY_2026-01-15_WEEK2_COMPLETE.md
- SESSION_SUMMARY_2026-01-15_DOMAIN_MODELS.md
- SESSION_SUMMARY_2026-01-15.md

### Active Folders
| Folder | Status |
|--------|--------|
| `curation_dashboard` | Present |
| `supabase` | Present |
| `production/core` | Present |
| `.deepagents` | Present |
| `canon` | Present |