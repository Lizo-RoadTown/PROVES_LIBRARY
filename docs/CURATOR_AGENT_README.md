# Curator Agent - PROVES Library

## Overview

The Curator Agent is an autonomous LLM-powered agent that extracts dependencies from CubeSat documentation and builds the PROVES Library knowledge graph.

## What It Does

The agent autonomously:
1. **Extracts dependencies** from documentation using GPT-4o-mini
2. **Validates** against existing knowledge to avoid duplicates
3. **Stores** high-quality dependencies in the Neon PostgreSQL knowledge graph
4. **Explains reasoning** for all decisions

## Architecture

```
User Request
    ↓
Curator Agent (GPT-4o-mini)
    ↓
[Uses 5 Tools]
    ├─ search_dependencies → Query existing knowledge
    ├─ extract_from_document → LLM extraction from docs
    ├─ validate_dependency → Check for conflicts
    ├─ store_dependency → Save to knowledge graph
    └─ list_recent_entries → Monitor what's been added
    ↓
Neon PostgreSQL Knowledge Graph
    ↓
LangSmith Traces (full observability)
```

## Tools Available to Agent

### 1. `search_dependencies(component_name)`
Search for existing dependencies of a component.

**Example:**
```python
search_dependencies("ImuManager")
# Returns: "Found 3 dependencies: LinuxI2cDriver, PowerManager, ConfigFile"
```

### 2. `extract_from_document(doc_path)`
Extract dependencies from a documentation file using LLM.

**Example:**
```python
extract_from_document("trial_docs/fprime_i2c_driver_full.md")
# Returns: "Extracted 25 dependencies (HIGH=15, MEDIUM=8, LOW=2)"
```

### 3. `validate_dependency(source, target, relationship_type)`
Check if dependency exists or conflicts.

**Example:**
```python
validate_dependency("ImuManager", "LinuxI2cDriver", "depends_on")
# Returns: "[WARNING] Already exists" or "[OK] OK to add"
```

### 4. `store_dependency(source, target, relationship_type, description, criticality)`
Store a validated dependency in the knowledge graph.

**Example:**
```python
store_dependency(
    source_component="ImuManager",
    target_component="LinuxI2cDriver",
    relationship_type="depends_on",
    description="ImuManager requires I2C driver to communicate with IMU sensor",
    criticality="HIGH"
)
# Returns: "[OK] Stored: ImuManager --[depends_on]--> LinuxI2cDriver (criticality: HIGH)"
```

### 5. `list_recent_entries(limit=10)`
List recently added components and relationships.

**Example:**
```python
list_recent_entries(5)
# Returns: List of 5 most recent entries + graph statistics
```

## ERV Relationship Types

The agent chooses from 6 relationship types:

| Type | Description | Example |
|------|-------------|---------|
| **depends_on** | Runtime dependency | ImuManager depends_on LinuxI2cDriver |
| **requires** | Build/config requirement | I2C driver requires board config |
| **enables** | Makes something possible | Load switch enables sensor power |
| **conflicts_with** | Incompatible | Two devices conflict on same I2C address |
| **mitigates** | Reduces risk | Watchdog mitigates infinite loop risk |
| **causes** | Leads to effect | Power glitch causes sensor reset |

## Usage

### 1. Test Mode
Quick test to verify agent is working:
```bash
.venv\Scripts\python.exe scripts\curator_agent.py --test
```

### 2. Process a Document
Extract and store dependencies from a specific document:
```bash
.venv\Scripts\python.exe scripts\curator_agent.py --doc trial_docs\fprime_i2c_driver_full.md
```

The agent will:
- Capture ALL dependencies to staging
- Validate and flag anomalies
- Stage everything for human verification
- Provide summary of what was captured

### 3. Interactive Mode
Chat with the agent:
```bash
.venv\Scripts\python.exe scripts\curator_agent.py --interactive
```

**Example conversation:**
```
You: Search for dependencies of ImuManager

Curator: Found 3 dependencies for 'ImuManager':
  - depends_on → LinuxI2cDriver
  - requires → ConfigFile
  - enables → SensorReadings

You: Extract from trial_docs/fprime_i2c_driver_full.md

Curator: [Calls extract_from_document tool]
Extracted 25 dependencies from 'fprime_i2c_driver_full.md'...

You: Stage these for human review

Curator: [Validates and stages all dependencies]
Staged 15 dependencies for human verification. All data awaits review.
```

## Environment Requirements

### API Keys Needed

In `.env` file:
```bash
# Database
NEON_DATABASE_URL=postgresql://...

# OpenAI (for GPT-4o-mini extraction)
OPENAI_API_KEY=sk-...

# LangSmith (for tracing)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_sk_...
LANGSMITH_PROJECT=pr-prickly-dollop-66
LANGSMITH_WORKSPACE_ID=...  # Get from https://smith.langchain.com/settings
```

## Observability with LangSmith

Every agent run is fully traced in LangSmith:

```
Curator Agent Session
├─ User request
├─ Agent reasoning (LLM call 1)
├─ Tool: extract_from_document
│   └─ Nested trace: dependency_extractor
│       ├─ Chunk document
│       ├─ Extract from chunk (LLM call)
│       └─ Merge dependencies
├─ Agent reasoning (LLM call 2)
├─ Tool: validate_dependency
├─ Agent reasoning (LLM call 3)
├─ Tool: store_dependency
│   └─ Database INSERT
└─ Final response
```

View traces at: https://smith.langchain.com (PROVES_Library project)

## Example Agent Workflow

**User Request:** "Process the F´ I2C driver documentation"

**Agent Execution:**
1. Calls `extract_from_document("trial_docs/fprime_i2c_driver_full.md")`
   - Captures ALL 25 dependencies with context
   - Categorizes and adds lineage metadata
2. For each dependency:
   - Calls `validate_dependency(source, target, type)`
   - Flags anomalies, checks patterns
   - Stages to `staging_extractions`
3. Returns summary:
   - "Staged 25 dependencies for human verification"
   - "Flagged 3 with anomalies for review"
   - "Full trace in LangSmith"

## Troubleshooting

### OpenAI Quota Exceeded
```
Error: 429 - insufficient_quota
```

**Solution:** Add credits at https://platform.openai.com/settings/organization/billing

### LangSmith Workspace Error
```
Error: This API key is org-scoped and requires workspace specification
```

**Solution:** Add to `.env`:
```bash
LANGSMITH_WORKSPACE_ID=<your-workspace-id>
```

Get it from https://smith.langchain.com/settings

### Database Connection Error
```
Error: Failed to connect to database
```

**Solution:** Check `NEON_DATABASE_URL` in `.env` file

## Files

| File | Purpose |
|------|---------|
| [curator_agent.py](../scripts/curator_agent.py) | Main agent implementation |
| [dependency_extractor.py](../scripts/dependency_extractor.py) | LLM-powered extraction |
| [graph_manager.py](../scripts/graph_manager.py) | Database CRUD operations |
| [.env](../.env) | API keys and configuration |

## Next Steps

1. **Add OpenAI Credits** - Agent needs GPT-4o-mini access
2. **Get LangSmith Workspace ID** - Enable full tracing
3. **Test on Trial Docs** - Process F´ and PROVES Kit documentation
4. **Compare to Manual Analysis** - Validate automated extraction quality
5. **Refine Prompts** - Improve extraction accuracy based on results
6. **Scale to Full Corpus** - Process all F´ and PROVES Kit docs

## Design Decisions

### Why GPT-4o-mini?
- Cost-effective for large-scale extraction
- Fast enough for interactive use
- Sufficient accuracy for dependency extraction
- Can process 1000+ pages for < $1

### Why LangGraph?
- Native support for tool calling
- Built-in retries and error handling
- Streaming support for long-running tasks
- Full LangSmith integration

### Why 5 Tools?
Each tool has a specific purpose:
- **search** = understand existing knowledge
- **extract** = get new knowledge from docs
- **validate** = ensure quality
- **store** = persist to database
- **list** = monitor progress

This separation allows the agent to reason about each step independently.

## Future Enhancements

1. **Multi-document extraction** - Cross-reference between F´ and PROVES Kit
2. **Knowledge gap detection** - Identify undocumented dependencies
3. **Team boundary analysis** - Map dependencies to organizational structure
4. **Cascade path finder** - Trace transitive dependency chains
5. **Risk scoring** - Flag high-risk dependencies automatically

---

**Status:** Built, ready to test once OpenAI quota is added

**Last Updated:** 2024-12-20
