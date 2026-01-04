#!/usr/bin/env python3
"""
Analyze Accepted Extractions Batch
===================================
Dry-run analysis of what would happen during batch promotion.

This script:
1. Queries all accepted extractions awaiting promotion
2. For each, checks for exact duplicates, aliases, and cross-ecosystem matches
3. Generates a detailed report without making any changes

Run this BEFORE batch promotion to understand what will happen.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add production/core to path
project_root = Path(__file__).parent.parent.parent
core_path = project_root / 'production' / 'core'
sys.path.insert(0, str(core_path))

from dotenv import load_dotenv
import psycopg

# Load environment
load_dotenv(project_root / '.env')


def get_db_connection():
    """Get database connection"""
    db_url = os.environ.get('NEON_DATABASE_URL')
    if not db_url:
        raise ValueError("NEON_DATABASE_URL not set")
    return psycopg.connect(db_url)


def get_accepted_extractions(conn):
    """Get all accepted extractions not yet promoted"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                extraction_id,
                candidate_key,
                candidate_type::text,
                ecosystem::text,
                confidence_score,
                created_at,
                snapshot_id
            FROM staging_extractions
            WHERE status::text = 'accepted'
            ORDER BY created_at ASC
        """)

        columns = ['extraction_id', 'candidate_key', 'candidate_type',
                   'ecosystem', 'confidence_score', 'created_at', 'snapshot_id']

        return [dict(zip(columns, row)) for row in cur.fetchall()]


def find_exact_duplicate(conn, candidate_key, ecosystem, entity_type):
    """Check if exact duplicate exists in core_entities"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, name, created_at
            FROM core_entities
            WHERE canonical_key = %s
            AND ecosystem::text = %s
            AND entity_type::text = %s
            LIMIT 1
        """, (candidate_key, ecosystem, entity_type))

        row = cur.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'created_at': row[2]
            }
        return None


def find_approved_alias(conn, candidate_key, ecosystem):
    """Check if there's an approved alias match"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                alias_id,
                canonical_key,
                canonical_entity_id,
                alias_type
            FROM entity_alias
            WHERE alias_text = %s
            AND ecosystem::text = %s
            AND resolution_status = 'resolved'
            LIMIT 1
        """, (candidate_key, ecosystem))

        row = cur.fetchone()
        if row:
            return {
                'alias_id': row[0],
                'canonical_key': row[1],
                'canonical_entity_id': row[2],
                'alias_type': row[3]
            }
        return None


def find_cross_ecosystem_matches(conn, candidate_key, entity_type, current_ecosystem):
    """Find entities with same key in different ecosystems"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                id,
                canonical_key,
                ecosystem::text,
                name
            FROM core_entities
            WHERE canonical_key = %s
            AND entity_type::text = %s
            AND ecosystem::text != %s
        """, (candidate_key, entity_type, current_ecosystem))

        matches = []
        for row in cur.fetchall():
            matches.append({
                'id': row[0],
                'canonical_key': row[1],
                'ecosystem': row[2],
                'name': row[3]
            })
        return matches


def analyze_extraction(conn, extraction):
    """Analyze a single extraction and determine what would happen"""
    candidate_key = extraction['candidate_key']
    ecosystem = extraction['ecosystem']
    entity_type = extraction['candidate_type']

    analysis = {
        'extraction': extraction,
        'action': None,
        'reason': None,
        'target_entity': None,
        'cross_ecosystem_matches': []
    }

    # Check 1: Exact duplicate (same key + ecosystem + type)
    exact_match = find_exact_duplicate(conn, candidate_key, ecosystem, entity_type)
    if exact_match:
        analysis['action'] = 'MERGE'
        analysis['reason'] = 'Exact duplicate found'
        analysis['target_entity'] = exact_match
        return analysis

    # Check 2: Approved alias match
    alias_match = find_approved_alias(conn, candidate_key, ecosystem)
    if alias_match:
        analysis['action'] = 'MERGE'
        analysis['reason'] = f'Alias match (type: {alias_match["alias_type"]})'
        analysis['target_entity'] = alias_match
        return analysis

    # Check 3: Cross-ecosystem matches (not auto-merge, just flag)
    cross_matches = find_cross_ecosystem_matches(conn, candidate_key, entity_type, ecosystem)
    if cross_matches:
        analysis['action'] = 'CREATE'
        analysis['reason'] = 'No exact match in same ecosystem'
        analysis['cross_ecosystem_matches'] = cross_matches
        return analysis

    # Default: Create new entity
    analysis['action'] = 'CREATE'
    analysis['reason'] = 'New entity - no duplicates or aliases found'
    return analysis


def generate_report(analyses):
    """Generate detailed analysis report"""

    # Count actions
    action_counts = defaultdict(int)
    ecosystem_counts = defaultdict(lambda: defaultdict(int))
    cross_ecosystem_pairs = []

    for analysis in analyses:
        action = analysis['action']
        ecosystem = analysis['extraction']['ecosystem']

        action_counts[action] += 1
        ecosystem_counts[ecosystem][action] += 1

        if analysis['cross_ecosystem_matches']:
            for match in analysis['cross_ecosystem_matches']:
                cross_ecosystem_pairs.append({
                    'source': analysis['extraction'],
                    'match': match
                })

    # Print report
    print("\n" + "=" * 80)
    print("BATCH PROMOTION ANALYSIS REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total accepted extractions analyzed: {len(analyses)}")
    print()

    # Summary
    print("ACTION SUMMARY")
    print("-" * 80)
    for action, count in sorted(action_counts.items()):
        pct = (count / len(analyses) * 100) if analyses else 0
        print(f"  {action:15s}: {count:4d} ({pct:5.1f}%)")
    print()

    # By ecosystem
    print("BREAKDOWN BY ECOSYSTEM")
    print("-" * 80)
    for ecosystem, actions in sorted(ecosystem_counts.items()):
        total = sum(actions.values())
        print(f"\n  {ecosystem.upper()}: {total} extractions")
        for action, count in sorted(actions.items()):
            print(f"    {action:12s}: {count:4d}")
    print()

    # Cross-ecosystem opportunities
    if cross_ecosystem_pairs:
        print("CROSS-ECOSYSTEM EQUIVALENCE OPPORTUNITIES")
        print("-" * 80)
        print(f"  Found {len(cross_ecosystem_pairs)} potential cross-ecosystem matches")
        print("  These will CREATE new entities + suggest equivalence candidates")
        print()

        # Group by ecosystem pair
        ecosystem_pairs = defaultdict(list)
        for pair in cross_ecosystem_pairs:
            src_eco = pair['source']['ecosystem']
            dst_eco = pair['match']['ecosystem']
            key = f"{src_eco} ↔ {dst_eco}"
            ecosystem_pairs[key].append(pair)

        for pair_key, pairs in sorted(ecosystem_pairs.items()):
            # Replace Unicode arrow with ASCII
            pair_key_ascii = pair_key.replace('↔', '<->')
            print(f"  {pair_key_ascii}: {len(pairs)} matches")
        print()

    # Detailed listings
    print("DETAILED ACTION LIST")
    print("-" * 80)

    # Group by action
    by_action = defaultdict(list)
    for analysis in analyses:
        by_action[analysis['action']].append(analysis)

    # Show merges first (most important)
    if 'MERGE' in by_action:
        print(f"\n  MERGES ({len(by_action['MERGE'])} items):")
        print("  " + "-" * 76)
        for analysis in by_action['MERGE']:
            ext = analysis['extraction']
            target = analysis['target_entity']
            print(f"    - {ext['candidate_key']:30s} ({ext['ecosystem']})")
            print(f"      -> Merge with entity {str(target.get('id', 'unknown'))[:8]}...")
            print(f"      Reason: {analysis['reason']}")
            print()

    # Show creates with cross-ecosystem matches
    creates_with_matches = [a for a in by_action.get('CREATE', [])
                           if a['cross_ecosystem_matches']]
    if creates_with_matches:
        print(f"\n  NEW ENTITIES WITH CROSS-ECOSYSTEM MATCHES ({len(creates_with_matches)} items):")
        print("  " + "-" * 76)
        for analysis in creates_with_matches:
            ext = analysis['extraction']
            print(f"    - {ext['candidate_key']:30s} ({ext['ecosystem']})")
            print(f"      -> Create new entity")
            for match in analysis['cross_ecosystem_matches']:
                print(f"      ** Similar in {match['ecosystem']}: {match['name']}")
            print()

    # Show simple creates
    simple_creates = [a for a in by_action.get('CREATE', [])
                     if not a['cross_ecosystem_matches']]
    if simple_creates:
        print(f"\n  NEW ENTITIES (no cross-ecosystem matches) ({len(simple_creates)} items):")
        print("  " + "-" * 76)
        for analysis in simple_creates[:10]:  # Show first 10
            ext = analysis['extraction']
            print(f"    - {ext['candidate_key']:30s} ({ext['ecosystem']})")
        if len(simple_creates) > 10:
            print(f"    ... and {len(simple_creates) - 10} more")
        print()

    print("=" * 80)
    print("\nNOTE: This is a DRY RUN - no changes have been made to the database.")
    print("Run batch_promote_accepted.py to execute the actual promotion.")
    print("=" * 80)
    print()


def main():
    """Main analysis function"""
    print("\n[ANALYSIS] Analyzing accepted extractions batch...")
    print("This may take a moment for large batches...\n")

    conn = get_db_connection()

    try:
        # Get all accepted extractions
        extractions = get_accepted_extractions(conn)
        print(f"Found {len(extractions)} accepted extractions awaiting promotion\n")

        if not extractions:
            print("No accepted extractions found. Nothing to analyze.")
            return

        # Analyze each one
        analyses = []
        for i, extraction in enumerate(extractions, 1):
            if i % 10 == 0:
                print(f"  Analyzing {i}/{len(extractions)}...", end='\r')

            analysis = analyze_extraction(conn, extraction)
            analyses.append(analysis)

        print(f"  Analyzed {len(extractions)}/{len(extractions)} [DONE]    ")

        # Generate report
        generate_report(analyses)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
