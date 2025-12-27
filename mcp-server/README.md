# PROVES Library MCP Server

MCP (Model Context Protocol) server for querying the PROVES Library knowledge graph. Exposes both **fast** (database-only) and **deep** (agent-backed) tools.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           MCP SERVER                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  FAST TOOLS (Database)              DEEP TOOLS (Agent-backed)          │
│  ──────────────────────             ─────────────────────────          │
│  • search_library                   • deep_search                      │
│  • get_entry                        • analyze_component                │
│  • get_relationships                • extract_from_docs                │
│  • find_conflicts                                                       │
│         │                                    │                          │
│         ▼                                    ▼                          │
│  ┌─────────────┐                   ┌─────────────────────┐             │
│  │  Neon DB    │                   │   CURATOR AGENT     │             │
│  │  (pgvector) │                   │  (uses source       │             │
│  └─────────────┘                   │   registry)         │             │
│                                    └─────────────────────┘             │
└─────────────────────────────────────────────────────────────────────────┘
```

## Tools

### Fast Tools (50ms response)

| Tool | Description |
|------|-------------|
| `search_library` | Semantic + keyword search across indexed entries |
| `get_entry` | Fetch full content of a specific entry |
| `get_relationships` | Get what a component depends on / conflicts with |
| `find_conflicts` | Find known conflicts for a component |
| `list_components` | List all indexed components by domain |

### Deep Tools (2-10s response, agent-backed)

| Tool | Description |
|------|-------------|
| `deep_search` | Search F' and ProvesKit docs for anything not in DB |
| `analyze_component` | Full component profile from multiple sources |
| `check_compatibility` | Agent reasons about whether X works with Y |

## Source Registry

The `source_registry.yaml` file pre-maps all knowledge sources so agents know exactly where to look:

- F' component locations (`Svc/CmdDispatcher/`, `Drv/LinuxI2cDriver/`, etc.)
- ProvesKit hardware mappings (RV3032, BNO085, etc.)
- Query mappings (user asks about "I2C" -> search these paths)
- Known conflict patterns

## Installation

```bash
cd mcp-server
pip install -e .
```

## Configuration

Create `.env` file (or use parent directory's `.env`):

```env
# Database
NEON_DATABASE_URL=postgresql://user:pass@host/dbname

# For deep tools (agent-backed)
ANTHROPIC_API_KEY=sk-ant-...

# Optional
LOG_LEVEL=INFO
```

## Running

### Local Development (stdio transport)

```bash
proves-mcp
```

### Remote Server (HTTP transport)

```bash
proves-mcp --transport streamable-http --port 8000
```

## Usage with LangGraph Agent

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "proves": {
        "transport": "http",
        "url": "http://localhost:8000/mcp",
    }
})

tools = await client.get_tools()
# Now your agent has access to search_library, get_entry, etc.
```

## Usage with VS Code / Claude

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "proves-library": {
      "command": "proves-mcp",
      "args": []
    }
  }
}
```

## Example Queries

```
User: "What conflicts with the MS5611 barometer?"

-> search_library(query="MS5611 conflicts")
-> Returns: "MS5611 uses I2C address 0x76, which conflicts with BME280..."

User: "How does F' handle command dispatching?"

-> deep_search(query="F' command dispatching")
-> Agent searches source_registry.yaml -> finds Svc/CmdDispatcher/
-> Fetches and extracts relevant patterns
-> Returns synthesized answer + caches to DB
```

## Development

```bash
# Run tests
pytest tests/

# Type checking
mypy src/

# Format
black src/
```
