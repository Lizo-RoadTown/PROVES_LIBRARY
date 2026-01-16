# Deep Agents Quick Start Guide

Get started with the `.deepagents` folder and understand the three RAG approaches.

## Structure

```
.deepagents/
├── agents/                    # Agent configurations
│   └── extraction_agent.yaml  # Example extraction agent config
├── workflows/                 # Workflow implementations
│   ├── sequential_rag_example.py    # Simple linear pipeline
│   ├── agentic_rag_example.py       # Conditional routing
│   ├── deepagents_rag_example.py    # Full deep agents
│   └── COMPARISON.md                # Side-by-side comparison
├── tools/                     # Custom tools (empty - add yours)
├── prompts/                   # Prompt templates (empty - add yours)
└── README.md                  # Overview documentation
```

## Quick Decision Tree

**Choose your approach:**

```
Is your task simple Q&A?
├─ YES → Use Sequential RAG
└─ NO → Does it need self-correction?
    ├─ YES → Is it multi-step research?
    │   ├─ YES → Use Deep Agents RAG
    │   └─ NO → Use Agentic RAG
    └─ NO → Use Sequential RAG
```

## Running the Examples

### 1. Sequential RAG (Simplest)

```bash
cd .deepagents/workflows
python sequential_rag_example.py
```

**When to use:** Simple retrieval, always need docs, want fast/predictable behavior.

**Output:** Linear pipeline with fixed steps.

### 2. Agentic RAG (Adaptive)

```bash
python agentic_rag_example.py
```

**When to use:** Variable questions, some don't need retrieval, want self-correction.

**Output:** Shows conditional routing and document grading.

### 3. Deep Agents RAG (Advanced)

```bash
python deepagents_rag_example.py
```

**When to use:** Complex research, need planning, manage large context, parallel subtasks.

**Output:** Shows planning, file management, subagent spawning.

## Customization

### Add Your Own Tools

Create tools in `.deepagents/tools/`:

```python
# .deepagents/tools/proves_tools.py
from langchain.tools import tool

@tool
def query_vectorstore(query: str) -> str:
    """Query the PROVES Library vectorstore."""
    from production.core.db import get_vectorstore
    vectorstore = get_vectorstore()
    docs = vectorstore.similarity_search(query, k=4)
    return "\n\n".join([doc.page_content for doc in docs])
```

Then import in your workflow:

```python
from deepagents.tools.proves_tools import query_vectorstore

agent = create_deep_agent(
    model=model,
    tools=[query_vectorstore],
    # ... other config
)
```

### Add Prompt Templates

Create prompts in `.deepagents/prompts/`:

```python
# .deepagents/prompts/extraction_prompts.py

EXTRACTION_SYSTEM_PROMPT = """
You are an extraction specialist for the PROVES Library...
"""

GRADING_PROMPT = """
Grade the following extraction for quality...
"""
```

### Create Agent Configs

Add YAML configs in `.deepagents/agents/`:

```yaml
# .deepagents/agents/verification_agent.yaml
name: verification_agent
description: "Verifies extracted knowledge quality"

model:
  provider: anthropic
  model_name: claude-sonnet-4.5

tools:
  - query_vectorstore
  - check_extraction_quality

workflow:
  type: sequential
```

## Integration with PROVES Library

### Use in Production Scripts

```python
# production/scripts/smart_extraction.py
from deepagents.workflows.deepagents_rag_example import create_proves_deep_agent

agent = create_proves_deep_agent()

result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Extract all entity types from F Prime documentation"
    }]
})
```

### Use in MCP Server

```python
# mcp-server/src/proves_mcp/server.py
from deepagents.workflows.agentic_rag_example import create_agentic_rag_graph

rag_graph = create_agentic_rag_graph()

@server.call_tool()
async def research_docs(query: str) -> str:
    result = rag_graph.invoke({"messages": [{"role": "user", "content": query}]})
    return result["messages"][-1].content
```

## Next Steps

1. **Read [COMPARISON.md](workflows/COMPARISON.md)** - Understand all three approaches
2. **Run all three examples** - See them in action
3. **Choose an approach** - Pick what fits your use case
4. **Customize** - Add your tools, prompts, and configs
5. **Deploy** - Integrate with PROVES production scripts

## Resources

- [Deep Agents Documentation](https://docs.langchain.com/docs/deepagents/)
- [LangGraph Tutorial](https://docs.langchain.com/docs/langgraph/tutorials/agentic-rag)
- [PROVES Production Scripts](../../production/scripts/)
- [PROVES MCP Server](../../mcp-server/)

## Troubleshooting

**Import errors?**
```bash
# Make sure you're in the project root
cd c:\Users\Liz\PROVES_LIBRARY
export PYTHONPATH=$PYTHONPATH:.
```

**Database connection issues?**
```bash
# Check .env file
cat .env | grep DATABASE_URL
```

**Torch/PyTorch errors?**
- Install Visual C++ Redistributable (should be done from setup)
- Restart terminal after installation

## Questions?

Check the main [README.md](../README.md) or open an issue in the repository.
