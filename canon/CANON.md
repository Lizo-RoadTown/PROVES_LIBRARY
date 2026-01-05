# CANON - Permanent Knowledge Repository

> **Purpose:** This file preserves critical lessons, design principles, and ontology that must NEVER be lost during documentation updates, refactoring, or agent handoffs. Treat this as institutional memory.

**Last Updated:** January 2026
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
| 3.0 | January 2026 | Added V3 pipeline lessons: classification patterns, per-type defaults, validation workflow, stateless agents, bifurcated architecture (15 new canon rules from V3 development) |
| 2.0 | December 2025 | Added 3-agent architecture, LangGraph loop control |
| 1.0 | December 2025 | Initial extraction from archived documentation |

---

## 12. Classification and Storage Patterns (V3 Lessons)

> **Context:** These lessons were learned during V3 pipeline development (January 2026) when fixing critical bugs where only 4-5 extractions were being stored instead of 14-20.

### 12.1 Classification Must Happen Early (Extractor Responsibility)

**Canon Rule:**
The extractor must explicitly assign `candidate_type` for every extraction.

**Why:**
Once something is labeled as `component` or `dependency`, downstream systems cannot reliably recover whether it was actually a `port`, `telemetry`, `command`, `event`, `parameter`, or `data_type`. Storage defaults cannot reconstruct lost class boundaries.

**Failure Mode We Saw:**
A "global default" strategy caused the extractor to collapse outputs into only:
- `component` (generic node)
- `dependency` (generic relationship)

Result: Notion review queue stopped receiving parameter/telemetry/command/event candidates even though the enum/schema supported them.

**Non-Negotiable:**
- `candidate_type` is not optional
- `candidate_type` must be from the database enum (10 types: component, port, command, telemetry, event, parameter, data_type, dependency, connection, inheritance)
- Classification is an **irreversible decision boundary**, so it cannot be deferred to storage

**Implementation:**
Extractor prompt includes explicit decision tree:
```
1. What am I extracting? (a thing that exists, or a relationship between things?)
2. If it's a THING (node), what kind?
   - Module/subsystem/unit → 'component'
   - Interface point/endpoint → 'port'
   - Operation/instruction → 'command'
   - Measurement/sensor reading → 'telemetry'
   - State change/trigger/notification → 'event'
   - Configuration value/setting → 'parameter'
   - Type definition/struct/enum → 'data_type'
3. If it's a RELATIONSHIP (edge), what kind?
   - Requires/depends_on → 'dependency'
   - Interface-level connection → 'connection'
   - Extends/inherits_from → 'inheritance'
```

### 12.2 Defaults Are Allowed Only After Type Is Known (Per-Type Defaults)

**Canon Rule:**
Defaults can exist, but they must be **per-type** (component defaults, parameter defaults, telemetry defaults, etc.), not global.

**Why:**
A single default path is only safe in homogeneous domains. PROVES is **heterogeneous by design** (nodes + anchored entities + relations). Global defaults collapse the ontology.

**What "Per-Type Default" Means:**
1. Extractor outputs typed minimal objects
2. Storage fills missing fields based on `candidate_type` templates
3. The template layer reduces verbosity without losing type identity

**Three-Layer Merge (V3 Implementation):**
```python
# Layer 1: Type-specific defaults (based on candidate_type)
type_defaults = TYPE_SPECIFIC_DEFAULTS.get(candidate_type, {})

# Layer 2: Page-level defaults (from extractor's epistemic_defaults)
merged = type_defaults.copy()
if page_defaults:
    merged.update(page_defaults)

# Layer 3: Candidate overrides (from extractor's epistemic_overrides)
if candidate_overrides:
    merged.update(candidate_overrides)

# Priority: candidate_overrides > page_defaults > type_defaults > function_params
```

**Example:**
```python
TYPE_SPECIFIC_DEFAULTS = {
    "telemetry": {
        "observer_type": "system",      # Telemetry is system-generated by default
        "contact_mode": "mediated",
        "signal_type": "telemetry"
    },
    "port": {
        "observer_type": "human",       # Ports are human-documented by default
        "contact_mode": "derived",
        "signal_type": "spec",
        "scope": "local"
    },
    # ... all 10 types
}
```

### 12.3 "Dependency" Is Overloaded; Disambiguate by Shape

**Canon Rule:**
Do not decide "node vs edge" based on the English word "dependency." Decide based on **structure**.

**Why:**
"Dependency" can mean:
1. **A thing you depend on** (driver, toolchain, framework) → node
2. **The relationship of depending** (A requires B) → edge

**Disambiguation Rule (Structural):**
- If payload includes `source` + `target` + `relationship_type` → **relationship-shaped** (edge candidate)
- If it describes a standalone artifact (tool, framework, module) without endpoints → **entity-shaped** (node candidate)

### 12.4 Anchored Entities: Node + Mandatory Attachment Edge

**Canon Rule:**
Some entities are first-class objects that only make sense when attached. They must be modeled as:
1. A **node** (identity/lifecycle/provenance)
2. Plus an **attachment edge** (where/how it applies)

**Applies To:**
- `parameter`
- `port`
- `telemetry`
- `command`
- `event`
- (often) procedures, constraints, requirements, failure modes

**Why:**
- **If these are only edges/properties:** You lose lifecycle/versioning/provenance/reuse
- **If these are only nodes:** You lose "applies to" context and override semantics

**Example:**
```
Node: parameter:MaxVoltage (has identity, version, provenance)
Edge: component:PowerMonitor --HAS_PARAMETER--> parameter:MaxVoltage (attachment context)
```

### 12.5 Relationships Should Remain Binary in Storage

**Canon Rule:**
Represent "depends on two things" as **two edges**, unless the text explicitly indicates conjunctive logic ("only works if BOTH").

**Why:**
Binary edges preserve:
- Separate evidence per coupling
- Separate coupling strengths/failure modes/scope
- Graph traversal simplicity

**Joint Dependency Exception:**
If the dependency is explicitly conjunctive (AND / quorum / k-of-n), model a group:
- Either a "dependency group node"
- Or shared `group_id` across edges

### 12.6 Evidence + Lineage Are Not Optional (Trust Contract)

**Canon Rule:**
Every stored candidate (node or relationship) **must** retain:
- `snapshot_id`
- `source_url`
- `raw_evidence` (exact quote)
- `evidence_type`
- `confidence` + `reason`
- Epistemic metadata (knowledge capture checklist)

**Why:**
Without evidence+lineage, the graph becomes un-auditable and cannot safely support:
- Cross-source reconciliation
- Upgrades/supersession
- Soft matching
- Downstream embeddings/chunking

**What Broke Without This:**
We saw extractions stored without proper lineage, making it impossible to trace back to source documentation for verification.

### 12.7 Stable Identity Comes Before Soft Matching

**Canon Rule:**
Hard identity rules (canonical keys, approved aliases, exact merges) must **stabilize IDs before** soft matching and before chunking/embeddings.

**Why:**
Unstable IDs produce:
- Duplicate embeddings
- Broken references
- "Truth drift" across runs
- Chaotic reconciliation loops

**What "Hard" Means Here:**
**Deterministic:**
- Canonicalization rules
- Exact key match within ecosystem/type
- Approved alias lookup
- Human-directed merges only

**Soft matching only proposes candidates; it never mutates identity automatically.**

### 12.8 Staging Must Not Filter: Capture Everything, Then Review

**Canon Rule:**
Storage should stage **all** candidate types the extractor emits, without filtering based on importance.

**Why:**
Filtering at ingestion permanently removes data and introduces invisible blind spots. Human review + promotion is where selection happens.

**Failure Mode We Saw:**
Storage agent was filtering to "most critical" or "representative samples" instead of storing all approved extractions. This caused only 4-5 out of 20 extractions to be stored.

**The Fix:**
Explicit anti-filtering rules in storage agent prompt:
```
CRITICAL RULE: Store EVERY APPROVED extraction. Do NOT:
- Filter based on importance or "focusing on the most critical"
- Store only "representative samples"
- Skip approved extractions
- Decide which ones matter more

If validator APPROVED it (not FLAGGED), YOU MUST STORE IT. No exceptions.
```

### 12.9 Per-Extraction Validation, Not Batch-Level

**Canon Rule:**
Validator must validate **EVERY extraction individually** and return per-extraction results (APPROVED/FLAGGED for each one).

**Why:**
Batch-level approvals ("CONDITIONALLY APPROVE the extraction set") prevent storage from knowing which specific extractions to store or skip.

**Failure Mode We Saw:**
Validator was spot-checking or giving batch-level verdicts instead of validating all extractions individually.

**The Fix:**
```
CRITICAL RULES:
- DO NOT give batch-level approvals like "CONDITIONALLY APPROVE the extraction set"
- DO NOT spot-check or sample - validate EVERY extraction
- DO NOT reject the whole batch if one extraction is a duplicate
- FLAG duplicates individually so storage can skip them
- Return results for ALL N extractions (if 20 received, return 20 validation results)

Output Format:
EXTRACTION 1 (candidate_key): APPROVED - no duplicate
EXTRACTION 2 (candidate_key): FLAGGED - duplicate found in core_entities
EXTRACTION 3 (candidate_key): APPROVED - no duplicate
...
EXTRACTION N (candidate_key): APPROVED - no duplicate
```

### 12.10 Stateless Agents Prevent Database Timeouts

**Canon Rule:**
Validator and storage agents should have `checkpointer=None`. Excessive checkpoint operations cause PostgreSQL SSL timeouts.

**Why:**
LangGraph's PostgreSQL checkpointer saves state after every tool call. For agents making many tool calls (validator checking 20 duplicates, storage storing 20 extractions), this causes:
- Excessive database writes
- SSL connection timeouts (`SSL error: bad length`)
- Pipeline failures

**What Needs Checkpointing:**
- **Extractor**: YES - makes external API calls, needs state preservation for retry
- **Validator**: NO - stateless validation, no retry needed
- **Storage**: NO - stateless storage, deterministic operation

**The Fix:**
```python
validator = create_agent(
    model=ChatAnthropic(model=validator_spec["model"], temperature=0.1),
    system_prompt=validator_spec["system_prompt"],
    tools=validator_spec["tools"],
    checkpointer=None,  # Stateless validation - no checkpointing needed
)

storage = create_agent(
    model=ChatAnthropic(model=storage_spec["model"], temperature=0.1),
    system_prompt=storage_spec["system_prompt"],
    tools=storage_spec["tools"],
    checkpointer=None,  # Stateless storage - no checkpointing needed
)
```

### 12.11 Storage Must Count and Verify

**Canon Rule:**
Storage agent must **count** extractions received and **verify** it stored ALL of them.

**Why:**
Without explicit counting, storage agents may silently filter or skip extractions without raising errors.

**The Fix:**
```
CRITICAL REQUIREMENTS:
- STORE EVERY SINGLE EXTRACTION - If you receive 7, store 7. If you receive 20, store 20. COUNT and VERIFY.
- After storage, call get_staging_statistics() to verify count matches
- Report: "Stored X nodes in staging_extractions, Y edges in staging_relationships"
```

### 12.12 Count Extractions by Structure, Not Keywords

**Canon Rule:**
Don't count extractions by looking for specific keywords like "Component" or "Dependency". Count by **CANDIDATE headers**.

**Why:**
Keyword-based counting misses entity types and undercounts when the extractor uses diverse vocabulary.

**Failure Mode We Saw:**
```python
# WRONG - only matches specific keywords
extraction_count = len(re.findall(r'\b(Component|Dependency|Port):', final_message, re.IGNORECASE))
# Result: Counted 7 when there were actually 20 extractions
```

**The Fix:**
```python
# CORRECT - counts by structure (CANDIDATE headers)
extraction_count = len(re.findall(r'###?\s*CANDIDATE\s+\d+:', final_message, re.IGNORECASE))
# Fallback if headers not found
if extraction_count == 0:
    extraction_count = len(re.findall(r'\*\*candidate_type:\*\*\s+(component|port|command|telemetry|event|parameter|data_type|dependency|connection|inheritance)', final_message, re.IGNORECASE))
```

### 12.13 Bifurcated Workflow Architecture

**Canon Rule:**
Two distinct pathways must remain separate:
1. **Pre-human review:** extraction → staging tables (`staging_extractions`, `staging_relationships`)
2. **Post-human review:** promotion → core tables (`core_entities`, `core_edges`)

**Why:**
This separation enables:
- Agents to capture **everything** without quality gates
- Humans to review **all** raw extractions
- Clean core graph with only verified data
- Audit trail of what was captured vs what was approved

**Critical Boundary:**
```
Agents ──────────────────────► Staging Tables (ALL data)
                                      │
                                      ▼
                               Human Review
                                      │
                                      ▼
Human ───────────────────────► Core Tables (Verified ONLY)
```

**No exceptions:** Agents never write directly to core tables. Humans never skip staging review.

### 12.14 Table Names Must Reflect Content

**Canon Rule:**
Table names should accurately describe their contents to prevent confusion.

**Problem We Saw:**
- `staging_extractions` - sounds like ALL extractions, but only contains **nodes**
- `staging_relationships` - sounds separate from extractions, but **edges ARE extractions**

**Confusion:**
When we say "total extractions", people think it's just `staging_extractions`, forgetting that relationships are also extractions.

**Proposed Fix (Roadmap):**
- `staging_extractions` → `staging_nodes`
- `staging_relationships` → `staging_edges`

**Clear Semantics:**
Total extractions = `staging_nodes` + `staging_edges`

### 12.15 URL Tracking Ensures Reproducibility

**Canon Rule:**
URLs should flow through a tracked queue:
```
urls_to_process (status=pending)
  → extraction pipeline
  → raw_snapshots created
  → urls_to_process (status=completed)
```

**Why:**
This ensures:
- Every snapshot has a corresponding URL
- No orphaned data from untraceable test runs
- Failed extractions can be retried
- Progress is auditable

**What We Found:**
Looking at the database showed:
- 30 URLs with status='completed'
- 43 snapshots in raw_snapshots
- Gap of 13 orphaned snapshots from test runs/legacy data

**Going Forward:**
All new extractions use the tracked queue. Historical orphans can be archived or backfilled.

---

## 13. Related Documents

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
