#!/usr/bin/env python3
"""Check pending extractions in staging_extractions table"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
db_url = os.getenv('NEON_DATABASE_URL')

conn = psycopg2.connect(db_url)
cur = conn.cursor()

# Get all pending extractions
cur.execute("""
    SELECT extraction_id, candidate_key, candidate_type::text,
           status::text, ecosystem::text, confidence_score,
           created_at, snapshot_id
    FROM staging_extractions
    ORDER BY created_at DESC
    LIMIT 20;
""")

results = cur.fetchall()

print("=" * 80)
print("STAGING EXTRACTIONS (Last 20)")
print("=" * 80)

for row in results:
    ext_id, key, ctype, status, eco, conf, created, snap_id = row
    print(f"\n{key} ({ctype})")
    print(f"  ID: {ext_id}")
    print(f"  Status: {status}")
    print(f"  Ecosystem: {eco}")
    print(f"  Confidence: {conf}")
    print(f"  Snapshot: {snap_id}")
    print(f"  Created: {created}")

print(f"\n" + "=" * 80)
print(f"Total: {len(results)}")
print("=" * 80)

cur.close()
conn.close()
