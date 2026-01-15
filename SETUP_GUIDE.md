# PROVES Library Setup Guide

Complete setup instructions for the PROVES Knowledge Management System.

## Prerequisites

- Python 3.14 (or 3.10+)
- Git
- PostgreSQL database (we use [Neon](https://neon.tech) - free tier available)
- Notion account (for human review workflow)
- Anthropic API key (for Claude AI agents)

## Setup Options

### Option A: Docker (Recommended for New Users)

**Prerequisites:** Docker and Docker Compose installed

```bash
# 1. Clone repositories
git clone https://github.com/Lizo-RoadTown/PROVES_LIBRARY.git
cd PROVES_LIBRARY
git clone https://github.com/Lizo-RoadTown/PROVES_NOTION.git PROVES_NOTION

# 2. Create .env file (see Environment Variables section below)

# 3. Start webhook server
docker-compose up webhook

# 4. Run extraction (in another terminal)
docker-compose run extractor
```

**Benefits:**
- No Python version conflicts
- All dependencies handled
- Consistent environment
- Easy deployment

### Option B: Python Virtual Environment (Manual Setup)

**Use this if you:**
- Want more control over the environment
- Are developing/debugging the system
- Don't want to install Docker

## Quick Start (Python venv Method)

### 1. Clone the Repository

```bash
git clone https://github.com/Lizo-RoadTown/PROVES_LIBRARY.git
cd PROVES_LIBRARY
```

### 2. Clone the Notion Integration (Required)

```bash
git clone https://github.com/Lizo-RoadTown/PROVES_NOTION.git PROVES_NOTION
```

The Notion integration is kept in a separate repository and is required for the human review workflow.

### 3. Create Python Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
# Core dependencies
pip install psycopg psycopg-pool python-dotenv
pip install langchain langchain-anthropic langchain-core langgraph
pip install httpx langgraph-checkpoint-postgres

# Notion integration dependencies
pip install notion-client fastapi uvicorn
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-...

# Neon PostgreSQL Database
NEON_DATABASE_URL=postgresql://user:password@host.region.neon.tech/neondb?sslmode=require

# Notion Integration
NOTION_TOKEN=ntn_...
NOTION_WEBHOOK_SECRET=your_webhook_secret
NOTION_EXTRACTION_DATABASE_ID=...
NOTION_ERROR_DATABASE_ID=...
NOTION_REPORT_DATABASE_ID=...

# LangSmith (Optional - for debugging)
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=proves-library
```

### 6. Run Database Migrations

```bash
# Navigate to migrations folder
cd neon-database/migrations

# Run migrations in order
python run_migration.py 001_initial_schema.sql
python run_migration.py 002_add_epistemic_fields.sql
python run_migration.py 003_add_notion_integration.sql
```

### 7. Setup Notion Databases

```bash
# Run the Notion setup script
cd ../../PROVES_NOTION/scripts
python setup_notion.py
```

Follow the prompts to:
1. Provide your Notion parent page ID
2. Script creates three databases (Extractions, Errors, Reports)
3. `.env` file is automatically updated with database IDs

### 8. Start the Notion Webhook Server

```bash
# From project root
cd PROVES_LIBRARY
.venv/Scripts/python notion/scripts/notion_webhook_server.py
```

The webhook server will:
- Poll database every 10 seconds for new extractions
- Automatically push them to Notion for human review
- Listen for approval/rejection decisions from Notion
- Update database when humans approve/reject extractions

Keep this running in a separate terminal window.

### 9. Run Your First Extraction

```bash
# From project root
cd "production/Version 3"
../../.venv/Scripts/python process_extractions_v3.py --limit 1
```

This will:
1. Fetch the highest-priority URL from your queue
2. Extract architectural entities using Claude
3. Validate extractions for duplicates and quality
4. Store ALL validated extractions to database
5. Automatically sync to Notion for human review

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ EXTRACTION PIPELINE (Fully Automated)                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Extractor Agent (Sonnet 4.5)                            │
│     - Fetches documentation pages                           │
│     - Extracts components, ports, dependencies              │
│     - Captures lineage (checksums, byte offsets)            │
│                                                              │
│  2. Validator Agent (Haiku)                                 │
│     - Checks for duplicates in database                     │
│     - Verifies epistemic metadata structure                 │
│     - Validates evidence lineage                            │
│                                                              │
│  3. Storage Agent (Sonnet 4.5) ⭐ CRITICAL                   │
│     - Stores ALL validated extractions                      │
│     - Includes full epistemic metadata (7-question model)   │
│     - No filtering - capture everything for human review    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ DATABASE (Neon PostgreSQL)                                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  staging_extractions - Pending human review                 │
│  core_entities - Approved knowledge base                    │
│  raw_snapshots - Source page snapshots                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ NOTION WEBHOOK SERVER (Bidirectional Sync)                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Database → Notion: Poll every 10s, push new extractions    │
│  Notion → Database: Webhook receives approval decisions     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ NOTION (Human Review Interface)                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Extractions Database - Review extracted entities           │
│  Status: Pending → Approved/Rejected                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ PROMOTION (Manual or Batch)                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  python curator/batch_promote_accepted.py                   │
│  - Promotes approved extractions to core_entities           │
│  - Creates cross-references                                 │
│  - Updates metadata                                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Key Configuration Notes

### Agent Models (Cost vs Reliability)

**Current Configuration (Optimized for Reliability):**
- Extractor: Sonnet 4.5 (~$0.15/URL) - Complex analysis required
- Validator: Haiku (~$0.04/URL) - Fast duplicate checking
- Storage: **Sonnet 4.5** (~$0.28/URL) - CRITICAL for storing ALL extractions

**Total Cost: ~$0.47 per URL**

**Why Sonnet 4.5 for Storage?**
- Haiku was stopping early, only storing 2-5 of 12+ extractions
- Haiku "helpfully" summarizes instead of completing all work
- Sonnet 4.5 reliably stores 100% of validated extractions
- For mission-critical data, 100% reliability > lower cost

### Connection Pooling

The system uses centralized PostgreSQL connection pooling:

```python
# production/Version 3/database.py
min_size: 2    # Keep 2 connections warm
max_size: 20   # Up to 20 concurrent operations
timeout: 60s   # Wait up to 60s for available connection
```

Separate pools:
- **Tool Pool** (20 connections): For agent database queries
- **Checkpointer Pool** (3 connections): For LangGraph state persistence
- **Total**: 23 connections (well under Neon free tier limit of 100)

### Recursion Limits

```python
# production/Version 3/process_extractions_v3.py
recursion_limit: 100  # Allows storage agent to store many extractions
```

Each tool call counts as 1 recursion step. With 12+ entities per page, need room for:
- 12+ store_extraction() calls
- Verification calls
- Status updates

## Troubleshooting

### "notion_client module not found"

**Cause:** Dependencies installed in venv, but running with system Python

**Fix:** Always use venv Python:
```bash
# Windows
.venv\Scripts\python script.py

# Mac/Linux
.venv/bin/python script.py
```

### Webhook Server Not Starting

**Check:**
1. Is PROVES_NOTION repo cloned? `ls PROVES_NOTION/scripts`
2. Are all dependencies installed? `pip list | grep notion`
3. Is .env configured with Notion credentials?
4. Is port 8000 available? `netstat -an | grep 8000`

### Only 2-5 Extractions Stored (Not All)

**Check:**
1. Storage agent model: Should be **Sonnet 4.5**, not Haiku
   - File: `production/Version 3/subagent_specs_v3.py` line 558
2. Recursion limit: Should be **100**, not 20
   - File: `production/Version 3/process_extractions_v3.py` line 268
3. Tool call limit: Should be **removed** (no "MAX 5 TOOL CALLS")
   - File: `production/Version 3/subagent_specs_v3.py` lines 510-533

### Connection Pool Timeout Errors

**Increase pool size:**
```python
# production/Version 3/database.py
max_size: 20  # Was 5, increase if seeing timeouts
```

## Cost Optimization

If cost is a concern after the system is stable:

1. **Keep Sonnet 4.5 for Extraction** - Core analysis needs it
2. **Keep Haiku for Validation** - Fast and cheap, works well
3. **Optimize Storage Agent Prompt** - Make it more efficient with tokens
4. **Consider Batch Processing** - Process multiple entities per tool call

**Do NOT downgrade Storage to Haiku** - this causes data loss.

## Next Steps

Once extraction is working:

1. **Monitor Notion** - Review and approve extractions
2. **Test Promotion** - Run `batch_promote_accepted.py`
3. **Stage 4: MBSE Export** - Implement XTCE/SysML/FPrime serializers
4. **Stage 5: Round-trip Sync** - Bidirectional updates

## Support

- **GitHub Issues**: https://github.com/Lizo-RoadTown/PROVES_LIBRARY/issues
- **LangSmith Traces**: Check agent behavior at https://smith.langchain.com/
- **Neon Dashboard**: Monitor database at https://console.neon.tech/

---

**Mission**: Reduce CubeSat failure rate from 88% through better knowledge management.

**Method**: FRAMES methodology - Socio-organizational provenance wrapping technical standards.

**Goal**: Capture the tacit knowledge that makes missions succeed or fail.
