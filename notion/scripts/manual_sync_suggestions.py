#!/usr/bin/env python3
"""Manually sync unsynced suggestions"""
import os
import psycopg
from dotenv import load_dotenv
from pathlib import Path
from src.curator.suggestion_sync import SuggestionSync

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

db_url = os.getenv('NEON_DATABASE_URL')
sync = SuggestionSync()

# Get unsynced suggestions
conn = psycopg.connect(db_url)
with conn.cursor() as cur:
    cur.execute('''
        SELECT suggestion_id, category, title, evidence, current_state,
               proposed_change, impact_count, confidence, extraction_ids, status, created_at
        FROM improvement_suggestions
        WHERE notion_page_id IS NULL
        LIMIT 10
    ''')
    rows = cur.fetchall()
conn.close()

print(f"Found {len(rows)} unsynced suggestions")
print()

for row in rows:
    suggestion_data = {
        'suggestion_id': row[0],
        'category': row[1],
        'title': row[2],
        'evidence': row[3],
        'current_state': row[4],
        'proposed_change': row[5],
        'impact_count': row[6],
        'confidence': row[7],
        'extraction_ids': row[8] or [],
        'status': row[9],
        'created_at': row[10]
    }

    try:
        page_id = sync.sync_suggestion(suggestion_data)
        print(f"✓ Synced: {suggestion_data['title'][:60]}...")
    except Exception as e:
        print(f"✗ Failed: {suggestion_data['title'][:60]}... - {e}")

print()
print("Done!")
