#!/usr/bin/env python3
"""
SIMPLE CHECK - Just tell me what happened
"""

import sqlite3
import pickle

print("\n" + "=" * 100)
print("WHAT'S IN THE DATABASE")
print("=" * 100)

conn = sqlite3.connect('curator_checkpoints.db')
cursor = conn.cursor()

# List all threads
cursor.execute('SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id')
threads = [row[0] for row in cursor.fetchall()]

print(f"\nFound {len(threads)} conversation threads:")
for t in threads:
    print(f"  - {t}")

# Check simple-test-1 specifically
print("\n" + "=" * 100)
print("SIMPLE-TEST-1 DETAILS")
print("=" * 100)

cursor.execute('''
    SELECT COUNT(*) FROM writes
    WHERE thread_id = 'simple-test-1'
''')
write_count = cursor.fetchone()[0]
print(f"\nTotal state writes: {write_count}")

# Get channels
cursor.execute('''
    SELECT DISTINCT channel FROM writes
    WHERE thread_id = 'simple-test-1'
''')
channels = [row[0] for row in cursor.fetchall()]
print(f"\nChannels used: {channels}")

# Try to see raw content
print("\n" + "=" * 100)
print("LATEST CHECKPOINT RAW DATA")
print("=" * 100)

cursor.execute('''
    SELECT checkpoint_id FROM checkpoints
    WHERE thread_id = 'simple-test-1'
    ORDER BY checkpoint_id DESC
    LIMIT 1
''')
latest_checkpoint = cursor.fetchone()[0]

cursor.execute('''
    SELECT channel, length(value) as size, value
    FROM writes
    WHERE thread_id = 'simple-test-1' AND checkpoint_id = ?
    ORDER BY idx DESC
    LIMIT 5
''', (latest_checkpoint,))

print(f"\nLast 5 writes in checkpoint {latest_checkpoint}:\n")
for channel, size, value_bytes in cursor.fetchall():
    print(f"Channel: {channel}")
    print(f"  Size: {size} bytes")

    # Try to unpickle
    try:
        data = pickle.loads(value_bytes)

        # Try to show something useful
        if isinstance(data, dict):
            keys = list(data.keys())
            print(f"  Type: dict with keys: {keys}")

            # Show deferred_storage if present
            if 'deferred_storage' in data:
                print(f"  DEFERRED_STORAGE: {data['deferred_storage']}")

            # Show approval if present
            if 'storage_approval' in data:
                print(f"  STORAGE_APPROVAL: {data['storage_approval']}")

        elif isinstance(data, list):
            print(f"  Type: list with {len(data)} items")

            # If it's messages, show the last one
            if len(data) > 0 and hasattr(data[-1], 'content'):
                last_msg = data[-1]
                content = str(last_msg.content)[:200]
                print(f"  Last message type: {last_msg.__class__.__name__}")
                print(f"  Last message content: {content}...")

        else:
            print(f"  Type: {type(data).__name__}")
            print(f"  Value: {str(data)[:100]}...")

    except Exception as e:
        print(f"  ERROR unpickling: {e}")

    print()

conn.close()

print("\n" + "=" * 100)
print("TO ANSWER YOUR QUESTIONS")
print("=" * 100)
print("""
1. "Was it recording all the other ones?"
   → Check: Did the extractor FIND multiple dependencies?
   → Only HIGH dependencies trigger approval
   → MEDIUM/LOW are stored automatically (no approval needed)
   → The test was FOCUSED on finding just ONE dependency

2. "Everything is invisible"
   → Conversation state: curator_checkpoints.db (SQLite)
   → Actual dependencies: Neo4j graph database
   → Need to install neo4j driver to see graph: pip install neo4j

3. Where is data stored?
   → Checkpoints (conversation): curator_checkpoints.db (THIS FILE)
   → Knowledge graph (real data): Neo4j at bolt://localhost:7687
   → Debug logs: curator_debug.log (if logging enabled)
""")
