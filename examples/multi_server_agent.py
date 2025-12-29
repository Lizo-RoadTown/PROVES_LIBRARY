"""
Multi-Server MCP Integration Example

This demonstrates how to use multiple MCP servers with a LangChain agent:
- PROVES Library MCP (knowledge graph queries)
- Filesystem MCP (file operations)
- GitHub MCP (optional - repository access)

The agent can seamlessly use tools from all servers.
"""

import asyncio
import os
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.callbacks import Callbacks, CallbackContext
from langchain_mcp_adapters.interceptors import MCPToolCallRequest
from mcp.types import LoggingMessageNotificationParams


# ============================================
# Callbacks for Progress and Logging
# ============================================

async def on_progress(
    progress: float,
    total: float | None,
    message: str | None,
    context: CallbackContext,
):
    """Handle progress updates from MCP servers."""
    percent = (progress / total * 100) if total else progress
    tool_info = f" ({context.tool_name})" if context.tool_name else ""
    print(f"[{context.server_name}{tool_info}] Progress: {percent:.1f}% - {message}")


async def on_logging_message(
    params: LoggingMessageNotificationParams,
    context: CallbackContext,
):
    """Handle log messages from MCP servers."""
    print(f"[{context.server_name}] {params.level}: {params.data}")


# ============================================
# Tool Interceptors
# ============================================

async def inject_database_credentials(
    request: MCPToolCallRequest,
    handler,
):
    """Inject database credentials for PROVES Library tools."""
    # Only inject for PROVES server tools
    if request.server_name == "proves":
        # Add database URL from environment if needed
        modified_request = request.override(
            args={
                **request.args,
                # Add any server-specific context here
            }
        )
        return await handler(modified_request)

    return await handler(request)


async def logging_interceptor(
    request: MCPToolCallRequest,
    handler,
):
    """Log all tool calls for debugging."""
    print(f"\n>>> Calling {request.server_name}.{request.name}")
    print(f"    Args: {request.args}")

    result = await handler(request)

    print(f"<<< {request.name} completed")
    return result


# ============================================
# Multi-Server Configuration
# ============================================

def get_multi_server_client() -> MultiServerMCPClient:
    """
    Create a MultiServerMCPClient with all configured servers.

    Servers:
    - proves: PROVES Library knowledge graph (HTTP)
    - filesystem: File operations (stdio) [OPTIONAL]
    - github: GitHub repository access (stdio) [OPTIONAL]
    """

    # Base configuration - PROVES Library is always included
    config = {
        "proves": {
            "transport": "http",
            "url": "http://localhost:8000/mcp",
            "headers": {
                # Add any custom headers here
                "X-Client": "PROVES-Curator",
            }
        }
    }

    # Optional: Add filesystem MCP server
    # Requires: npm install -g @modelcontextprotocol/server-filesystem
    if os.getenv("ENABLE_FILESYSTEM_MCP", "false").lower() == "true":
        workspace_path = os.getenv("WORKSPACE_PATH", str(Path.cwd()))
        config["filesystem"] = {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", workspace_path]
        }
        print(f"✓ Filesystem MCP enabled: {workspace_path}")

    # Optional: Add GitHub MCP server
    # Requires: npm install -g @modelcontextprotocol/server-github
    # Requires: GITHUB_PERSONAL_ACCESS_TOKEN in environment
    if os.getenv("ENABLE_GITHUB_MCP", "false").lower() == "true":
        if os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN"):
            config["github"] = {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"]
            }
            print("✓ GitHub MCP enabled")
        else:
            print("⚠ GitHub MCP disabled: GITHUB_PERSONAL_ACCESS_TOKEN not set")

    # Create client with callbacks and interceptors
    client = MultiServerMCPClient(
        config,
        callbacks=Callbacks(
            on_progress=on_progress,
            on_logging_message=on_logging_message,
        ),
        tool_interceptors=[
            logging_interceptor,
            inject_database_credentials,
        ]
    )

    return client


# ============================================
# Example Agent Workflows
# ============================================

async def example_knowledge_query():
    """
    Example: Search PROVES Library for knowledge about I2C conflicts.
    """
    print("\n" + "="*60)
    print("Example 1: Knowledge Graph Query")
    print("="*60)

    client = get_multi_server_client()
    tools = await client.get_tools()

    print(f"✓ Loaded {len(tools)} tools from {len(client._server_configs)} server(s)")

    # Create agent
    model = ChatAnthropic(model="claude-sonnet-4-5-20250929")
    agent = create_agent(model, tools)

    # Run query
    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "Search the PROVES Library for known I2C address conflicts. What components conflict with each other?"
        }]
    })

    print("\n--- Agent Response ---")
    print(result["messages"][-1].content)


async def example_multi_server_workflow():
    """
    Example: Use multiple servers in one workflow.

    Demonstrates using both PROVES Library and filesystem tools.
    """
    print("\n" + "="*60)
    print("Example 2: Multi-Server Workflow")
    print("="*60)

    client = get_multi_server_client()
    tools = await client.get_tools()

    # Group tools by server
    tools_by_server = {}
    for tool in tools:
        server = tool.name.split('_')[0] if '_' in tool.name else 'unknown'
        if server not in tools_by_server:
            tools_by_server[server] = []
        tools_by_server[server].append(tool.name)

    print("\n✓ Available tools by server:")
    for server, tool_names in tools_by_server.items():
        print(f"  [{server}]: {len(tool_names)} tools")
        for name in tool_names[:3]:  # Show first 3
            print(f"    - {name}")
        if len(tool_names) > 3:
            print(f"    ... and {len(tool_names) - 3} more")

    # Create agent
    model = ChatAnthropic(model="claude-sonnet-4-5-20250929")
    agent = create_agent(model, tools)

    # Example workflow: Search PROVES and optionally save results to file
    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "Search the PROVES Library for information about the MS5611 barometer. Show me what you find."
        }]
    })

    print("\n--- Agent Response ---")
    print(result["messages"][-1].content)


async def example_dimensional_metadata_query():
    """
    Example: Query verified knowledge layer with dimensional metadata.

    This shows how to access Knowledge Canonicalization data through MCP.
    """
    print("\n" + "="*60)
    print("Example 3: Dimensional Metadata Query")
    print("="*60)

    client = get_multi_server_client()
    tools = await client.get_tools()

    model = ChatAnthropic(model="claude-sonnet-4-5-20250929")
    agent = create_agent(model, tools)

    # Query for entities with specific dimensional characteristics
    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": """Search the PROVES Library for knowledge about reaction wheel bearings.

            I'm particularly interested in:
            1. What failures or issues are documented?
            2. What's the epistemic grounding of this knowledge (embodied vs inferred)?
            3. Are there any temporal patterns (history, lifecycle)?
            """
        }]
    })

    print("\n--- Agent Response ---")
    print(result["messages"][-1].content)


async def example_source_registry_lookup():
    """
    Example: Use the source registry to find where to look for specific topics.
    """
    print("\n" + "="*60)
    print("Example 4: Source Registry Lookup")
    print("="*60)

    client = get_multi_server_client()
    tools = await client.get_tools()

    model = ChatAnthropic(model="claude-sonnet-4-5-20250929")
    agent = create_agent(model, tools)

    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "Where should I look in the F' codebase to learn about command dispatching? Give me the specific paths."
        }]
    })

    print("\n--- Agent Response ---")
    print(result["messages"][-1].content)


# ============================================
# Main Entry Point
# ============================================

async def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("Multi-Server MCP Integration Examples")
    print("="*60)
    print("\nBefore running:")
    print("1. Start the PROVES MCP server:")
    print("   cd mcp-server")
    print("   proves-mcp --transport streamable-http --port 8000")
    print()
    print("2. Optionally enable filesystem/GitHub servers:")
    print("   export ENABLE_FILESYSTEM_MCP=true")
    print("   export ENABLE_GITHUB_MCP=true")
    print("   export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...")
    print()
    print("3. Ensure ANTHROPIC_API_KEY is set")
    print("="*60)

    # Check if PROVES server is likely running
    try:
        import httpx
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get("http://localhost:8000/health", timeout=2.0)
            print("✓ PROVES MCP server is running")
    except:
        print("⚠ PROVES MCP server not detected on port 8000")
        print("  Please start it first: proves-mcp --transport streamable-http --port 8000")
        return

    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not set")
        return

    print("✓ API key found")
    print()

    # Run examples
    try:
        await example_knowledge_query()
        await example_multi_server_workflow()
        await example_dimensional_metadata_query()
        await example_source_registry_lookup()

        print("\n" + "="*60)
        print("All examples completed!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
