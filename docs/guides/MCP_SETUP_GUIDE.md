# MCP Server Setup Guide for PROVES Library

This guide will help you configure the MCP (Model Context Protocol) servers needed for the PROVES Library agentic AI system.

## Overview

The PROVES Library uses two MCP servers:

1. **Neon Database MCP** - Provides tools to query and manage your PostgreSQL database
2. **LangChain MCP** - Provides LangChain tools for agent orchestration and RAG

## Prerequisites

- VSCode with Claude Code extension installed
- Neon database account and project created
- LangChain API account (optional, for tracing)
- Anthropic API key (for Claude agents)

---

## Step 1: Get Your Neon Database Credentials

### 1.1 Log in to Neon Console
Go to [https://console.neon.tech/](https://console.neon.tech/)

### 1.2 Get Your Project Details
From your Neon dashboard:

1. **API Key**: Settings -> API Keys -> Generate New Key
2. **Project ID**: Copy from project URL or dashboard
3. **Database Connection String**: Click "Connection Details" on your database

Your connection string will look like:
```
postgresql://username:password@ep-xxx-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

### 1.3 Fill in `.env` File
Open the `.env` file in the root of this repo and fill in:

```bash
NEON_API_KEY=neon_api_xxxxxxxxxxxxxxxxxx
NEON_PROJECT_ID=ep-xxx-xxx
NEON_DATABASE_URL=postgresql://username:password@ep-xxx.aws.neon.tech/neondb?sslmode=require

# Parse out the individual components:
PGHOST=ep-xxx-xxx.us-east-2.aws.neon.tech
PGPORT=5432
PGDATABASE=neondb
PGUSER=username
PGPASSWORD=password
```

---

## Step 2: Configure VSCode MCP Servers

### 2.1 Locate Your Claude Code Settings

The MCP servers are configured in your Claude Code settings file, typically at:
- **Windows**: `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`
- **Mac/Linux**: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

### 2.2 Expected Configuration

Your MCP settings should include both servers:

```json
{
  "mcpServers": {
    "neon": {
      "command": "npx",
      "args": ["-y", "@neondatabase/mcp-server-neon"],
      "env": {
        "NEON_API_KEY": "${NEON_API_KEY}",
        "NEON_DATABASE_URL": "${NEON_DATABASE_URL}"
      }
    },
    "langchain": {
      "command": "npx",
      "args": ["-y", "@langchain/mcp-server"],
      "env": {
        "LANGCHAIN_API_KEY": "${LANGCHAIN_API_KEY}",
        "LANGCHAIN_TRACING_V2": "true",
        "LANGCHAIN_PROJECT": "proves-library"
      }
    }
  }
}
```

### 2.3 Environment Variable Loading

The `${VARIABLE_NAME}` syntax tells Claude Code to load values from your `.env` file. Make sure:
1. Your `.env` file is in the workspace root
2. VSCode is opened to the PROVES_LIBRARY folder
3. You restart VSCode after creating/editing `.env`

---

## Step 3: Verify MCP Server Connection

### 3.1 Check VSCode Output Panel
1. Open VSCode Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
2. Type "Output: Show Output"
3. Select "Claude Code" from the dropdown
4. Look for these success messages:

```
[info] Starting server neondatabase/mcp-server-neon
[info] Connection state: Running
[info] Discovered 27 tools
```

### 3.2 Common Issues

**Issue: "404 status sending message to https://mcp.neon.tech/sse"**
- **Cause**: Missing or invalid `NEON_API_KEY`
- **Fix**: Double-check your API key in `.env` and restart VSCode

**Issue: "Error reading SSE stream: terminated"**
- **Cause**: Network timeout or invalid credentials
- **Fix**: Check your internet connection and verify database URL

**Issue: "Could not fetch resource metadata"**
- **Cause**: Database doesn't exist or user lacks permissions
- **Fix**: Create database in Neon console and verify user permissions

---

## Step 4: Test Database Connection

Once connected, you should be able to ask me (Claude) to:

1. **List databases**: "Show me what databases are available in Neon"
2. **Query tables**: "List all tables in the proves_library database"
3. **Run SQL**: "Create a test table called 'hello_world' with an id column"

If I can execute these commands, your Neon MCP is working!

---

## Step 5: Configure LangChain MCP (Optional)

LangChain MCP provides tools for:
- Document loading and splitting
- Vector store management
- Agent tool creation
- Prompt template management

### 5.1 Get LangChain API Key
1. Go to [https://smith.langchain.com/](https://smith.langchain.com/)
2. Sign in or create account
3. Navigate to Settings -> API Keys
4. Create a new API key

### 5.2 Add to `.env`
```bash
LANGCHAIN_API_KEY=lsv2_pt_xxxxxxxxxxxxxxxx
LANGCHAIN_PROJECT=proves-library
LANGCHAIN_TRACING_V2=true
```

### 5.3 Restart VSCode
Close and reopen VSCode to reload MCP servers with new credentials.

---

## Step 6: Initialize Database Schema

Once connected, we'll create the initial database schema for:
1. **Knowledge graph tables** (ERV relationships)
2. **Library metadata index** (markdown entry tracking)
3. **Agent state storage** (curator/builder workflows)

This will be done in the next setup phase.

---

## Troubleshooting

### MCP Server Not Starting
1. Check VSCode output panel for specific error messages
2. Verify `npx` is available: `npx --version`
3. Clear npm cache: `npx clear-npx-cache`
4. Manually test server: `npx -y @neondatabase/mcp-server-neon`

### Environment Variables Not Loading
1. Ensure `.env` file is in workspace root (not a subdirectory)
2. Check file has no BOM (byte order mark) - save as UTF-8
3. Variable names must match exactly (case-sensitive)
4. Restart VSCode after any `.env` changes

### Database Connection Fails
1. Test connection string manually: `psql "your_connection_string"`
2. Check SSL mode is set: `?sslmode=require`
3. Verify IP allowlist in Neon console (if applicable)
4. Check firewall isn't blocking port 5432

---

## Next Steps

Once both MCP servers are connected and showing "Running" status:

1. [YES] Initialize database schema
2. [YES] Create initial ERV relationship types
3. [YES] Set up vector embeddings table
4. [YES] Test knowledge graph queries
5. [YES] Begin implementing Curator agent

You're ready to build the agentic AI system!

---

## References

- [Neon MCP Server Docs](https://github.com/neondatabase/mcp-server-neon)
- [LangChain MCP Server Docs](https://github.com/langchain-ai/langchain-mcp)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Claude Code MCP Guide](https://github.com/anthropics/claude-code)
