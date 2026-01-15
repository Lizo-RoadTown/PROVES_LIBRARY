"""
Core Entity Domain Model

Represents human-verified knowledge entities in the PROVES system.
This is the "truth layer" - entities that have passed human review
and are ready for export to MBSE tools.

Separate from CandidateExtraction (staging layer) to maintain
clear semantic boundaries.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from production.core.identifiers import ProvesIdentifier
from .frames_dimensions import FramesDimensions
from .provenance_ref import ProvenanceRef


@dataclass
class CoreEntity:
    """
    Human-verified entity in the knowledge base.

    This represents the "truth layer" - knowledge that has:
    1. Been extracted from documentation
    2. Passed validation checks
    3. Been reviewed and approved by humans
    4. Had FRAMES dimensions verified/adjusted

    CoreEntity is what gets exported to MBSE tools (SysML, XTCE, etc.).
    It is NOT the same as CandidateExtraction (staging layer).
    """

    # Core identity (required fields first)
    id: UUID
    entity_type: str  # 'component', 'port', 'dependency', etc.
    canonical_key: str  # Unique key within ecosystem
    name: str
    ecosystem: str  # 'fprime', 'ros2', 'cubesat', 'proveskit'

    # Optional identity fields
    display_name: Optional[str] = None
    namespace: Optional[str] = None

    # Flexible attributes (entity-specific data)
    attributes: Dict[str, Any] = None

    # FRAMES dimensions (human-verified)
    dimensions: Optional[FramesDimensions] = None

    # Verification metadata
    verification_status: str = 'pending'  # 'human_verified', 'auto_approved', 'pending', 'needs_review'
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    approval_source: Optional[str] = None  # 'notion_webhook', 'manual_review', 'auto_promotion'

    # Provenance (where did this come from?)
    source_snapshot_id: Optional[UUID] = None

    # Versioning (soft deletes)
    version: int = 1
    is_current: bool = True
    superseded_by_id: Optional[UUID] = None

    # Notion integration
    notion_page_id: Optional[str] = None

    # Human notes
    epistemic_notes: Optional[str] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize defaults"""
        if self.attributes is None:
            self.attributes = {}
        if self.display_name is None:
            self.display_name = self.name

    def to_identifier(self) -> ProvesIdentifier:
        """
        Get PROVES identifier for this entity.

        Returns:
            ProvesIdentifier with URI/URN support

        Examples:
            >>> entity = CoreEntity(
            ...     id=UUID(...),
            ...     entity_type='component',
            ...     canonical_key='TestDriver',
            ...     name='TestDriver',
            ...     ecosystem='fprime',
            ...     verification_status='human_verified'
            ... )
            >>> entity.to_identifier().uri
            'http://proves.space/fprime/component/testdriver'
        """
        return ProvesIdentifier(
            entity_type=self.entity_type,
            key=self.canonical_key,
            ecosystem=self.ecosystem
        )

    def is_verified(self) -> bool:
        """
        Check if entity has been human-verified.

        Returns:
            True if verification_status is 'human_verified'

        Examples:
            >>> entity = CoreEntity(..., verification_status='human_verified')
            >>> entity.is_verified()
            True
        """
        return self.verification_status == 'human_verified'

    def is_exportable(self) -> bool:
        """
        Check if entity is ready for export to MBSE tools.

        An entity is exportable if:
        - It's the current version (not superseded)
        - It's been verified (human or auto)

        Returns:
            True if safe to export

        Examples:
            >>> entity = CoreEntity(
            ...     ...,
            ...     verification_status='human_verified',
            ...     is_current=True
            ... )
            >>> entity.is_exportable()
            True
        """
        return (self.is_current and
                self.verification_status in ['human_verified', 'auto_approved'])

    def get_epistemic_risk(self) -> Optional[str]:
        """
        Assess epistemic risk level based on FRAMES dimensions.

        Returns:
            Risk category if dimensions available, None otherwise

        Examples:
            >>> entity = CoreEntity(
            ...     ...,
            ...     dimensions=FramesDimensions(
            ...         knowledge_form='embodied',
            ...         formalizability='tacit'
            ...     )
            ... )
            >>> entity.get_epistemic_risk()
            'high_loss_risk'
        """
        if self.dimensions:
            return self.dimensions.assess_epistemic_risk()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary (format-agnostic).

        Returns:
            Dictionary representation suitable for JSON or further processing

        Examples:
            >>> entity = CoreEntity(...)
            >>> data = entity.to_dict()
            >>> data['entity_type']
            'component'
        """
        result = {
            'id': str(self.id),
            'identifier': self.to_identifier().uri,
            'entity_type': self.entity_type,
            'canonical_key': self.canonical_key,
            'name': self.name,
            'display_name': self.display_name,
            'ecosystem': self.ecosystem,
            'namespace': self.namespace,
            'attributes': self.attributes,
            'verification_status': self.verification_status,
            'verified_by': self.verified_by,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'approval_source': self.approval_source,
            'source_snapshot_id': str(self.source_snapshot_id) if self.source_snapshot_id else None,
            'version': self.version,
            'is_current': self.is_current,
            'superseded_by_id': str(self.superseded_by_id) if self.superseded_by_id else None,
            'notion_page_id': self.notion_page_id,
            'epistemic_notes': self.epistemic_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        # Add dimensions if present
        if self.dimensions:
            result['dimensions'] = self.dimensions.to_dict()
            result['epistemic_risk'] = self.get_epistemic_risk()
            result['dimensional_confidence_avg'] = self.dimensions.avg_confidence()

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CoreEntity":
        """
        Deserialize from dictionary.

        Args:
            data: Dictionary with entity data

        Returns:
            CoreEntity instance

        Examples:
            >>> data = {
            ...     'id': '123e4567-e89b-12d3-a456-426614174000',
            ...     'entity_type': 'component',
            ...     'canonical_key': 'TestDriver',
            ...     'name': 'TestDriver',
            ...     'ecosystem': 'fprime',
            ...     'verification_status': 'human_verified'
            ... }
            >>> entity = CoreEntity.from_dict(data)
            >>> entity.canonical_key
            'TestDriver'
        """
        # Handle UUID conversions
        entity_id = data['id']
        if isinstance(entity_id, str):
            entity_id = UUID(entity_id)

        source_snapshot_id = data.get('source_snapshot_id')
        if isinstance(source_snapshot_id, str):
            source_snapshot_id = UUID(source_snapshot_id)

        superseded_by_id = data.get('superseded_by_id')
        if isinstance(superseded_by_id, str):
            superseded_by_id = UUID(superseded_by_id)

        # Handle datetime conversions
        verified_at = data.get('verified_at')
        if isinstance(verified_at, str):
            verified_at = datetime.fromisoformat(verified_at.replace('Z', '+00:00'))

        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

        updated_at = data.get('updated_at')
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))

        # Handle dimensions
        dimensions = None
        if 'dimensions' in data and data['dimensions']:
            dimensions = FramesDimensions.from_dict(data['dimensions'])

        return cls(
            id=entity_id,
            entity_type=data['entity_type'],
            canonical_key=data['canonical_key'],
            name=data['name'],
            display_name=data.get('display_name'),
            ecosystem=data['ecosystem'],
            namespace=data.get('namespace'),
            attributes=data.get('attributes', {}),
            dimensions=dimensions,
            verification_status=data.get('verification_status', 'pending'),
            verified_by=data.get('verified_by'),
            verified_at=verified_at,
            approval_source=data.get('approval_source'),
            source_snapshot_id=source_snapshot_id,
            version=data.get('version', 1),
            is_current=data.get('is_current', True),
            superseded_by_id=superseded_by_id,
            notion_page_id=data.get('notion_page_id'),
            epistemic_notes=data.get('epistemic_notes'),
            created_at=created_at,
            updated_at=updated_at,
        )

    def __str__(self) -> str:
        """Human-readable summary"""
        verified = "verified" if self.is_verified() else "pending"
        return f"CoreEntity({self.ecosystem}/{self.entity_type}/{self.canonical_key}, {verified})"

    def __repr__(self) -> str:
        """Debug representation"""
        return f"CoreEntity(id={self.id}, key={self.canonical_key}, type={self.entity_type}, verified={self.is_verified()})"
