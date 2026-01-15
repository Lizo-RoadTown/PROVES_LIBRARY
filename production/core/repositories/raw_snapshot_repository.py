"""
RawSnapshot Repository Interface

Abstract interface for querying raw documentation snapshots.
Read-only by design for provenance tracking.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from production.core.domain.raw_snapshot import RawSnapshot


class RawSnapshotRepository(ABC):
    """
    Abstract repository for querying RawSnapshot instances.

    Design principles:
    - Read-only: Snapshots are immutable once captured
    - Provenance: Used to trace entity lineage back to source
    - Performance: Minimal queries (snapshots are large JSONB)
    """

    @abstractmethod
    def get_by_id(self, snapshot_id: UUID) -> Optional[RawSnapshot]:
        """
        Retrieve snapshot by UUID.

        Args:
            snapshot_id: UUID of snapshot

        Returns:
            RawSnapshot if found, None otherwise
        """
        pass

    @abstractmethod
    def find_by_source_url(self, source_url: str, limit: int = 10) -> List[RawSnapshot]:
        """
        Find snapshots by source URL.

        Args:
            source_url: Source URL filter
            limit: Max results

        Returns:
            List of RawSnapshot instances, ordered by captured_at DESC
        """
        pass

    @abstractmethod
    def get_latest_for_url(self, source_url: str) -> Optional[RawSnapshot]:
        """
        Get most recent snapshot for a source URL.

        Args:
            source_url: Source URL

        Returns:
            Most recent RawSnapshot if found, None otherwise
        """
        pass
