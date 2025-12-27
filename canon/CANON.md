# CANON - Permanent Knowledge Repository

> **Purpose:** This file preserves critical lessons, design principles, and ontology that must NEVER be lost during documentation updates, refactoring, or agent handoffs. Treat this as institutional memory.

**Last Updated:** December 2025  
**Status:** Living Document

---

## 1. Core Design Principles

### 1.1 Autonomous Intelligence, Not Automation

> "Give goals, not instructions."

The curator agent is designed to be **intelligent**, not just automated. The difference:

| Automation | Intelligence |
|------------|-------------|
| Follow script exactly | Understand goal, decide approach |
| Fail if unexpected input | Adapt to new situations |
| Do what you said | Do what you meant |
| No learning | Gets smarter over time |

**Pattern:** Provide rich context and clear goals -> Let the agent decide HOW to achieve them.

### 1.2 Truth Layer Architecture

> "Agents provide context. Humans establish truth."

**Critical Design Decision:** The system has distinct layers:

1. **Capture Layer (Agents):** Grab ALL raw data, categorize it, add lineage/source
2. **Staging Layer (Agents):** Validate, flag anomalies, prepare for human review
3. **Truth Layer (Human):** Human verifies EACH piece, aligns across sources
4. **Graph Layer:** Only human-verified data enters the knowledge graph

**Why This Matters:**
- Sources won't match in language - that's expected
- Humans align disparate sources into unified truth
- Human-aligned layers create clean matrix for GNN
- Context is EVERYTHING - agents provide it, humans verify it

**The Flow:**
```
Raw Sources -> Agent Capture -> Agent Staging -> Human Verification -> Truth Graph
     ↑              ↑               ↑                ↑
  (all data)   (categorize)    (flag/context)   (align/verify)
```

### 1.3 Four Pillars of Trustworthy AI Agents

1. **Rich Context** - Domain knowledge + examples -> Better decisions
2. **Clear Goals** - Well-defined objectives -> Focused execution
3. **Transparency** - Show all reasoning -> Human can verify
4. **Human Oversight** - Approve before executing -> Safety guaranteed

---

## 2. FRAMES Ontology (Foundational)

> **Source:** "FRAMES: A Structural Diagnostic for Resilience in Modular University Space Programs" (Osborn, 2025)
>
> **Implementation:** [ONTOLOGY.md](ONTOLOGY.md) - Loaded into EVERY extraction prompt to prevent drift

### 2.1 What Agents Extract vs. What Humans Decide

| Concept | Who Does It | What It Means |
|---------|-------------|---------------|
| **Components** | Agent captures | The discrete modules in a system (drivers, sensors, boards) |
| **Interfaces** | Agent captures | WHERE components connect (ports, buses, protocols) |
| **Flows** | Agent captures | WHAT moves through interfaces (data, signals, power, commands) |
| **Mechanisms** | Agent captures | What maintains the interface (documentation, protocols, schemas) |
| **Criticality** | Human assigns | Mission impact - how bad if this fails? |
| **Alignment** | Human verifies | Do sources agree? Resolve conflicts. |

### 2.2 FRAMES Core Vocabulary

**From FRAMES research:**

> "Interface mechanisms are the specific roles, processes, and tools that maintain connections at an interface and prevent them from degrading."

| FRAMES Term | Definition | Agent Task |
|-------------|------------|------------|
| **Module** | Semi-autonomous unit (team, component, subsystem) | Capture as `Component` |
| **Interface** | Connection point where modules touch | Capture as `Interface` |
| **Coupling** | Strength of bond (strong internal, weak external) | Note as `coupling_strength` |
| **Interface Mechanism** | What maintains the connection | Capture as `Mechanism` |
| **Flow** | What moves through an interface | Capture as `Flow` |

### 2.3 The Fundamental Question

> "What MOVES through this system, and through which interfaces?"

**NOT:** "What depends on what and how critical is it?"

Human judgment assigns criticality AFTER understanding:
- What components exist
- What interfaces connect them  
- What moves through those interfaces
- What happens when that movement stops

### 2.4 Example: Correct vs. Incorrect Extraction

**[NO] OLD (Wrong - agent making judgments):**
> "I2C Driver DEPENDS ON Temperature Sensor - HIGH criticality"

**[YES] NEW (FRAMES-aligned - agent capturing structure):**
> - **Component:** I2C_Driver
> - **Interface:** I2C_Bus (address 0x48)
> - **Flow:** temperature_readings (data), polling_commands (commands), ACK/NACK (signals)
> - **Mechanism:** I2C protocol spec, driver documentation, timing constraints
> - **Coupling:** Hardware interface, synchronous
> - **Confidence:** HIGH (clearly documented in driver source)

Human then reviews and assigns: "Criticality: HIGH - thermal protection depends on this"

---

## 3. Human-in-the-Loop (HITL) Patterns

### 3.1 Human Verification for Truth

| Layer | Agent Role | Human Role |
|-------|------------|------------|
| **Capture** | Grab all raw data | - |
| **Staging** | Categorize, flag, add context | - |
| **Truth** | Prepare review queue | Verify EACH piece, align across sources |
| **Graph** | - | Only verified data enters |

**Current Implementation:** Human reviews ALL staged data before it becomes truth.

### 3.2 Plan-Then-Execute Pattern

> "The agent should plan autonomously but execute with approval."

**Workflow:**
1. Agent analyzes task and creates plan
2. Agent shows plan to human
3. Human approves/modifies plan
4. Agent executes approved plan
5. Agent reports results

**Why:** Humans are good at judging plans, agents are good at executing them.

### 3.3 Trust-Building Phases

```
Phase 1: Full Review      -> Human reviews ALL data (current phase)
Phase 2: Assisted Review  -> Agents pre-sort, humans verify
Phase 3: Spot-Check       -> Humans spot-check agent categorizations
Phase 4: Exception-Based  -> Humans review only flagged anomalies
```

Each phase builds confidence in agent categorization before reducing human review scope.

> **Note:** Even at Phase 4, humans establish truth. Agents always assist, never decide.

---

## 4. Transfer Learning Methodology

### 4.1 Learning from Examples

> "The agent learns methodology from examples, not just copies content."

**Pattern:** Show the agent good examples -> Agent extracts the methodology -> Agent applies methodology to new content.

**Example Flow:**
```
Input: Student work showing good dependency extraction
Agent learns: How to identify dependencies, assess criticality, describe relationships
Output: Agent extracts new dependencies using learned methodology
```

### 4.2 What Gets Transferred

- **Methodology:** HOW to analyze documents
- **Ontology:** Relationship types, criticality levels, component categories
- **Quality Standards:** What makes a good extraction
- **Domain Context:** Satellite systems, F´ framework, PROVES Kit specifics

---

## 5. Transparency Stack

```
┌─────────────────────────────────────┐
│  USER: Sees decisions in real-time  │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  CONSOLE: Live progress updates     │
│  [CURATOR] Thinking...              │
│  [CURATOR] Planning to call...      │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  CHECKPOINTS: Full conversation     │
│  Every message, decision, result    │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  LOGS: Detailed reasoning           │
│  Why each decision was made         │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  DATABASE: Final stored results     │
│  Knowledge graph with provenance    │
└─────────────────────────────────────┘
```

**Console Output Patterns:**
```
[CURATOR] Starting analysis of {document}...
[CURATOR] Captured {n} dependencies -> staging tables
[CURATOR] Flagged {n} items with anomalies for review
[CURATOR] All data staged for human verification
```

---

## 6. Three-Agent Architecture (v2)

> **Updated December 2025:** Simplified from 9 agents to 3 focused agents.

### 6.1 The Three Agents

| Agent | Purpose | Output |
|-------|---------|--------|
| **Extractor** | Grab ALL raw data, smart categorization attempt ("this component belongs to this hardware") | `raw_snapshots`, `staging_extractions` with context |
| **Validator** | Check everything in place, verify confidence, flag anomalies, note pattern breaks, flag uncited data | Updates `staging_extractions` with flags/notes, can loop back to Extractor |
| **Decision Maker** | Route to appropriate table: clean staging OR flagged table with reasoning | Prepares human review queue with context |

> **Key Insight:** Agents are assistants preparing data for human verification. They provide context to help humans eliminate ambiguity.

### 5.2 What's NOT an Agent

These are **deterministic pipeline functions**, not LLM agents:

| Function | Why Not an Agent |
|----------|------------------|
| **Chunking** | Deterministic text splitting (no LLM needed) |
| **Embedding** | API call to embedding model (no reasoning) |
| **Graph Building** | Deterministic node/edge creation from entities |
| **Scoring** | Rule-based or ML model inference (no agent loop) |

**Key Insight:** Only steps requiring LLM reasoning are agents. Everything else is a batch job.

### 5.3 Refinement Loop

```
Extractor ◄──► Validator ──► Decision Maker ──► Human Review
    │              │                │                 │
    ▼              ▼                ▼                 ▼
raw data      flag/verify       route to         ESTABLISH
w/context     confidence        staging          TRUTH
```

- Validator can loop back to Extractor for more context
- Loop is bounded by LangGraph's `recursion_limit`
- Decision Maker routes: clean table OR flagged table with reasoning
- Human reviews ALL staged data, aligns across sources
- Only human-verified data enters the truth graph

---

## 6. LangGraph Loop Control

> **Principle:** Use framework built-ins, don't reinvent the wheel.

### 6.1 Graph-Level: `recursion_limit`

```python
# Default: 25 super-steps
graph.invoke(inputs, config={"recursion_limit": 5})
```

- Counts super-steps (each node execution in graph)
- Raises `GraphRecursionError` when exceeded
- Handle gracefully -> escalate to human

### 6.2 Agent-Level: `ToolCallLimitMiddleware`

```python
from langchain.agents.middleware import ToolCallLimitMiddleware

limiter = ToolCallLimitMiddleware(
    thread_limit=50,   # Max across entire conversation
    run_limit=15,      # Max per single invocation
    exit_behavior="continue"  # or "error" or "end"
)
```

### 6.3 Per-Tool Limits

```python
# Limit expensive operations
fetch_limiter = ToolCallLimitMiddleware(
    tool_name="fetch_document",
    run_limit=3,
    exit_behavior="error"
)
```

**Observable in LangSmith:**
- Super-step count in metadata (`langgraph_step`)
- Tool call counts per agent
- `GraphRecursionError` in error panel

---

## 7. Sub-Agent Pattern (Historical)

> **Note:** This section describes the original sub-agent-as-tools pattern.
> See Section 5 for the current 3-agent architecture.

### 7.1 Specialization Pattern

Each sub-agent has ONE focused responsibility:

| Sub-Agent | Responsibility | Model | Tools |
|-----------|---------------|-------|-------|
| **Extractor** | Read docs, identify dependencies | Claude Sonnet | `read_documentation_file` |
| **Validator** | Check for duplicates | Claude Haiku | `check_if_dependency_exists` |
| **Storage** | Write to database | Claude Haiku | `store_dependency_relationship` |

### 7.2 Why Sub-Agents?

1. **Single Responsibility** - Each agent is expert at one thing
2. **Model Optimization** - Use expensive models only where needed
3. **Testability** - Test each capability independently
4. **Composability** - Coordinator decides when to invoke each

---

## 8. ERV Ontology (Entity-Relationship-Value)

### 8.1 Relationship Types

| Type | Meaning | Example |
|------|---------|----------|
| `depends_on` | A needs B to function | I2C_Driver depends_on HAL |
| `requires` | A must have B present | Component requires specific config |
| `enables` | A makes B possible | Framework enables rapid development |
| `conflicts_with` | A and B cannot coexist | Two drivers conflict on same bus |
| `mitigates` | A reduces risk from B | Watchdog mitigates lockup risk |
| `causes` | A leads to B happening | Power surge causes reset |

### 8.2 Criticality Levels (Post-Verification Metadata)

| Level | Definition | Assigned When |
|-------|------------|---------------|
| **HIGH** | Mission/safety critical | Human assigns during verification |
| **MEDIUM** | Important for functionality | Human assigns during verification |
| **LOW** | Nice to have, minimal impact | Human assigns during verification |

**Note:** Criticality is metadata assigned by humans AFTER verification, not a gate for capture.

### 8.3 Component Categories

- `software` - Code, drivers, libraries
- `hardware` - Physical components, boards
- `interface` - Communication protocols, APIs
- `system` - Complete systems, assemblies
- `documentation` - Specs, guides, references

---

## 9. Operational Patterns

### 9.1 Monitoring Setup

**Where data lives:**
1. **Conversation State:** PostgreSQL (checkpointer tables)
2. **Knowledge Graph:** PostgreSQL (nodes, edges, etc.)
3. **Debug Logs:** Console output + optional log files

**Quick health checks:**
```bash
# See recent agent activity
python run_with_approval.py

# Check database contents
SELECT COUNT(*) FROM nodes;
SELECT COUNT(*) FROM edges;
```

### 9.2 Error Handling Philosophy

> "Fail visibly, recover gracefully."

- All errors must be logged and visible
- Partial progress should be saved
- Human can resume or retry
- Never silently drop data

### 9.3 GitHub API Sync Pattern

**For external repos (F´, etc.):**
- Use API instead of local clones (saves disk space)
- Track commit SHA for incremental updates
- Rate limit: 5000 requests/hour authenticated
- Daily sync recommended

---

## 10. Key Takeaways (Summary)

### For Building Intelligent Agents:

1. **Context is Intelligence** - Rich domain knowledge + good examples = better decisions
2. **Transparency Enables Trust** - Show all decisions so humans can verify
3. **HITL is About Control** - Gate on execution, not thinking
4. **Learning Compounds** - Each session improves the system

### For Users/Operators:

1. **Give Context, Not Commands** - "Here's what good looks like" > "Do exactly this"
2. **Ask "Why?" Not Just "What?"** - Understand agent reasoning
3. **Review Sessions, Improve Prompts** - Each run teaches lessons
4. **Trust, But Verify** - Spot-check stored dependencies

---

## 11. Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | December 2025 | Added 3-agent architecture, LangGraph loop control |
| 1.0 | December 2025 | Initial extraction from archived documentation |

---

## 12. Related Documents

**Current Documentation:**
- [README.md](README.md) - Project overview
- [GETTING_STARTED.md](GETTING_STARTED.md) - Setup guide
- [docs/ROADMAP.md](docs/ROADMAP.md) - Development roadmap
- [docs/ARCHIVING_GUIDELINES.md](docs/ARCHIVING_GUIDELINES.md) - How to extract canon during sweeps

**Archived Sources (lessons extracted from):**
- `archive/curator-agent-old/AGENT_INTELLIGENCE_GUIDE.md`
- `archive/curator-agent-old/DESIGN_ACTION_LEVEL_HITL.md`
- `archive/curator-agent-old/OPTION_REMOVE_HITL.md`
- `archive/curator-agent-old/README_MONITORING.md`
- `archive/outdated-docs/LANGSMITH_INTEGRATION.md`
- `archive/outdated-docs/GITHUB_API_SYNC_QUICKSTART.md`
