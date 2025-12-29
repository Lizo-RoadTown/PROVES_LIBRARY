# MCP Integration with LangChain

This guide shows how to use the PROVES Library MCP server with LangChain agents using `langchain-mcp-adapters`.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   LangChain Agent (Curator)                 │
│                                                             │
│  Uses langchain-mcp-adapters to access MCP tools            │
│  ↓                                                          │
│  MultiServerMCPClient                                       │
│  ├── PROVES Library MCP (fast tools: search, get_entry)    │
│  ├── Other MCP Servers (filesystem, github, etc.)          │
│  └── Custom domain-specific MCP servers                    │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
pip install langchain-mcp-adapters
```

This installs:
- `langchain-mcp-adapters` (0.2.1) - LangChain integration layer
- `mcp` (1.25.0) - Official Model Context Protocol SDK

## Quick Start

### Option 1: stdio Transport (Local Development)

Use this when running the MCP server as a subprocess:

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

client = MultiServerMCPClient({
    "proves": {
        "transport": "stdio",
        "command": "python",
        "args": ["-m", "proves_mcp.server"],
    }
})

tools = await client.get_tools()
agent = create_agent("claude-sonnet-4-5-20250929", tools)

response = await agent.ainvoke({
    "messages": [{"role": "user", "content": "Search for MS5611 conflicts"}]
})
```

### Option 2: HTTP Transport (Production)

Use this when the MCP server is running as a separate service:

```bash
# Start the MCP server (in separate terminal)
cd mcp-server
python -m proves_mcp.server --transport streamable-http --port 8000
```

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

client = MultiServerMCPClient({
    "proves": {
        "transport": "http",
        "url": "http://localhost:8000/mcp",
    }
})

tools = await client.get_tools()
agent = create_agent("claude-sonnet-4-5-20250929", tools)
```

## Integration with Curator Agent

### Adding MCP Tools to Existing Agent

If you already have a curator agent, add MCP tools alongside existing tools:

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from production.curator.subagents.extractor import fetch_webpage
from langchain.agents import create_agent

# Your existing tools
existing_tools = [
    fetch_webpage,
    # ... other tools
]

# Add MCP tools
client = MultiServerMCPClient({
    "proves": {
        "transport": "http",
        "url": "http://localhost:8000/mcp",
    }
})

mcp_tools = await client.get_tools()

# Combine tools
all_tools = existing_tools + mcp_tools

agent = create_agent("claude-sonnet-4-5-20250929", all_tools)
```

### Using Tool Interceptors for Context

Add runtime context (user ID, API keys, etc.) to MCP tool calls:

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.interceptors import MCPToolCallRequest

async def inject_database_credentials(
    request: MCPToolCallRequest,
    handler,
):
    """Inject Neon database credentials into MCP tool calls."""
    runtime = request.runtime

    # Add database URL from environment
    modified_request = request.override(
        args={
            **request.args,
            "database_url": os.getenv("NEON_DATABASE_URL")
        }
    )
    return await handler(modified_request)

client = MultiServerMCPClient(
    {
        "proves": {
            "transport": "http",
            "url": "http://localhost:8000/mcp",
        }
    },
    tool_interceptors=[inject_database_credentials],
)
```

### Accessing Dimensional Metadata via MCP

Your MCP server can expose dimensional metadata from the verified knowledge layer:

```python
# MCP server tool (in mcp-server/src/proves_mcp/server.py)
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("PROVES")

@mcp.tool()
async def get_entity_with_dimensions(entity_id: str) -> dict:
    """Get entity with full dimensional metadata."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                canonical_key,
                knowledge_form, knowledge_form_confidence,
                contact_level, contact_confidence,
                directionality, directionality_confidence,
                temporality, temporality_confidence,
                formalizability, formalizability_confidence,
                carrier, carrier_confidence,
                needs_human_review
            FROM core_entities
            WHERE id = %s AND is_current = TRUE
        """, (entity_id,))
        result = cur.fetchone()

    return {
        "entity": result["canonical_key"],
        "dimensions": {
            "knowledge_form": {
                "value": result["knowledge_form"],
                "confidence": result["knowledge_form_confidence"]
            },
            # ... other dimensions
        },
        "needs_review": result["needs_human_review"]
    }
```

## Multi-Server Configuration

Combine PROVES Library tools with other MCP servers:

```python
client = MultiServerMCPClient({
    "proves": {
        "transport": "http",
        "url": "http://localhost:8000/mcp",
    },
    "filesystem": {
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/workspace"],
    },
    "github": {
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
    }
})

tools = await client.get_tools()
# Now your agent has access to:
# - PROVES Library search/query tools
# - Filesystem operations
# - GitHub API access
```

## Advanced Features

### Progress Notifications for Long Extractions

Track progress of long-running extraction tasks:

```python
from langchain_mcp_adapters.callbacks import Callbacks, CallbackContext

async def on_progress(
    progress: float,
    total: float | None,
    message: str | None,
    context: CallbackContext,
):
    percent = (progress / total * 100) if total else progress
    print(f"[{context.server_name}] {percent:.1f}% - {message}")

client = MultiServerMCPClient(
    {"proves": {...}},
    callbacks=Callbacks(on_progress=on_progress),
)
```

### Stateful Sessions for Validator Agent

When the validator agent needs to maintain context across multiple checks:

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

client = MultiServerMCPClient({"proves": {...}})

# Create persistent session
async with client.session("proves") as session:
    tools = await load_mcp_tools(session)

    # Validator can now make multiple tool calls
    # with shared context
    agent = create_agent("claude-3-5-haiku-20241022", tools)

    # All validation checks share the same session
    result = await agent.ainvoke({...})
```

### Resource Access for Documentation

Load PROVES documentation as resources:

```python
# Load all available documentation
blobs = await client.get_resources("proves")

for blob in blobs:
    print(f"Document: {blob.metadata['uri']}")
    print(f"Content: {blob.as_string()[:200]}...")
```

## Example: Full Curator Workflow with MCP

```python
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent

async def run_curator_with_mcp():
    """Run curator agent with PROVES MCP tools."""

    # Initialize MCP client
    client = MultiServerMCPClient({
        "proves": {
            "transport": "http",
            "url": "http://localhost:8000/mcp",
            "headers": {
                "X-API-Key": os.getenv("PROVES_API_KEY"),
            }
        }
    })

    # Get MCP tools
    tools = await client.get_tools()

    # Create agent
    model = ChatAnthropic(model="claude-sonnet-4-5-20250929")
    agent = create_agent(model, tools)

    # Run extraction workflow
    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "Extract architecture from https://nasa.github.io/fprime/UsersGuide/user/command-and-data-handling.html"
        }]
    })

    print("Extraction complete!")
    print(result["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(run_curator_with_mcp())
```

## Deployment Options

### Local Development (stdio)
- **Pros**: Easy debugging, no network overhead
- **Cons**: New subprocess per agent run (unless using stateful sessions)
- **Use case**: Development, testing

### HTTP Server (streamable-http)
- **Pros**: Persistent server, multiple clients, production-ready
- **Cons**: Network latency, requires server management
- **Use case**: Production deployments, multi-agent systems

### LangGraph Cloud Deployment
- Deploy MCP server alongside your LangGraph agent
- Use HTTP transport for inter-service communication
- Configure via environment variables

## Troubleshooting

### MCP Server Not Found
```bash
# Ensure mcp-server is installed
pip install -e mcp-server/
```

### Connection Refused (HTTP)
```bash
# Start the MCP server
cd mcp-server
python -m proves_mcp.server --transport streamable-http --port 8000
```

### Tool Not Available
```python
# List available tools
tools = await client.get_tools()
for tool in tools:
    print(f"{tool.name}: {tool.description}")
```

## Next Steps

1. **Install mcp-server package**: `pip install -e mcp-server/`
2. **Start MCP server**: See [mcp-server/README.md](../mcp-server/README.md)
3. **Integrate with curator**: Add MCP tools to your extraction workflow
4. **Expose dimensional metadata**: Create MCP tools for verified knowledge layer
5. **Deploy to production**: Use HTTP transport with LangGraph Cloud

## References

- [LangChain MCP Documentation](https://python.langchain.com/docs/integrations/tools/mcp)
- [Model Context Protocol Spec](https://modelcontextprotocol.io/introduction)
- [PROVES MCP Server](../mcp-server/README.md)
- [langchain-mcp-adapters GitHub](https://github.com/langchain-ai/langchain-mcp-adapters)
