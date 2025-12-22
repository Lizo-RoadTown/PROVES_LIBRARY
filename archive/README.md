# Archive Directory

This directory contains outdated, superseded, or unimplemented code and documentation from the PROVES Library project evolution.

## Archive Organization

### curator-agent-old/
**Superseded curator agent scripts and documentation**
- Old monitoring scripts, demo files, and design docs
- Replaced by simplified agent architecture in `curator-agent/`

Contents:
- `README_OLD.md` - Old README before simplification
- `AGENT_INTELLIGENCE_GUIDE.md` - Old training approach doc
- `DESIGN_ACTION_LEVEL_HITL.md` - Design doc for HITL patterns
- `demo_learning.py`, `quick_monitor.py` - Old demo/monitoring scripts

### legacy-agents/
**Superseded agent implementations**
- Old standalone agent architecture (before LangGraph Deep Agents)
- Replaced by: [curator-agent/](../curator-agent/)

Contents:
- `agents/` - Old agent design docs and incomplete implementations
- `curator_agent.py` - Standalone curator agent (superseded by Deep Agent system)

### design-docs/
**Design documents for unimplemented features**
- Components that were designed but never built
- Kept for future reference

Contents:
- `mcp-server/` - MCP server design (not implemented)
- `risk-scanner/` - Risk scanner design (not implemented)

### outdated-docs/
**Documentation that no longer reflects current architecture**
- Old setup guides, architecture docs
- Superseded by current documentation

Contents:
- `LANGSMITH_INTEGRATION.md` - Old LangSmith setup (tracing now disabled)
- `OPENTELEMETRY_INTEGRATION.md` - OpenTelemetry docs (not implemented)
- `GITHUB_ACTIONS_SETUP.md` - CI/CD docs (not yet implemented)
- `GITHUB_API_SYNC_QUICKSTART.md` - GitHub sync (not yet implemented)

### old-configs/
**Deprecated configuration templates**
- Old database configurations (Neo4j)
- Outdated environment templates

### historical/
**Point-in-time records**
- Setup logs from specific dates
- Status snapshots

## Why Archive Instead of Delete?

Archiving preserves:
1. **Historical context** - Understanding how the project evolved
2. **Design decisions** - Why certain approaches were chosen or abandoned
3. **Future reference** - Ideas that might be revisited later
4. **Attribution** - Credit for work done, even if superseded

## What's Current?

See [FOLDER_STRUCTURE.md](../FOLDER_STRUCTURE.md) for the current project organization.

---

Last Updated: December 22, 2025
