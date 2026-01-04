#!/usr/bin/env python3
"""
Batch Promote Accepted Extractions
===================================
Promotes all accepted extractions to core_entities using hard matching logic.

This script calls the enhanced promote_to_core() function for each
accepted extraction that hasn't been promoted yet.

The function performs:
- Idempotency checks (won't re-promote)
- Hard identity matching (exact duplicates, approved aliases)
- Enrichment recording (tracks merges)
- Promotion tracking (updates promoted_at, promoted_to_entity_id)
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add production/core to path
project_root = Path(__file__).parent.parent.parent
core_path = project_root / 'production' / 'core'
sys.path.insert(0, str(core_path))

# Add Version 3 to path for storage module
version3_path = project_root / 'production' / 'Version 3'
sys.path.insert(0, str(version3_path))

from dotenv import load_dotenv
import psycopg

# Import promote_to_core - it's a @tool, so we need to call .invoke()
from storage_v3 import promote_to_core as promote_tool

# Load environment
load_dotenv(project_root / '.env')


def get_db_connection():
    """Get database connection"""
    db_url = os.environ.get('NEON_DATABASE_URL')
    if not db_url:
        raise ValueError("NEON_DATABASE_URL not set")
    return psycopg.connect(db_url)


def get_unpromoted_accepted(conn):
    """Get all accepted extractions not yet promoted"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                extraction_id,
                candidate_key,
                candidate_type::text,
                ecosystem::text,
                confidence_score,
                created_at
            FROM staging_extractions
            WHERE status::text = 'accepted'
            AND promoted_at IS NULL
            AND promotion_action IS NULL
            ORDER BY created_at ASC
        """)

        columns = ['extraction_id', 'candidate_key', 'candidate_type',
                   'ecosystem', 'confidence_score', 'created_at']

        return [dict(zip(columns, row)) for row in cur.fetchall()]


def parse_promotion_result(result_msg):
    """Parse the result message from promote_to_core()"""
    if '[CREATED]' in result_msg:
        return 'created'
    elif '[MERGED]' in result_msg:
        return 'merged'
    elif '[SKIPPED]' in result_msg:
        return 'skipped'
    elif 'Error' in result_msg:
        return 'error'
    else:
        return 'unknown'


def save_results_log(results, filename='batch_promotion_results.json'):
    """Save detailed results to JSON file"""
    output_path = Path(__file__).parent / filename

    # Convert datetime objects to strings for JSON serialization
    json_results = []
    for result in results:
        json_result = result.copy()
        if 'created_at' in json_result and json_result['created_at']:
            json_result['created_at'] = json_result['created_at'].isoformat()
        json_results.append(json_result)

    with open(output_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_processed': len(results),
            'results': json_results
        }, f, indent=2)

    print(f"\n  Detailed results saved to: {output_path}")


def print_summary_report(results):
    """Print summary report of promotion results"""

    # Count by action
    action_counts = defaultdict(int)
    for result in results:
        action_counts[result['action']] += 1

    # Count by ecosystem and action
    ecosystem_actions = defaultdict(lambda: defaultdict(int))
    for result in results:
        ecosystem_actions[result['ecosystem']][result['action']] += 1

    # Collect errors
    errors = [r for r in results if r['action'] == 'error']

    # Print report
    print("\n" + "=" * 80)
    print("BATCH PROMOTION SUMMARY REPORT")
    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total processed: {len(results)}")
    print()

    # Action summary
    print("ACTION SUMMARY")
    print("-" * 80)
    for action, count in sorted(action_counts.items()):
        pct = (count / len(results) * 100) if results else 0
        print(f"  {action.upper():15s}: {count:4d} ({pct:5.1f}%)")
    print()

    # By ecosystem
    print("BREAKDOWN BY ECOSYSTEM")
    print("-" * 80)
    for ecosystem, actions in sorted(ecosystem_actions.items()):
        total = sum(actions.values())
        print(f"\n  {ecosystem.upper()}: {total} entities")
        for action, count in sorted(actions.items()):
            print(f"    {action:12s}: {count:4d}")
    print()

    # Show errors if any
    if errors:
        print("ERRORS")
        print("-" * 80)
        for err in errors:
            print(f"  - {err['candidate_key']} ({err['ecosystem']})")
            print(f"    Error: {err.get('error_msg', 'Unknown error')[:100]}")
        print()

    # Show sample promotions
    created = [r for r in results if r['action'] == 'created']
    merged = [r for r in results if r['action'] == 'merged']

    if merged:
        print(f"SAMPLE MERGES (showing {min(5, len(merged))} of {len(merged)})")
        print("-" * 80)
        for result in merged[:5]:
            print(f"  - {result['candidate_key']} ({result['ecosystem']})")
            print(f"    {result['message']}")
        print()

    if created:
        print(f"SAMPLE CREATIONS (showing {min(5, len(created))} of {len(created)})")
        print("-" * 80)
        for result in created[:5]:
            print(f"  - {result['candidate_key']} ({result['ecosystem']})")
        print()

    print("=" * 80)
    print()


def main():
    """Main batch promotion function"""
    print("\n" + "=" * 80)
    print("BATCH PROMOTION OF ACCEPTED EXTRACTIONS")
    print("=" * 80)
    print()

    conn = get_db_connection()

    try:
        # Get unpromoted extractions
        unpromoted = get_unpromoted_accepted(conn)
        print(f"Found {len(unpromoted)} accepted extractions awaiting promotion")

        if not unpromoted:
            print("\nNothing to promote. All accepted extractions already promoted.")
            return

        print(f"Starting batch promotion...\n")

        # Process each extraction
        results = []
        for i, extraction in enumerate(unpromoted, 1):
            print(f"[{i}/{len(unpromoted)}] Processing: {extraction['candidate_key']} ({extraction['ecosystem']})...", end=' ')

            try:
                # Call the enhanced promote_to_core function via tool interface
                result_msg = promote_tool.invoke({'extraction_id': str(extraction['extraction_id'])})

                action = parse_promotion_result(result_msg)

                results.append({
                    'extraction_id': str(extraction['extraction_id']),
                    'candidate_key': extraction['candidate_key'],
                    'ecosystem': extraction['ecosystem'],
                    'action': action,
                    'message': result_msg,
                    'created_at': extraction['created_at']
                })

                print(f"{action.upper()}")

            except Exception as e:
                results.append({
                    'extraction_id': str(extraction['extraction_id']),
                    'candidate_key': extraction['candidate_key'],
                    'ecosystem': extraction['ecosystem'],
                    'action': 'error',
                    'error_msg': str(e),
                    'created_at': extraction['created_at']
                })

                print(f"ERROR: {str(e)[:60]}")

        # Print summary
        print_summary_report(results)

        # Save detailed log
        save_results_log(results)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
