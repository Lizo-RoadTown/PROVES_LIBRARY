"""
Provenance Reference

Tracks evidence lineage back to source documentation snapshots.
Critical for verifying knowledge claims and maintaining audit trails.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class ProvenanceRef:
    """
    Evidence provenance pointer.

    Links knowledge entities back to the source documentation snapshot
    where they were extracted, with optional byte-level evidence pointers.

    This enables:
    - Verification: Humans can check original sources
    - Audit trails: Track knowledge back to its origin
    - Re-extraction: If confidence is low, re-extract from source
    - Lineage verification: Validate evidence integrity via checksums
    """

    # Source snapshot reference
    source_snapshot_id: UUID
    source_url: str
    snapshot_checksum: str
    fetched_at: datetime

    # Optional: Byte-level evidence locators
    # (Available for staging extractions, may not be preserved in core_entities)
    evidence_checksum: Optional[str] = None
    evidence_byte_offset: Optional[int] = None
    evidence_byte_length: Optional[int] = None

    def has_byte_level_evidence(self) -> bool:
        """
        Check if byte-level evidence pointers are available.

        Returns:
            True if evidence_checksum and offsets are present

        Examples:
            >>> prov = ProvenanceRef(
            ...     source_snapshot_id=UUID(...),
            ...     source_url='https://example.com/docs',
            ...     snapshot_checksum='abc123',
            ...     fetched_at=datetime.now(),
            ...     evidence_checksum='def456',
            ...     evidence_byte_offset=1024
            ... )
            >>> prov.has_byte_level_evidence()
            True
        """
        return (self.evidence_checksum is not None and
                self.evidence_byte_offset is not None)

    def to_dict(self) -> dict:
        """
        Serialize to dictionary.

        Returns:
            Dictionary representation suitable for JSON

        Examples:
            >>> prov = ProvenanceRef(...)
            >>> data = prov.to_dict()
            >>> data['source_url']
            'https://example.com/docs'
        """
        return {
            'source_snapshot_id': str(self.source_snapshot_id),
            'source_url': self.source_url,
            'snapshot_checksum': self.snapshot_checksum,
            'fetched_at': self.fetched_at.isoformat(),
            'evidence_checksum': self.evidence_checksum,
            'evidence_byte_offset': self.evidence_byte_offset,
            'evidence_byte_length': self.evidence_byte_length,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProvenanceRef":
        """
        Deserialize from dictionary.

        Args:
            data: Dictionary with provenance data

        Returns:
            ProvenanceRef instance

        Examples:
            >>> data = {
            ...     'source_snapshot_id': '123e4567-e89b-12d3-a456-426614174000',
            ...     'source_url': 'https://example.com/docs',
            ...     'snapshot_checksum': 'abc123',
            ...     'fetched_at': '2025-01-15T10:00:00Z'
            ... }
            >>> prov = ProvenanceRef.from_dict(data)
            >>> prov.source_url
            'https://example.com/docs'
        """
        # Handle UUID and datetime conversions
        snapshot_id = data['source_snapshot_id']
        if isinstance(snapshot_id, str):
            snapshot_id = UUID(snapshot_id)

        fetched_at = data['fetched_at']
        if isinstance(fetched_at, str):
            fetched_at = datetime.fromisoformat(fetched_at.replace('Z', '+00:00'))

        return cls(
            source_snapshot_id=snapshot_id,
            source_url=data['source_url'],
            snapshot_checksum=data['snapshot_checksum'],
            fetched_at=fetched_at,
            evidence_checksum=data.get('evidence_checksum'),
            evidence_byte_offset=data.get('evidence_byte_offset'),
            evidence_byte_length=data.get('evidence_byte_length'),
        )

    def __str__(self) -> str:
        """Human-readable summary"""
        evidence_info = ""
        if self.has_byte_level_evidence():
            evidence_info = f" +evidence@{self.evidence_byte_offset}"

        return f"ProvenanceRef({self.source_url}{evidence_info})"
