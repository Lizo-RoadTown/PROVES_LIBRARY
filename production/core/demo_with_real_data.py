"""
Demo: Domain Models with Real Data from Neon

Shows how to query core_entities from Neon and create KnowledgeNodes
ready for export to MBSE tools.

Run: python production/core/demo_with_real_data.py
"""

import os
import sys
from datetime import datetime
from uuid import UUID
from dotenv import load_dotenv
import psycopg

# Add parent to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from production.core.domain import CoreEntity, KnowledgeNode, VerificationLevel
from production.core.domain.raw_snapshot import RawSnapshot
from production.core.identifiers import ProvesIdentifier


def fetch_sample_entities(limit=5):
    """
    Fetch sample entities from Neon core_entities table.

    Args:
        limit: Number of entities to fetch

    Returns:
        List of CoreEntity instances
    """
    load_dotenv()
    db_url = os.getenv('DATABASE_URL')

    entities = []

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    entity_type,
                    canonical_key,
                    name,
                    display_name,
                    ecosystem,
                    namespace,
                    attributes,
                    verification_status,
                    verified_by,
                    verified_at,
                    source_snapshot_id,
                    version,
                    is_current,
                    created_at
                FROM core_entities
                WHERE is_current = TRUE
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))

            for row in cur.fetchall():
                entity = CoreEntity(
                    id=row[0],
                    entity_type=row[1],
                    canonical_key=row[2],
                    name=row[3],
                    display_name=row[4],
                    ecosystem=row[5] or 'unknown',
                    namespace=row[6],
                    attributes=row[7] or {},
                    dimensions=None,  # Not yet migrated in Neon schema
                    verification_status=row[8] or 'pending',
                    verified_by=row[9],
                    verified_at=row[10],
                    source_snapshot_id=row[11],
                    version=row[12],
                    is_current=row[13],
                    created_at=row[14]
                )
                entities.append(entity)

    return entities


def fetch_snapshot(snapshot_id):
    """
    Fetch raw snapshot from Neon.

    Args:
        snapshot_id: UUID of snapshot

    Returns:
        RawSnapshot instance or None
    """
    load_dotenv()
    db_url = os.getenv('DATABASE_URL')

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    source_url,
                    content_hash,
                    captured_at,
                    payload
                FROM raw_snapshots
                WHERE id = %s
            """, (snapshot_id,))

            row = cur.fetchone()
            if row:
                return RawSnapshot(
                    id=row[0],
                    source_url=row[1],
                    checksum=row[2] or 'unknown',
                    fetched_at=row[3] or datetime.now(),
                    raw_payload=row[4] or {}
                )

    return None


def demo_identifiers():
    """Demo 1: Stable identifiers for entities"""
    print("=" * 70)
    print("DEMO 1: STABLE IDENTIFIERS")
    print("=" * 70)

    entities = fetch_sample_entities(limit=3)

    print(f"\nFetched {len(entities)} entities from Neon")
    print("\nGenerating stable URIs for external tool integration:\n")

    for entity in entities:
        identifier = entity.to_identifier()
        print(f"Entity: {entity.canonical_key}")
        print(f"  Type:      {entity.entity_type}")
        print(f"  Ecosystem: {entity.ecosystem}")
        print(f"  URI:       {identifier.uri}")
        print(f"  URN:       {identifier.urn}")
        print()


def demo_knowledge_nodes():
    """Demo 2: Creating KnowledgeNodes for export"""
    print("=" * 70)
    print("DEMO 2: KNOWLEDGE NODES FOR EXPORT")
    print("=" * 70)

    entities = fetch_sample_entities(limit=3)

    print(f"\nFetched {len(entities)} entities from Neon")
    print("\nCreating KnowledgeNodes for MBSE export:\n")

    for entity in entities:
        # Try to fetch actual snapshot
        snapshot = None
        if entity.source_snapshot_id:
            snapshot = fetch_snapshot(entity.source_snapshot_id)

        # Create mock snapshot if not found
        if not snapshot:
            snapshot = RawSnapshot(
                id=entity.source_snapshot_id or UUID('00000000-0000-0000-0000-000000000000'),
                source_url='https://example.com/docs',
                checksum='mock',
                fetched_at=datetime.now(),
                raw_payload={}
            )

        # Only create KnowledgeNode if entity is verified
        if entity.is_verified() or entity.verification_status == 'auto_approved':
            node = KnowledgeNode.from_core_entity(entity, snapshot)

            print(f"KnowledgeNode: {entity.canonical_key}")
            print(f"  Verification:  {node.verification.value}")
            print(f"  Exportable:    {node.is_exportable_to_standards()}")
            print(f"  Source URL:    {node.provenance.source_url}")
            print(f"  Identifier:    {node.identifier.uri}")
            print()
        else:
            print(f"Skipping {entity.canonical_key} - not verified")
            print(f"  Status: {entity.verification_status}")
            print()


def demo_verification_semantics():
    """Demo 3: Verification semantics enforcement"""
    print("=" * 70)
    print("DEMO 3: VERIFICATION SEMANTICS")
    print("=" * 70)

    entities = fetch_sample_entities(limit=10)

    verified_count = sum(1 for e in entities if e.is_verified())
    exportable_count = sum(1 for e in entities if e.is_exportable())

    print(f"\nAnalyzed {len(entities)} entities:")
    print(f"  Verified:   {verified_count}")
    print(f"  Exportable: {exportable_count}")
    print(f"  Pending:    {len(entities) - verified_count}")

    print("\nVerification Status Breakdown:")
    status_counts = {}
    for entity in entities:
        status = entity.verification_status
        status_counts[status] = status_counts.get(status, 0) + 1

    for status, count in sorted(status_counts.items()):
        print(f"  {status:20} {count}")

    print("\n✓ Only VERIFIED entities can be exported to MBSE tools")
    print("✓ Prevents accidental export of unverified candidate knowledge")


def demo_serialization():
    """Demo 4: Serialization for export"""
    print("=" * 70)
    print("DEMO 4: SERIALIZATION FOR EXPORT")
    print("=" * 70)

    entities = fetch_sample_entities(limit=1)

    if entities:
        entity = entities[0]

        # Create snapshot
        snapshot = RawSnapshot(
            id=entity.source_snapshot_id or UUID('00000000-0000-0000-0000-000000000000'),
            source_url='https://example.com/docs',
            checksum='mock',
            fetched_at=datetime.now(),
            raw_payload={}
        )

        print(f"\nEntity: {entity.canonical_key}")
        print(f"Status: {entity.verification_status}\n")

        if entity.is_verified() or entity.verification_status == 'auto_approved':
            # Create KnowledgeNode
            node = KnowledgeNode.from_core_entity(entity, snapshot)

            # Serialize to dict
            data = node.to_dict()

            print("Serialized to dictionary (format-agnostic):")
            print(f"  identifier:    {data['identifier']}")
            print(f"  entity_type:   {data['entity_type']}")
            print(f"  key:           {data['key']}")
            print(f"  ecosystem:     {data['ecosystem']}")
            print(f"  verification:  {data['verification']}")

            if 'attributes' in data and data['attributes']:
                print(f"  attributes:    {len(data['attributes'])} keys")

            print("\n✓ Ready for export to:")
            print("  - SysML v2 (MBSE integration)")
            print("  - XTCE (spacecraft telemetry)")
            print("  - GraphML (Gephi visualization)")
            print("  - JSON-LD (semantic web)")
        else:
            print("Cannot export - entity not verified")


def main():
    """Run all demos"""
    try:
        demo_identifiers()
        print("\n")

        demo_knowledge_nodes()
        print("\n")

        demo_verification_semantics()
        print("\n")

        demo_serialization()

        print("\n" + "=" * 70)
        print("✓ Domain models ready for MBSE integration")
        print("=" * 70)

    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("  1. .env file exists with DATABASE_URL")
        print("  2. You have network access to Neon database")
        print("  3. core_entities table has data")


if __name__ == "__main__":
    main()
