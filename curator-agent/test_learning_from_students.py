#!/usr/bin/env python3
"""
TEST: Can the agent learn from students' work and improve on it?

This test gives the agent:
1. Examples of dependencies the students already extracted
2. Context about the CubeSat domain and why dependencies matter
3. Access to the same documentation
4. A goal to find MORE or BETTER dependencies

We'll see if it can:
- Understand the students' approach
- Find dependencies they missed
- Provide higher-level insights
- Suggest improvements to the methodology
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.curator.agent import graph
from langgraph.types import Command


def test_learning():
    """Test if agent can learn from students' work and improve on it."""

    # This is the critical part: give the agent CONTEXT
    task = """You are helping build the PROVES Library - a knowledge graph to prevent CubeSat mission failures.

DOMAIN CONTEXT:
CubeSats are small satellites with severe constraints. Hidden dependencies between subsystems cause cascade failures.
Example: FalconSat-2 failed because a power system dependency on the I2C bus wasn't documented.

STUDENTS' APPROACH:
Students manually analyzed F´ (fprime) documentation and extracted these dependencies:

EXAMPLE 1 (from their work):
  Source: ImuManager
  Target: LinuxI2cDriver
  Relationship: depends_on
  Criticality: HIGH
  Reasoning: "IMU provides orientation data via I2C. If I2C fails, satellite can't orient solar panels → power loss → mission failure"

EXAMPLE 2 (from their work):
  Source: AdcsSystem
  Target: ImuManager
  Relationship: depends_on
  Criticality: HIGH
  Reasoning: "ADCS (attitude control) needs IMU data to maintain orientation. Failure cascades to power and communication systems."

EXAMPLE 3 (from their work):
  Source: SensorDataCollector
  Target: I2cBus
  Relationship: requires
  Criticality: MEDIUM
  Reasoning: "Sensor data collection uses I2C but has backup polling. Degraded but not catastrophic."

YOUR TASK:
1. Read the F´ I2C driver documentation: ../trial_docs/fprime_i2c_driver_full.md

2. Learn from the students' examples:
   - What makes a dependency HIGH vs MEDIUM vs LOW?
   - What patterns did they focus on?
   - What level of detail did they capture?

3. Find dependencies they might have MISSED:
   - Subtle cross-system dependencies
   - Transitive dependencies (A→B→C means A implicitly depends on C)
   - Error handling dependencies
   - Configuration dependencies

4. Propose IMPROVEMENTS to their methodology:
   - Are there dependency types they should track?
   - Should criticality assessment consider more factors?
   - What additional context would make the graph more useful?

5. Extract NEW dependencies following their approach but improving on it

Be thoughtful and analytical. Show your reasoning. We want to see if you can:
- Understand their methodology
- Build on their work
- Discover things they missed
- Suggest how to do it better
"""

    config = {"configurable": {"thread_id": "learning-test"}}

    print("=" * 100)
    print("LEARNING TEST: Can Agent Improve on Students' Work?")
    print("=" * 100)
    print()
    print("Context provided:")
    print("  ✓ CubeSat domain knowledge")
    print("  ✓ Mission failure examples")
    print("  ✓ Students' extracted dependencies (with reasoning)")
    print("  ✓ Their assessment criteria")
    print()
    print("Agent's task:")
    print("  1. Learn from examples")
    print("  2. Find missing dependencies")
    print("  3. Suggest methodology improvements")
    print("  4. Extract with higher quality")
    print()
    print("-" * 100)
    print()

    # Run agent
    result = graph.invoke({
        "messages": [{"role": "user", "content": task}]
    }, config)

    state = graph.get_state(config)

    # Handle approvals
    approval_count = 0
    while "__interrupt__" in state.values:
        approval_count += 1
        interrupt_data = state.values["__interrupt__"]

        print()
        print("=" * 100)
        print(f"AGENT ACTION REQUEST #{approval_count}")
        print("=" * 100)
        print()

        tool = interrupt_data.get('tool', interrupt_data.get('type', 'unknown'))
        task_desc = interrupt_data.get('task', '')

        print(f"Agent wants to: {tool}")
        if task_desc:
            print(f"Task: {task_desc[:200]}...")
        print()

        # Show what the agent is trying to do
        print("Agent's reasoning:")
        if result and "messages" in result:
            # Look for the agent's last message before tool call
            for msg in reversed(result["messages"]):
                if hasattr(msg, 'content') and msg.content and not hasattr(msg, 'tool_calls'):
                    print(f"  {msg.content[:300]}...")
                    break

        print()
        decision = input("Approve this action? (yes/no): ").strip().lower()

        if decision in ['yes', 'y']:
            print(f"✓ Approved - executing {tool}...")
            result = graph.invoke(Command(resume="approved"), config)
        else:
            print(f"✗ Rejected - skipping {tool}")
            result = graph.invoke(Command(resume="rejected"), config)

        state = graph.get_state(config)

    print()
    print("=" * 100)
    print("TEST COMPLETE - AGENT'S FINDINGS")
    print("=" * 100)
    print()

    # Show final analysis
    if result and "messages" in result:
        final_msg = result["messages"][-1]
        if hasattr(final_msg, 'content'):
            print(final_msg.content)

    print()
    print("-" * 100)
    print("EVALUATION CRITERIA:")
    print("-" * 100)
    print()
    print("Did the agent:")
    print("  1. Understand the students' methodology? (HIGH = mission-critical, etc.)")
    print("  2. Find dependencies the students missed?")
    print("  3. Provide good reasoning for criticality assessments?")
    print("  4. Suggest improvements to the extraction process?")
    print("  5. Show higher-level understanding of CubeSat architecture?")
    print()

    return result


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(line_buffering=True)
    test_learning()
