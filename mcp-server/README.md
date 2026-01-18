# PROVES Library MCP Server

MCP (Model Context Protocol) server for querying the PROVES Library knowledge base. Provides tools to search verified knowledge, find external documentation, and look up hardware specifications.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           MCP SERVER                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  KNOWLEDGE TOOLS              REGISTRY TOOLS        EXTERNAL DOC TOOLS  │
│  ───────────────             ─────────────          ────────────────    │
│  • search_knowledge          • get_source_locations • search_fprime_docs│
│  • get_entity                • get_hardware_info    • search_proveskit  │
│  • list_entities             • find_conflicts       • get_datasheet     │
│  • get_library_stats                                                    │
│         │                           │                       │           │
│         ▼                           ▼                       ▼           │
│  ┌─────────────┐          ┌────────────────┐      ┌────────────────┐   │
│  │  Supabase   │          │ source_registry│      │ External Links │   │
│  │  (pgvector) │          │    .yaml       │      │  F', PROVES,   │   │
│  └─────────────┘          └────────────────┘      │  Datasheets    │   │
│                                                   └────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Tools

### Knowledge Search Tools

| Tool | Description |
|------|-------------|
| `search_knowledge` | Search verified entities and pending extractions |
| `get_entity` | Fetch full content of a verified entity |
| `list_entities` | List verified entities by ecosystem/type |
| `get_library_stats` | Get counts of entities and extractions |

### Source Registry Tools

| Tool | Description |
|------|-------------|
| `get_source_locations` | Get paths to search in F' and PROVES Kit repos |
| `get_hardware_info` | Hardware specs, I2C addresses, driver mappings |
| `find_conflicts` | Find I2C address conflicts and known incompatibilities |

### External Documentation Tools

| Tool | Description |
|------|-------------|
| `search_fprime_docs` | Get links to relevant F' documentation |
| `search_proveskit_docs` | Get links to PROVES Kit repos and docs |
| `get_datasheet_links` | Get manufacturer datasheet URLs |

## Source Registry

The `source_registry.yaml` file pre-maps all knowledge sources:

- F' component locations (`Svc/CmdDispatcher/`, `Drv/LinuxI2cDriver/`, etc.)
- ProvesKit hardware mappings (RV3032, BNO085, MS5611, etc.)
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
# Database (Supabase)
DATABASE_URL=postgresql://postgres:pass@db.your-project.supabase.co:5432/postgres

# Optional: For deep tools (agent-backed)
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

### Docker Deployment

The MCP server ships as a Docker container for production use.

#### Quick Start

```bash
# Build the image
docker build -t proves-mcp .

# Run with environment variables
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  proves-mcp
```

#### Using Docker Compose

```bash
# Production
docker-compose up -d proves-mcp

# Development (with hot-reload)
docker-compose --profile dev up proves-mcp-dev
```

#### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string (Supabase) |
| `NEXT_PUBLIC_SUPABASE_URL` | No | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | No | Supabase anon key |
| `ANTHROPIC_API_KEY` | No | For deep agent tools |
| `LOG_LEVEL` | No | DEBUG, INFO, WARNING, ERROR (default: INFO) |
| `MCP_PORT` | No | Server port (default: 8000) |

#### Docker Compose Environment

Create a `.env` file in the `mcp-server` directory:

```env
DATABASE_URL=postgresql://postgres:pass@db.your-project.supabase.co:5432/postgres
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
ANTHROPIC_API_KEY=sk-ant-...
LOG_LEVEL=INFO
MCP_PORT=8000
```

#### Transport Modes

- **stdio** (default): For local IDE integrations (Claude Code, VS Code)
- **streamable-http**: For Docker/remote deployment

When running in Docker, the server automatically uses `streamable-http` transport on port 8000.

#### Health Check

The container includes a health check. You can also query:

```bash
# Using MCP tool
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "health_check"}}'
```

#### Security Considerations

When exposing the MCP server over HTTP:

1. **Use HTTPS** in production (terminate TLS at load balancer)
2. **Restrict Origins** - Configure allowed origins for CORS
3. **Network Isolation** - Run in private subnet, expose only through API gateway
4. **Authentication** - Add auth layer (API keys, JWT) at the gateway level

## Usage with Claude Code / VS Code

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

### Connecting to Docker Server

For remote MCP server (Docker), use HTTP transport:

```json
{
  "mcpServers": {
    "proves-library": {
      "transport": "streamable-http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Dashboard Integration

The curation dashboard connects to the MCP server via HTTP. Configure the endpoint:

```typescript
// In dashboard .env.local
NEXT_PUBLIC_MCP_SERVER_URL=http://localhost:8000
```

Or in production:

```typescript
NEXT_PUBLIC_MCP_SERVER_URL=https://mcp.your-domain.com
```

## Example Queries

```
User: "What conflicts with the MS5611 barometer?"

-> get_hardware_info(hardware_name="ms5611")
-> find_conflicts(component="ms5611")
-> Returns: MS5611 uses I2C address 0x76, which conflicts with BME280...

User: "How does F' handle command dispatching?"

-> search_fprime_docs(query="command dispatching")
-> get_source_locations(topic="commands")
-> Returns: Links to F' docs + paths in repo to check

User: "What's the BNO085 I2C address?"

-> get_hardware_info(hardware_name="bno085")
-> Returns: I2C address 0x4A or 0x4B, with datasheet link
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
