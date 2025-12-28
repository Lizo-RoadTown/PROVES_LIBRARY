# LangChain/LangGraph Integration

This directory contains LangGraph deployment configuration and documentation for the curator agent system.

## Structure

### config/

LangGraph configuration files:

- **langgraph.json** - LangGraph deployment configuration
  - Defines the curator agent graph
  - Points to agent implementation in `curator-agent/src/curator/`
  - Environment configuration

### docs/

Documentation for LangChain/LangGraph integration:

- Agent architecture
- Deployment guides
- LangSmith observability setup

## LangGraph Agent

The curator agent is implemented using LangGraph and deployed using LangChain's deployment infrastructure.

**Agent Implementation:**
- Located in: `curator-agent/src/curator/`
- Main graph: `agent_v2.py` or `agent_v3.py`
- Subagent specifications: `subagent_specs.py`, `subagent_specs_v3.py`

**Deployment:**
```bash
# Deploy to LangGraph Cloud
langgraph deploy

# Test locally
langgraph dev
```

## Environment Setup

The agent uses environment variables from `.env` in the root directory:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=pr-...
ANTHROPIC_API_KEY=sk-ant-api03-...
NEON_DATABASE_URL=postgresql://...
```

## Observability

Agent traces and runs are monitored via LangSmith:
- Project: `pr-prickly-dollop-66` (configured in `.env`)
- View traces at: https://smith.langchain.com

## Related Directories

- **curator-agent/** - Agent implementation and core logic
- **neon-database/** - Database schema and migrations
- **notion/** - Notion integration for human review
