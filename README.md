# PROVES Library

An agentic system for teams that move fast. Captures knowledge, creates SOPs, and understands workflows so lean teams can stay focused on building.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Database: Supabase](https://img.shields.io/badge/database-Supabase-3ECF8E.svg)](https://supabase.com)

---

## What It Does

### Automated Knowledge Capture

Captures your organization's knowledge at multiple levels—both documented and embodied—so nothing gets lost along the way.

- **Scans documentation** — Reads through repos, wikis, and docs to extract components, procedures, and dependencies
- **Listens in meetings** — Captures decisions, action items, and context from team discussions *(in progress)*
- **Updates from correspondence** — Learns from written and verbal communication to keep knowledge current

The system captures what your team knows before it walks out the door.

### SOPs and Workflows

Turns scattered information into structured procedures and maps how your systems connect.

### Lean Team Support

Automates the busywork so small teams can punch above their weight.

---

Built for [PROVES Kit](https://docs.proveskit.space/), an open-source CubeSat framework on NASA JPL's [F´](https://nasa.github.io/fprime/) flight software.

---

## How It Works

```
Sources → Agents capture → Engineers verify → Knowledge base → Team queries
```

Agents process your documentation, meetings, and correspondence. Engineers do a quick review to catch errors. Verified knowledge goes into a searchable database your whole team can query.

---

## Components

| Component | Description |
|-----------|-------------|
| **Extraction Pipeline** | LangGraph agents that process documentation |
| **Knowledge Graph** | PostgreSQL + pgvector for entities and relationships |
| **Dashboard** | Web UI for verification ([live](https://proves-curation-dashboard.vercel.app/)) |
| **MCP Server** | Query interface for team questions |

---

## Quick Start

```bash
git clone https://github.com/Lizo-RoadTown/PROVES_LIBRARY.git
cd PROVES_LIBRARY
pip install -r requirements.txt
cp .env.example .env
# Add Supabase credentials and Anthropic API key

python production/scripts/find_good_urls.py --proveskit
python production/Version\ 3/process_extractions_v3.py --limit 5
```

---

## Stack

- **LLM**: Claude (Anthropic)
- **Orchestration**: LangGraph
- **Database**: Supabase (PostgreSQL + pgvector)
- **Frontend**: React, Vite
- **Query**: Model Context Protocol

---

## Related

- [PROVES Kit](https://docs.proveskit.space/)
- [F´ (F Prime)](https://nasa.github.io/fprime/)
- [Bronco Space Lab](https://broncospace.cpp.edu/)

---

MIT License | **Bronco Space Lab** | Cal Poly Pomona
