"""Check if epistemic metadata is being stored in knowledge_epistemics sidecar."""
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
print("KNOWLEDGE EPISTEMICS SIDECAR CHECK")
print("=" * 60)

with conn.cursor() as cur:
    # Check if knowledge_epistemics table has any data
    cur.execute("SELECT COUNT(*) FROM knowledge_epistemics")
    total = cur.fetchone()[0]
    print(f"\nTotal rows in knowledge_epistemics: {total}")

    if total == 0:
        print("\n⚠️  NO EPISTEMIC DATA IS BEING RECORDED!")
        print("   The extractor is not populating the knowledge_epistemics sidecar table.")
    else:
        # Get a sample of epistemic data
        cur.execute("""
            SELECT
                ke.extraction_id,
                se.candidate_key,
                ke.observer_id,
                ke.observer_type,
                ke.contact_mode,
                ke.contact_strength,
                ke.pattern_storage,
                ke.dependencies,
                ke.validity_conditions,
                ke.staleness_risk,
                ke.author_id,
                ke.intent,
                ke.reenactment_required,
                ke.skill_transferability
            FROM knowledge_epistemics ke
            JOIN staging_extractions se ON ke.extraction_id = se.extraction_id
            ORDER BY ke.created_at DESC
            LIMIT 3
        """)
        rows = cur.fetchall()

        print(f"\nSample of 3 most recent epistemic records:\n")
        for row in rows:
            print("-" * 50)
            print(f"Extraction: {row[1]} (ID: {str(row[0])[:8]}...)")
            print(f"\n  7 Questions Checklist:")
            print(f"  Q1 - Who knew this?")
            print(f"       observer_id: {row[2]}")
            print(f"       observer_type: {row[3]}")
            print(f"       contact_mode: {row[4]}")
            print(f"       contact_strength: {row[5]}")
            print(f"  Q2 - Where does experience live?")
            print(f"       pattern_storage: {row[6]}")
            print(f"  Q3 - What must stay connected?")
            print(f"       dependencies: {row[7]}")
            print(f"  Q4 - Under what conditions?")
            print(f"       validity_conditions: {row[8]}")
            print(f"  Q5 - When does this expire?")
            print(f"       staleness_risk: {row[9]}")
            print(f"  Q6 - Who wrote this and why?")
            print(f"       author_id: {row[10]}")
            print(f"       intent: {row[11]}")
            print(f"  Q7 - Does this require reenactment?")
            print(f"       reenactment_required: {row[12]}")
            print(f"       skill_transferability: {row[13]}")
            print()

    # Check how many extractions have epistemics vs don't
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE ke.extraction_id IS NOT NULL) as with_epistemics,
            COUNT(*) FILTER (WHERE ke.extraction_id IS NULL) as without_epistemics
        FROM staging_extractions se
        LEFT JOIN knowledge_epistemics ke ON se.extraction_id = ke.extraction_id
    """)
    with_ep, without_ep = cur.fetchone()
    print(f"\nExtractions with epistemics: {with_ep}")
    print(f"Extractions WITHOUT epistemics: {without_ep}")

conn.close()
