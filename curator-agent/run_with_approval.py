"""
Curator Agent with CLI-based Human-in-the-Loop Approval

This script runs the curator agent with command-line prompts for
approving HIGH criticality dependencies before they're stored.

Usage:
    python run_with_approval.py

Features:
- Pauses execution when HIGH criticality dependencies are detected
- Shows dependency details for human review
- Requires explicit approval before storage
- Maintains conversation state via SQLite checkpointer
- Visible progress with print statements
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


def run_curator_with_approval(task: str, thread_id: str = "curator-session-1"):
    """
    Run curator agent with CLI-based human approval for HIGH criticality dependencies.

    Args:
        task: The task to give the curator (e.g., "Extract dependencies from trial_docs/fprime_i2c_driver_full.md")
        thread_id: Unique ID for this conversation (for resuming)
    """
    config = {"configurable": {"thread_id": thread_id}}

    print("=" * 80)
    print("CURATOR AGENT - HUMAN-IN-THE-LOOP MODE")
    print("=" * 80)
    print()
    print(f"Task: {task}")
    print(f"Thread ID: {thread_id}")
    print()
    print("-" * 80)
    print()

    # Initial run
    print("Starting curator agent...")
    print()
    result = graph.invoke({
        "messages": [{"role": "user", "content": task}]
    }, config)

    # Loop to handle all interrupts
    while True:
        # Check if there are any interrupts
        state = graph.get_state(config)

        if "__interrupt__" not in state.values:
            # No more interrupts, agent is done
            break

        interrupt_data = state.values["__interrupt__"]

        # Handle dependency approval
        if interrupt_data.get("type") == "dependency_approval":
            print()
            print("=" * 80)
            print("APPROVAL REQUIRED - HIGH CRITICALITY DEPENDENCY")
            print("=" * 80)
            print()
            print(f"Task: {interrupt_data['task']}")
            print(f"Criticality: {interrupt_data['criticality']}")
            print()
            print(f"Message: {interrupt_data['message']}")
            print()
            print("This dependency is mission-critical. If it fails, the mission fails.")
            print()

            # Get human decision
            while True:
                decision = input("Approve this dependency? (yes/no): ").strip().lower()
                if decision in ['yes', 'y', 'no', 'n']:
                    break
                print("Please enter 'yes' or 'no'")

            print()

            # Resume with decision
            if decision in ['yes', 'y']:
                print("Resuming with approval...")
                result = graph.invoke(Command(resume="approved"), config)
            else:
                print("Resuming with rejection...")
                result = graph.invoke(Command(resume="rejected"), config)

    # Show final results
    print()
    print("=" * 80)
    print("CURATOR COMPLETE")
    print("=" * 80)
    print()

    # Get final message
    if result and "messages" in result:
        final_message = result["messages"][-1]
        if hasattr(final_message, 'content'):
            print(final_message.content)
        else:
            print(final_message)

    print()
    print("Session saved to thread:", thread_id)
    print("To resume: Use the same thread_id")
    print()

    return result


def simple_test():
    """Run a simple test of the curator with a small task."""
    import uuid
    task = """
Extract dependencies from the fprime I2C driver documentation.
Focus on HIGH criticality dependencies only.

File: ../trial_docs/fprime_i2c_driver_full.md

Store any HIGH criticality dependencies you find (they will require approval).
"""

    # Use unique thread ID to avoid any checkpoint pollution
    thread_id = f"test-{uuid.uuid4().hex[:8]}"
    print(f"Using fresh thread ID: {thread_id}")
    run_curator_with_approval(task, thread_id=thread_id)


def autonomous_exploration():
    """Run the autonomous exploration task from earlier."""
    task = """
You are the curator agent for the PROVES Library - a knowledge graph system for CubeSat mission safety.

YOUR MISSION: Explore the repository and decide what dependency extraction work should be done next.

AVAILABLE RESOURCES:
1. Trial mapping results: ../trial_docs/COMPREHENSIVE_DEPENDENCY_MAP.md
2. Source documentation:
   - ../trial_docs/fprime_i2c_driver_full.md
   - ../trial_docs/proves_kit_power_mgmt_full.md
3. Research goals and ontology:
   - ../docs/ROADMAP.md
   - ../docs/KNOWLEDGE_GRAPH_SCHEMA.md

YOUR TASK:
Analyze what's been done and decide the best next step:

Option A: Replicate the trial mapping using your extraction sub-agent
Option B: Find new files to process
Option C: Improve the ontology

YOU DECIDE: Use your sub-agents (extractor, validator, storage) to execute your chosen approach.

Think step-by-step and explain your reasoning.
IMPORTANT: Only extract and store HIGH criticality dependencies for this test.
"""

    run_curator_with_approval(task, thread_id="autonomous-exploration-1")


if __name__ == "__main__":
    import sys

    print()
    print("Available tests:")
    print("1. Simple test (extract HIGH criticality from fprime I2C driver)")
    print("2. Autonomous exploration (agent decides what to do)")
    print()

    # Check for command-line argument
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        # Try interactive input, fall back to simple test
        try:
            choice = input("Enter choice (1 or 2): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("No input detected, defaulting to simple test (1)")
            choice = "1"

    if choice == "1":
        simple_test()
    elif choice == "2":
        autonomous_exploration()
    else:
        print(f"Invalid choice '{choice}'. Running simple test...")
        simple_test()
