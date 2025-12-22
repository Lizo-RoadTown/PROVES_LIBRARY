# PROVES Library Curator Agent

**Autonomous AI agent that learns from human expertise to build CubeSat dependency knowledge graphs**

## What We Built

An **intelligent autonomous agent** that demonstrates:
- **Learning from examples** - Transfers methodology from students' work
- **Autonomous decision-making** - Decides which tools to call and when
- **Transparent operation** - Every decision visible and traceable
- **Human oversight** - Requests approval before critical actions

Built with **LangGraph + Claude Sonnet 4.5**, running locally with full control.

## Quick Start

```bash
# 1. Set up environment (.env file with ANTHROPIC_API_KEY and Neo4j credentials)
# 2. Run a demo
python demo_learning.py

# 3. Watch what it does
python quick_monitor.py watch

# 4. View session history
python view_session.py
```

## What Makes This Special

### 1. It Actually Learns

Give it examples, it learns the methodology:

```python
"""
LEARN FROM THESE EXAMPLES:
  ImuManager depends_on LinuxI2cDriver (HIGH criticality)
  Reasoning: "I2C failure → can't orient solar panels → power loss → mission failure"

Now analyze new documentation and apply the same reasoning.
"""
```

The agent learns:
- What makes dependencies HIGH vs MEDIUM vs LOW
- How to assess mission impact
- Pattern recognition in technical docs
- Reasoning methodology to follow

### 2. It Makes Decisions Autonomously

You give it goals, not instructions:

```
❌ Old way: "Extract ImuManager→LinuxI2cDriver from line 47"
✅ New way: "Build a dependency graph for the I2C subsystem"
```

The agent decides:
1. I need to read the fprime I2C driver documentation
2. I'll call extractor_agent to analyze it
3. Found 4 dependencies - need to validate them
4. Calling validator_agent 4 times
5. Ready to store - requesting approval

### 3. Full Transparency

Every action is visible:

```
[CURATOR] Thinking...
[CURATOR] Planning to call 1 sub-agent(s):
  -> extractor_agent
[TOOLS] Executing sub-agent tool calls...
[CURATOR] Planning to call 4 sub-agent(s):
  -> validator_agent (x4)
```

Plus:
- SQLite checkpoints (full conversation history)
- Neo4j graph (stored dependencies)
- Optional debug logs (detailed reasoning)

### 4. Human-in-the-Loop

Agent asks before executing critical actions:

```
Agent: "I want to store this HIGH criticality dependency:
       ImuManager depends_on LinuxI2cDriver
       This is mission-critical because..."

You: Approve? (yes/no)
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  CURATOR AGENT (Claude Sonnet 4.5 - $15/MTok)               │
│  - Learns from examples                                     │
│  - Makes autonomous decisions                               │
│  - Coordinates sub-agents                                   │
│  - Requests human approval                                  │
└───────┬──────────────┬──────────────┬──────────────────────┘
        │              │              │
        ▼              ▼              ▼
┌───────────┐  ┌──────────┐  ┌──────────────┐
│ EXTRACTOR │  │VALIDATOR │  │   STORAGE    │
│(Sonnet 4.5│  │(Haiku 3.5│  │ (Haiku 3.5)  │
│ $15/MTok) │  │ $1/MTok) │  │  $1/MTok)    │
│           │  │          │  │              │
│ Analyzes  │  │ Checks   │  │ Stores to    │
│ docs for  │  │ for      │  │ Neo4j graph  │
│ deps      │  │duplicates│  │              │
└───────────┘  └──────────┘  └──────────────┘
```

**Cost Optimization**: Haiku for simple tasks = 90% savings on sub-agents!

## Core Files

**Agent System:**
- `src/curator/agent.py` - Main curator (coordinates everything)
- `src/curator/subagents/extractor.py` - Document analysis
- `src/curator/subagents/validator.py` - Duplicate checking
- `src/curator/subagents/storage.py` - Neo4j storage

**Monitoring Tools:**
- `view_session.py` - View conversation history
- `quick_monitor.py` - Watch Neo4j in real-time
- `simple_check.py` - Quick status check

**Tests & Demos:**
- `demo_learning.py` - Main demo (learning from students)
- `test_simple_extraction.py` - Single dependency test
- `run_with_approval.py` - Interactive CLI

**Documentation:**
- `README.md` - This file
- `AGENT_INTELLIGENCE_GUIDE.md` - **How to build intelligent agents**
- `README_MONITORING.md` - Complete monitoring guide
- `QUICK_START_MONITORING.md` - 3-step visibility setup

## How It Works: Demo Walkthrough

Run: `python demo_learning.py`

**What Happens:**

1. **Context Loading**: Agent receives students' example dependencies

2. **Autonomous Planning**:
   ```
   [CURATOR] Thinking...
   [CURATOR] Planning to call: extractor_agent
   ```
   Agent decides: "I should read the fprime I2C driver docs"

3. **Extraction**:
   ```
   [TOOLS] Executing sub-agent tool calls...
   ```
   Extractor analyzes documentation autonomously

4. **Validation**:
   ```
   [CURATOR] Planning to call 4 sub-agent(s):
     -> validator_agent (x4)
   ```
   Agent validates each found dependency

5. **Approval Request**:
   ```
   [HITL] Requesting approval: Store HIGH criticality dependency
   Task: ImuDriver depends_on LinuxI2cDriver
   ```

6. **Storage**: After you approve, stores to Neo4j

7. **Analysis**: Reports what it found and suggests improvements

## Databases

**SQLite Checkpoints** (`curator_checkpoints.db`):
- Full conversation history
- Every message, tool call, result
- Human approval decisions
- Complete audit trail

**Neo4j Knowledge Graph**:
```cypher
(Component {name: "ImuManager"})
  -[:DEPENDS_ON {
    criticality: "HIGH",
    description: "...",
    created_at: timestamp
  }]->
(Component {name: "LinuxI2cDriver"})
```

## Configuration

### Environment (.env file):
```bash
ANTHROPIC_API_KEY=your-key-here
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```

### Interactive Mode:

Edit `src/curator/agent.py` line ~392:
```python
# Ask before EVERY action:
graph = create_curator(interactive_mode=True)

# Only ask for HIGH criticality storage:
graph = create_curator(interactive_mode=False)
```

## Monitoring Commands

```bash
# View what happened in a session
python view_session.py <thread-id>
python view_session.py list  # Show all sessions

# Watch Neo4j in real-time
python quick_monitor.py
python quick_monitor.py watch 5  # Update every 5 seconds

# Quick status check
python simple_check.py
```

## Key Insights

### Intelligence Comes From Context

The agent doesn't just follow rules - it learns patterns from examples:

```
Good Example → Agent learns → Applies to new data → Better results
```

### Transparency Builds Trust

When you can see:
- What the agent is thinking
- Why it made each decision
- What tools it's calling
- What results it got

You can trust it to work autonomously.

### HITL is About Control, Not Micromanagement

Let the agent:
- ✓ Read documentation
- ✓ Analyze dependencies
- ✓ Validate findings
- ✓ Propose actions

Gate only:
- ⚠️ Storing HIGH criticality data
- ⚠️ Irreversible operations
- ⚠️ Critical decisions

## Documentation Guide

1. **Start here**: README.md (this file)
2. **Learn principles**: [AGENT_INTELLIGENCE_GUIDE.md](AGENT_INTELLIGENCE_GUIDE.md)
3. **Set up monitoring**: [QUICK_START_MONITORING.md](QUICK_START_MONITORING.md)
4. **Deep dive monitoring**: [README_MONITORING.md](README_MONITORING.md)

Design docs (for customization):
- [DESIGN_ACTION_LEVEL_HITL.md](DESIGN_ACTION_LEVEL_HITL.md) - Different approval strategies
- [OPTION_REMOVE_HITL.md](OPTION_REMOVE_HITL.md) - Remove/modify approval gates

## Troubleshooting

**"Can't see what the agent is doing"**
```bash
python view_session.py  # View conversation history
python quick_monitor.py  # Watch Neo4j database
```

**"Agent not finding dependencies"**
- Check the examples in your task prompt
- Verify file paths are correct
- Review extractor results in checkpoints

**"Database connection error"**
```bash
# Test Neo4j
python -c "from neo4j import GraphDatabase; print('OK')"

# Install if needed
pip install neo4j
```

## What We Demonstrated

✅ **Autonomous Intelligence**: Agent decides what to do, not just what you tell it

✅ **Transfer Learning**: Learns methodology from examples, applies to new data

✅ **Transparent Operation**: Every decision visible and traceable

✅ **Cost Optimization**: 90% savings on sub-agents using Haiku

✅ **Human Oversight**: Approval before critical actions

✅ **Full Traceability**: Complete audit trail in checkpoints and logs

## Requirements

```bash
pip install langchain langchain-anthropic langgraph neo4j python-dotenv
```

Python 3.10+ required.

## Future Enhancements

- [ ] Plan-then-execute pattern (show full plan upfront)
- [ ] Batch processing of multiple documents
- [ ] Confidence scores on extracted dependencies
- [ ] Automatic methodology improvement from feedback
- [ ] Export to various formats (JSON, GraphML, etc.)

## Key Principle

**Intelligence emerges from rich context, autonomous reasoning, and transparent decision-making under human oversight.**

Not automation - intelligence.

---

Built with Claude Sonnet 4.5, LangGraph, and Neo4j for the PROVES Library project.
