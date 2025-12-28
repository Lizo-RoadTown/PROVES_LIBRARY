#!/usr/bin/env python3
"""Create LangGraph PostgresSaver checkpointer tables in Neon."""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
db_url = os.getenv('NEON_DATABASE_URL')

if not db_url:
    print("Error: NEON_DATABASE_URL not set")
    exit(1)

conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

print("Creating LangGraph checkpointer tables...")

# Create tables
statements = [
    ("checkpoint_migrations", 
     "CREATE TABLE IF NOT EXISTS checkpoint_migrations (v INTEGER PRIMARY KEY)"),
    
    ("checkpoints",
     """CREATE TABLE IF NOT EXISTS checkpoints (
        thread_id TEXT NOT NULL,
        checkpoint_ns TEXT NOT NULL DEFAULT '',
        checkpoint_id TEXT NOT NULL,
        parent_checkpoint_id TEXT,
        type TEXT,
        checkpoint JSONB NOT NULL,
        metadata JSONB NOT NULL DEFAULT '{}',
        PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
     )"""),
    
    ("checkpoint_blobs",
     """CREATE TABLE IF NOT EXISTS checkpoint_blobs (
        thread_id TEXT NOT NULL,
        checkpoint_ns TEXT NOT NULL DEFAULT '',
        channel TEXT NOT NULL,
        version TEXT NOT NULL,
        type TEXT NOT NULL,
        blob BYTEA,
        PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
     )"""),
    
    ("checkpoint_writes",
     """CREATE TABLE IF NOT EXISTS checkpoint_writes (
        thread_id TEXT NOT NULL,
        checkpoint_ns TEXT NOT NULL DEFAULT '',
        checkpoint_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        idx INTEGER NOT NULL,
        channel TEXT NOT NULL,
        type TEXT,
        blob BYTEA NOT NULL,
        PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
     )"""),
]

for name, sql in statements:
    try:
        cur.execute(sql)
        print(f"  [OK] {name}")
    except Exception as e:
        print(f"  [INFO] {name}: {e}")

# Create indexes
indexes = [
    "CREATE INDEX IF NOT EXISTS checkpoints_thread_id_idx ON checkpoints(thread_id)",
    "CREATE INDEX IF NOT EXISTS checkpoint_blobs_thread_id_idx ON checkpoint_blobs(thread_id)",
    "CREATE INDEX IF NOT EXISTS checkpoint_writes_thread_id_idx ON checkpoint_writes(thread_id)",
]

for sql in indexes:
    try:
        cur.execute(sql)
    except:
        pass
print("  [OK] Indexes")

# Add task_path column
try:
    cur.execute("ALTER TABLE checkpoint_writes ADD COLUMN IF NOT EXISTS task_path TEXT NOT NULL DEFAULT ''")
    print("  [OK] task_path column")
except:
    pass

# Record migrations
for v in range(10):
    try:
        cur.execute(f"INSERT INTO checkpoint_migrations (v) VALUES ({v}) ON CONFLICT (v) DO NOTHING")
    except:
        pass
print("  [OK] Migrations recorded")

# Verify
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'checkpoint%'")
tables = [t[0] for t in cur.fetchall()]
print(f"\nCheckpointer tables in database: {tables}")

cur.execute("SELECT COUNT(*) FROM checkpoint_migrations")
print(f"Migration versions: {cur.fetchone()[0]}")

conn.close()
print("\nDone! Checkpointer is ready.")
