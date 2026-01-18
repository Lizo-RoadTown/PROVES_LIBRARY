# PROVES Library - Revised Architecture & Roadmap

## Vision

The PROVES Library is an **evolving collective brain** for space systems engineering.

It's not just a database - it's a **neural network of knowledge** that:
- **Learns** from every conversation, document, and decision engineers make
- **Connects** disparate pieces of information into a coherent understanding
- **Augments** engineers by surfacing relevant knowledge when they need it
- **Grows** smarter over time as more knowledge flows through it

## System Overview

The system has three flows:

1. **Ingest** - Data from wherever engineers work flows into the brain
2. **Process** - Agentic AI extracts, connects, and organizes knowledge
3. **Serve** - The brain feeds knowledge back to engineers (and university teams)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                            ┌─────────────────────┐                          │
│                            │   COLLECTIVE BRAIN  │                          │
│                            │                     │                          │
│   INGEST                   │  ┌───┐ ┌───┐ ┌───┐ │              SERVE        │
│   ──────                   │  │ ● │─│ ● │─│ ● │ │              ─────        │
│                            │  └─┬─┘ └─┬─┘ └─┬─┘ │                           │
│   Discord ───┐             │    │╲   │   ╱│    │         ┌──────────────┐   │
│   Notion ────┤             │  ┌─┴─┐ ┌┴───┴┐┌─┴─┐│         │  MCP Server  │   │
│   GitHub ────┼──▶ EXTRACT ─┼─▶│ ● │─│  ●  ││ ● │┼────────▶│  (Docker)    │   │
│   G Drive ───┤    + LEARN  │  └─┬─┘ └──┬──┘└─┬─┘│         └──────┬───────┘   │
│   Papers ────┘             │    │╱   │   ╲│    │                │           │
│                            │  ┌─┴─┐ ┌┴───┴┐┌─┴─┐│                ▼           │
│        ▲                   │  │ ● │─│  ●  ││ ● │┼──▶  University Teams      │
│        │                   │  └───┘ └─────┘└───┘│      Claude Code, IDE     │
│        │                   │                     │                           │
│        │                   │   Knowledge Graph   │                           │
│        │                   │   + Embeddings      │         ┌──────────────┐   │
│        │                   │   + Relationships   │         │  Engineer UI │   │
│        │                   └──────────┬──────────┘         │  (Oversight) │   │
│        │                              │                    └──────┬───────┘   │
│        │                              ▼                           │           │
│        │                     ┌────────────────┐                   │           │
│        └─────────────────────│  FEEDBACK LOOP │◀──────────────────┘           │
│                              │  (Learning)    │                               │
│                              └────────────────┘                               │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

**The Brain is a Neural Network:**
- **Nodes** = Knowledge entities (procedures, components, decisions, lessons)
- **Edges** = Relationships (uses, conflicts-with, depends-on, supersedes)
- **Embeddings** = Semantic understanding (similar concepts cluster together)
- **Learning** = Feedback from engineers improves classification, connections, confidence

---

## The Agentic AI Creates Features

The Agentic AI doesn't just process data - **its work creates features for people to use**.

The library it builds in the background **enables** those features:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  AGENTIC AI WORK                         FEATURES THAT EMERGE               │
│  ─────────────────                       ───────────────────                │
│                                                                             │
│  Extracts procedures from Discord   ──▶  "How do I run ADCS calibration?"  │
│                                          → Returns step-by-step procedure   │
│                                                                             │
│  Maps I2C addresses from datasheets ──▶  "What conflicts with MS5611?"     │
│                                          → Returns address conflicts        │
│                                                                             │
│  Links components to interfaces     ──▶  "What connects to the BNO085?"    │
│                                          → Returns interface diagram        │
│                                                                             │
│  Tracks decisions and rationale     ──▶  "Why did we choose F-Prime?"      │
│                                          → Returns ADR with context         │
│                                                                             │
│  Captures lessons from post-mortems ──▶  "What went wrong with power?"     │
│                                          → Returns lessons learned          │
│                                                                             │
│  Builds relationship graph          ──▶  "Show me the EPS subsystem"       │
│                                          → Returns connected components     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**The pattern:**
1. Agentic AI does work in the background (extract, classify, connect, embed)
2. That work populates the library (knowledge graph + vector embeddings)
3. The library enables features (search, Q&A, recommendations, conflict detection)
4. Engineers and teams use those features through MCP / UI

**Features don't exist without the library. The library doesn't exist without the AI's work.**

---

## Three Core Components

### 1. Agentic Extractor (Backend)

**Purpose:** Continuously ingest and process data from all sources into the knowledge base.

**What it does:**
- Watches configured sources for new/changed content
- Runs extraction pipeline (chunk → embed → classify → queue)
- Feeds `pending_extractions` table for review
- Auto-promotes high-confidence extractions
- Flags conflicts and duplicates

**Deployment:** Docker container(s) or scheduled jobs

**Status:** Pipeline code exists, needs orchestration layer

---

### 2. Engineer UI (Oversight Dashboard)

**Purpose:** The interface where engineers **oversee the agentic AI** and **manage the library**.

This is NOT a simple admin panel - it's the **mission control** for the entire knowledge system.

**Two Core Functions:**

#### A. Agentic AI Oversight
Engineers monitor and guide the AI that processes incoming data.

| View | What Engineers See/Do |
|------|----------------------|
| **Activity Feed** | Real-time view of what the AI is extracting |
| **Confidence Dashboard** | AI's certainty levels, where it needs help |
| **Review Queue** | Items flagged for human judgment |
| **Agent Behavior** | Configure how the AI classifies, prioritizes, connects |
| **Error Log** | Failed extractions, source issues, conflicts |

#### B. Library Management
Engineers curate and maintain the verified knowledge base.

| View | What Engineers See/Do |
|------|----------------------|
| **Knowledge Browser** | Search, filter, explore verified entities |
| **Entity Editor** | Edit, merge, split, archive knowledge items |
| **Coverage Map** | What domains are well-covered vs. gaps |
| **Relationship Graph** | How knowledge connects (components → interfaces → procedures) |
| **Quality Metrics** | Freshness, accuracy flags, usage stats |

**Key Principle:** The AI does the heavy lifting, engineers provide oversight and course correction.

**Deployment:** Web app (React) - engineers access via browser

**Status:** Scaffolded (Ask/Library/Admin surfaces), needs deeper agentic oversight features

---

### 3. MCP Server (API)

**Purpose:** Serve the knowledge brain to university teams.

**How teams connect:**
- **Claude Code:** Add MCP server to config, query via chat
- **VS Code:** MCP extension connects to server
- **Their Docker:** Pull image, connect to hosted server or run locally

**Tools available:**
- `search_knowledge` - Semantic search across verified KB
- `get_entity` - Fetch specific knowledge item
- `get_hardware_info` - Component specs, I2C addresses
- `find_conflicts` - Known incompatibilities
- `search_external` - Web, papers, manufacturer docs

**Deployment:** You host centrally (Docker), teams connect

**Status:** Built, Docker-ready, needs data to search

---

## Roadmap

### Phase 1: Foundation (Current → 2 weeks)

**Goal:** Get the extraction pipeline running and feeding real data.

| Task | Description | Status |
|------|-------------|--------|
| 1.1 | Test MCP Docker build locally | Not started |
| 1.2 | Set up extraction orchestration (cron/queue) | Not started |
| 1.3 | Run Discord extractor on real channels | Not started |
| 1.4 | Run Notion extractor on real workspaces | Not started |
| 1.5 | Verify data flows to `pending_extractions` | Not started |
| 1.6 | Manual review: promote first batch to `core_entities` | Not started |
| 1.7 | Test MCP search with real data | Not started |

**Deliverable:** MCP server returns real results from your knowledge base.

---

### Phase 2: Admin UI - Core Functions (2-4 weeks)

**Goal:** Engineers can manage the system without touching code.

| Task | Description | Priority |
|------|-------------|----------|
| 2.1 | Sources page: Add/edit/delete data sources | High |
| 2.2 | Queue page: Review interface with approve/reject/edit | High |
| 2.3 | Pipeline config: Extraction rules UI | Medium |
| 2.4 | Health dashboard: Extraction stats, errors, coverage | Medium |
| 2.5 | Library browser: Search/filter verified KB | Medium |

**Deliverable:** Team can operate the system through the UI.

---

### Phase 3: Agentic Intelligence (4-6 weeks)

**Goal:** The extractor gets smarter, requires less manual review.

| Task | Description | Priority |
|------|-------------|----------|
| 3.1 | Auto-classification: Route extractions by type/domain | High |
| 3.2 | Confidence scoring: Auto-promote high-confidence | High |
| 3.3 | Duplicate detection: Flag/merge similar entities | Medium |
| 3.4 | Conflict detection: Alert on contradictions | Medium |
| 3.5 | Gap analysis: Identify missing documentation | Low |
| 3.6 | Agent builder UI: Configure extraction behavior | Low |

**Deliverable:** System runs with minimal human intervention.

---

### Phase 4: MCP Production & Distribution (6-8 weeks)

**Goal:** University teams actively using the system.

| Task | Description | Priority |
|------|-------------|----------|
| 4.1 | Publish MCP Docker image to registry | High |
| 4.2 | Write team onboarding documentation | High |
| 4.3 | Add authentication layer to MCP | Medium |
| 4.4 | Usage analytics: Track queries, popular topics | Medium |
| 4.5 | Feedback loop: Teams can flag bad answers | Low |

**Deliverable:** Teams are querying the library, getting useful answers.

---

### Phase 5: Scale & Polish (8+ weeks)

| Task | Description |
|------|-------------|
| 5.1 | Additional source integrations (Slack, Confluence, etc.) |
| 5.2 | Multi-team permissions (who sees what) |
| 5.3 | Export/sync to external systems |
| 5.4 | Advanced search (filters, facets, time ranges) |
| 5.5 | Knowledge graph visualization |

---

## Architecture Decisions

### Why You Host MCP Centrally

- **One source of truth:** All teams query the same verified KB
- **You control quality:** Extractions are reviewed before being served
- **Simpler for teams:** They just connect, don't manage infrastructure
- **Updates propagate:** Improve KB once, everyone benefits

### Why Admin UI is Separate from MCP

- **Different users:** Your engineers vs. university teams
- **Different needs:** Configuration/curation vs. querying
- **Security:** Admin actions shouldn't be exposed via MCP

### Why Agentic Extraction

- **Scale:** Too much content for manual entry
- **Freshness:** Auto-ingest keeps KB current
- **Coverage:** Catches knowledge that would be missed manually

---

## Current State Summary

| Component | Code | Data | Deployment | Status |
|-----------|------|------|------------|--------|
| MCP Server | ✅ Built | ❌ Empty | ✅ Docker ready | Needs data |
| Admin UI | 🟡 Scaffolded | N/A | ❌ Not deployed | Needs features |
| Extractor | 🟡 Pipelines written | ❌ Not running | ❌ Not orchestrated | Needs to run |
| Database | ✅ Schema ready | ❌ Empty | ✅ Supabase | Needs population |

**The critical path:** Run extractors → Populate DB → MCP becomes useful

---

## Immediate Next Steps

1. **Test Docker build** - Verify MCP server runs in container
2. **Pick one source** - Start with Discord or Notion (whichever has most content)
3. **Run extraction** - Get real data into `pending_extractions`
4. **Manual review** - Promote first batch to verify flow works
5. **Test MCP queries** - Confirm search returns real results

Once this loop works end-to-end, scale up sources and build out Admin UI.

---

## Detailed Task Breakdown

### Phase 1: Foundation

```
[ ] 1.1 Test MCP Docker Build
    [ ] cd mcp-server && docker build -t proves-mcp .
    [ ] Run with test DATABASE_URL
    [ ] Verify health_check tool responds
    [ ] Test search_knowledge with empty DB (should return empty, not error)

[ ] 1.2 Extraction Orchestration
    [ ] Review existing pipeline code in curation_dashboard/src/lib/extraction/
    [ ] Create extraction runner script (Python or Node)
    [ ] Set up scheduler (cron, GitHub Actions, or queue like BullMQ)
    [ ] Configure which sources to watch and how often

[ ] 1.3 Run Discord Extractor
    [ ] Configure Discord bot token and channel IDs
    [ ] Run extraction on 1-2 active channels
    [ ] Verify messages flow to pending_extractions
    [ ] Check extracted content quality

[ ] 1.4 Run Notion Extractor
    [ ] Configure Notion integration token
    [ ] Run extraction on 1-2 key pages/databases
    [ ] Verify content flows to pending_extractions
    [ ] Check extracted content quality

[ ] 1.5 Verify Data Flow
    [ ] Query pending_extractions table
    [ ] Confirm source_type, content, metadata populated
    [ ] Check embedding generation (if implemented)
    [ ] Identify any pipeline errors

[ ] 1.6 Manual Review & Promotion
    [ ] Review 10-20 pending extractions manually
    [ ] Promote good ones to core_entities
    [ ] Identify patterns (what's valuable, what's noise)
    [ ] Document review criteria for future automation

[ ] 1.7 Test MCP with Real Data
    [ ] Run search_knowledge queries
    [ ] Verify results match promoted entities
    [ ] Test get_entity retrieval
    [ ] Check search relevance (does semantic search work?)
```

### Phase 2: Engineer UI

```
[ ] 2.1 Sources Management
    [ ] List connected sources with status
    [ ] Add new source form (Discord channel, Notion page, GitHub repo)
    [ ] Edit source configuration
    [ ] Enable/disable source
    [ ] Delete source (with confirmation)

[ ] 2.2 Review Queue
    [ ] List pending_extractions with filters (source, date, type)
    [ ] Preview extracted content
    [ ] Approve → move to core_entities
    [ ] Reject → mark as rejected with reason
    [ ] Edit → modify before approving
    [ ] Bulk actions (approve all from source, etc.)

[ ] 2.3 Activity Feed
    [ ] Real-time view of extraction activity
    [ ] Show: source, type, timestamp, status
    [ ] Filterable by source, time range
    [ ] Click to see extraction details

[ ] 2.4 Health Dashboard
    [ ] Extraction counts by source (today, week, month)
    [ ] Error rates and failure reasons
    [ ] Review queue depth
    [ ] Coverage by domain/type
    [ ] System status (DB connected, extractors running)

[ ] 2.5 Library Browser
    [ ] Search core_entities
    [ ] Filter by type, domain, date
    [ ] View entity details
    [ ] Edit entity content
    [ ] Archive/delete entity
    [ ] View relationships
```

### Phase 3: Agentic Intelligence

```
[ ] 3.1 Auto-Classification
    [ ] Define entity types and classification rules
    [ ] Implement LLM-based classifier
    [ ] Route extractions by type automatically
    [ ] Track classification accuracy

[ ] 3.2 Confidence Scoring
    [ ] Define confidence metrics (source quality, content clarity, etc.)
    [ ] Calculate confidence for each extraction
    [ ] Auto-promote above threshold
    [ ] Flag low-confidence for review

[ ] 3.3 Duplicate Detection
    [ ] Implement similarity search on new extractions
    [ ] Flag potential duplicates
    [ ] UI for merge/keep decisions
    [ ] Track duplicate rate by source

[ ] 3.4 Conflict Detection
    [ ] Define conflict types (contradicting facts, outdated info, etc.)
    [ ] Cross-reference new extractions with existing KB
    [ ] Alert on detected conflicts
    [ ] UI for resolution

[ ] 3.5 Gap Analysis
    [ ] Define expected coverage (all components documented, etc.)
    [ ] Compare KB against expected coverage
    [ ] Generate gap reports
    [ ] Suggest sources that might fill gaps

[ ] 3.6 Agent Behavior Config
    [ ] UI to adjust classification thresholds
    [ ] Configure confidence scoring weights
    [ ] Set auto-promote rules
    [ ] Define domain-specific extraction rules
```

### Phase 4: MCP Production

```
[ ] 4.1 Publish Docker Image
    [ ] Set up GitHub Actions for CI/CD
    [ ] Push to Docker Hub or GitHub Container Registry
    [ ] Version tagging strategy
    [ ] Document image usage

[ ] 4.2 Team Onboarding Docs
    [ ] Quick start guide
    [ ] Claude Code configuration
    [ ] VS Code MCP extension setup
    [ ] Example queries and use cases
    [ ] Troubleshooting guide

[ ] 4.3 Authentication
    [ ] Implement API key auth for MCP
    [ ] Team registration flow
    [ ] Key management in Admin UI
    [ ] Rate limiting per team

[ ] 4.4 Usage Analytics
    [ ] Log queries with team ID
    [ ] Dashboard: queries/day, popular topics
    [ ] Track which tools are used most
    [ ] Identify knowledge gaps from query patterns

[ ] 4.5 Feedback Loop
    [ ] Add feedback tool to MCP (rate answer, flag issue)
    [ ] Store feedback in DB
    [ ] Review feedback in Admin UI
    [ ] Use feedback to improve KB
```

---

## Summary

**What we're building:** A collective brain that learns from engineering work and serves knowledge back.

**Three components:**
1. **Agentic Extractor** - Ingests and processes data (background)
2. **Engineer UI** - Oversees AI and manages library (your team)
3. **MCP Server** - Serves knowledge to teams (Docker, hosted)

**Critical path:** Get data flowing first, then build UI, then scale intelligence.

**Start here:** Test MCP Docker → Run one extractor → Review → Test queries
