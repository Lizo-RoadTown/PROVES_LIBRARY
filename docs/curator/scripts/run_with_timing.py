"""
Quick test with built-in timing
Shows exactly where time is being spent
"""
import sys
sys.path.insert(0, "src")

from curator.agent import graph, get_timing_summary

def test_extraction_with_timing():
    """Run a simple extraction and show timing breakdown"""

    task = """Extract dependencies from: ../trial_docs/fprime_i2c_driver_full.md

Find all component dependencies and assess their criticality."""

    config = {"configurable": {"thread_id": "timing-test-1"}}

    print("\n" + "="*60)
    print("RUNNING EXTRACTION WITH TIMING")
    print("="*60 + "\n")

    try:
        result = graph.invoke(
            {"messages": [{"role": "user", "content": task}]},
            config
        )

        print("\n" + "="*60)
        print("EXTRACTION COMPLETE")
        print("="*60 + "\n")

        # Show timing summary
        print(get_timing_summary())

        # Show result
        print("\n" + "="*60)
        print("AGENT RESPONSE")
        print("="*60 + "\n")
        if result and "messages" in result:
            last_message = result["messages"][-1]
            print(last_message.content if hasattr(last_message, 'content') else str(last_message))

    except Exception as e:
        print(f"\nERROR: {e}")
        print("\n" + get_timing_summary())

if __name__ == "__main__":
    test_extraction_with_timing()
