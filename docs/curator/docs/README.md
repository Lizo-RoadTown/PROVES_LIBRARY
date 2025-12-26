# PROVES Library Curator Agent

**LangGraph-based agent for extracting CubeSat dependencies from documentation**

## Overview

The Curator Agent analyzes technical documentation (F´ framework, PROVES Kit) and extracts dependency relationships into a knowledge graph. It captures ALL data to staging tables, then humans verify EVERY piece before it enters the truth graph.

## Quick Start

```bash
# 1. Ensure .env is configured (see ../GETTING_STARTED.md)

# 2. Run with human verification for staged items
python run_with_approval.py

# 3. Or run the test script
python test_agent.py
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  CURATOR AGENT (Claude Sonnet 4.5)                          │
│  - Coordinates sub-agents                                   │
│  - Prepares data for HUMAN verification                     │
│  - Provides context to eliminate ambiguity                  │
└───────┬──────────────┬──────────────┬──────────────────────┘
        │              │              │
        ▼              ▼              ▼
┌───────────┐  ┌──────────┐  ┌──────────────┐
│ EXTRACTOR │  │VALIDATOR │  │   STORAGE    │
│(Sonnet 4.5)  │(Haiku 3.5)  │ (Haiku 3.5)  │
│             │             │               │
│ Captures   │  │ Flags    │  │ Routes to   │
│ ALL data   │  │ anomalies│  │ staging     │
│ + context  │  │ + notes  │  │ tables      │
└───────────┘  └──────────┘  └──────────────┘
        │              │              │
        └──────────────┴──────────────┘
                       ▼
              ┌──────────────────┐
              │ HUMAN VERIFICATION │
              │ (Reviews EACH piece)│
              └────────┬─────────┘
                       ▼
              ┌──────────────────┐
              │   TRUTH GRAPH      │
              │  (Neon PostgreSQL) │
              └──────────────────┘
```

**Cost Optimization:** Haiku for simple tasks = 90% savings on sub-agents!

## File Structure

```
curator-agent/
├── src/curator/
│   ├── agent.py              # Main curator agent + HITL
│   └── subagents/
│       ├── extractor.py      # Document analysis
│       ├── validator.py      # Duplicate checking
│       └── storage.py        # Database storage
├── run_with_approval.py      # CLI entry point
├── test_agent.py             # Basic test
├── test_autonomous_exploration.py
├── test_full_extraction.py
├── test_simple_extraction.py
├── langgraph.json            # LangGraph deployment config
└── pyproject.toml            # Python package definition
```

## How It Works

1. **Input:** Path to documentation file (markdown, code, specs)
2. **Extractor:** Captures ALL raw data with smart categorization and lineage
3. **Validator:** Checks confidence, flags anomalies, notes pattern breaks
4. **Storage:** Routes to staging tables (clean or flagged with reasoning)
5. **Human Verification:** Human reviews EACH piece, aligns across sources
6. **Truth Graph:** Only human-verified data enters the knowledge graph

### ERV Relationship Types

| Type | Meaning | Example |
|------|---------|---------|
| `depends_on` | Runtime dependency | ImuManager → LinuxI2cDriver |
| `requires` | Build requirement | Component → Toolchain |
| `enables` | Makes possible | LoadSwitch → SensorPower |
| `conflicts_with` | Incompatible | UARTDebug ↔ RadioTX |
| `mitigates` | Reduces risk | Watchdog → InfiniteLoop |
| `causes` | Leads to | BrownoutReset → StateCorruption |

### Criticality Levels (Post-Verification Metadata)

| Level | Meaning | Assigned By |
|-------|---------|-------------|
| **HIGH** | Mission-critical | Human during verification |
| **MEDIUM** | Important | Human during verification |
| **LOW** | Minor impact | Human during verification |

> **Note:** Criticality is metadata assigned by humans AFTER verification.

## Configuration

The agent uses environment variables from `../.env`:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-...
DATABASE_URL=postgresql://...

# Optional (tracing disabled by default)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=lsv2_pt_...
```

## State Persistence

Agent state is persisted using LangGraph's PostgresSaver checkpointer:
- Checkpoints stored in Neon PostgreSQL
- Tables: `checkpoints`, `checkpoint_blobs`, `checkpoint_writes`, `checkpoint_migrations`
- Created by: `python ../scripts/setup_checkpointer.py`

## Current Status

🔄 **In Development**

The agent is functional but workflow refinement is ongoing:
- [ ] Stop conditions need tuning (agent loops on extractor calls)
- [ ] Task/outcome definition needs clarity
- [ ] Integration testing with trial documents

## Training Data

HITL interactions can be exported for fine-tuning local LLMs.
See: `../notebooks/02_training_local_llm.ipynb`

---

Last Updated: December 22, 2025
