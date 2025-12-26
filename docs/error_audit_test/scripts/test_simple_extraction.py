"""
Simple direct test of the optimized curator agent.
Tests the full flow: extract -> validate -> stage for human verification
"""

import os
import sys
from dotenv import load_dotenv
from langgraph.types import Command

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.curator.agent import graph


def test_extraction():
    """Test extracting a dependency from fprime I2C driver and staging it."""

    task = """Extract dependencies from ../trial_docs/fprime_i2c_driver_full.md.

Find the dependency where ImuManager depends on LinuxI2cDriver.

Use your extractor sub-agent to find it, then stage it for human verification.

Be direct and focused - just find this one dependency."""

    config = {"configurable": {"thread_id": "simple-test-1"}}

    print("=", * 80)
    print("SIMPLE EXTRACTION TEST")
    print("=" * 80)
    print()
    print("Task: Extract ImuManager -> LinuxI2cDriver dependency")
    print("Expected: Dependency staged for human verification")
    print()
    print("-" * 80)
    print()

    # Run agent
    result = graph.invoke({
        "messages": [{"role": "user", "content": task}]
    }, config)

    # Check for interrupt
    state = graph.get_state(config)

    if "__interrupt__" in state.values:
        interrupt_data = state.values["__interrupt__"]

        print()
        print("=" * 80)
        print("HITL APPROVAL REQUEST")
        print("=" * 80)
        print()
        print(f"Type: {interrupt_data.get('type')}")
        print(f"Task: {interrupt_data.get('task')}")
        print(f"Criticality: {interrupt_data.get('criticality')}")
        print()

        # Auto-approve for test
        print("Auto-approving for test...")
        result = graph.invoke(Command(resume="approved"), config)

    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print()

    # Show final message
    if result and "messages" in result:
        final_msg = result["messages"][-1]
        if hasattr(final_msg, 'content'):
            print(final_msg.content)

    return result


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(line_buffering=True)  # Unbuffered output
    test_extraction()
