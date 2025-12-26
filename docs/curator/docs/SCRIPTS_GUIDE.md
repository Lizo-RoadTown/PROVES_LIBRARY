# Curator Agent Scripts Guide

**Purpose:** Document all scripts in the curator-agent system - what they do, when to use them, and how to run them.

**Important:** Do NOT create new scripts without documenting them here. Do NOT overwrite existing scripts.

---

## Overview

The curator-agent system has several scripts for different use cases. Each script is specialized for a specific workflow.

---

## Production Scripts

### `run_with_approval.py` - Main Production Script

**Status:** ✅ WORKING PERFECTLY - DO NOT MODIFY

**What it does:**
- Runs curator agent with human-in-the-loop verification
- Captures ALL dependencies to staging tables
- Humans verify EVERY staged item before truth graph entry
- Supports approve, reject, or CORRECT (edit AI output)
- Maintains conversation state via PostgreSQL checkpointer
- Collects training data for local LLM fine-tuning

**When to use:**
- General-purpose extraction tasks
- When you want to choose from multiple test scenarios
- When testing different extraction modes

**How to run:**
```bash
cd curator-agent
python run_with_approval.py
```

**Interactive menu offers:**
1. Simple test (extract from local fprime I2C driver)
2. Autonomous exploration (agent decides what to do)
3. F' web crawl (fetch from nasa/fprime GitHub repo)
4. ProvesKit web crawl (fetch from docs.proveskit.space)

**Command-line usage:**
```bash
python run_with_approval.py 1  # Run option 1 directly
python run_with_approval.py 4  # Run option 4 directly
```

**Thread IDs:**
- Auto-generated for each run with format: `{task-type}-{uuid}`
- Saved to PostgreSQL checkpointer for resuming
- Check console output for thread ID

---

### `run_proveskit_incremental.py` - Incremental PROVES Kit Extraction

**Status:** ✅ NEW - For incremental documentation processing

**What it does:**
- Processes PROVES Kit documentation ONE PAGE AT A TIME
- Develops and records a comprehensive plan BEFORE extracting
- Saves progress for resuming in future sessions
- Same HITL verification workflow as run_with_approval.py
- Maintains all drift-prevention mechanisms (ONTOLOGY.md, FRAMES methodology)

**When to use:**
- Starting fresh extraction of PROVES Kit documentation
- When you want agent to develop an extraction plan first
- When processing large documentation incrementally
- When you need to return later to continue work

**How to run:**
```bash
cd curator-agent
python run_proveskit_incremental.py
```

**Workflow:**
1. Agent explores https://docs.proveskit.space/en/latest/
2. Agent develops a comprehensive plan (which pages, in what order)
3. Agent presents plan for your approval
4. You approve or modify the plan
5. Agent extracts from FIRST PAGE ONLY
6. Progress saved with thread ID
7. You return later to continue with next page

**Thread IDs:**
- Format: `proveskit-incremental-{uuid}`
- Displayed at start of session
- Use same thread ID to resume later

**Resuming a session:**
You'll need to modify the script to pass your saved thread_id:
```python
# In the script, change this line:
thread_id = f"proveskit-incremental-{uuid.uuid4().hex[:8]}"

# To this (with your actual thread ID):
thread_id = "proveskit-incremental-abc12345"
```

---

## Test Scripts

### `test_agent.py` - Basic Connectivity Test

**What it does:**
- Quick test to verify curator agent is working
- Tests basic graph invocation
- No database operations
- Minimal extraction

**When to use:**
- After installing dependencies
- After modifying agent code
- To verify environment is set up correctly

**How to run:**
```bash
cd curator-agent
python test_agent.py
```

---

### `test_simple_extraction.py` - Single Dependency Extraction Test

**What it does:**
- Tests extracting ONE specific dependency
- Uses local trial docs
- Tests full flow: extract → validate → stage
- Auto-approves HITL interrupts (test mode)

**When to use:**
- Testing changes to extraction logic
- Verifying staging tables work
- Quick validation of changes

**How to run:**
```bash
cd curator-agent
python test_simple_extraction.py
```

---

### `test_full_extraction.py` - Full Trial Document Extraction

**What it does:**
- Extracts from full trial document
- Tests complete extraction pipeline
- May produce multiple extractions
- Tests HITL approval workflow

**When to use:**
- Integration testing
- Verifying full pipeline works
- Before production runs

**How to run:**
```bash
cd curator-agent
python test_full_extraction.py
```

---

### `test_autonomous_exploration.py` - Autonomous Decision-Making Test

**What it does:**
- Tests agent's ability to decide what to do
- Agent explores available resources
- Agent chooses next steps autonomously
- Tests sub-agent coordination

**When to use:**
- Testing agent autonomy
- Verifying agent can explore and decide
- Testing sub-agent tools

**How to run:**
```bash
cd curator-agent
python test_autonomous_exploration.py
```

---

## Script Architecture

### Common Components (DO NOT MODIFY)

All scripts share these critical components:

1. **ONTOLOGY.md loading** - Prevents extraction drift
2. **HITL approval workflow** - Human verification gate
3. **PostgreSQL checkpointer** - State persistence
4. **Training data collection** - Corrections logged as GOLD data
5. **FRAMES methodology** - Components, Interfaces, Flows, Mechanisms

### What Makes Scripts Different

Scripts differ ONLY in their **task strings** - the instructions given to the curator agent.

**DO NOT:**
- Change the HITL approval logic
- Change the ontology loading mechanism
- Remove FRAMES methodology references
- Remove source citation requirements
- Remove "capture ALL" instructions

**DO:**
- Modify task strings to focus on different sources
- Add new extraction scenarios with new scripts
- Document new scripts in this guide

---

## Thread IDs and Resuming Work

### What are Thread IDs?

Thread IDs are unique identifiers for conversation sessions:
- Stored in PostgreSQL checkpointer tables
- Allow resuming interrupted work
- Preserve full conversation history

### Format

```
{task-type}-{random-hex}

Examples:
- test-a3f2b1c8
- proveskit-crawl-d4e8f2a1
- proveskit-incremental-9a7b3c2d
```

### How to Resume

**Method 1: Note the Thread ID from console output**
```
Session saved to thread: proveskit-incremental-9a7b3c2d
To resume: Use the same thread_id
```

**Method 2: Modify the script**
```python
# Find this line in the script:
thread_id = f"proveskit-incremental-{uuid.uuid4().hex[:8]}"

# Replace with your saved thread ID:
thread_id = "proveskit-incremental-9a7b3c2d"
```

**Method 3: Create a resume script** (future enhancement)

---

## Environment Requirements

All scripts require:

1. **Virtual environment activated:**
   ```bash
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Mac/Linux
   ```

2. **Environment variables in `../.env`:**
   ```bash
   ANTHROPIC_API_KEY=sk-ant-api03-...
   NEON_DATABASE_URL=postgresql://...
   ```

3. **Database schema initialized:**
   ```bash
   cd ..
   python scripts/apply_schema.py
   python scripts/setup_domain_tables.py
   python scripts/setup_checkpointer.py
   ```

---

## Common Issues

### "ModuleNotFoundError: No module named 'dotenv'"

**Solution:**
```bash
cd curator-agent
pip install -r ../requirements.txt
```

### "NEON_DATABASE_URL not set"

**Solution:**
Check `../.env` file exists and has:
```bash
NEON_DATABASE_URL=postgresql://...
```

### "Agent loops infinitely"

**Current known issue:**
- Stop conditions need tuning
- Interrupt the script with Ctrl+C
- Thread state is saved, you can resume

---

## Creating New Scripts

If you need a new script for a different use case:

1. **Copy `run_with_approval.py`** as your starting point
2. **Name it descriptively:** `run_{purpose}_{mode}.py`
3. **Modify ONLY the task string** - keep all other mechanisms
4. **Document it in this guide** with:
   - What it does
   - When to use it
   - How to run it
   - Thread ID format
5. **Test thoroughly** before production use
6. **DO NOT overwrite existing working scripts**

---

## Script Comparison Matrix

| Script | Use Case | Plan First? | Incremental? | Data Source | HITL? |
|--------|----------|-------------|--------------|-------------|-------|
| `run_with_approval.py` | General purpose | No | No | Configurable | Yes |
| `run_proveskit_incremental.py` | PROVES Kit docs | Yes | Yes | docs.proveskit.space | Yes |
| `test_agent.py` | Connectivity test | No | No | None | No |
| `test_simple_extraction.py` | Single extraction | No | No | Local file | Auto |
| `test_full_extraction.py` | Full pipeline test | No | No | Local file | Yes |
| `test_autonomous_exploration.py` | Autonomy test | No | No | Mixed | Yes |

---

## Future Enhancements

Planned improvements:

1. **Resume helper script** - Easy resuming with thread ID input
2. **F' Prime incremental script** - Like PROVES Kit but for F' Prime
3. **Progress tracking** - Show pages completed/remaining
4. **Plan validation** - Check plan against documentation structure
5. **Batch mode** - Process multiple pages with approval checkpoints

---

**Last Updated:** December 22, 2025
**Maintainer:** Human + AI pair programming
**Status:** Living document - update when adding new scripts
