"""
Check what actually got extracted and staged in the last run
"""
import os
import psycopg
from dotenv import load_dotenv
import json

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

db_url = os.environ.get('NEON_DATABASE_URL')
conn = psycopg.connect(db_url)

print("=" * 80)
print("CHECKING LAST RUN STATE")
print("=" * 80)
print()

# Check staging_extractions
print("1. STAGING EXTRACTIONS (what was staged for verification):")
print("-" * 80)
with conn.cursor() as cur:
    cur.execute("""
        SELECT extraction_id, candidate_type::text, candidate_key,
               confidence_score, status::text, created_at
        FROM staging_extractions
        ORDER BY created_at DESC
        LIMIT 10
    """)
    rows = cur.fetchall()

    if not rows:
        print("   (No extractions staged)")
    else:
        for row in rows:
            ext_id, ctype, key, conf, status, created = row
            print(f"   {ctype}: {key}")
            print(f"     ID: {ext_id}")
            print(f"     Confidence: {conf}")
            print(f"     Status: {status}")
            print(f"     Created: {created}")
            print()

print()
print("2. RAW SNAPSHOTS (what content was fetched):")
print("-" * 80)
with conn.cursor() as cur:
    cur.execute("""
        SELECT id, source_url, source_type::text,
               payload_size_bytes, status::text, captured_at
        FROM raw_snapshots
        ORDER BY captured_at DESC
        LIMIT 5
    """)
    rows = cur.fetchall()

    if not rows:
        print("   (No snapshots)")
    else:
        for row in rows:
            snap_id, url, stype, size, status, captured = row
            print(f"   {stype}: {url[:80]}...")
            print(f"     ID: {snap_id}")
            print(f"     Size: {size} bytes")
            print(f"     Status: {status}")
            print(f"     Captured: {captured}")
            print()

print()
print("3. LANGGRAPH CHECKPOINTS (curator conversation state):")
print("-" * 80)
with conn.cursor() as cur:
    cur.execute("""
        SELECT thread_id, checkpoint_id, checkpoint_ns,
               parent_checkpoint_id
        FROM checkpoints
        WHERE thread_id LIKE 'daily-extraction%'
        ORDER BY checkpoint_id DESC
        LIMIT 5
    """)
    rows = cur.fetchall()

    if not rows:
        print("   (No checkpoints for daily-extraction threads)")
    else:
        for row in rows:
            thread, ckpt, ns, parent = row
            print(f"   Thread: {thread}")
            print(f"     Checkpoint: {ckpt}")
            print(f"     Namespace: {ns}")
            print()

conn.close()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print("If you see extractions in staging, the curator DID extract something")
print("but hit the recursion limit before presenting them for verification.")
print()
print("Next step: Either increase recursion_limit or fix the curator's stop logic.")
