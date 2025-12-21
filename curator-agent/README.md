# PROVES Library Curator Agent

**A Deep Agent system for autonomous dependency extraction and knowledge graph curation**

## What is This?

This is a **Deep Agent** - a LangGraph application that:
- ✅ **Spawns specialized sub-agents** (Extractor, Validator, Storage)
- ✅ **Coordinates multi-step workflows** autonomously
- ✅ **Enables human-in-the-loop** via LangSmith Studio
- ✅ **Traces everything** to LangSmith for full observability

## Architecture

```
Main Curator Agent
    ↓ spawns as tools
    ├─ Extractor Sub-Agent (extracts dependencies from docs)
    ├─ Validator Sub-Agent (validates against knowledge graph)
    └─ Storage Sub-Agent (stores in Neon PostgreSQL)
```

### Sub-Agents

Each sub-agent is a **specialized agent** with its own tools:

#### 1. Extractor Agent
**Tools:**
- `chunk_document` - Read and chunk documentation
- `extract_dependencies_from_text` - LLM extraction

**Specializes in:**
- Processing documentation files
- Identifying ERV relationship types
- Assessing criticality levels

#### 2. Validator Agent
**Tools:**
- `check_if_dependency_exists` - Check for duplicates
- `verify_schema_compliance` - Validate ERV schema
- `search_similar_dependencies` - Find related components

**Specializes in:**
- Duplicate detection
- Schema validation
- Conflict detection

#### 3. Storage Agent
**Tools:**
- `create_or_get_node` - Create nodes
- `store_dependency_relationship` - Store relationships
- `get_graph_statistics` - Graph stats

**Specializes in:**
- Database operations
- Transaction management
- Data integrity

## Setup

### 1. Install Dependencies

From the `curator-agent` directory:

```bash
cd curator-agent
pip install -e .
```

### 2. Configure Environment

The agent uses the parent `.env` file (configured in `langgraph.json`).

Required variables:
```bash
# In ../. env
ANTHROPIC_API_KEY=sk-ant-...
LANGSMITH_API_KEY=lsv2_sk_...
LANGSMITH_PROJECT=pr-prickly-dollop-66
LANGSMITH_WORKSPACE_ID=...  # Get from https://smith.langchain.com/settings
NEON_DATABASE_URL=postgresql://...
```

### 3. Deploy to LangSmith Cloud

```bash
# From curator-agent directory
langgraph deploy
```

Or run locally:

```bash
langgraph dev
```

This starts the Agent Server and opens:
- **API**: http://localhost:2024
- **Studio UI**: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024

## Usage

### Via Studio UI (Recommended - Human-in-the-Loop!)

1. Start the agent:
   ```bash
   langgraph dev
   ```

2. Open Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024

3. Send a message:
   ```
   Extract dependencies from ../trial_docs/fprime_i2c_driver_full.md
   and store HIGH criticality ones
   ```

4. **Watch the agent work:**
   - See it spawn the Extractor sub-agent
   - See validation checks happen
   - See storage operations
   - **Pause and intervene** at any point!

### Via Python SDK

```python
from langgraph_sdk import get_client

client = get_client(url="http://localhost:2024")

# Start a thread
thread = client.threads.create()

# Send a message
for chunk in client.runs.stream(
    thread["thread_id"],
    "curator",  # Assistant ID from langgraph.json
    input={
        "messages": [{
            "role": "user",
            "content": "Extract dependencies from ../trial_docs/fprime_i2c_driver_full.md"
        }]
    },
):
    print(chunk.data)
```

### Via REST API

```bash
curl -X POST "http://localhost:2024/runs/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "curator",
    "input": {
      "messages": [{
        "role": "user",
        "content": "Extract dependencies from ../trial_docs/fprime_i2c_driver_full.md"
      }]
    }
  }'
```

## How It Works

### Workflow Example

**User Request:** "Process the F´ I2C driver documentation"

**Curator Agent Execution:**

1. **Spawns Extractor Sub-Agent**
   ```
   Curator → extractor_agent("Extract from fprime_i2c_driver.md")
     → Extractor uses chunk_document tool
     → Extractor uses extract_dependencies_from_text
     → Returns: "Found 25 dependencies (15 HIGH, 8 MEDIUM, 2 LOW)"
   ```

2. **Spawns Validator Sub-Agent** (for each HIGH dependency)
   ```
   Curator → validator_agent("Check if ImuManager depends_on LinuxI2cDriver exists")
     → Validator uses check_if_dependency_exists
     → Returns: "[OK] Safe to add"
   ```

3. **Spawns Storage Sub-Agent** (for validated dependencies)
   ```
   Curator → storage_agent("Store: ImuManager depends_on LinuxI2cDriver (HIGH)")
     → Storage uses store_dependency_relationship
     → Returns: "[STORED] ImuManager --[depends_on]--> LinuxI2cDriver (ID: ...)"
   ```

4. **Returns Summary**
   ```
   Curator → User: "Stored 15 HIGH criticality dependencies from F´ I2C driver"
   ```

### LangSmith Tracing

Every step is traced in LangSmith:

```
Curator Agent Session
├─ User message: "Process F´ I2C driver docs"
├─ Curator reasoning (LLM call 1)
├─ Tool call: extractor_agent(...)
│   └─ Extractor Sub-Agent Session
│       ├─ Tool: chunk_document
│       ├─ Tool: extract_dependencies_from_text
│       └─ Returns results
├─ Curator reasoning (LLM call 2)
├─ Tool call: validator_agent(...)
│   └─ Validator Sub-Agent Session
│       ├─ Tool: check_if_dependency_exists
│       └─ Returns: [OK]
├─ Curator reasoning (LLM call 3)
├─ Tool call: storage_agent(...)
│   └─ Storage Sub-Agent Session
│       ├─ Tool: store_dependency_relationship
│       └─ Returns: [STORED]
└─ Final response to user
```

**View in LangSmith Studio:** Full visualization with ability to pause, inspect, and modify!

## Why This Architecture?

### Deep Agents Pattern

**Sub-agents as tools** (from LangChain docs):
- Main agent coordinates specialized workers
- Each sub-agent is stateless (main agent maintains state)
- Context isolation prevents bloat
- Enables complex multi-step workflows

### Human-in-the-Loop

LangSmith Studio lets you:
- **Watch** agents work in real-time
- **Pause** execution at any point
- **Inspect** sub-agent reasoning
- **Modify** inputs before continuing
- **Approve/reject** actions

### Full Observability

Every agent action is traced:
- Which sub-agent was called
- What tools it used
- What it returned
- How long it took
- Any errors or issues

## Files Structure

```
curator-agent/
├── langgraph.json          # LangGraph config
├── pyproject.toml          # Python dependencies
├── README.md               # This file
└── src/curator/
    ├── __init__.py
    ├── agent.py            # Main curator agent
    └── subagents/
        ├── __init__.py
        ├── extractor.py    # Extractor sub-agent
        ├── validator.py    # Validator sub-agent
        └── storage.py      # Storage sub-agent
```

## Next Steps

1. **Add ANTHROPIC_API_KEY** to `../.env`
2. **Add LANGSMITH_WORKSPACE_ID** to `../.env`
3. **Test locally:** `langgraph dev`
4. **Open Studio UI** and watch it work!
5. **Deploy to Cloud:** `langgraph deploy` (when ready)

## Comparison to Old Approach

| Feature | Old (standalone script) | New (Deep Agent) |
|---------|------------------------|------------------|
| Architecture | Single agent | Main + 3 sub-agents |
| Deployment | Manual `python script.py` | LangGraph application |
| Observability | Basic LangSmith | Full multi-agent tracing |
| Human-in-the-loop | None | Studio UI with pause/inspect |
| Scalability | Limited | Can add more sub-agents |
| API | None | REST/SDK/Streaming |
| Studio UI | ❌ No | ✅ Yes |

## Documentation

- [LangGraph Docs](https://docs.langchain.com/langgraph)
- [Deep Agents Guide](https://docs.langchain.com/oss/python/deepagents/overview.md)
- [Sub-agents Pattern](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents.md)
- [LangSmith Studio](https://smith.langchain.com/studio)

---

**Built with:** LangGraph, Claude Sonnet 4.5, LangSmith
**Architecture:** Deep Agents with Sub-agent Coordination
**Deployment:** LangSmith Cloud/Hybrid/Self-hosted
