"""Tests for KnowledgeNode projection"""

import pytest
from datetime import datetime
from uuid import uuid4
from production.core.domain.knowledge_node import KnowledgeNode, VerificationLevel
from production.core.domain.core_entity import CoreEntity
from production.core.domain.frames_dimensions import FramesDimensions
from production.core.domain.provenance_ref import ProvenanceRef
from production.core.domain.raw_snapshot import RawSnapshot
from production.core.identifiers import ProvesIdentifier


class TestVerificationSemantics:
    """Test explicit verification semantics"""

    def test_verified_node_from_core_entity(self):
        """Verified node should have VERIFIED level and no confidence"""
        entity = CoreEntity(
            id=uuid4(),
            entity_type='component',
            canonical_key='TestDriver',
            name='TestDriver',
            ecosystem='fprime',
            verification_status='human_verified',
            source_snapshot_id=uuid4()
        )

        snapshot = RawSnapshot(
            id=uuid4(),
            source_url='https://example.com/docs',
            checksum='abc123',
            fetched_at=datetime.now(),
            raw_payload={}
        )

        node = KnowledgeNode.from_core_entity(entity, snapshot)

        assert node.verification == VerificationLevel.VERIFIED
        assert node.confidence is None  # Verified has no machine confidence
        assert node.is_verified() is True
        assert node.is_exportable_to_standards() is True

    def test_verified_flag_must_match_source(self):
        """VERIFIED flag must only come from verified entities"""
        # Pending entity should fail
        entity = CoreEntity(
            id=uuid4(),
            entity_type='component',
            canonical_key='test',
            name='test',
            ecosystem='fprime',
            verification_status='pending',  # Not verified!
            source_snapshot_id=uuid4()
        )

        snapshot = RawSnapshot(
            id=uuid4(),
            source_url='https://example.com',
            checksum='abc',
            fetched_at=datetime.now(),
            raw_payload={}
        )

        # Should raise assertion error
        with pytest.raises(AssertionError, match="must be verified"):
            KnowledgeNode.from_core_entity(entity, snapshot)


class TestExportability:
    """Test exportability checks"""

    def test_verified_exportable_to_standards(self):
        """Verified nodes should be exportable to standards"""
        node = KnowledgeNode(
            identifier=ProvesIdentifier('component', 'test', ecosystem='fprime'),
            key='test',
            entity_type='component',
            label='Test Component',
            ecosystem='fprime',
            namespace=None,
            attributes={},
            dimensions=None,
            provenance=ProvenanceRef(
                source_snapshot_id=uuid4(),
                source_url='https://example.com',
                snapshot_checksum='abc',
                fetched_at=datetime.now()
            ),
            verification=VerificationLevel.VERIFIED,
            confidence=None
        )

        assert node.is_exportable_to_standards() is True

    def test_candidate_not_exportable_to_standards(self):
        """Candidate nodes should NOT be exportable to standards"""
        node = KnowledgeNode(
            identifier=ProvesIdentifier('component', 'test', ecosystem='fprime'),
            key='test',
            entity_type='component',
            label='Test Component',
            ecosystem='fprime',
            namespace=None,
            attributes={},
            dimensions=None,
            provenance=ProvenanceRef(
                source_snapshot_id=uuid4(),
                source_url='https://example.com',
                snapshot_checksum='abc',
                fetched_at=datetime.now()
            ),
            verification=VerificationLevel.CANDIDATE,
            confidence=0.85
        )

        assert node.is_exportable_to_standards() is False


class TestDimensionsAndRisk:
    """Test FRAMES dimensions integration"""

    def test_get_epistemic_risk_with_dimensions(self):
        """Should assess risk when dimensions present"""
        dims = FramesDimensions(
            knowledge_form='embodied',
            formalizability='tacit'
        )

        node = KnowledgeNode(
            identifier=ProvesIdentifier('component', 'test', ecosystem='fprime'),
            key='test',
            entity_type='component',
            label='Test',
            ecosystem='fprime',
            namespace=None,
            attributes={},
            dimensions=dims,
            provenance=ProvenanceRef(
                source_snapshot_id=uuid4(),
                source_url='https://example.com',
                snapshot_checksum='abc',
                fetched_at=datetime.now()
            ),
            verification=VerificationLevel.VERIFIED
        )

        assert node.get_epistemic_risk() == 'high_loss_risk'

    def test_get_epistemic_risk_no_dimensions(self):
        """Should return None when no dimensions"""
        node = KnowledgeNode(
            identifier=ProvesIdentifier('component', 'test', ecosystem='fprime'),
            key='test',
            entity_type='component',
            label='Test',
            ecosystem='fprime',
            namespace=None,
            attributes={},
            dimensions=None,
            provenance=ProvenanceRef(
                source_snapshot_id=uuid4(),
                source_url='https://example.com',
                snapshot_checksum='abc',
                fetched_at=datetime.now()
            ),
            verification=VerificationLevel.CANDIDATE,
            confidence=0.8
        )

        assert node.get_epistemic_risk() is None


class TestSerialization:
    """Test to_dict serialization"""

    def test_to_dict_verified_with_dimensions(self):
        """Verified node with dimensions should serialize correctly"""
        dims = FramesDimensions(
            contact_level='direct',
            contact_confidence=0.9
        )

        node = KnowledgeNode(
            identifier=ProvesIdentifier('component', 'TestDriver', ecosystem='fprime'),
            key='TestDriver',
            entity_type='component',
            label='Test Driver',
            ecosystem='fprime',
            namespace='test.components',
            attributes={'version': '1.0'},
            dimensions=dims,
            provenance=ProvenanceRef(
                source_snapshot_id=uuid4(),
                source_url='https://example.com',
                snapshot_checksum='abc',
                fetched_at=datetime.now()
            ),
            verification=VerificationLevel.VERIFIED
        )

        data = node.to_dict()

        assert data['key'] == 'TestDriver'
        assert data['entity_type'] == 'component'
        assert data['ecosystem'] == 'fprime'
        assert data['verification'] == 'verified'
        assert 'confidence' not in data  # No confidence for verified
        assert 'dimensions' in data
        assert data['dimensions']['contact_level'] == 'direct'
        assert 'epistemic_risk' in data
        assert 'dimensional_confidence_avg' in data

    def test_to_dict_candidate_with_confidence(self):
        """Candidate node should include confidence"""
        node = KnowledgeNode(
            identifier=ProvesIdentifier('component', 'test', ecosystem='fprime'),
            key='test',
            entity_type='component',
            label='Test',
            ecosystem='fprime',
            namespace=None,
            attributes={},
            dimensions=None,
            provenance=ProvenanceRef(
                source_snapshot_id=uuid4(),
                source_url='https://example.com',
                snapshot_checksum='abc',
                fetched_at=datetime.now()
            ),
            verification=VerificationLevel.CANDIDATE,
            confidence=0.85
        )

        data = node.to_dict()

        assert data['verification'] == 'candidate'
        assert data['confidence'] == 0.85
        assert 'dimensions' not in data  # Candidates don't have dimensions


class TestFromCoreEntity:
    """Test creating KnowledgeNode from CoreEntity"""

    def test_from_core_entity_minimal(self):
        """Should create node from minimal entity"""
        entity_id = uuid4()
        snapshot_id = uuid4()

        entity = CoreEntity(
            id=entity_id,
            entity_type='component',
            canonical_key='TestDriver',
            name='TestDriver',
            ecosystem='fprime',
            verification_status='human_verified',
            source_snapshot_id=snapshot_id
        )

        snapshot = RawSnapshot(
            id=snapshot_id,
            source_url='https://github.com/nasa/fprime',
            checksum='abc123def',
            fetched_at=datetime(2025, 1, 15, 10, 0, 0),
            raw_payload={'content': 'test'}
        )

        node = KnowledgeNode.from_core_entity(entity, snapshot)

        assert node.key == 'TestDriver'
        assert node.entity_type == 'component'
        assert node.ecosystem == 'fprime'
        assert node.verification == VerificationLevel.VERIFIED
        assert node.provenance.source_url == 'https://github.com/nasa/fprime'
        assert node.provenance.source_snapshot_id == snapshot_id

    def test_from_core_entity_with_dimensions(self):
        """Should include dimensions from entity"""
        dims = FramesDimensions(
            contact_level='direct',
            contact_confidence=0.9
        )

        entity = CoreEntity(
            id=uuid4(),
            entity_type='component',
            canonical_key='TestDriver',
            name='TestDriver',
            ecosystem='fprime',
            dimensions=dims,
            verification_status='human_verified',
            source_snapshot_id=uuid4()
        )

        snapshot = RawSnapshot(
            id=uuid4(),
            source_url='https://example.com',
            checksum='abc',
            fetched_at=datetime.now(),
            raw_payload={}
        )

        node = KnowledgeNode.from_core_entity(entity, snapshot)

        assert node.dimensions is not None
        assert node.dimensions.contact_level == 'direct'
        assert node.get_epistemic_risk() is not None


class TestStringRepresentation:
    """Test string representations"""

    def test_str_verified(self):
        """Should show verified status"""
        node = KnowledgeNode(
            identifier=ProvesIdentifier('component', 'test', ecosystem='fprime'),
            key='test',
            entity_type='component',
            label='Test',
            ecosystem='fprime',
            namespace=None,
            attributes={},
            dimensions=None,
            provenance=ProvenanceRef(
                source_snapshot_id=uuid4(),
                source_url='https://example.com',
                snapshot_checksum='abc',
                fetched_at=datetime.now()
            ),
            verification=VerificationLevel.VERIFIED
        )

        s = str(node)
        assert 'verified' in s.lower()
        assert 'fprime' in s
        assert 'component' in s
        assert 'test' in s

    def test_str_candidate(self):
        """Should show candidate status"""
        node = KnowledgeNode(
            identifier=ProvesIdentifier('component', 'test', ecosystem='fprime'),
            key='test',
            entity_type='component',
            label='Test',
            ecosystem='fprime',
            namespace=None,
            attributes={},
            dimensions=None,
            provenance=ProvenanceRef(
                source_snapshot_id=uuid4(),
                source_url='https://example.com',
                snapshot_checksum='abc',
                fetched_at=datetime.now()
            ),
            verification=VerificationLevel.CANDIDATE,
            confidence=0.8
        )

        s = str(node)
        assert 'candidate' in s.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
