"""
Test MCP Setup

Verifies that the MCP server and client are properly configured.
Run this before using the multi-server examples.
"""

import asyncio
import os
import sys


async def test_server_running():
    """Test if PROVES MCP server is running."""
    print("\n1. Testing PROVES MCP server connection...")
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            # Try to connect to the server
            try:
                response = await client.get("http://localhost:8000/health", timeout=2.0)
                print("   ✓ Server is running on port 8000")
                return True
            except httpx.ConnectError:
                print("   ❌ Server not running on port 8000")
                print("      Start it with: proves-mcp --transport streamable-http --port 8000")
                return False
            except Exception as e:
                print(f"   ⚠ Connection error: {e}")
                return False
    except ImportError:
        print("   ⚠ httpx not installed, skipping server check")
        return None


async def test_mcp_client():
    """Test if MCP client can connect and list tools."""
    print("\n2. Testing MCP client connection...")
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        client = MultiServerMCPClient({
            "proves": {
                "transport": "http",
                "url": "http://localhost:8000/mcp",
            }
        })

        print("   ✓ MultiServerMCPClient created")

        # Try to get tools
        try:
            tools = await client.get_tools()
            print(f"   ✓ Successfully loaded {len(tools)} tools")
            print("\n   Available tools:")
            for tool in tools:
                print(f"     - {tool.name}")
            return True
        except Exception as e:
            print(f"   ❌ Failed to get tools: {e}")
            return False

    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        print("      Install with: pip install langchain-mcp-adapters")
        return False


async def test_anthropic_key():
    """Test if Anthropic API key is set."""
    print("\n3. Testing Anthropic API key...")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("   ❌ ANTHROPIC_API_KEY not set")
        print("      Set it with: export ANTHROPIC_API_KEY=sk-ant-...")
        return False
    elif api_key.startswith("sk-ant-"):
        print("   ✓ API key is set")
        return True
    else:
        print("   ⚠ API key format looks incorrect (should start with sk-ant-)")
        return False


async def test_database_connection():
    """Test if database connection is configured."""
    print("\n4. Testing database configuration...")
    db_url = os.getenv("NEON_DATABASE_URL")
    if not db_url:
        print("   ⚠ NEON_DATABASE_URL not set")
        print("      Set it in .env file or export NEON_DATABASE_URL=...")
        print("      (Optional for testing, required for database tools)")
        return None
    else:
        print("   ✓ Database URL is set")
        # Don't actually test connection to avoid requiring psycopg
        return True


async def test_proves_package():
    """Test if proves-mcp-server package is installed."""
    print("\n5. Testing proves-mcp-server installation...")
    try:
        import proves_mcp
        print("   ✓ proves-mcp-server package is installed")
        return True
    except ImportError:
        print("   ❌ proves-mcp-server not installed")
        print("      Install with: pip install -e mcp-server/")
        return False


async def test_langchain_packages():
    """Test if required LangChain packages are installed."""
    print("\n6. Testing LangChain packages...")
    missing = []

    try:
        import langchain_anthropic
        print("   ✓ langchain-anthropic")
    except ImportError:
        print("   ❌ langchain-anthropic")
        missing.append("langchain-anthropic")

    try:
        import langchain_mcp_adapters
        print("   ✓ langchain-mcp-adapters")
    except ImportError:
        print("   ❌ langchain-mcp-adapters")
        missing.append("langchain-mcp-adapters")

    try:
        import langchain
        print("   ✓ langchain")
    except ImportError:
        print("   ❌ langchain")
        missing.append("langchain")

    if missing:
        print(f"\n   Install missing packages: pip install {' '.join(missing)}")
        return False

    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("MCP Setup Test Suite")
    print("=" * 60)

    results = {}

    # Run all tests
    results["packages"] = await test_langchain_packages()
    results["proves_package"] = await test_proves_package()
    results["api_key"] = await test_anthropic_key()
    results["database"] = await test_database_connection()
    results["server"] = await test_server_running()
    results["client"] = await test_mcp_client()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)

    print(f"✓ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    if skipped:
        print(f"⚠ Skipped: {skipped}")

    if failed == 0:
        print("\n🎉 All tests passed! You're ready to use MCP.")
        print("\nNext steps:")
        print("1. Run quick start: python examples/quick_start_mcp.py")
        print("2. Try multi-server: python examples/multi_server_agent.py")
        return 0
    else:
        print("\n⚠ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
