"""
PostgreSQL Implementation of CoreEntityRepository

Uses existing database.py connection pool from Version 3.
Maps Neon schema to CoreEntity domain model.
"""

import sys
from pathlib import Path
from typing import List, Optional
from uuid import UUID

# Add Version 3 to path for database import
version3_path = Path(__file__).parent.parent.parent / "Version 3"
sys.path.insert(0, str(version3_path))

from database import get_connection
from production.core.domain.core_entity import CoreEntity
from production.core.repositories.core_entity_repository import CoreEntityRepository


class PostgresCoreEntityRepository(CoreEntityRepository):
    """
    PostgreSQL implementation of CoreEntityRepository.

    Maps Neon database schema to CoreEntity domain model.
    Uses shared connection pool from production/Version 3/database.py.

    Schema notes:
    - Only queries is_current=TRUE entities
    - FRAMES dimensions not yet migrated (migration 009 pending)
    - Handles NULL values gracefully
    """

    def _row_to_entity(self, row) -> CoreEntity:
        """
        Convert database row to CoreEntity domain model.

        Args:
            row: Database row tuple

        Returns:
            CoreEntity instance

        Note:
            Handles NULL values and missing FRAMES dimensions gracefully.
        """
        return CoreEntity(
            id=row[0],
            entity_type=row[1],
            canonical_key=row[2],
            name=row[3],
            display_name=row[4],
            ecosystem=row[5] or 'unknown',
            namespace=row[6],
            attributes=row[7] or {},
            dimensions=None,  # Migration 009 not run yet
            verification_status=row[8] or 'pending',
            verified_by=row[9],
            verified_at=row[10],
            source_snapshot_id=row[11],
            version=row[12],
            is_current=row[13],
            created_at=row[14]
        )

    def get_by_id(self, entity_id: UUID) -> Optional[CoreEntity]:
        """
        Retrieve entity by UUID.

        Args:
            entity_id: UUID of entity

        Returns:
            CoreEntity if found, None otherwise
        """
        with get_connection() as conn:
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
                    WHERE id = %s AND is_current = TRUE
                """, (entity_id,))

                row = cur.fetchone()
                if row:
                    return self._row_to_entity(row)
                return None

    def get_by_canonical_key(self, canonical_key: str) -> Optional[CoreEntity]:
        """
        Retrieve entity by canonical key.

        Args:
            canonical_key: Unique canonical key

        Returns:
            CoreEntity if found, None otherwise
        """
        with get_connection() as conn:
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
                    WHERE canonical_key = %s AND is_current = TRUE
                """, (canonical_key,))

                row = cur.fetchone()
                if row:
                    return self._row_to_entity(row)
                return None

    def find_by_type(self, entity_type: str, limit: int = 100) -> List[CoreEntity]:
        """
        Find entities by type.

        Args:
            entity_type: Entity type filter
            limit: Max results

        Returns:
            List of CoreEntity instances
        """
        with get_connection() as conn:
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
                    WHERE entity_type = %s AND is_current = TRUE
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (entity_type, limit))

                return [self._row_to_entity(row) for row in cur.fetchall()]

    def find_by_ecosystem(self, ecosystem: str, limit: int = 100) -> List[CoreEntity]:
        """
        Find entities by ecosystem.

        Args:
            ecosystem: Ecosystem filter
            limit: Max results

        Returns:
            List of CoreEntity instances
        """
        with get_connection() as conn:
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
                    WHERE ecosystem = %s AND is_current = TRUE
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (ecosystem, limit))

                return [self._row_to_entity(row) for row in cur.fetchall()]

    def find_verified(self, limit: int = 100) -> List[CoreEntity]:
        """
        Find all verified entities ready for export.

        Args:
            limit: Max results

        Returns:
            List of verified CoreEntity instances
        """
        with get_connection() as conn:
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
                      AND verification_status IN ('human_verified', 'auto_approved')
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))

                return [self._row_to_entity(row) for row in cur.fetchall()]

    def find_by_namespace(self, namespace: str, limit: int = 100) -> List[CoreEntity]:
        """
        Find entities by namespace.

        Args:
            namespace: Namespace filter
            limit: Max results

        Returns:
            List of CoreEntity instances
        """
        with get_connection() as conn:
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
                    WHERE namespace = %s AND is_current = TRUE
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (namespace, limit))

                return [self._row_to_entity(row) for row in cur.fetchall()]

    def count_by_type(self) -> dict:
        """
        Count entities grouped by type.

        Returns:
            Dict mapping entity_type -> count
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT entity_type, COUNT(*)
                    FROM core_entities
                    WHERE is_current = TRUE
                    GROUP BY entity_type
                    ORDER BY entity_type
                """)

                return {row[0]: row[1] for row in cur.fetchall()}

    def count_by_verification_status(self) -> dict:
        """
        Count entities grouped by verification status.

        Returns:
            Dict mapping verification_status -> count
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT verification_status, COUNT(*)
                    FROM core_entities
                    WHERE is_current = TRUE
                    GROUP BY verification_status
                    ORDER BY verification_status
                """)

                return {row[0]: row[1] for row in cur.fetchall()}
