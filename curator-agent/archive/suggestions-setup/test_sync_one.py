"""Test syncing one extraction with formatted content blocks"""
from src.curator.notion_sync import NotionSync
import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

sync = NotionSync()

# Get one unsynced extraction
conn = psycopg.connect(os.getenv('NEON_DATABASE_URL'))
with conn.cursor() as cur:
    cur.execute("""
        SELECT
            extraction_id, candidate_type, candidate_key, status,
            confidence_score, confidence_reason, ecosystem, evidence,
            created_at, lineage_verified, lineage_confidence,
            candidate_payload, snapshot_id
        FROM staging_extractions
        WHERE notion_page_id IS NULL
        LIMIT 1
    """)

    row = cur.fetchone()
    if not row:
        print("No unsynced extractions found")
        exit()

    extraction_data = {
        'extraction_id': row[0],
        'candidate_type': row[1],
        'candidate_key': row[2],
        'status': row[3],
        'confidence_score': row[4],
        'confidence_reason': row[5],
        'ecosystem': row[6],
        'evidence': row[7],
        'created_at': row[8],
        'lineage_verified': row[9],
        'lineage_confidence': row[10],
        'candidate_payload': row[11],
        'snapshot_id': row[12]
    }

    print(f"Syncing extraction: {extraction_data['candidate_key']}")
    print(f"Type: {extraction_data['candidate_type']}")
    print(f"Has payload: {extraction_data['candidate_payload'] is not None}")
    print(f"Payload value: {extraction_data['candidate_payload']}")
    print(f"Confidence reason: {extraction_data.get('confidence_reason')}")
    print(f"Snapshot ID: {extraction_data.get('snapshot_id')}")
    print()

    try:
        page_id = sync.sync_extraction(extraction_data)
        print(f"\n✓ Successfully synced to Notion!")
        print(f"Page ID: {page_id}")
        print(f"\nOpen in Notion: https://notion.so/{page_id.replace('-', '')}")

        # Update database with notion_page_id
        cur.execute(
            "UPDATE staging_extractions SET notion_page_id = %s WHERE extraction_id = %s",
            (page_id, extraction_data['extraction_id'])
        )
        conn.commit()

    except Exception as e:
        print(f"\n❌ Error syncing: {e}")
        import traceback
        traceback.print_exc()

conn.close()
