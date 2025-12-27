# Getting Started with PROVES Library

**Welcome!** This guide will get you up and running with the PROVES Library in under 15 minutes.

---

## What You'll Set Up

- [YES] Curator Agent system (LangGraph + Claude Sonnet 4.5)
- [YES] Neon PostgreSQL knowledge graph (cloud-hosted)
- [YES] LangGraph checkpointer for agent state persistence
- [YES] Infrastructure utilities for database operations
- [YES] Domain staging tables (evidence + confidence workflow)

---

## Prerequisites

### Required

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/))
- **API Keys:**
  - [Anthropic API Key](https://console.anthropic.com/) - For Claude Sonnet 4.5
  - [Neon Database URL](https://neon.tech/) - For cloud PostgreSQL

### Optional

- **VS Code** ([Download](https://code.visualstudio.com/)) - Recommended IDE
- **LangSmith API Key** ([smith.langchain.com](https://smith.langchain.com/)) - For tracing (disabled by default)

### Hardware Requirements

- 4GB RAM minimum (8GB recommended)
- 2GB free disk space
- Internet connection (cloud-based services)

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Lizo-RoadTown/PROVES_LIBRARY.git
cd PROVES_LIBRARY
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env with your API keys
# Required variables:
#   ANTHROPIC_API_KEY=sk-ant-api03-...
#   DATABASE_URL=postgresql://...
#
# Optional (tracing disabled by default):
#   LANGCHAIN_TRACING_V2=false
```

### 4. Initialize Database Schema

```bash
# Apply knowledge graph schema to Neon database
python scripts/apply_schema.py
python scripts/setup_domain_tables.py

# Create LangGraph checkpointer tables
python scripts/setup_checkpointer.py

# Verify connection
python scripts/db_connector.py
```

### 5. Run the Curator Agent

```bash
# Navigate to curator-agent
cd curator-agent

# Run with human-in-the-loop approval
python run_with_approval.py

# Or run the test script
python test_agent.py
```

Success! You now have the PROVES Library running.

---

## Detailed Setup

### Step 1: Get Your API Keys

#### Anthropic (Claude Sonnet 4.5)

1. Sign up at https://console.anthropic.com/
2. Navigate to **API Keys**
3. Create a new key
4. Copy key starting with `sk-ant-api03-...`
5. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-api03-...`

**Free Tier:** $5 credit for new users

#### Neon PostgreSQL (Knowledge Graph Database)

1. Sign up at https://neon.tech/
2. Create a new project: "PROVES Library"
3. Copy connection string (looks like `postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/proves`)
4. Add to `.env`: `DATABASE_URL=postgresql://...`

**Free Tier:** 500MB storage, 10GB data transfer/month

#### LangSmith (Optional - For Tracing)

Tracing is **disabled by default**. To enable:

1. Sign up at https://smith.langchain.com/
2. Navigate to **Settings > API Keys**
3. Create a **personal API key** (not org-scoped)
4. Copy key starting with `lsv2_pt_...`
5. Add to `.env`:
   ```bash
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=lsv2_pt_...
   ```

**Note:** Org-scoped keys require workspace specification and may cause issues.

### Step 2: Understand the Repository Structure

See [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md) for complete organization guide.

```
PROVES_LIBRARY/
├── curator-agent/       # 🤖 Curator Agent system (PRIMARY)
│   ├── src/curator/     # Main coordinator + 3 sub-agents
│   ├── run_with_approval.py  # CLI with HITL
│   └── README.md        # Agent documentation
│
├── scripts/             # Infrastructure utilities
│   ├── db_connector.py  # Database connection pooling
│   ├── graph_manager.py # Knowledge graph CRUD
│   ├── apply_schema.py  # Schema initialization
│   ├── setup_domain_tables.py  # Staging + domain tables
│   └── setup_checkpointer.py  # LangGraph tables
│
├── notebooks/           # Jupyter notebooks
│   ├── 01_setup_and_explore.ipynb
│   └── 02_training_local_llm.ipynb
│
├── docs/                # Technical documentation
├── trial_docs/          # Manual analysis results
├── library/             # Knowledge base entries
└── .env.example         # Environment template
```

### Step 3: Verify Your Setup

#### Test Database Connection

```bash
python scripts/db_connector.py
```

**Expected output:**
```
[YES] Connected to Neon PostgreSQL
Database: proves
Tables: kg_nodes, kg_relationships, library_entries
```

#### Test Knowledge Graph Operations

```bash
python scripts/graph_manager.py
```

**Expected output:**
```
[YES] Knowledge graph initialized
Nodes: 6, Relationships: 3
```

#### Test Curator Agent

```bash
cd curator-agent
python test_agent.py
```

**Expected output:**
```
The knowledge graph currently contains:
- 6 nodes total
- 3 relationships total
Nodes: Hardware (3), Component (2), Pattern (1)
```

---

## What's Next?

### Learn the Deep Agent System

Read [curator-agent/README.md](curator-agent/README.md) to understand:

- Main Curator Agent (coordinator)
- Extractor Sub-Agent (dependency discovery)
- Validator Sub-Agent (schema compliance)
- Storage Sub-Agent (knowledge graph operations)
- Sub-agents-as-tools pattern

### Run Your First Extraction

```bash
cd curator-agent
python -c "
from src.curator.agent import graph

result = graph.invoke({
    'messages': [{
        'role': 'user',
        'content': 'Extract dependencies from ../trial_docs/fprime_i2c_driver_full.md'
    }]
})

print(result['messages'][-1].content)
"
```

### View Traces in LangSmith

1. Go to https://smith.langchain.com/
2. Select "PROVES_Library" project
3. View traces of agent execution
4. See sub-agent spawning and tool calls

### Use LangSmith Studio (Human-in-the-Loop)

**Note:** Requires local dev server (see troubleshooting below)

1. Go to https://smith.langchain.com/studio/
2. Connect to local agent (requires `langgraph dev`)
3. Pause, inspect, and modify agent execution in real-time

---

## Project Workflows

### Adding New Knowledge to the Graph

**Option 1: Manual Entry**

Create a markdown file in `library/` with YAML frontmatter:

```markdown
---
title: UART Driver
type: software
tags: [driver, serial, communication]
dependencies:
  - name: GPIO Controller
    relationship: depends_on
    criticality: HIGH
---

# UART Driver

## Description
Universal Asynchronous Receiver-Transmitter driver...
```

**Option 2: Automated Extraction (Deep Agent)**

```python
from curator_agent import graph

result = graph.invoke({
    "messages": [{
        "role": "user",
        "content": "Extract dependencies from path/to/documentation.md"
    }]
})
```

### Querying the Knowledge Graph

```python
from scripts.graph_manager import GraphManager

gm = GraphManager()

# Find a component
node = gm.get_node_by_name("ImuManager")

# Get its dependencies
deps = gm.get_node_relationships(node['id'], direction='outgoing')

# Find transitive dependencies
chain = gm.get_transitive_dependencies(node['id'], max_depth=5)
```

### Syncing Documentation

```python
from scripts.github_doc_sync import GitHubDocSync

sync = GitHubDocSync()

# Sync F' framework docs
sync.sync_repo("nasa/fprime", "docs/")

# Sync PROVES Kit docs
sync.sync_repo("BroncoSpace/PROVES", "docs/")
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'langchain'"

**Solution:**
```bash
# Make sure virtual environment is activated
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Database connection failed"

**Solution:**
```bash
# Check DATABASE_URL in .env
# Should start with: postgresql://

# Test connection
python scripts/db_connector.py

# Check Neon dashboard for database status
```

### Issue: "403 Forbidden" errors in LangSmith

**Solution:**
```bash
# Check API key is correct in .env
# Should start with: lsv2_sk_

# Check LangSmith workspace permissions
# Personal accounts may have limited access
```

### Issue: "langgraph dev" requires Rust compilation (Windows)

**Context:** Local dev server for Studio UI requires Microsoft Visual C++ Build Tools

**Options:**

1. **Install Visual Studio Build Tools** (~6GB):
   - Download from: https://visualstudio.microsoft.com/downloads/
   - Select "Desktop development with C++"
   - Restart terminal after install

2. **Use Python SDK directly** (works without dev server):
   ```bash
   cd curator-agent
   python test_agent.py
   ```

3. **Deploy to LangSmith Cloud** (requires paid plan)

### Issue: Agent execution is slow

**Common causes:**

1. **Large documents:** Chunk documents before extraction
2. **Network latency:** Check internet connection to Anthropic API
3. **Database operations:** Use connection pooling (already configured)

**Monitor with LangSmith:**
- View execution traces
- Identify bottlenecks
- Optimize prompts based on token usage

---

## Development Best Practices

### 1. Follow the Folder Structure

See [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md) for guidelines on where to add new files.

**Quick reference:**

| What you're adding | Where it goes |
|-------------------|---------------|
| New sub-agent | `curator-agent/src/curator/subagents/` |
| Database utility | `scripts/` |
| Documentation | `docs/` |
| Knowledge entry | `library/` |
| Test | `tests/` |

### 2. Use Consistent Naming

- **Python files:** `lowercase_with_underscores.py`
- **Classes:** `PascalCase`
- **Functions:** `lowercase_with_underscores`
- **Docs:** `UPPERCASE_WITH_UNDERSCORES.md` (major) or `lowercase-with-hyphens.md` (specific)

### 3. Keep Documentation Current

When you change architecture or add features:

1. Update relevant docs in `docs/`
2. Update README.md if major change
3. Update FOLDER_STRUCTURE.md if adding new directory
4. Add entry to decision log

### 4. Test Before Committing

```bash
# Test database operations
python scripts/db_connector.py

# Test agent system
cd curator-agent && python test_agent.py

# Run tests (when available)
pytest tests/
```

### 5. Use LangSmith for Debugging

Every agent execution is traced in LangSmith:

1. Check traces for errors
2. View token usage and costs
3. Analyze prompt performance
4. Debug sub-agent spawning

---

## Additional Resources

### Documentation

- [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md) - Repository organization
- [curator-agent/README.md](curator-agent/README.md) - Deep Agent system
- [docs/KNOWLEDGE_GRAPH_SCHEMA.md](docs/KNOWLEDGE_GRAPH_SCHEMA.md) - Database schema
- [docs/LANGSMITH_INTEGRATION.md](docs/LANGSMITH_INTEGRATION.md) - Tracing setup

### External Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Claude API Docs](https://docs.anthropic.com/)
- [LangSmith Docs](https://docs.smith.langchain.com/)
- [Neon PostgreSQL Docs](https://neon.tech/docs/)

### Community

- **GitHub Issues:** https://github.com/Lizo-RoadTown/PROVES_LIBRARY/issues
- **Email:** eosborn@cpp.edu

---

## Next Steps

1. [YES] Complete this setup guide
2. Read [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md) for project organization
3. Read [curator-agent/README.md](curator-agent/README.md) for Deep Agent details
4. Explore [trial_docs/COMPREHENSIVE_DEPENDENCY_MAP.md](trial_docs/COMPREHENSIVE_DEPENDENCY_MAP.md) for example analysis
5. Run your first dependency extraction
6. View traces in LangSmith
7. Add knowledge entries to the graph

Welcome to the PROVES Library! 🚀

---

**Last Updated:** December 21, 2024
**Maintained by:** Elizabeth Osborn (eosborn@cpp.edu)
