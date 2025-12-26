"""
Autonomous Deep Agent Exploration Test

This test gives the curator agent an open-ended task to:
1. Explore the existing trial mapping results
2. Understand the ontology and research goals
3. Decide what to do next (replicate, improve, or find new files)
4. Execute autonomously using sub-agents
"""

import os
import sys
from dotenv import load_dotenv

# Load environment from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.curator.agent import graph

def run_autonomous_exploration():
    """Give the curator agent an open-ended exploration task."""

    print("=" * 80)
    print("AUTONOMOUS DEEP AGENT EXPLORATION")
    print("=" * 80)
    print()
    print("Task: Explore the PROVES Library repository and decide what to do next.")
    print()
    print("The agent will:")
    print("  1. Review existing trial mapping results (trial_docs/)")
    print("  2. Understand the ontology and research goals (docs/)")
    print("  3. Decide whether to replicate, improve, or find new files")
    print("  4. Execute autonomously using sub-agents")
    print()
    print("Monitoring: View execution in LangSmith Studio")
    print("  -> https://smith.langchain.com/")
    print()
    print("-" * 80)
    print()

    # Open-ended task that gives the agent autonomy
    task = """
You are the curator agent for the PROVES Library - a knowledge graph system for CubeSat mission safety.

YOUR MISSION: Explore the repository and decide what dependency extraction work should be done next.

AVAILABLE RESOURCES:
1. Trial mapping results: ../trial_docs/COMPREHENSIVE_DEPENDENCY_MAP.md
   - Manual analysis of F' I2C Driver and PROVES Kit Power Management
   - Found 45+ dependencies, 4 critical cross-system dependencies

2. Source documentation:
   - ../trial_docs/fprime_i2c_driver_full.md
   - ../trial_docs/proves_kit_power_mgmt_full.md

3. Research goals and ontology:
   - ../docs/ROADMAP.md
   - ../docs/KNOWLEDGE_GRAPH_SCHEMA.md
   - ../FOLDER_STRUCTURE.md

YOUR TASK:
Analyze what's been done and decide the best next step:

Option A: Replicate the trial mapping using your extraction sub-agent
  - Extract dependencies from fprime_i2c_driver_full.md
  - Compare automated extraction vs manual analysis
  - Validate against existing knowledge graph

Option B: Find new files to process
  - Search for other documentation in the repository
  - Identify high-value files for dependency extraction
  - Process them using your sub-agents

Option C: Improve the ontology
  - Review the ERV (Engineering Relationship Vocabulary)
  - Suggest improvements based on the trial results
  - Propose new relationship types or validation rules

YOU DECIDE: Use your sub-agents (extractor, validator, storage) to execute your chosen approach.

Think step-by-step and explain your reasoning.
"""

    try:
        # Invoke the curator agent
        result = graph.invoke({
            "messages": [{
                "role": "user",
                "content": task
            }]
        })

        print()
        print("=" * 80)
        print("AGENT RESPONSE:")
        print("=" * 80)
        print()

        # Get the final message
        final_message = result['messages'][-1].content
        print(final_message)

        print()
        print("=" * 80)
        print("EXECUTION COMPLETE")
        print("=" * 80)
        print()
        print("Check LangSmith for full trace:")
        print("  -> https://smith.langchain.com/")
        print()

        return result

    except Exception as e:
        print()
        print("=" * 80)
        print("ERROR OCCURRED:")
        print("=" * 80)
        print()
        print(f"Error: {e}")
        print()
        print("Check LangSmith for detailed trace:")
        print("  -> https://smith.langchain.com/")
        print()
        raise

if __name__ == "__main__":
    run_autonomous_exploration()
