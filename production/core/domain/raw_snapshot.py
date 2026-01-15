"""
Raw Snapshot Model

Represents a snapshot of source documentation at a point in time.
Used for provenance tracking.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
from uuid import UUID


@dataclass
class RawSnapshot:
    """
    Raw documentation snapshot.

    Represents a captured version of source documentation (HTML, markdown, etc.)
    at a specific point in time. Used for provenance tracking and lineage
    verification.
    """

    id: UUID
    source_url: str
    checksum: str  # SHA256 of payload
    fetched_at: datetime
    raw_payload: Dict[str, Any]  # JSONB with page content

    def __str__(self) -> str:
        """Human-readable summary"""
        return f"RawSnapshot({self.source_url}, {self.fetched_at.date()})"

    def __repr__(self) -> str:
        """Debug representation"""
        return f"RawSnapshot(id={self.id}, url={self.source_url})"
