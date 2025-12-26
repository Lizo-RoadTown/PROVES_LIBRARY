"""
Curator Agent - Incremental PROVES Kit Extraction

This script runs incremental extraction from PROVES Kit documentation,
processing ONE PAGE AT A TIME with plan recording for resuming later.

Usage:
    python run_proveskit_incremental.py

Features:
- Develops and records a plan before extraction
- Processes ONE PAGE AT A TIME
- Saves progress for resuming later sessions
- Captures ALL architecture data to staging tables
- Humans verify EVERY staged item before truth graph entry
- Maintains conversation state via PostgreSQL checkpointer (Neon)
- Collects training data for local LLM fine-tuning
"""

import os
import sys
import json
from dotenv import load_dotenv
from langgraph.types import Command

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.curator.agent import graph


def run_curator_with_approval(task: str, thread_id: str = "curator-session-1"):
    """
    Run curator agent with CLI-based human verification for ALL staged data.

    Args:
        task: The task to give the curator (e.g., "Extract dependencies from trial_docs/fprime_i2c_driver_full.md")
        thread_id: Unique ID for this conversation (for resuming)
    """
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 10}

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

        # Handle staged data verification (architecture elements)
        if interrupt_data.get("type") == "dependency_approval":
            print()
            print("=" * 80)
            print("EXTRACTION FOR VERIFICATION")
            print("=" * 80)
            print()

            # Source Information
            print(f"Source: {interrupt_data.get('source_url', 'Unknown')}")
            print(f"Type: {interrupt_data.get('entity_type', 'unknown')} | Key: {interrupt_data.get('entity_key', 'unknown')}")
            print(f"Ecosystem: {interrupt_data.get('ecosystem', 'unknown')}")
            print()

            # Evidence (exact quote from source)
            evidence = interrupt_data.get('evidence_quote', '')
            print("Evidence (from source):")
            print("─" * 40)
            print(evidence[:500] + "..." if len(evidence) > 500 else evidence)
            print("─" * 40)
            print()

            # Confidence & Reasoning
            conf_score = interrupt_data.get('confidence_score', 0.0)
            conf_reason = interrupt_data.get('confidence_reason', 'Not specified')
            print(f"Confidence: {conf_score:.2f} / 1.0")
            print(f"Reasoning: {conf_reason}")
            print()

            # Agent Reasoning Trail (if available)
            reasoning_trail = interrupt_data.get('reasoning_trail', {})
            if reasoning_trail:
                print("Agent Consulted:")
                verified_entities = reasoning_trail.get('verified_entities_consulted', [])
                staging_reviewed = reasoning_trail.get('staging_examples_reviewed', 0)
                comparison_logic = reasoning_trail.get('comparison_logic', '')
                uncertainty = reasoning_trail.get('uncertainty_factors', [])

                if verified_entities:
                    print(f"  • Verified entities: {len(verified_entities)} ({', '.join(verified_entities[:3])}...)")
                if staging_reviewed > 0:
                    print(f"  • Staging examples: {staging_reviewed}")
                if comparison_logic:
                    print(f"  • Comparison: {comparison_logic}")
                if uncertainty:
                    print(f"  • Uncertainties: {', '.join(uncertainty[:2])}")
                print()

            # Duplicate Check (if available)
            dup_check = interrupt_data.get('duplicate_check', {})
            if dup_check:
                recommendation = dup_check.get('recommendation', 'not_checked')
                similar = dup_check.get('similar_entities', [])
                print(f"Duplicate Check: {recommendation}")
                if similar:
                    print(f"  Similar: {len(similar)} entities found")
                print()

            # Properties/Payload
            properties = interrupt_data.get('properties', {})
            if properties:
                import json
                print("Properties:")
                print(json.dumps(properties, indent=2)[:300])
                print()

            print("=" * 80)
            print()
            print("You decide: Is this accurate? What's the mission impact?")
            print()
            print("-" * 40)
            print("OPTIONS:")
            print("  [y]es    - Verify and store (becomes TRUTH)")
            print("  [n]o     - Reject (wrong/inaccurate)")
            print("  [e]dit   - Correct this (GOLD training data!)")
            print("-" * 40)
            print()

            # Get human decision
            while True:
                decision = input("Your choice (y/n/e): ").strip().lower()
                if decision in ['yes', 'y', 'no', 'n', 'edit', 'e']:
                    break
                print("Please enter 'y', 'n', or 'e'")

            print()

            # Resume with decision
            if decision in ['yes', 'y']:
                print("Resuming with approval...")
                result = graph.invoke(Command(resume="approved"), config)
            elif decision in ['edit', 'e']:
                print()
                print("=" * 60)
                print("CORRECTION MODE - Your edits become training data!")
                print("=" * 60)
                print()
                print("Current AI output (task):")
                print("-" * 40)
                task_str = interrupt_data.get('task', '')
                print(task_str[:1000] + "..." if len(task_str) > 1000 else task_str)
                print("-" * 40)
                print()
                print("Enter your corrections:")
                print("  Option 1: Paste corrected JSON (for structured edits)")
                print("  Option 2: Type 'task: <corrected task string>'")
                print("  Option 3: Press Enter twice when done with multi-line input")
                print()

                # Collect multi-line input
                lines = []
                empty_count = 0
                print("(Enter your correction, press Enter twice to submit)")
                while True:
                    try:
                        line = input()
                        if line == "":
                            empty_count += 1
                            if empty_count >= 2:
                                break
                        else:
                            empty_count = 0
                            lines.append(line)
                    except EOFError:
                        break

                correction_text = "\n".join(lines).strip()

                if not correction_text:
                    print("No correction provided, approving as-is...")
                    result = graph.invoke(Command(resume="approved"), config)
                else:
                    # Try to parse as JSON, otherwise wrap in task object
                    try:
                        correction_data = json.loads(correction_text)
                    except json.JSONDecodeError:
                        # Not JSON, check for "task:" prefix
                        if correction_text.lower().startswith("task:"):
                            correction_data = {"task": correction_text[5:].strip()}
                        else:
                            correction_data = {"task": correction_text}

                    print()
                    print(f"Submitting correction: {json.dumps(correction_data, indent=2)[:200]}...")
                    print("This will be logged as GOLD training data!")
                    result = graph.invoke(Command(resume=correction_data), config)
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


def proveskit_incremental_extraction():
    """
    Incremental extraction from PROVES Kit documentation.

    Process ONE PAGE AT A TIME, developing and recording a plan
    for resuming in future sessions.
    """
    import uuid

    task = """
You are the curator agent for the PROVES Library.

YOUR MISSION: Map PROVES Kit system architecture ONE PAGE AT A TIME.

DOCUMENTATION SOURCE:
- Start at: https://docs.proveskit.space/en/latest/
- Do NOT explore GitHub repos yet
- Do NOT explore F' Prime documentation yet

YOUR TASK - FIRST SESSION:
1. Pick a good starting page from PROVES Kit documentation (hardware overview, architecture, etc.)
2. Tell me which page you picked and why
3. Extract architecture from that ONE page only
4. Note what page you completed for next session

EXTRACTION METHODOLOGY (from ONTOLOGY.md - already loaded in your extraction prompt):
Using FRAMES vocabulary, capture:
- COMPONENTS: Hardware/software modules (sensors, boards, F' components)
- INTERFACES: Connection points (I2C, SPI, UART buses, ports)
- FLOWS: What moves through interfaces (data, commands, power, signals)
- MECHANISMS: What maintains connections (drivers, protocols, documentation)

FOCUS AREAS FOR PROVES KIT:
- Hardware components (sensors, radios, boards)
- F' Prime components that PROVES Kit integrates with
- I2C/SPI/UART interfaces and their addresses
- Dependencies between components
- Power management patterns
- Communication patterns

WORKFLOW:
- Extract from ONE page only
- Capture ALL relevant architecture data
- Stage everything for human verification
- Cite source URLs for every extraction
- STOP after completing one page
- We'll return later for the next page

REMEMBER:
- Do NOT assign criticality (humans decide mission impact)
- Do NOT filter based on importance (capture ALL structure)
- You are building institutional memory for student teams
- Stage ALL findings for human verification
"""

    thread_id = f"proveskit-incremental-{uuid.uuid4().hex[:8]}"
    print(f"Using fresh thread ID: {thread_id}")
    print()
    print("=" * 80)
    print("INCREMENTAL EXTRACTION MODE")
    print("=" * 80)
    print("This session will:")
    print("1. Develop a comprehensive extraction plan")
    print("2. Get your approval of the plan")
    print("3. Extract from ONE page only")
    print("4. Save progress for continuing later")
    print()
    print("Thread ID saved for resuming:", thread_id)
    print("=" * 80)
    print()

    run_curator_with_approval(task, thread_id=thread_id)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(line_buffering=True)  # Unbuffered output
    proveskit_incremental_extraction()
