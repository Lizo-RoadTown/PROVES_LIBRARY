# Archive Directory

This directory contains outdated, superseded, or unimplemented code and documentation from the PROVES Library project evolution.

## Archive Organization

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

### old-configs/
**Deprecated configuration templates**
- Old database configurations (Neo4j)
- Outdated environment templates

Contents:
- `.env.template` - Old template with Neo4j config (use `.env.example` instead)

## Why Archive Instead of Delete?

Archiving preserves:
1. **Historical context** - Understanding how the project evolved
2. **Design decisions** - Why certain approaches were chosen or abandoned
3. **Future reference** - Ideas that might be revisited later
4. **Attribution** - Credit for work done, even if superseded

## What's Current?

See [FOLDER_STRUCTURE.md](../FOLDER_STRUCTURE.md) for the current project organization.

---

Archived: December 21, 2024
