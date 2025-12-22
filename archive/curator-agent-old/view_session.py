#!/usr/bin/env python3
"""
VIEW WHAT HAPPENED IN A SESSION
Simple tool to see what the agent did without requiring Neo4j
"""

import sqlite3
import json
import sys
from datetime import datetime

def view_session(thread_id: str = None):
    """View conversation history and actions from a session"""

    conn = sqlite3.connect('curator_checkpoints.db')
    cursor = conn.cursor()

    # Get latest thread if not specified
    if not thread_id:
        cursor.execute('''
            SELECT DISTINCT thread_id
            FROM checkpoints
            ORDER BY thread_id DESC
            LIMIT 1
        ''')
        result = cursor.fetchone()
        if result:
            thread_id = result[0]
            print(f"Using latest thread: {thread_id}")
        else:
            print("No sessions found!")
            return

    print("\n" + "=" * 100)
    print(f"SESSION: {thread_id}")
    print("=" * 100)

    # Get all checkpoints for this thread
    cursor.execute('''
        SELECT checkpoint_id, parent_checkpoint_id, type
        FROM checkpoints
        WHERE thread_id = ?
        ORDER BY checkpoint_id
    ''', (thread_id,))

    checkpoints = cursor.fetchall()
    print(f"\nTotal checkpoints: {len(checkpoints)}")

    # Get the latest checkpoint
    if checkpoints:
        latest_checkpoint = checkpoints[-1][0]

        print("\n" + "-" * 100)
        print("CONVERSATION MESSAGES")
        print("-" * 100)

        # Get messages from writes table
        cursor.execute('''
            SELECT channel, value
            FROM writes
            WHERE thread_id = ? AND checkpoint_id = ?
            ORDER BY idx
        ''', (thread_id, latest_checkpoint))

        for channel, data_bytes in cursor.fetchall():
            if not data_bytes:
                continue

            try:
                # Deserialize the BLOB using pickle (LangGraph uses pickle)
                import pickle
                data = pickle.loads(data_bytes)

                # Handle messages
                if isinstance(data, list):
                    for msg in data:
                        if isinstance(msg, dict):
                            msg_type = msg.get('type', 'unknown')
                            content = msg.get('content', '')

                            print(f"\n[{msg_type.upper()}]")

                            # Show content
                            if isinstance(content, str):
                                # Limit length
                                if len(content) > 500:
                                    print(content[:500] + "... (truncated)")
                                else:
                                    print(content)
                            elif isinstance(content, list):
                                for item in content[:3]:  # First 3 items
                                    print(f"  - {item}")

                            # Show tool calls
                            if 'tool_calls' in msg and msg['tool_calls']:
                                print("\n  Tool Calls:")
                                for tc in msg['tool_calls']:
                                    tool_name = tc.get('name', 'unknown')
                                    args = tc.get('args', {})
                                    task = args.get('task', '')
                                    if task:
                                        print(f"    → {tool_name}(\"{task[:80]}...\")")
                                    else:
                                        print(f"    → {tool_name}()")

                elif isinstance(data, dict):
                    # Handle state updates
                    if 'messages' in data:
                        continue  # Already handled above
                    elif 'deferred_storage' in data:
                        deferred = data['deferred_storage']
                        if deferred:
                            print(f"\n[DEFERRED STORAGE]")
                            for item in deferred:
                                print(f"  Task: {item.get('task', 'unknown')}")
                    elif 'storage_approval' in data:
                        approval = data['storage_approval']
                        if approval:
                            print(f"\n[APPROVAL]: {approval}")

            except Exception as e:
                print(f"\n[ERROR parsing data]: {e}")
                continue

    conn.close()

    print("\n" + "=" * 100)
    print("END OF SESSION")
    print("=" * 100)


def list_sessions():
    """List all available sessions"""
    conn = sqlite3.connect('curator_checkpoints.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT thread_id,
               MIN(checkpoint_id) as first_checkpoint,
               MAX(checkpoint_id) as last_checkpoint,
               COUNT(*) as checkpoint_count
        FROM checkpoints
        GROUP BY thread_id
        ORDER BY thread_id DESC
    ''')

    print("\n" + "=" * 100)
    print("AVAILABLE SESSIONS")
    print("=" * 100)

    for thread_id, first, last, count in cursor.fetchall():
        print(f"\nThread: {thread_id}")
        print(f"  First checkpoint: {first}")
        print(f"  Last checkpoint: {last}")
        print(f"  Total checkpoints: {count}")

    conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_sessions()
        else:
            view_session(sys.argv[1])
    else:
        # Show latest session
        view_session()
        print("\n💡 Usage:")
        print("  python view_session.py              # View latest session")
        print("  python view_session.py list         # List all sessions")
        print("  python view_session.py <thread_id>  # View specific session")
