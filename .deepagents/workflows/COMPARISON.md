# RAG Workflow Comparison

This document compares THREE different approaches to building RAG (Retrieval-Augmented Generation) systems using LangGraph and Deep Agents.

## Files to Compare

1. **[sequential_rag_example.py](sequential_rag_example.py)** - Sequential/Linear approach
2. **[agentic_rag_example.py](agentic_rag_example.py)** - Agentic/Reactive approach
3. **[deepagents_rag_example.py](deepagents_rag_example.py)** - Deep Agents approach

## Visual Comparison

### 1. Sequential RAG Flow
```
START
  ↓
retrieve (always)
  ↓
prepare_context
  ↓
generate_answer
  ↓
END
```

### 2. Agentic RAG Flow
```
START
  ↓
generate_query_or_respond  ← (rewrite if needed)
  ↓ (decide)              ↑
  ├─→ retrieve ──→ grade ─┤
  │                ↓
  │           generate_answer
  │                ↓
  └─→ END ←────────┘
```

### 3. Deep Agents RAG Flow
```
START
  ↓
plan (write_todos)
  ↓
for each todo:
  ├─→ retrieve
  ├─→ write_file (save context)
  ├─→ task (spawn subagent)
  └─→ update_todos
  ↓
synthesize from files
  ↓
END
```

## Key Differences

| Aspect | Sequential | Agentic | Deep Agents |
|--------|------------|---------|-------------|
| **Complexity** | Low ⭐ | Medium ⭐⭐ | High ⭐⭐⭐ |
| **Decision Making** | None (fixed) | Conditional routing | Planning + routing |
| **State Type** | Custom `RAGState` | `MessagesState` | `MessagesState` + Files |
| **Control Flow** | Linear | Conditional edges | Dynamic + iterative |
| **Self-Correction** | None | Question rewriting | Planning updates |
| **Context Mgmt** | In-memory | In-memory | File system |
| **Parallelization** | None | None | Subagents |
| **Memory** | None | None | Cross-session |
| **Latency** | Fast (1.8s) | Variable (2-5s) | Slow (5-15s) |
| **Token Cost** | Medium | Low-High | High |
| **Best For** | Simple Q&A | Adaptive retrieval | Complex research |

## Code Comparison

### 1. State Definition

**Agentic:**
```python
from langgraph.graph import MessagesState

# Uses built-in MessagesState
# State is a list of chat messages
```

**Sequential:**
```python
class RAGState(BaseModel):
    question: str
    retrieved_docs: List[str]
    context: str
    answer: str
    metadata: dict
```

### 2. Graph Construction

**Agentic:**
```python
# Conditional edges based on LLM decisions
workflow.add_conditional_edges(
    "generate_query_or_respond",
    tools_condition,  # LLM decides: retrieve or respond
    {"tools": "retrieve", END: END}
)

workflow.add_conditional_edges(
    "retrieve",
    grade_documents,  # Grade: relevant or irrelevant
)
```

**Sequential:**
```python
# Simple linear edges
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "prepare_context")
workflow.add_edge("prepare_context", "generate_answer")
workflow.add_edge("generate_answer", END)
```

### 3. Tool Usage

**Agentic:**
```python
# LLM decides to use tool via .bind_tools()
response_model.bind_tools([retriever_tool]).invoke(state["messages"])
```

**Sequential:**
```python
# Direct function call - no tool binding
docs = retrieve_documents(state.question, k=4)
```

## When to Use Each Approach

### Use **Agentic RAG** when:

✅ Questions vary widely (some need context, some don't)
✅ Retrieval quality is unpredictable
✅ You want self-correction capabilities
✅ Token efficiency matters (skip unnecessary retrievals)
✅ You need sophisticated, adaptive behavior
✅ Debugging tools are available (LangSmith tracing)

**Example Use Cases:**
- Chatbots with mixed question types
- Systems with varying document quality
- Production systems with LangSmith monitoring
- Complex domain where retrieval may fail

### Use **Sequential RAG** when:

✅ All questions require retrieved context
✅ Retrieval quality is consistently good
✅ Simpler code/debugging is priority
✅ Lower latency is critical
✅ Predictable behavior is required
✅ Team is less familiar with agentic patterns

**Example Use Cases:**
- Q&A over well-structured documentation
- Search-based applications
- Internal knowledge bases
- Prototyping and MVPs

## Hybrid Approach

You can also combine both approaches:

```python
def create_hybrid_rag():
    """
    Use sequential for simple queries,
    agentic for complex ones
    """
    workflow = StateGraph(MessagesState)

    # Route based on query complexity
    workflow.add_conditional_edges(
        START,
        classify_query_complexity,
        {
            "simple": "sequential_pipeline",
            "complex": "agentic_pipeline"
        }
    )

    return workflow.compile()
```

## Performance Benchmarks

Based on typical usage patterns:

| Metric | Agentic | Sequential |
|--------|---------|------------|
| Avg Latency (simple Q) | 2.3s | 1.8s |
| Avg Latency (complex Q) | 5.1s | 1.8s |
| Token Cost (simple Q) | 60% lower | baseline |
| Token Cost (complex Q) | 20% higher | baseline |
| Success Rate | 94% | 87% |
| Code Lines | ~250 | ~150 |

*Note: Benchmarks are illustrative. Actual performance depends on your specific use case.*

## PROVES Library Recommendation

For the PROVES Library extraction pipeline, consider:

1. **Extraction Tasks** → **Sequential RAG**
   - Documents are always needed for extraction
   - Predictable, well-structured input
   - Debugging simplicity is valuable

2. **Q&A Interface** → **Agentic RAG**
   - Users ask varied questions
   - Some questions don't need retrieval
   - Self-correction improves accuracy

3. **Verification Workflow** → **Hybrid**
   - Simple cases use sequential path
   - Complex/ambiguous cases use agentic path

## Next Steps

1. **Test both approaches** with your actual PROVES data
2. **Measure performance** using LangSmith
3. **Choose based on** your specific requirements
4. **Iterate** - you can always switch or combine approaches

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Agentic RAG Tutorial](https://docs.langchain.com/docs/langgraph/tutorials/agentic-rag)
- [PROVES Library Production Scripts](../../production/scripts/)
