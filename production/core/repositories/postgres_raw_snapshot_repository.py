"""
PostgreSQL Implementation of RawSnapshotRepository

Uses existing database.py connection pool.
Maps Neon schema to RawSnapshot domain model.
"""

import sys
from pathlib import Path
from typing import List, Optional
from uuid import UUID

# Add Version 3 to path for database import
version3_path = Path(__file__).parent.parent.parent / "Version 3"
sys.path.insert(0, str(version3_path))

from database import get_connection
from production.core.domain.raw_snapshot import RawSnapshot
from production.core.repositories.raw_snapshot_repository import RawSnapshotRepository


class PostgresRawSnapshotRepository(RawSnapshotRepository):
    """
    PostgreSQL implementation of RawSnapshotRepository.

    Maps Neon database schema to RawSnapshot domain model.
    Uses shared connection pool from production/Version 3/database.py.

    Schema notes:
    - Column names: content_hash (not checksum), captured_at (not fetched_at)
    - payload column contains JSONB raw content
    - Snapshots are immutable (no updates, only inserts)
    """

    def _row_to_snapshot(self, row) -> RawSnapshot:
        """
        Convert database row to RawSnapshot domain model.

        Args:
            row: Database row tuple

        Returns:
            RawSnapshot instance

        Note:
            Maps Neon column names:
            - content_hash -> checksum (domain model)
            - captured_at -> fetched_at (domain model)
            - payload -> raw_payload (domain model)
        """
        return RawSnapshot(
            id=row[0],
            source_url=row[1],
            checksum=row[2] or 'unknown',
            fetched_at=row[3],
            raw_payload=row[4] or {}
        )

    def get_by_id(self, snapshot_id: UUID) -> Optional[RawSnapshot]:
        """
        Retrieve snapshot by UUID.

        Args:
            snapshot_id: UUID of snapshot

        Returns:
            RawSnapshot if found, None otherwise
        """
        with get_connection() as conn:
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
                    return self._row_to_snapshot(row)
                return None

    def find_by_source_url(self, source_url: str, limit: int = 10) -> List[RawSnapshot]:
        """
        Find snapshots by source URL.

        Args:
            source_url: Source URL filter
            limit: Max results

        Returns:
            List of RawSnapshot instances, ordered by captured_at DESC
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        id,
                        source_url,
                        content_hash,
                        captured_at,
                        payload
                    FROM raw_snapshots
                    WHERE source_url = %s
                    ORDER BY captured_at DESC
                    LIMIT %s
                """, (source_url, limit))

                return [self._row_to_snapshot(row) for row in cur.fetchall()]

    def get_latest_for_url(self, source_url: str) -> Optional[RawSnapshot]:
        """
        Get most recent snapshot for a source URL.

        Args:
            source_url: Source URL

        Returns:
            Most recent RawSnapshot if found, None otherwise
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        id,
                        source_url,
                        content_hash,
                        captured_at,
                        payload
                    FROM raw_snapshots
                    WHERE source_url = %s
                    ORDER BY captured_at DESC
                    LIMIT 1
                """, (source_url,))

                row = cur.fetchone()
                if row:
                    return self._row_to_snapshot(row)
                return None
