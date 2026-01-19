# PROVES Library

Agentic AI for lean teams building in emergent technology. Extracts what matters from documentation, verifies it with engineers, and builds a knowledge graph that grows smarter over time.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Database: Supabase](https://img.shields.io/badge/database-Supabase-3ECF8E.svg)](https://supabase.com)
[![Dashboard](https://img.shields.io/badge/dashboard-live-blue.svg)](https://proves-curation-dashboard.vercel.app/)

Built for engineering teams in rapid prototyping phases who need to move fast without losing embodied knowledge.

---

## The Problem

Small teams building complex systems lose knowledge constantly. Documentation gets stale. Decisions get forgotten. When someone leaves, their expertise walks out the door.

Traditional knowledge bases don't help because they require manual entry and maintenance that lean teams don't have time for.

## The Solution

AI agents that read your documentation and extract the **couplings** that matter: what connects to what, what breaks if something fails, what procedures maintain critical systems.

But agents make mistakes. So engineers review every extraction before it enters the shared knowledge graph. This human-in-the-loop approach means the graph contains verified truth, not AI hallucinations.

The result: a growing knowledge graph that answers questions, identifies risks, and eventually powers predictive modeling.

---

## How It Works

```
Sources → AI Extraction → Engineer Review → Knowledge Graph → Team Queries
                              ↓
                    (nothing enters without approval)
```

**Agents extract.** They read repos, wikis, and docs to identify components, interfaces, procedures, and dependencies.

**Engineers verify.** Every extraction goes through human review. Approve, reject, or edit. Nothing enters the shared graph without sign-off.

**Agents learn.** Engineer feedback improves the agents over time. Each approval, rejection, and correction teaches the system better domain knowledge. This is active learning (human-in-the-loop) - the same approach used to train modern AI systems like ChatGPT. The more your team reviews, the smarter the extraction becomes for your specific technical context, and the less oversight engineers need to provide.

**Knowledge normalizes.** Before entering the graph, verified knowledge goes through a normalization process that prepares it for multiple immediately useful processes: semantic search, relationship mapping, gap analysis, and future predictive modeling. This standardization ensures consistent structure across all team contributions.

**Knowledge accumulates.** Verified and normalized extractions become the authoritative source of truth that the whole team can query.

---

## Architecture

The system has three surfaces:

### Mission Control (Shared Awareness)

A read-only view showing activity across all teams. Heat maps of who's active, pipeline flow visualization, real-time awareness of what's happening across the project.

### Library (Validated Knowledge)

The shared knowledge graph. Search and browse verified entities, relationships, and procedures. This is the source of truth that all teams contribute to and query from.

### Admin (Team Workspace)

Each team's private workspace. Manage your sources, review your extractions, monitor your ingestion pipeline. Your data stays yours until you promote it to the shared graph.

---

## For Distributed Teams

Multiple remote teams, each with their own workspace, building one unified knowledge base.

Each team:
- Connects their own sources (repos, docs, wikis)
- Reviews their own extractions
- Promotes verified knowledge to the shared graph

The shared graph grows from contributions across all teams. Mission Control shows who's active and where knowledge is flowing.

---

## What Gets Extracted

Not generic "knowledge" - **couplings**. The system focuses on what connects to what:

| Question | Why It Matters |
|----------|----------------|
| What flows between components? | Data, power, commands, thermal |
| What breaks if this fails? | Downstream dependencies |
| What maintains this? | Procedures, monitoring, redundancy |
| How critical is this coupling? | Critical / Important / Minor |

This coupling-aware extraction is what makes the graph useful for risk analysis and future predictive modeling.

---

## The Roadmap

**Now:** Extraction pipeline, human review, knowledge graph, team workspaces

**Next:** Query interface via MCP, natural language questions against the graph

**Planned:** Graph neural network for predictive analysis - using the verified knowledge graph as training data to anticipate issues before they happen

---

## Stack

| Layer | Technology |
|-------|------------|
| **Database** | Supabase (PostgreSQL + pgvector) |
| **LLM** | Claude (Anthropic) |
| **Orchestration** | LangGraph |
| **Frontend** | React + Vite |
| **Query** | Model Context Protocol (MCP) |

---

## Quick Start

```bash
git clone https://github.com/Lizo-RoadTown/PROVES_LIBRARY.git
cd PROVES_LIBRARY
pip install -r requirements.txt
cp .env.example .env
# Fill in: ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE keys, DATABASE_URL
```

**Run migrations:**
```powershell
cd supabase
.\migrate.ps1 -List          # See available migrations
.\migrate.ps1 034            # Apply a specific migration
```

**Process some documentation:**
```bash
python production/scripts/find_good_urls.py --proveskit
python production/Version\ 3/process_extractions_v3.py --limit 5
```

Extractions appear in the [dashboard](https://proves-curation-dashboard.vercel.app/) ready for review.

---

## Repository Structure

| Folder | Purpose |
|--------|---------|
| `curation_dashboard/` | React dashboard (separate repo, deployed via Vercel) |
| `supabase/migrations/` | Database schema migrations |
| `production/` | Extraction pipeline code |
| `canon/` | Design principles and ontology |
| `.deepagents/` | Agent contracts and implementation roadmap |

---

## Currently In Use

Built for [PROVES Kit](https://docs.proveskit.space/), an open-source CubeSat framework running on NASA JPL's [F' (F Prime)](https://nasa.github.io/fprime/) flight software.

Active teams: Cal Poly Pomona, Columbia University, Northeastern University, UC Santa Cruz, Texas State University

Each team builds their own satellites and ground stations. The shared knowledge graph helps them learn from each other without duplicating mistakes.

---

## Contact

**Liz Osborn** - eosborn@cpp.edu
**Michael Pham** - mpham@cpp.edu

[Bronco Space Lab](https://broncospace.cpp.edu/) | Cal Poly Pomona

---

MIT License
