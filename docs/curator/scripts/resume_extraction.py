"""
Resume the pending PROVES Prime extraction with the snapshot ID
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.curator.agent import graph
from langgraph.types import Command

# The stuck thread
thread_id = 'daily-extraction-f0f70861'
config = {'configurable': {'thread_id': thread_id}}

# The snapshot ID we found
snapshot_id = '979e18be-bb9e-40fa-bd19-c9506f1f2d90'

print("=" * 80)
print("RESUMING EXTRACTION WITH SNAPSHOT ID")
print("=" * 80)
print()
print(f"Thread: {thread_id}")
print(f"Snapshot ID: {snapshot_id}")
print()

# Build a response telling the storage agent to use this snapshot ID
resume_message = f"""Use snapshot ID: {snapshot_id}

This is the raw_snapshot for the PROVES Prime page that was already fetched.
Proceed with storing all the extractions using this snapshot_id."""

print("Resuming graph with snapshot ID...")
print()

try:
    # Resume the graph
    result = graph.invoke(
        Command(resume={"snapshot_id": snapshot_id}),
        config
    )

    print()
    print("=" * 80)
    print("RESULT")
    print("=" * 80)
    print()
    if result and 'messages' in result:
        print(result['messages'][-1].content)
    else:
        print(result)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
