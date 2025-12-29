# MCP Multi-Server Setup Guide

Complete guide for setting up and using multiple MCP servers with the PROVES Library.

## Quick Start (PROVES Only)

### 1. Start the PROVES MCP Server

```bash
# Terminal 1: Start PROVES MCP server
cd mcp-server
proves-mcp --transport streamable-http --port 8000
```

### 2. Run the Example

```bash
# Terminal 2: Run example agent
python examples/quick_start_mcp.py
```

## Multi-Server Setup

### Available Servers

| Server | Purpose | Installation | Transport |
|--------|---------|--------------|-----------|
| **PROVES Library** | Knowledge graph queries | `pip install -e mcp-server/` | HTTP |
| **Filesystem** | File operations | `npm install -g @modelcontextprotocol/server-filesystem` | stdio |
| **GitHub** | Repository access | `npm install -g @modelcontextprotocol/server-github` | stdio |

### Configuration

Create a `.env` file or export environment variables:

```bash
# Required for PROVES
export NEON_DATABASE_URL="postgresql://user:pass@host/db"
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional: Enable additional servers
export ENABLE_FILESYSTEM_MCP=true
export WORKSPACE_PATH="/path/to/workspace"

export ENABLE_GITHUB_MCP=true
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_..."
```

### Start All Servers

```bash
# Terminal 1: PROVES MCP (always required)
proves-mcp --transport streamable-http --port 8000

# Filesystem and GitHub are started automatically by MultiServerMCPClient
# when ENABLE_*_MCP=true
```

### Run Multi-Server Example

```bash
python examples/multi_server_agent.py
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   LangChain Agent (Curator)                 │
│                                                             │
│  MultiServerMCPClient                                       │
│  ├── proves (HTTP: localhost:8000)                          │
│  │   Tools: search_library, get_entry, find_conflicts      │
│  │                                                          │
│  ├── filesystem (stdio: subprocess)                         │
│  │   Tools: read_file, write_file, list_directory          │
│  │                                                          │
│  └── github (stdio: subprocess)                             │
│      Tools: get_file_contents, search_repositories         │
└─────────────────────────────────────────────────────────────┘
```

## PROVES MCP Tools

### Fast Tools (Database-backed, ~50ms)

- **search_library**: Semantic + keyword search
- **get_entry**: Fetch full entry content
- **get_relationships**: Component dependencies/conflicts
- **find_conflicts**: I2C address collisions, timing conflicts
- **list_components**: Browse indexed components

### Registry Tools

- **get_source_locations**: Find where to look in F'/ProvesKit
- **get_hardware_info**: I2C addresses, driver mappings

### Deep Tools (Agent-backed, 2-10s) - Coming Soon

- **deep_search**: Search F'/ProvesKit docs not yet indexed
- **analyze_component**: Full component profile
- **check_compatibility**: Reasoning about compatibility

## Example Queries

### 1. Knowledge Graph Query

```python
await agent.ainvoke({
    "messages": [{
        "role": "user",
        "content": "What conflicts with the MS5611 barometer?"
    }]
})
```

### 2. Dimensional Metadata

```python
await agent.ainvoke({
    "messages": [{
        "role": "user",
        "content": "Search for embodied knowledge about reaction wheel bearings. What tacit knowledge exists?"
    }]
})
```

### 3. Source Lookup

```python
await agent.ainvoke({
    "messages": [{
        "role": "user",
        "content": "Where in the F' codebase should I look to learn about command dispatching?"
    }]
})
```

### 4. Multi-Server Workflow

```python
# Uses both PROVES and filesystem servers
await agent.ainvoke({
    "messages": [{
        "role": "user",
        "content": "Search PROVES for I2C conflicts, then save the results to conflicts.md"
    }]
})
```

## Troubleshooting

### PROVES Server Won't Start

```bash
# Check if port 8000 is available
netstat -an | grep 8000

# Or use different port
proves-mcp --transport streamable-http --port 8001
```

### Database Connection Error

```bash
# Check NEON_DATABASE_URL is set
echo $NEON_DATABASE_URL

# Test database connection
psql $NEON_DATABASE_URL -c "SELECT 1"
```

### Tools Not Available

```python
# List all available tools
client = MultiServerMCPClient({...})
tools = await client.get_tools()
for tool in tools:
    print(f"{tool.name}: {tool.description}")
```

### Filesystem/GitHub MCP Not Starting

```bash
# Ensure Node.js is installed
node --version

# Install MCP servers globally
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-github

# Test manually
npx @modelcontextprotocol/server-filesystem --help
```

## Next Steps

1. **Add Dimensional Metadata Tools**: Expose verified knowledge layer
2. **Implement Deep Search**: Connect curator agent for live extraction
3. **Add Custom Interceptors**: Inject user context, API keys
4. **Deploy to Production**: Use LangGraph Cloud with HTTP transport

## References

- [LangChain MCP Documentation](https://python.langchain.com/docs/integrations/tools/mcp)
- [PROVES MCP Integration Guide](../docs/MCP_INTEGRATION.md)
- [FastMCP Documentation](https://gofastmcp.com)
- [Model Context Protocol Spec](https://modelcontextprotocol.io/introduction)
