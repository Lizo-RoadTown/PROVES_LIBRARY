"""Quick script to check what's in staging_extractions."""
import os
import psycopg
from dotenv import load_dotenv
from pathlib import Path

project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

db_url = os.environ.get('DIRECT_URL') or os.environ.get('DATABASE_URL')
# Strip pgbouncer param if present
if db_url and 'pgbouncer' in db_url:
    db_url = db_url.split('?')[0]

conn = psycopg.connect(db_url)

print("=" * 60)
print("STAGING_EXTRACTIONS STATUS")
print("=" * 60)

with conn.cursor() as cur:
    # Count by status
    cur.execute("""
        SELECT status, COUNT(*) as count
        FROM staging_extractions
        GROUP BY status
        ORDER BY count DESC
    """)
    rows = cur.fetchall()

    print("\nStatus counts:")
    for row in rows:
        print(f"  {row[0]}: {row[1]}")

    # Show recent extractions
    cur.execute("""
        SELECT extraction_id, candidate_key, candidate_type, status,
               confidence_score, lineage_verified, created_at
        FROM staging_extractions
        ORDER BY created_at DESC
        LIMIT 10
    """)
    rows = cur.fetchall()

    print(f"\nRecent extractions (last 10):")
    for row in rows:
        print(f"  [{row[3]}] {row[2]}: {row[1]} (conf={row[4]}, lineage={row[5]})")
        print(f"           created: {row[6]}")

print("\n" + "=" * 60)
print("URLS_TO_PROCESS STATUS")
print("=" * 60)

with conn.cursor() as cur:
    # Count by status
    cur.execute("""
        SELECT status, COUNT(*) as count
        FROM urls_to_process
        GROUP BY status
        ORDER BY count DESC
    """)
    rows = cur.fetchall()

    print("\nStatus counts:")
    for row in rows:
        print(f"  {row[0]}: {row[1]}")

conn.close()
