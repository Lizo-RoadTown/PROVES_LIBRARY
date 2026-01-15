# Deep Agents Integration with PROVES Library

This document explains how the deepagents framework is integrated into the PROVES Library for knowledge extraction.

## Overview

PROVES Library uses **Deep Agents** for its multi-step knowledge extraction pipeline because:

1. **Complex Documentation Analysis** - Breaking down technical docs requires planning
2. **Large Context Management** - Satellite system docs are extensive, need file system
3. **Parallel Extraction** - Can spawn subagents for different documentation sections
4. **Quality Verification** - Multi-step workflow: extract → verify → stage → approve

## Installation

The deepagents package is installed from your forked repository:

```bash
# Already done during setup
pip install -e deepagents-repo/libs/deepagents/
```

## Integration Points

### 1. Main Extraction Agent

**File:** [production/core/deep_extraction_agent.py](../production/core/deep_extraction_agent.py)

This is the primary deep agent that handles knowledge extraction from documentation.

**Capabilities:**
- Planning with TodoList middleware
- File system for managing large docs
- Custom tools for database interaction
- Subagent delegation for parallel extraction

**Usage:**
```python
from production.core.deep_extraction_agent import create_proves_extraction_agent

# Create agent
agent = create_proves_extraction_agent()

# Extract from URL
result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Extract knowledge from https://nasa.github.io/fprime/..."
    }]
})
```

### 2. Custom Tools

PROVES provides domain-specific tools to the agent:

**Database Tools:**
- `query_staging_extractions` - Search existing extractions
- `insert_staging_extraction` - Add new extraction to staging table

**Documentation Tools:**
- `fetch_documentation` - Retrieve documentation content

**Built-in DeepAgents Tools:**
- `write_todos` - Create extraction plan
- `update_todos` - Track progress
- `read_file`, `write_file`, `edit_file` - Manage extraction context
- `task` - Spawn subagents for parallel work

### 3. Extraction Workflow

```
User Request
    ↓
Deep Agent (Planning)
    ↓
write_todos([
    "Fetch documentation",
    "Extract components",
    "Extract interfaces",
    "Extract dependencies",
    "Quality check"
])
    ↓
For each todo:
    ├─→ fetch_documentation(url)
    ├─→ write_file("extraction.md", content)
    ├─→ task("Extract components", tools=[...])
    └─→ update_todos(completed)
    ↓
insert_staging_extraction({...})
    ↓
Return summary
```

## Configuration

### System Prompt

The extraction agent uses a specialized system prompt that defines:

- **FRAMES methodology** (Components, Interfaces, Flows, Dependencies)
- **5-attribute edge model** (Directionality, Strength, Mechanism, Knownness, Scope)
- **Quality requirements** (Source refs, confidence scores, context)
- **Workflow steps** (Planning → Extraction → QA → Output)

See `EXTRACTION_SYSTEM_PROMPT` in [deep_extraction_agent.py](../production/core/deep_extraction_agent.py)

### Model Configuration

Default model: `claude-sonnet-4-5-20250929`

Can be customized:
```python
agent = create_proves_extraction_agent(
    model_name="openai:gpt-4o",  # Or any LangChain model
    enable_subagents=True,
    enable_memory=True,
)
```

## Comparison with Previous Approach

| Aspect | Old Approach | Deep Agents |
|--------|-------------|-------------|
| **Planning** | Manual script logic | AI-driven TodoList |
| **Context** | In-memory strings | File system management |
| **Parallelization** | Sequential only | Subagent delegation |
| **Adaptability** | Fixed pipeline | Dynamic workflow |
| **Error Handling** | Try-catch | Self-correction via planning |

## Production Scripts

### Current Integration Status

✅ **Deep agent created** - [production/core/deep_extraction_agent.py](../production/core/deep_extraction_agent.py)
🚧 **Script integration** - Need to update `process_extractions.py` to use deep agent
📋 **Database tools** - Need to implement actual DB queries (currently placeholders)

### Next Steps

1. **Implement Database Tools**:
   ```python
   # production/core/db_tools.py
   def query_staging_extractions(query: str):
       conn = get_db()
       results = conn.fetch_all(
           "SELECT * FROM staging_extractions WHERE candidate_key LIKE %s",
           (f"%{query}%",)
       )
       return results
   ```

2. **Update process_extractions.py**:
   ```python
   # production/scripts/process_extractions.py
   from production.core.deep_extraction_agent import batch_extract_from_queue

   results = batch_extract_from_queue(limit=args.limit)
   ```

3. **Add Verification Workflow**:
   - Extract → Staging → Notion (existing)
   - Deep agent tracks todos for verification status
   - Auto-promotes verified extractions

## Testing

### Unit Tests

```bash
# Test the agent creation
python production/core/deep_extraction_agent.py
```

### Integration Tests

```bash
# Process single URL (when DB tools implemented)
python -c "
from production.core.deep_extraction_agent import extract_from_url
result = extract_from_url('https://nasa.github.io/fprime/...')
print(result)
"
```

### Full Pipeline Test

```bash
# Run extraction pipeline with deep agents
python production/scripts/process_extractions.py --limit 5 --use-deep-agents
```

## Monitoring & Debugging

### LangSmith Tracing

Deep agents automatically integrate with LangSmith (if configured in `.env`):

```bash
# .env
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=your_key_here
LANGSMITH_PROJECT=PROVES_Library
```

View agent execution traces at: https://smith.langchain.com

### Local Debugging

The agent saves intermediate files to the workspace:
- Extraction plans → `extraction_plan.md`
- Documentation chunks → `doc_chunk_*.md`
- Results → `extraction_results.json`

## Best Practices

### 1. Planning First

Always let the agent create a todo list before extraction:
```python
result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "First create a plan for extracting from this URL, then execute it: ..."
    }]
})
```

### 2. File System for Large Docs

For documentation > 10KB, tell agent to use files:
```python
content = "Please save this documentation to a file before extracting: ..."
```

### 3. Conservative Confidence Scores

System prompt enforces < 0.5 for assumptions, but remind in prompts:
```python
content = "Extract with conservative confidence scores (< 0.5 unless verified)"
```

### 4. Batch Processing

Reuse agent instance for multiple URLs:
```python
agent = create_proves_extraction_agent()

for url in urls:
    result = extract_from_url(url, agent=agent)
    # Agent maintains memory across extractions
```

## Troubleshooting

### "Tool not found" errors

Make sure custom tools are passed to `create_deep_agent`:
```python
agent = create_deep_agent(tools=[query_staging, insert_staging, ...])
```

### Memory issues with large docs

Agent should automatically use file system, but can force it:
```python
content = "This is a large document. Save it to 'large_doc.md' before processing."
```

### Subagent errors

Check that subagent has access to necessary tools:
```python
# Subagents inherit tools by default, but can customize
agent = create_deep_agent(
    tools=custom_tools,
    # Subagent gets same tools
)
```

## Resources

- **[DeepAgents Repo](../deepagents-repo/)** - Your forked repository
- **[Official Docs](https://docs.langchain.com/oss/python/deepagents/overview)** - LangChain documentation
- **[Quickstarts](https://github.com/langchain-ai/deepagents-quickstarts)** - Example implementations
- **[PROVES Extraction Agent](../production/core/deep_extraction_agent.py)** - Main implementation
- **[Workflow Examples](workflows/)** - Three RAG approaches compared

## Contributing

When enhancing the deep agent:

1. Update system prompt in `deep_extraction_agent.py`
2. Add custom tools as decorated functions
3. Test with sample documentation
4. Update this integration guide
5. Commit changes to both PROVES_LIBRARY and deepagents fork if needed

---

**Status**: ✅ Agent created | 🚧 Database tools pending | 📋 Script integration pending
