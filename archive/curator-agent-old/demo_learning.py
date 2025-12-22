#!/usr/bin/env python3
"""
DEMONSTRATION: Agent Learning from Students' Work

Shows if the agent can understand methodology and improve on it.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.curator.agent import graph
from langgraph.types import Command


def demo():
    """Demonstrate agent learning and improving on students' work."""

    task = """You are helping build the PROVES Library - a knowledge graph for CubeSat mission safety.

CONTEXT - Learn from the students' previous work:

The students manually extracted dependencies from F' documentation. Here are examples:

EXAMPLE 1:
  ImuManager depends_on LinuxI2cDriver
  Criticality: HIGH
  Why: "IMU gets orientation via I2C. If I2C fails, satellite can't orient solar panels -> power loss -> mission failure"

EXAMPLE 2:
  AdcsSystem depends_on ImuManager
  Criticality: HIGH
  Why: "ADCS needs IMU for attitude control. Failure cascades to power and comms"

EXAMPLE 3:
  SensorCollector requires I2cBus
  Criticality: MEDIUM
  Why: "Sensors use I2C but have backup polling. Degraded not catastrophic"

YOUR TASK:

1. Analyze the file: ../trial_docs/fprime_i2c_driver_full.md

2. Learn from their approach:
   - What makes something HIGH vs MEDIUM vs LOW?
   - What patterns did they focus on?
   - What level of reasoning did they provide?

3. Find dependencies they MISSED:
   - Subtle cross-system dependencies
   - Error handling dependencies
   - Configuration dependencies
   - Transitive dependencies

4. Suggest improvements to their methodology

5. Extract new dependencies using improved approach

Show your reasoning at each step."""

    config = {"configurable": {"thread_id": "demo-learning"}}

    print("="*80)
    print("LEARNING DEMONSTRATION")
    print("="*80)
    print()
    print("Testing if agent can:")
    print("  1. Learn from examples")
    print("  2. Find missing dependencies")
    print("  3. Suggest improvements")
    print("  4. Demonstrate understanding")
    print()
    print("-"*80)
    print()

    # Run
    result = graph.invoke({
        "messages": [{"role": "user", "content": task}]
    }, config)

    state = graph.get_state(config)

    # Handle approvals
    count = 0
    while "__interrupt__" in state.values:
        count += 1
        interrupt_data = state.values["__interrupt__"]

        print()
        print("="*80)
        print(f"APPROVAL REQUEST #{count}")
        print("="*80)
        print()

        tool = interrupt_data.get('tool', interrupt_data.get('type', 'unknown'))
        task_desc = interrupt_data.get('task', '')

        print(f"Agent wants to: {tool}")
        if task_desc:
            print(f"Details: {task_desc[:150]}...")
        print()

        decision = input("Approve? (yes/no): ").strip().lower()

        if decision in ['yes', 'y']:
            print("[APPROVED]")
            result = graph.invoke(Command(resume="approved"), config)
        else:
            print("[REJECTED]")
            result = graph.invoke(Command(resume="rejected"), config)

        state = graph.get_state(config)

    print()
    print("="*80)
    print("AGENT'S ANALYSIS")
    print("="*80)
    print()

    if result and "messages" in result:
        final_msg = result["messages"][-1]
        if hasattr(final_msg, 'content'):
            print(final_msg.content)

    print()
    print("-"*80)
    print("EVALUATION:")
    print("  Did it understand the students' methodology?")
    print("  Did it find new dependencies?")
    print("  Did it provide good reasoning?")
    print("  Did it suggest improvements?")
    print()


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    demo()
