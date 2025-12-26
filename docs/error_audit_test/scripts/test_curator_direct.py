"""
Direct interaction with curator agent for testing/debugging
"""
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.curator.agent import graph

# Configuration
config = {
    "configurable": {"thread_id": "test-session-001"},
    "recursion_limit": 25  # Increase from default 10
}

# Simple task
task = """
Fetch the PROVES Kit hardware overview page and extract ONE component with full metadata.

URL: https://docs.proveskit.space/en/latest/core_documentation/hardware/index.md

Extract just the Battery Board component with:
- Evidence quote from source
- Confidence reasoning
- Source citation

Then STOP. Don't extract everything, just demonstrate the workflow.
"""

print("=" * 80)
print("TESTING CURATOR DIRECTLY")
print("=" * 80)
print()
print("Task:", task)
print()
print("Starting...")
print()

# Invoke
result = graph.invoke(
    {"messages": [{"role": "user", "content": task}]},
    config
)

print()
print("=" * 80)
print("RESULT")
print("=" * 80)
print()
print("Final message:", result['messages'][-1].content)
