"""
Knowledge Node Projection

Unified export model that can represent both verified and candidate knowledge
while explicitly declaring verification semantics.

CRITICAL: Exporters must check verification level before exporting to
prevent accidental export of unverified candidate extractions as "official"
knowledge to MBSE tools.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional
from uuid import UUID

from production.core.identifiers import ProvesIdentifier
from .frames_dimensions import FramesDimensions
from .provenance_ref import ProvenanceRef


class VerificationLevel(Enum):
    """
    Explicit verification semantics.

    VERIFIED = Human-verified from core_entities
    CANDIDATE = Unverified from staging_extractions
    """
    VERIFIED = "verified"
    CANDIDATE = "candidate"


@dataclass
class KnowledgeNode:
    """
    Unified projection for export serializers.

    This allows exporters to work with both staging and core entities,
    but REQUIRES explicit declaration of verification level to prevent
    semantic blur.

    Rules:
    1. Stage 4 exporters should default to VERIFIED only
    2. CANDIDATE exports require explicit flag (debug/prototype mode)
    3. Verification level must match source (VERIFIED from core_entities,
       CANDIDATE from staging_extractions)

    Examples:
        >>> # From verified entity
        >>> node = KnowledgeNode.from_core_entity(entity, snapshot)
        >>> node.verification
        <VerificationLevel.VERIFIED: 'verified'>
        >>> node.confidence  # None for verified
        None

        >>> # From candidate (staging)
        >>> node = KnowledgeNode.from_candidate_extraction(candidate, snapshot)
        >>> node.verification
        <VerificationLevel.CANDIDATE: 'candidate'>
        >>> node.confidence  # Has machine confidence
        0.85
    """

    # Identity
    identifier: ProvesIdentifier
    key: str
    entity_type: str
    label: str  # Display name

    # Ecosystem context
    ecosystem: str
    namespace: Optional[str]

    # Flexible attributes (entity-specific data)
    attributes: Dict[str, Any]

    # FRAMES dimensions (only for VERIFIED)
    dimensions: Optional[FramesDimensions]

    # Provenance (where did this come from?)
    provenance: ProvenanceRef

    # VERIFICATION STATUS (REQUIRED)
    verification: VerificationLevel

    # Machine confidence (only for CANDIDATE)
    # Verified entities don't have "confidence" - they're human-verified
    confidence: Optional[float] = None

    def is_verified(self) -> bool:
        """
        Check if this is verified knowledge.

        Returns:
            True if VerificationLevel.VERIFIED

        Examples:
            >>> node = KnowledgeNode(..., verification=VerificationLevel.VERIFIED)
            >>> node.is_verified()
            True
        """
        return self.verification == VerificationLevel.VERIFIED

    def is_exportable_to_standards(self) -> bool:
        """
        Check if safe to export to standards formats (SysML, XTCE).

        Only verified knowledge should be exported to "official" formats.
        Candidates are for debug/prototype only.

        Returns:
            True if verified (safe for standards export)

        Examples:
            >>> verified_node = KnowledgeNode(..., verification=VerificationLevel.VERIFIED)
            >>> verified_node.is_exportable_to_standards()
            True

            >>> candidate_node = KnowledgeNode(..., verification=VerificationLevel.CANDIDATE)
            >>> candidate_node.is_exportable_to_standards()
            False
        """
        return self.is_verified()

    def get_epistemic_risk(self) -> Optional[str]:
        """
        Assess epistemic risk (if dimensions available).

        Only verified entities have FRAMES dimensions.

        Returns:
            Risk category if dimensions present, None otherwise
        """
        if self.dimensions:
            return self.dimensions.assess_epistemic_risk()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary.

        Returns:
            Format-agnostic dictionary suitable for export

        Examples:
            >>> node = KnowledgeNode(...)
            >>> data = node.to_dict()
            >>> data['verification']
            'verified'
        """
        result = {
            'identifier': str(self.identifier),
            'key': self.key,
            'entity_type': self.entity_type,
            'label': self.label,
            'ecosystem': self.ecosystem,
            'namespace': self.namespace,
            'attributes': self.attributes,
            'verification': self.verification.value,
            'provenance': self.provenance.to_dict(),
        }

        # Add confidence if present (only for candidates)
        if self.confidence is not None:
            result['confidence'] = self.confidence

        # Add dimensions if present (only for verified)
        if self.dimensions:
            result['dimensions'] = self.dimensions.to_dict()
            result['epistemic_risk'] = self.get_epistemic_risk()
            result['dimensional_confidence_avg'] = self.dimensions.avg_confidence()

        return result

    @classmethod
    def from_core_entity(
        cls,
        entity: "CoreEntity",  # type: ignore
        snapshot: "RawSnapshot"  # type: ignore
    ) -> "KnowledgeNode":
        """
        Create from verified core entity.

        Args:
            entity: CoreEntity instance (verified)
            snapshot: RawSnapshot with source documentation

        Returns:
            KnowledgeNode with VerificationLevel.VERIFIED

        Examples:
            >>> entity = CoreEntity(..., verification_status='human_verified')
            >>> snapshot = RawSnapshot(...)
            >>> node = KnowledgeNode.from_core_entity(entity, snapshot)
            >>> node.verification
            <VerificationLevel.VERIFIED: 'verified'>
            >>> node.confidence  # None for verified
            None
        """
        from .core_entity import CoreEntity  # Avoid circular import

        assert isinstance(entity, CoreEntity), "Must be CoreEntity instance"
        assert entity.is_verified() or entity.verification_status == 'auto_approved', \
            "Entity must be verified to create VERIFIED node"

        return cls(
            identifier=entity.to_identifier(),
            key=entity.canonical_key,
            entity_type=entity.entity_type,
            label=entity.display_name or entity.name,
            ecosystem=entity.ecosystem,
            namespace=entity.namespace,
            attributes=entity.attributes or {},
            dimensions=entity.dimensions,
            provenance=ProvenanceRef(
                source_snapshot_id=entity.source_snapshot_id or snapshot.id,
                source_url=snapshot.source_url,
                snapshot_checksum=snapshot.checksum,
                fetched_at=snapshot.fetched_at,
                # Note: Byte-level evidence not preserved in core_entities
                evidence_checksum=None,
                evidence_byte_offset=None,
                evidence_byte_length=None,
            ),
            verification=VerificationLevel.VERIFIED,
            confidence=None,  # Verified entities don't have machine confidence
        )

    @classmethod
    def from_candidate_extraction(
        cls,
        candidate: "CandidateExtraction",  # type: ignore
        snapshot: "RawSnapshot"  # type: ignore
    ) -> "KnowledgeNode":
        """
        Create from unverified candidate extraction.

        Args:
            candidate: CandidateExtraction instance (staging)
            snapshot: RawSnapshot with source documentation

        Returns:
            KnowledgeNode with VerificationLevel.CANDIDATE

        Examples:
            >>> candidate = CandidateExtraction(..., status='pending')
            >>> snapshot = RawSnapshot(...)
            >>> node = KnowledgeNode.from_candidate_extraction(candidate, snapshot)
            >>> node.verification
            <VerificationLevel.CANDIDATE: 'candidate'>
            >>> node.confidence  # Has machine confidence
            0.85
        """
        # Note: CandidateExtraction not yet implemented, so this is a placeholder
        # This will be implemented when we add write support to repositories

        return cls(
            identifier=ProvesIdentifier(
                entity_type=candidate.candidate_type,
                key=candidate.candidate_key,
                ecosystem=candidate.ecosystem
            ),
            key=candidate.candidate_key,
            entity_type=candidate.candidate_type,
            label=candidate.candidate_key,  # No display_name in staging
            ecosystem=candidate.ecosystem,
            namespace=None,  # Not in staging
            attributes=candidate.candidate_payload or {},
            dimensions=None,  # Candidates don't have verified dimensions
            provenance=ProvenanceRef(
                source_snapshot_id=candidate.snapshot_id,
                source_url=snapshot.source_url,
                snapshot_checksum=snapshot.checksum,
                fetched_at=snapshot.fetched_at,
                evidence_checksum=candidate.evidence_checksum,
                evidence_byte_offset=candidate.evidence_byte_offset,
                evidence_byte_length=candidate.evidence_byte_length,
            ),
            verification=VerificationLevel.CANDIDATE,
            confidence=candidate.confidence_score,
        )

    def __str__(self) -> str:
        """Human-readable summary"""
        verification_str = "✓ verified" if self.is_verified() else "? candidate"
        return f"KnowledgeNode({self.ecosystem}/{self.entity_type}/{self.key}, {verification_str})"

    def __repr__(self) -> str:
        """Debug representation"""
        return f"KnowledgeNode(key={self.key}, type={self.entity_type}, verification={self.verification.value})"
