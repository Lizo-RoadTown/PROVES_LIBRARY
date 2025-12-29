"""
Quick Start: PROVES MCP with LangChain

Minimal example to get started with the PROVES Library MCP server.
"""

import asyncio
import os

from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient


async def main():
    """Simple PROVES Library MCP example."""

    print("Quick Start: PROVES Library MCP Integration")
    print("=" * 60)

    # Step 1: Create MCP client (PROVES server only)
    client = MultiServerMCPClient({
        "proves": {
            "transport": "http",
            "url": "http://localhost:8000/mcp",
        }
    })

    print("✓ MCP client created")

    # Step 2: Get available tools
    tools = await client.get_tools()
    print(f"✓ Loaded {len(tools)} tools from PROVES Library:")
    for tool in tools:
        print(f"  - {tool.name}")

    # Step 3: Create agent with Claude
    model = ChatAnthropic(model="claude-sonnet-4-5-20250929")
    agent = create_agent(model, tools)
    print("✓ Agent created with Claude Sonnet 4.5")

    # Step 4: Run a simple query
    print("\n" + "=" * 60)
    print("Running query: Search for I2C conflicts")
    print("=" * 60)

    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "Search the PROVES Library for I2C address conflicts. What do you find?"
        }]
    })

    # Step 5: Display result
    print("\n--- Response ---")
    print(result["messages"][-1].content)

    print("\n" + "=" * 60)
    print("✓ Quick start complete!")
    print("=" * 60)


if __name__ == "__main__":
    # Prerequisites check
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not set")
        print("   Please set your API key:")
        print("   export ANTHROPIC_API_KEY=sk-ant-...")
        exit(1)

    print("\nPrerequisites:")
    print("1. Start PROVES MCP server in another terminal:")
    print("   cd mcp-server")
    print("   proves-mcp --transport streamable-http --port 8000")
    print()
    print("2. Press Enter to continue...")
    input()

    asyncio.run(main())
