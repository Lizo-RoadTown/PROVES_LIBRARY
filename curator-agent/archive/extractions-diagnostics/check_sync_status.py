#!/usr/bin/env python3
"""Check sync status of suggestions"""
import os
import psycopg
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

conn = psycopg.connect(os.getenv('NEON_DATABASE_URL'))
with conn.cursor() as cur:
    cur.execute('SELECT COUNT(*) FROM improvement_suggestions WHERE notion_page_id IS NULL')
    unsynced_count = cur.fetchone()[0]

    cur.execute('SELECT COUNT(*) FROM improvement_suggestions WHERE notion_page_id IS NOT NULL')
    synced_count = cur.fetchone()[0]

    cur.execute('SELECT COUNT(*) FROM improvement_suggestions')
    total_count = cur.fetchone()[0]
conn.close()

print(f"Suggestion Sync Status:")
print(f"  Total:    {total_count}")
print(f"  Synced:   {synced_count}")
print(f"  Unsynced: {unsynced_count}")
