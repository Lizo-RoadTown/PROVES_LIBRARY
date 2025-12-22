#!/usr/bin/env python3
"""
FULL EXTRACTION TEST - Extract ALL dependencies from a document
Shows that MEDIUM/LOW are stored automatically, only HIGH requires approval
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


def test_full_extraction():
    """Extract ALL dependencies from fprime I2C driver (not just one)."""

    task = """Extract ALL dependencies from ../trial_docs/fprime_i2c_driver_full.md.

Extract every dependency you can find - HIGH, MEDIUM, and LOW criticality.

For each dependency:
1. Extract the relationship (depends_on, requires, etc.)
2. Assess criticality based on impact
3. Store it (HIGH will require approval, MEDIUM/LOW auto-store)

Be thorough - find all dependencies in the document."""

    config = {"configurable": {"thread_id": "full-extraction-test"}}

    print("=" * 80)
    print("FULL EXTRACTION TEST")
    print("=" * 80)
    print()
    print("Task: Extract ALL dependencies from fprime I2C driver")
    print("Expected: Multiple dependencies found")
    print("  - HIGH criticality → approval prompts")
    print("  - MEDIUM/LOW → auto-stored")
    print()
    print("-" * 80)
    print()

    # Run agent
    state = graph.get_state(config)

    # Check if we're resuming
    if "__interrupt__" in state.values:
        print("RESUMING from previous interrupt...")
        result = graph.invoke(Command(resume="approved"), config)
        state = graph.get_state(config)
    else:
        print("STARTING fresh extraction...")
        result = graph.invoke({
            "messages": [{"role": "user", "content": task}]
        }, config)
        state = graph.get_state(config)

    # Handle interrupts in a loop
    approval_count = 0
    while "__interrupt__" in state.values:
        approval_count += 1
        interrupt_data = state.values["__interrupt__"]

        print()
        print("=" * 80)
        print(f"APPROVAL REQUEST #{approval_count}")
        print("=" * 80)
        print()
        print(f"Type: {interrupt_data.get('type')}")
        print(f"Task: {interrupt_data.get('task')}")
        print(f"Criticality: {interrupt_data.get('criticality')}")
        print()

        # Auto-approve for test
        print(f"Auto-approving HIGH dependency #{approval_count}...")
        result = graph.invoke(Command(resume="approved"), config)
        state = graph.get_state(config)

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

    print()
    print("-" * 80)
    print(f"Total HIGH criticality approvals: {approval_count}")
    print("(MEDIUM/LOW dependencies were auto-stored without approval)")
    print()

    return result


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(line_buffering=True)  # Unbuffered output
    test_full_extraction()
