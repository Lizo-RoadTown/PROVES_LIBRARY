"""
Sync Staging Extractions to Notion for Human Review

Queries staging_extractions for pending items and creates entries in Notion
Extraction Review database for human verification.

Usage:
    python sync_to_notion.py [--database-id DATABASE_ID] [--dry-run]

Options:
    --database-id   Notion database ID for Extraction Review (required)
    --dry-run       Preview what would be synced without creating Notion pages
"""

import psycopg
import os
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(project_root, '.env'))

def get_pending_extractions(conn):
    """
    Get all pending extractions that need human review.

    Returns:
        List of dicts with extraction data
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                e.extraction_id,
                e.candidate_key,
                e.candidate_type,
                e.ecosystem,
                e.confidence_score,
                e.evidence,
                e.candidate_payload,
                e.created_at,
                e.snapshot_id,
                e.lineage_confidence,
                e.lineage_verified,
                e.extraction_attempt,
                e.is_reextraction,
                e.requires_mandatory_review,
                e.mandatory_review_reason,
                rs.source_url,
                rs.payload
            FROM staging_extractions e
            JOIN raw_snapshots rs ON e.snapshot_id = rs.id
            WHERE e.status = 'pending'
            ORDER BY
                e.requires_mandatory_review DESC,
                e.lineage_confidence ASC NULLS FIRST,
                e.created_at DESC
        """)

        rows = cur.fetchall()

        extractions = []
        for row in rows:
            extractions.append({
                'extraction_id': str(row[0]),
                'candidate_key': row[1],
                'candidate_type': row[2],
                'ecosystem': row[3],
                'confidence_score': float(row[4]) if row[4] else 0.0,
                'evidence': row[5],
                'candidate_payload': row[6],
                'created_at': row[7].isoformat() if row[7] else None,
                'snapshot_id': str(row[8]),
                'lineage_confidence': float(row[9]) if row[9] else 0.0,
                'lineage_verified': row[10],
                'extraction_attempt': row[11],
                'is_reextraction': row[12],
                'requires_mandatory_review': row[13],
                'mandatory_review_reason': row[14],
                'source_url': row[15],
                'payload': row[16]
            })

        return extractions

def format_for_notion(extraction):
    """
    Format extraction data for Notion page properties.

    Args:
        extraction: Dict with extraction data

    Returns:
        Dict with Notion page properties
    """
    # Extract evidence text
    evidence = extraction['evidence']
    evidence_text = ''
    if isinstance(evidence, dict):
        evidence_text = evidence.get('raw_text', evidence.get('quote', ''))
    elif isinstance(evidence, str):
        evidence_text = evidence

    # Truncate evidence if too long (Notion has limits)
    if len(evidence_text) > 2000:
        evidence_text = evidence_text[:1997] + '...'

    # Format candidate_payload for display
    candidate_payload = extraction.get('candidate_payload', {})
    if isinstance(candidate_payload, dict):
        payload_text = json.dumps(candidate_payload, indent=2)
    else:
        payload_text = str(candidate_payload)

    # Truncate payload if too long
    if len(payload_text) > 2000:
        payload_text = payload_text[:1997] + '...'

    # Determine initial status
    if extraction['requires_mandatory_review']:
        status = 'Needs Investigation'
    elif extraction['is_reextraction']:
        status = 'Re-extraction (Review Required)'
    else:
        status = 'Pending Review'

    # Build Notion properties
    notion_props = {
        'Name': {
            'title': [{'text': {'content': extraction['candidate_key']}}]
        },
        'Type': {
            'select': {'name': extraction['candidate_type'] or 'unknown'}
        },
        'Ecosystem': {
            'select': {'name': extraction['ecosystem'] or 'unknown'}
        },
        'Confidence': {
            'number': extraction['confidence_score']
        },
        'Lineage': {
            'number': extraction['lineage_confidence']
        },
        'Status': {
            'select': {'name': status}
        },
        'Extraction ID': {
            'rich_text': [{'text': {'content': extraction['extraction_id']}}]
        },
        'Source URL': {
            'url': extraction['source_url']
        },
        'Evidence': {
            'rich_text': [{'text': {'content': evidence_text}}]
        },
        'Attributes': {
            'rich_text': [{'text': {'content': payload_text}}]
        },
        'Created': {
            'date': {'start': extraction['created_at']}
        },
        'Lineage Verified': {
            'checkbox': extraction['lineage_verified'] or False
        },
        'Extraction Attempt': {
            'number': extraction['extraction_attempt'] or 1
        },
        'Requires Investigation': {
            'checkbox': extraction['requires_mandatory_review'] or False
        }
    }

    return notion_props

def create_notion_page(database_id, properties, use_api=False, api_key=None):
    """
    Create a page in Notion database.

    Args:
        database_id: Notion database ID
        properties: Page properties dict
        use_api: If True, use Notion API directly (requires api_key)
        api_key: Notion API key (if use_api=True)

    Returns:
        Page ID if successful, None otherwise
    """
    if use_api:
        # Direct Notion API call
        import requests

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }

        data = {
            'parent': {'database_id': database_id},
            'properties': properties
        }

        response = requests.post(
            'https://api.notion.com/v1/pages',
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            return response.json()['id']
        else:
            print(f"  [ERROR] Notion API error: {response.status_code}")
            print(f"  {response.text}")
            return None
    else:
        # Print instructions for manual creation or MCP usage
        print("\n  [NOTION MCP] Create page with properties:")
        print(f"  Database: {database_id}")
        print(f"  Properties: {json.dumps(properties, indent=2)}")
        return None

def sync_extractions_to_notion(dry_run=False, database_id=None, use_api=False):
    """
    Main sync function.

    Args:
        dry_run: If True, only preview what would be synced
        database_id: Notion database ID
        use_api: If True, use Notion API directly
    """
    print("\n" + "="*80)
    print("SYNC STAGING EXTRACTIONS TO NOTION")
    print("="*80 + "\n")

    # Connect to database
    conn = psycopg.connect(os.environ['NEON_DATABASE_URL'])

    try:
        # Get pending extractions
        extractions = get_pending_extractions(conn)

        print(f"Found {len(extractions)} pending extractions\n")

        if len(extractions) == 0:
            print("No extractions to sync!")
            return

        # Preview
        print("="*80)
        print("PREVIEW")
        print("="*80 + "\n")

        for i, ext in enumerate(extractions, 1):
            status_flag = "[!]" if ext['requires_mandatory_review'] else "[OK]"
            print(f"{i}. {status_flag} {ext['candidate_key']}")
            print(f"   Type: {ext['candidate_type']}, Ecosystem: {ext['ecosystem']}")
            print(f"   Confidence: {ext['confidence_score']:.2f}, Lineage: {ext['lineage_confidence']:.2f}")
            print(f"   Lineage Verified: {ext['lineage_verified']}")
            print(f"   Extraction Attempt: {ext['extraction_attempt']}")
            if ext['requires_mandatory_review']:
                print(f"   [!] REQUIRES INVESTIGATION: {ext['mandatory_review_reason']}")
            print(f"   Source: {ext['source_url']}")
            print()

        if dry_run:
            print("="*80)
            print("DRY RUN - No pages created")
            print("="*80 + "\n")
            return

        # Check if we can sync
        if not database_id:
            print("="*80)
            print("MANUAL SYNC REQUIRED")
            print("="*80 + "\n")
            print("To sync to Notion, you need to:")
            print("1. Create 'Extraction Review' database in Notion")
            print("2. Add properties as defined in notion_schemas.md")
            print("3. Get database ID from URL (the part after workspace/ and before ?)")
            print("4. Run: python sync_to_notion.py --database-id YOUR_DATABASE_ID")
            print("\nAlternatively, use Notion MCP in Claude Desktop to create pages.")
            return

        # Sync to Notion
        print("="*80)
        print("SYNCING TO NOTION")
        print("="*80 + "\n")

        notion_api_key = os.getenv('NOTION_API_KEY') if use_api else None

        synced_count = 0
        failed_count = 0

        for ext in extractions:
            print(f"Syncing: {ext['candidate_key']}...")

            # Format for Notion
            properties = format_for_notion(ext)

            # Create page
            page_id = create_notion_page(
                database_id,
                properties,
                use_api=use_api,
                api_key=notion_api_key
            )

            if page_id or not use_api:
                synced_count += 1
                print(f"  [OK] Created page: {page_id or 'Manual creation required'}")
            else:
                failed_count += 1
                print(f"  [FAIL] Could not create page")

            print()

        # Summary
        print("="*80)
        print("SYNC COMPLETE")
        print("="*80 + "\n")
        print(f"Total extractions: {len(extractions)}")
        print(f"Synced successfully: {synced_count}")
        print(f"Failed: {failed_count}")
        print()

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(
        description='Sync staging extractions to Notion for human review'
    )
    parser.add_argument(
        '--database-id',
        type=str,
        help='Notion database ID for Extraction Review database'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be synced without creating pages'
    )
    parser.add_argument(
        '--use-api',
        action='store_true',
        help='Use Notion API directly (requires NOTION_API_KEY in .env)'
    )

    args = parser.parse_args()

    sync_extractions_to_notion(
        dry_run=args.dry_run,
        database_id=args.database_id,
        use_api=args.use_api
    )

if __name__ == "__main__":
    main()
