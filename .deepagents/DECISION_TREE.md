# Which RAG Approach Should I Use?

A visual decision tree to help you choose between Sequential, Agentic, and Deep Agents RAG.

## The Decision Tree

```
START: What kind of task do you have?
│
├─❓ "Simple question-answering"
│  └─➡️ Use SEQUENTIAL RAG
│      Examples:
│      - "What is entity extraction?"
│      - "How does PROVES handle duplicates?"
│      - "List all supported entity types"
│
├─❓ "Questions with variable complexity"
│  │
│  ├─ Some questions don't need retrieval?
│  │  ├─ YES ─➡️ Use AGENTIC RAG
│  │  │          Examples:
│  │  │          - "Hello!" (no retrieval)
│  │  │          - "What are the benefits of F Prime?" (needs retrieval)
│  │  │          - "Thanks!" (no retrieval)
│  │  │
│  │  └─ NO ──➡️ Use SEQUENTIAL RAG
│  │             All questions need context
│  │
│  └─ Retrieval quality varies?
│     ├─ YES ─➡️ Use AGENTIC RAG
│     │          (Self-correction via rewriting)
│     │
│     └─ NO ──➡️ Use SEQUENTIAL RAG
│                (Consistent quality)
│
└─❓ "Complex multi-step research"
   │
   ├─ Need to break down into subtasks?
   │  └─ YES ─➡️ Use DEEP AGENTS RAG
   │             Examples:
   │             - "Compare three canonicalization approaches"
   │             - "Research and summarize F Prime architecture"
   │
   ├─ Need to manage large amounts of context?
   │  └─ YES ─➡️ Use DEEP AGENTS RAG
   │             (File system prevents overflow)
   │
   ├─ Need parallel investigation?
   │  └─ YES ─➡️ Use DEEP AGENTS RAG
   │             (Spawn subagents)
   │
   ├─ Need cross-session memory?
   │  └─ YES ─➡️ Use DEEP AGENTS RAG
   │             (Persistent memory)
   │
   └─ None of the above?
      └─➡️ Use AGENTIC RAG
           (Simpler than Deep Agents)
```

## Quick Reference Table

| Scenario | Approach | Reason |
|----------|----------|--------|
| **Q&A chatbot** | Agentic | Mixed question types |
| **Documentation search** | Sequential | Always needs docs |
| **Research assistant** | Deep Agents | Multi-step tasks |
| **FAQ system** | Sequential | Predictable queries |
| **Code explanation** | Agentic | Variable complexity |
| **Comparative analysis** | Deep Agents | Parallel research |
| **Simple lookup** | Sequential | Fast & straightforward |
| **Exploration task** | Deep Agents | Planning required |

## Complexity vs Capability

```
Sequential ─────────┬───────────> Simple to implement
                    │             Fast response
                    │             Predictable behavior
                    ↓
Agentic ────────────┬───────────> Adaptive retrieval
                    │             Self-correction
                    │             Dynamic routing
                    ↓
Deep Agents ────────┴───────────> Multi-step planning
                                  Context management
                                  Parallel investigation
                                  Cross-session memory
```

## Performance Characteristics

### Latency

```
Sequential:   [████░░░░░░] 1.8s  ⚡ FASTEST
Agentic:      [██████░░░░] 2-5s  ⚡ Variable
Deep Agents:  [██████████] 5-15s 🐌 SLOWEST
```

### Token Cost

```
Sequential:   [█████░░░░░] Medium     💰
Agentic:      [███░░░░░░░] Low-High   💰 Variable
Deep Agents:  [████████░░] High       💰💰💰
```

### Accuracy (on complex tasks)

```
Sequential:   [██████░░░░] 70%
Agentic:      [████████░░] 85%
Deep Agents:  [█████████░] 94%   ⭐ BEST
```

## When NOT to Use Each

### ❌ Don't Use Sequential If:
- Questions don't always need retrieval
- Retrieval quality is inconsistent
- Need self-correction
- Task requires planning

### ❌ Don't Use Agentic If:
- All questions are simple and predictable
- Task requires multi-step planning
- Need to manage very large context
- Need cross-session memory

### ❌ Don't Use Deep Agents If:
- Task is simple question-answering
- Low latency is critical
- Budget/token cost is constrained
- Team unfamiliar with agent patterns

## Migration Path

**Start Simple → Add Complexity as Needed**

```
Phase 1: Sequential RAG
   ↓ (Getting inconsistent results?)
Phase 2: Agentic RAG
   ↓ (Need multi-step research?)
Phase 3: Deep Agents RAG
```

You can always start with Sequential and upgrade later. The patterns are compatible!

## Real PROVES Library Use Cases

### ✅ Sequential RAG
- **Entity lookup**: "What is the entity type for Port?"
- **Quick checks**: "Does PROVES support F Prime?"
- **Simple queries**: "List all extraction sources"

### ✅ Agentic RAG
- **Mixed chatbot**: Users ask both simple and complex questions
- **MCP server**: Queries via Claude Desktop
- **Interactive sessions**: Conversation-style interactions

### ✅ Deep Agents RAG
- **Documentation research**: "Analyze F Prime documentation and extract all component types"
- **Comparative studies**: "Compare three approaches to entity canonicalization"
- **Pipeline development**: "Research verification workflow and propose improvements"

## Still Not Sure?

**Default Recommendations:**

- **Prototyping?** → Start with **Sequential**
- **Production chatbot?** → Use **Agentic**
- **Research tool?** → Use **Deep Agents**

**Budget-Constrained?** → Start with **Sequential** (lowest cost)
**Need Best Quality?** → Use **Deep Agents** (highest accuracy)
**Need Speed?** → Use **Sequential** (fastest)

## Try Them All!

The best way to decide is to run all three examples:

```bash
cd .deepagents/workflows

# Try each one
python sequential_rag_example.py
python agentic_rag_example.py
python deepagents_rag_example.py
```

Then compare the results and choose what fits your needs!

## References

- [workflows/COMPARISON.md](workflows/COMPARISON.md) - Detailed comparison
- [QUICKSTART.md](QUICKSTART.md) - Getting started guide
- [workflows/](workflows/) - Example implementations
