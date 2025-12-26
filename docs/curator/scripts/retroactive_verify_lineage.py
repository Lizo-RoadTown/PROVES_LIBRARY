"""
Retroactive Lineage Verification

Verifies the 6 existing PROVES Prime extractions that were created before
the lineage tracking system was implemented.

For each extraction:
1. Fetch the evidence and snapshot
2. Verify evidence exists in snapshot payload
3. Calculate checksums
4. Set lineage_confidence based on verification
5. Update database
"""

import psycopg
from dotenv import load_dotenv
import os
import json
import hashlib
from datetime import datetime, timezone

# Load environment
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(project_root, '.env'))

def verify_extraction_lineage(conn, extraction_id):
    """
    Verify lineage for one extraction.

    Returns:
        dict with verification results
    """
    checks_passed = []
    failures = []

    with conn.cursor() as cur:
        # Get extraction data
        cur.execute("""
            SELECT
                e.extraction_id,
                e.snapshot_id,
                e.candidate_key,
                e.evidence,
                e.confidence_score
            FROM staging_extractions e
            WHERE e.extraction_id = %s::uuid
        """, (extraction_id,))

        extraction = cur.fetchone()
        if not extraction:
            return {"error": "Extraction not found"}

        ext_id, snapshot_id, candidate_key, evidence, confidence_score = extraction

        # Check 1: Extraction exists
        checks_passed.append("Extraction exists in database")

        # Get snapshot data
        cur.execute("""
            SELECT
                payload,
                content_hash,
                source_url
            FROM raw_snapshots
            WHERE id = %s::uuid
        """, (snapshot_id,))

        snapshot = cur.fetchone()
        if not snapshot:
            failures.append("Snapshot not found - broken foreign key")
            return build_result(checks_passed, failures, ext_id, candidate_key)

        checks_passed.append("Snapshot exists and is linked")

        snapshot_payload, snapshot_checksum, source_url = snapshot

        # Check 2: Evidence exists in snapshot
        evidence_text = evidence.get('raw_text', '') if isinstance(evidence, dict) else ''

        if not evidence_text:
            failures.append("Evidence raw_text is empty")
            return build_result(checks_passed, failures, ext_id, candidate_key)

        # Convert payload to string for searching
        payload_str = json.dumps(snapshot_payload, sort_keys=True)

        # Find evidence in payload
        evidence_offset = payload_str.find(evidence_text)

        if evidence_offset == -1:
            # Try searching in the text field specifically
            if 'text' in snapshot_payload and evidence_text in snapshot_payload['text']:
                checks_passed.append("Evidence found in snapshot.text field")
                evidence_offset = snapshot_payload['text'].find(evidence_text)
            else:
                failures.append(f"Evidence quote not found in snapshot (searched for: '{evidence_text[:50]}...')")
                return build_result(checks_passed, failures, ext_id, candidate_key)
        else:
            checks_passed.append("Evidence found in snapshot payload")

        # Check 3: Calculate evidence checksum
        evidence_checksum = hashlib.sha256(evidence_text.encode()).hexdigest()
        evidence_length = len(evidence_text.encode())

        checks_passed.append("Evidence checksum calculated")

        # Check 4: Snapshot checksum (already exists as content_hash)
        if snapshot_checksum:
            checks_passed.append("Snapshot checksum exists")

        # Calculate lineage confidence
        total_checks = len(checks_passed) + len(failures)
        lineage_confidence = len(checks_passed) / total_checks if total_checks > 0 else 0.0

        # Update extraction with lineage data
        cur.execute("""
            UPDATE staging_extractions
            SET
                evidence_checksum = %s,
                evidence_byte_offset = %s,
                evidence_byte_length = %s,
                lineage_verified = %s,
                lineage_verified_at = %s,
                lineage_confidence = %s,
                lineage_verification_details = %s::jsonb,
                extraction_attempt = 1,
                is_reextraction = FALSE
            WHERE extraction_id = %s::uuid
        """, (
            evidence_checksum,
            evidence_offset,
            evidence_length,
            (len(failures) == 0),
            datetime.now(timezone.utc),
            lineage_confidence,
            json.dumps({
                "checks_passed": checks_passed,
                "checks_failed": failures,
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "verification_method": "retroactive"
            }),
            extraction_id
        ))

    return {
        "extraction_id": ext_id,
        "candidate_key": candidate_key,
        "lineage_confidence": lineage_confidence,
        "lineage_verified": (len(failures) == 0),
        "checks_passed": len(checks_passed),
        "checks_failed": len(failures),
        "failures": failures,
        "source_url": source_url
    }

def build_result(checks_passed, failures, ext_id, candidate_key):
    """Build partial result when verification fails early."""
    total_checks = len(checks_passed) + len(failures)
    lineage_confidence = len(checks_passed) / total_checks if total_checks > 0 else 0.0

    return {
        "extraction_id": ext_id,
        "candidate_key": candidate_key,
        "lineage_confidence": lineage_confidence,
        "lineage_verified": False,
        "checks_passed": len(checks_passed),
        "checks_failed": len(failures),
        "failures": failures
    }

def main():
    print("\n" + "="*80)
    print("RETROACTIVE LINEAGE VERIFICATION")
    print("="*80 + "\n")

    # Connect to database
    conn = psycopg.connect(os.environ['NEON_DATABASE_URL'])

    try:
        # Get all pending extractions
        with conn.cursor() as cur:
            cur.execute("""
                SELECT extraction_id, candidate_key
                FROM staging_extractions
                WHERE status = 'pending'
                ORDER BY created_at
            """)
            extractions = cur.fetchall()

        print(f"Found {len(extractions)} pending extractions to verify\n")

        results = []
        for extraction_id, candidate_key in extractions:
            print(f"Verifying: {candidate_key} ({extraction_id})...")
            result = verify_extraction_lineage(conn, extraction_id)
            results.append(result)

            if result.get('lineage_verified'):
                print(f"  [OK] Lineage confidence: {result['lineage_confidence']:.2f}")
            else:
                print(f"  [WARN] Lineage confidence: {result['lineage_confidence']:.2f}")
                for failure in result.get('failures', []):
                    print(f"    - {failure}")
            print()

        # Commit all updates
        conn.commit()

        # Summary
        print("="*80)
        print("SUMMARY")
        print("="*80 + "\n")

        verified_count = sum(1 for r in results if r.get('lineage_verified'))
        partial_count = sum(1 for r in results if not r.get('lineage_verified') and r.get('lineage_confidence', 0) > 0)
        failed_count = sum(1 for r in results if r.get('lineage_confidence', 0) == 0)

        print(f"Total extractions: {len(results)}")
        print(f"Fully verified: {verified_count}")
        print(f"Partially verified: {partial_count}")
        print(f"Failed verification: {failed_count}")
        print()

        for result in results:
            status = "[VERIFIED]" if result.get('lineage_verified') else "[PARTIAL]"
            confidence = result.get('lineage_confidence', 0)
            print(f"{status} {result['candidate_key']:<40} Confidence: {confidence:.2f}")

        print("\n" + "="*80)
        print("Verification complete!")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\nError during verification: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
