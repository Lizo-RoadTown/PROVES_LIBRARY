#!/usr/bin/env python3
"""
QUICK MONITORING TOOL - Run this to see what the curator is doing in real-time
"""

import sqlite3
import time
import os
from datetime import datetime
from neo4j import GraphDatabase

class QuickMonitor:
    """Simple real-time monitor for curator agent"""

    def __init__(self):
        self.checkpoint_db = "curator_checkpoints.db"

        # Neo4j connection
        self.neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
        self.neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')

    def show_current_state(self):
        """Show current state of both databases"""
        print("\n" + "=" * 100)
        print(f"CURATOR AGENT STATUS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)

        # Check Neo4j
        self._check_neo4j()

        # Check checkpoints
        self._check_checkpoints()

    def _check_neo4j(self):
        """Check Neo4j database"""
        print("\n📊 NEO4J KNOWLEDGE GRAPH:")
        print("-" * 100)

        try:
            driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )

            with driver.session() as session:
                # Count nodes
                result = session.run('MATCH (n) RETURN count(n) as count')
                node_count = result.single()['count']

                # Count dependencies
                result = session.run('MATCH ()-[r:DEPENDS_ON]->() RETURN count(r) as count')
                dep_count = result.single()['count']

                print(f"  Total nodes: {node_count}")
                print(f"  Total dependencies: {dep_count}")

                if dep_count > 0:
                    print("\n  Recent dependencies:")
                    result = session.run('''
                        MATCH (a)-[r:DEPENDS_ON]->(b)
                        RETURN a.name as source, b.name as target,
                               r.criticality as criticality,
                               r.description as description
                        ORDER BY r.created_at DESC
                        LIMIT 10
                    ''')

                    for i, record in enumerate(result, 1):
                        crit = record["criticality"]
                        emoji = "🔴" if crit == "HIGH" else "🟡" if crit == "MEDIUM" else "🟢"
                        print(f"    {i}. {emoji} {record['source']} → {record['target']}")
                        print(f"       [{crit}] {record['description'][:80]}...")

            driver.close()

        except Exception as e:
            print(f"  ❌ Neo4j Error: {e}")
            print(f"  Make sure Neo4j is running at {self.neo4j_uri}")

    def _check_checkpoints(self):
        """Check checkpoint database"""
        print("\n💾 CONVERSATION CHECKPOINTS:")
        print("-" * 100)

        if not os.path.exists(self.checkpoint_db):
            print(f"  ❌ No checkpoint database found at {self.checkpoint_db}")
            return

        conn = sqlite3.connect(self.checkpoint_db)
        cursor = conn.cursor()

        # Count threads
        cursor.execute('SELECT COUNT(DISTINCT thread_id) FROM checkpoints')
        thread_count = cursor.fetchone()[0]

        # Count total checkpoints
        cursor.execute('SELECT COUNT(*) FROM checkpoints')
        checkpoint_count = cursor.fetchone()[0]

        print(f"  Total threads: {thread_count}")
        print(f"  Total checkpoints: {checkpoint_count}")

        # Show recent threads
        cursor.execute('''
            SELECT thread_id, MAX(created_at) as last_activity, COUNT(*) as checkpoint_count
            FROM checkpoints
            GROUP BY thread_id
            ORDER BY last_activity DESC
            LIMIT 5
        ''')

        print("\n  Recent threads:")
        for thread_id, last_activity, count in cursor.fetchall():
            print(f"    • {thread_id}")
            print(f"      Last activity: {last_activity}")
            print(f"      Checkpoints: {count}")

        conn.close()

    def watch(self, interval: int = 5):
        """Watch in real-time (refresh every N seconds)"""
        print("Starting real-time monitoring (Ctrl+C to stop)...")
        print(f"Refreshing every {interval} seconds")

        try:
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                self.show_current_state()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")


if __name__ == "__main__":
    import sys

    monitor = QuickMonitor()

    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        monitor.watch(interval)
    else:
        monitor.show_current_state()
        print("\n💡 TIP: Run 'python quick_monitor.py watch' for real-time monitoring")
