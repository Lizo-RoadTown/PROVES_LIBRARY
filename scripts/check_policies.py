"""Check what RLS policies exist on staging_extractions."""
import os
import psycopg
from dotenv import load_dotenv
from pathlib import Path

project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

db_url = os.environ.get('DIRECT_URL') or os.environ.get('DATABASE_URL')
if db_url and 'pgbouncer' in db_url:
    db_url = db_url.split('?')[0]

conn = psycopg.connect(db_url)

print("=" * 60)
print("RLS POLICIES ON staging_extractions")
print("=" * 60)

with conn.cursor() as cur:
    cur.execute("""
        SELECT
            policyname,
            permissive,
            roles,
            cmd,
            qual
        FROM pg_policies
        WHERE tablename = 'staging_extractions'
        ORDER BY policyname
    """)
    rows = cur.fetchall()

    if not rows:
        print("\nNo policies found!")
    else:
        print(f"\nFound {len(rows)} policies:")
        for row in rows:
            print(f"\n  Policy: {row[0]}")
            print(f"    Permissive: {row[1]}")
            print(f"    Roles: {row[2]}")
            print(f"    Command: {row[3]}")
            print(f"    Condition: {row[4][:100] if row[4] else 'None'}...")

    # Also check if RLS is enabled
    cur.execute("""
        SELECT relrowsecurity, relforcerowsecurity
        FROM pg_class
        WHERE relname = 'staging_extractions'
    """)
    rls_row = cur.fetchone()
    print(f"\n\nRLS enabled: {rls_row[0]}")
    print(f"Force RLS: {rls_row[1]}")

conn.close()
