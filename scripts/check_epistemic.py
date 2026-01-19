"""Check if epistemic metadata is being stored in extractions."""
import os
import json
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
print("EPISTEMIC METADATA CHECK")
print("=" * 60)

with conn.cursor() as cur:
    # Get a few recent extractions with their full payload
    cur.execute("""
        SELECT
            extraction_id,
            candidate_key,
            candidate_type,
            candidate_payload,
            evidence,
            created_at
        FROM staging_extractions
        WHERE status = 'pending'
        ORDER BY created_at DESC
        LIMIT 3
    """)
    rows = cur.fetchall()

    if not rows:
        print("\nNo pending extractions found!")
    else:
        print(f"\nChecking {len(rows)} recent extractions:\n")

        for row in rows:
            extraction_id, key, ctype, payload, evidence, created = row
            print(f"─" * 50)
            print(f"ID: {extraction_id[:8]}...")
            print(f"Key: {key}")
            print(f"Type: {ctype}")
            print(f"Created: {created}")

            # Check candidate_payload for epistemic data
            print(f"\n  CANDIDATE_PAYLOAD keys: {list(payload.keys()) if payload else 'None'}")

            if payload:
                # Look for epistemic fields
                epistemic_fields = ['contact', 'directionality', 'temporality', 'formalizability',
                                   'epistemic', 'epistemic_metadata', 'knowledge_type']
                found_epistemic = {k: payload.get(k) for k in epistemic_fields if k in payload}

                if found_epistemic:
                    print(f"  EPISTEMIC DATA FOUND:")
                    for k, v in found_epistemic.items():
                        print(f"    {k}: {v}")
                else:
                    print(f"  NO EPISTEMIC FIELDS in payload")
                    print(f"  Full payload sample: {json.dumps(payload, indent=4)[:500]}...")

            # Check evidence field
            print(f"\n  EVIDENCE keys: {list(evidence.keys()) if evidence else 'None'}")
            if evidence:
                print(f"  Evidence sample: {json.dumps(evidence, indent=4)[:300]}...")

            print()

conn.close()
