"""
Manually Promote Extraction to Core Entities

After human review in Notion, use this script to promote approved extractions
to the core_entities truth table.

Usage:
    python promote_extraction.py EXTRACTION_ID [--dry-run]

Options:
    --dry-run    Preview what would be promoted without making changes
"""

import psycopg
import os
import sys
import argparse
from datetime import datetime, timezone
from dotenv import load_dotenv
import json

# Load environment
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(project_root, '.env'))

def promote_extraction(extraction_id, dry_run=False):
    """
    Promote an extraction from staging to core_entities.

    Args:
        extraction_id: UUID of extraction to promote
        dry_run: If True, preview only
    """
    print("\n" + "="*80)
    print("PROMOTE EXTRACTION TO CORE ENTITIES")
    print("="*80 + "\n")

    conn = psycopg.connect(os.environ['NEON_DATABASE_URL'])

    try:
        with conn.cursor() as cur:
            # Get extraction details
            cur.execute("""
                SELECT
                    e.extraction_id,
                    e.candidate_key,
                    e.candidate_type,
                    e.ecosystem,
                    e.candidate_payload,
                    e.confidence_score,
                    e.evidence,
                    e.snapshot_id,
                    e.pipeline_run_id,
                    e.status,
                    e.lineage_verified,
                    e.lineage_confidence,
                    rs.source_url
                FROM staging_extractions e
                JOIN raw_snapshots rs ON e.snapshot_id = rs.id
                WHERE e.extraction_id = %s::uuid
            """, (extraction_id,))

            extraction = cur.fetchone()

            if not extraction:
                print(f"[ERROR] Extraction not found: {extraction_id}")
                return False

            (ext_id, key, type_, ecosystem, payload, confidence, evidence,
             snapshot_id, run_id, status, lineage_verified, lineage_confidence,
             source_url) = extraction

            # Display extraction details
            print("EXTRACTION DETAILS")
            print("-" * 80)
            print(f"ID:               {ext_id}")
            print(f"Key:              {key}")
            print(f"Type:             {type_}")
            print(f"Ecosystem:        {ecosystem}")
            print(f"Confidence:       {confidence:.2f}")
            print(f"Lineage:          {lineage_confidence:.2f if lineage_confidence else 'N/A'}")
            print(f"Lineage Verified: {lineage_verified}")
            print(f"Status:           {status}")
            print(f"Source:           {source_url}")
            print()

            # Check if already promoted
            if status == 'approved':
                cur.execute("""
                    SELECT promoted_to_id, promoted_at
                    FROM staging_extractions
                    WHERE extraction_id = %s::uuid
                """, (extraction_id,))
                promoted = cur.fetchone()
                if promoted and promoted[0]:
                    print(f"[WARNING] Already promoted to {promoted[0]} at {promoted[1]}")
                    print("Skipping promotion.")
                    return False

            # Validate extraction is ready for promotion
            warnings = []

            if status == 'rejected':
                print("[ERROR] Cannot promote rejected extraction")
                return False

            if lineage_confidence and lineage_confidence < 0.5:
                warnings.append(f"Low lineage confidence ({lineage_confidence:.2f})")

            if confidence < 0.6:
                warnings.append(f"Low confidence score ({confidence:.2f})")

            if not lineage_verified:
                warnings.append("Lineage not fully verified")

            if warnings:
                print("WARNINGS")
                print("-" * 80)
                for warning in warnings:
                    print(f"  [!] {warning}")
                print()

            # Show what will be promoted
            print("PROMOTION PREVIEW")
            print("-" * 80)
            print("Will create entry in core_entities with:")
            print(f"  entity_type:        {type_}")
            print(f"  entity_key:         {key}")
            print(f"  ecosystem:          {ecosystem}")
            print(f"  confidence_score:   {confidence:.2f}")
            print(f"  source_snapshot_id: {snapshot_id}")
            print(f"  created_by_run_id:  {run_id}")
            print(f"  is_current:         TRUE")
            print(f"  version:            1")
            print()

            if dry_run:
                print("="*80)
                print("DRY RUN - No changes made")
                print("="*80)
                return True

            # Confirm promotion
            print("="*80)
            response = input("Promote this extraction to core_entities? [y/N]: ")
            if response.lower() != 'y':
                print("Promotion cancelled.")
                return False

            # Perform promotion
            print("\nPromoting...")

            # Insert into core_entities
            cur.execute("""
                INSERT INTO core_entities (
                    entity_type,
                    entity_key,
                    ecosystem,
                    attributes,
                    confidence_score,
                    evidence,
                    source_snapshot_id,
                    created_by_run_id,
                    is_current,
                    version,
                    created_at
                )
                SELECT
                    candidate_type,
                    candidate_key,
                    ecosystem,
                    candidate_payload,
                    confidence_score,
                    evidence,
                    snapshot_id,
                    pipeline_run_id,
                    TRUE,
                    1,
                    NOW()
                FROM staging_extractions
                WHERE extraction_id = %s::uuid
                RETURNING id
            """, (extraction_id,))

            entity_id = cur.fetchone()[0]

            # Update staging_extractions
            cur.execute("""
                UPDATE staging_extractions
                SET
                    status = 'approved',
                    promoted_to_id = %s,
                    promoted_at = NOW(),
                    updated_at = NOW()
                WHERE extraction_id = %s::uuid
            """, (entity_id, extraction_id))

            conn.commit()

            print("\n" + "="*80)
            print("PROMOTION SUCCESSFUL")
            print("="*80)
            print(f"Core Entity ID: {entity_id}")
            print(f"Extraction ID:  {extraction_id}")
            print(f"Status updated: approved")
            print()

            return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False

    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(
        description='Promote extraction to core_entities after human review'
    )
    parser.add_argument(
        'extraction_id',
        type=str,
        help='UUID of extraction to promote'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview promotion without making changes'
    )

    args = parser.parse_args()

    success = promote_extraction(args.extraction_id, dry_run=args.dry_run)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
