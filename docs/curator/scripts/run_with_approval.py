"""
Curator Agent with CLI-based Human Verification

This script runs the curator agent with command-line prompts for
verifying ALL staged data before it enters the truth graph.

Usage:
    python run_with_approval.py

Features:
- Captures ALL dependencies to staging tables
- Humans verify EVERY staged item before truth graph entry
- Supports: approve, reject, or CORRECT (edit the AI's output)
- Maintains conversation state via PostgreSQL checkpointer (Neon)
- Collects training data for local LLM fine-tuning
- Visible progress with print statements
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
    }, config, {"recursion_limit": 10})

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
                result = graph.invoke(Command(resume="approved"), config, {"recursion_limit": 10})
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
                    result = graph.invoke(Command(resume="approved"), config, {"recursion_limit": 10})
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
                    result = graph.invoke(Command(resume=correction_data), config, {"recursion_limit": 10})
            else:
                print("Resuming with rejection...")
                result = graph.invoke(Command(resume="rejected"), config, {"recursion_limit": 10})

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
    """
    LEGACY TEST - Kept for basic connectivity testing only.
    Use options 3 or 4 for actual crawling work.
    """
    import uuid
    import os
    
    # Get absolute path to the trial docs
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    doc_path = os.path.join(project_root, "trial_docs", "fprime_i2c_driver_full.md")
    
    task = f"""
ARCHITECTURE MAPPING TEST - Verify the FRAMES extraction pipeline.

Read this local file and map the system architecture:
File: {doc_path}

Using FRAMES methodology, capture:
- COMPONENTS: What modules/units exist?
- INTERFACES: Where do they connect? (ports, buses, protocols)
- FLOWS: What moves through those connections? (data, commands, power, signals)
- MECHANISMS: What maintains those interfaces? (documentation, schemas, drivers)

For each element, note:
- Source: Where did you find this? (file path, line numbers)
- Confidence: How clearly documented? (HIGH/MEDIUM/LOW)

Remember: You are building institutional memory for student teams.
Stage what you find for human verification. Humans will assign criticality.
"""

    thread_id = f"test-{uuid.uuid4().hex[:8]}"
    print(f"Using fresh thread ID: {thread_id}")
    print("NOTE: This is a legacy test. Use options 3 or 4 for real crawling.")
    run_curator_with_approval(task, thread_id=thread_id)


def autonomous_exploration():
    """Run the autonomous exploration task from earlier."""
    task = """
You are the curator agent for the PROVES Library - building institutional memory for university space programs.

THE PROBLEM: University CubeSat programs have 88% failure rate because knowledge is lost when students graduate.
YOUR MISSION: Map the system architecture so weak interfaces can be identified and strengthened.

Using FRAMES methodology, explore and map:
- COMPONENTS: What modules exist in this software system?
- INTERFACES: Where do they connect?
- FLOWS: What moves through those connections?
- MECHANISMS: What documentation/schemas maintain those interfaces?

AVAILABLE RESOURCES:
1. Trial mapping results: ../trial_docs/COMPREHENSIVE_DEPENDENCY_MAP.md
2. Source documentation:
   - ../trial_docs/fprime_i2c_driver_full.md
   - ../trial_docs/proves_kit_power_mgmt_full.md
3. Research goals and ontology:
   - ../docs/ROADMAP.md
   - ../ONTOLOGY.md (defines extraction vocabulary)

YOUR TASK:
Analyze what's been done and decide the best next step:

Option A: Replicate the trial mapping using FRAMES extraction
Option B: Find new files to process
Option C: Improve component coverage

YOU DECIDE: Use your sub-agents (extractor, validator, storage) to execute your chosen approach.

Remember: You are building a map that prevents knowledge loss.
Stage ALL findings for human verification. Humans connect to organizational context.
"""

    run_curator_with_approval(task, thread_id="autonomous-exploration-1")


def fprime_web_crawl():
    """Test web crawling of F' documentation."""
    import uuid
    
    task = """
You are the curator agent for the PROVES Library.

YOUR MISSION: Crawl F' (F Prime) documentation and extract dependencies.

START WITH THE F' GITHUB REPOSITORY:
1. Use list_github_directory to explore: github.com/nasa/fprime (branch: devel)
2. Focus on the Svc/ and Drv/ directories - these contain flight software components
3. For each component, use fetch_github_file to read README.md or .fpp files
4. Extract dependencies between components

IMPORTANT URLs:
- GitHub repo: nasa/fprime (use the GitHub tools, NOT the website)
- Start with: Svc/ directory, then Drv/ directory

EXTRACTION FOCUS:
- Component-to-component dependencies
- Port connections (what ports components expose/require)
- Configuration parameters
- Any safety-critical constraints mentioned

For this test, process at most 3 components to verify the tools work.

Capture ALL dependencies to staging tables for human verification.
For each fact you extract, CITE THE SOURCE URL.
"""

    thread_id = f"fprime-crawl-{uuid.uuid4().hex[:8]}"
    print(f"Using fresh thread ID: {thread_id}")
    run_curator_with_approval(task, thread_id=thread_id)


def proveskit_web_crawl():
    """Test web crawling of ProvesKit documentation."""
    import uuid
    
    task = """
You are the curator agent for the PROVES Library.

YOUR MISSION: Crawl ProvesKit documentation and extract dependencies.

START WITH THE PROVESKIT DOCUMENTATION:
1. Use fetch_webpage to read: https://docs.proveskit.space/en/latest/
2. Follow links to explore the Power Management and Flight Software sections
3. Extract dependencies and component relationships

ALSO EXPLORE THE GITHUB REPO:
1. Use list_github_directory to explore: github.com/proveskit/flight_software
2. Look for README files, CircuitPython code, and configuration

EXTRACTION FOCUS:
- Hardware-software interfaces (which CircuitPython code controls which hardware)
- Power management dependencies
- Flight modes and their requirements
- Safety constraints

For this test, process at most 3 pages/files to verify the tools work.

Capture ALL dependencies to staging tables for human verification.
For each fact you extract, CITE THE SOURCE URL.
"""

    thread_id = f"proveskit-crawl-{uuid.uuid4().hex[:8]}"
    print(f"Using fresh thread ID: {thread_id}")
    run_curator_with_approval(task, thread_id=thread_id)


if __name__ == "__main__":
    import sys

    print()
    print("Available tests:")
    print("1. Simple test (extract from local fprime I2C driver)")
    print("2. Autonomous exploration (agent decides what to do)")
    print("3. F' web crawl (fetch from nasa/fprime GitHub repo)")
    print("4. ProvesKit web crawl (fetch from docs.proveskit.space)")
    print()

    # Check for command-line argument
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        # Try interactive input, fall back to simple test
        try:
            choice = input("Enter choice (1-4): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("No input detected, defaulting to simple test (1)")
            choice = "1"

    if choice == "1":
        simple_test()
    elif choice == "2":
        autonomous_exploration()
    elif choice == "3":
        fprime_web_crawl()
    elif choice == "4":
        proveskit_web_crawl()
    else:
        print(f"Invalid choice '{choice}'. Running simple test...")
        simple_test()
