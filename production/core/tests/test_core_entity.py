"""Tests for CoreEntity domain model"""

import pytest
from datetime import datetime
from uuid import UUID, uuid4
from production.core.domain.core_entity import CoreEntity
from production.core.domain.frames_dimensions import FramesDimensions


class TestIdentifierGeneration:
    """Test PROVES identifier generation"""

    def test_to_identifier(self):
        """Should generate correct identifier"""
        entity = CoreEntity(
            id=uuid4(),
            entity_type='component',
            canonical_key='TestDriver',
            name='TestDriver',
            ecosystem='fprime',
            verification_status='human_verified'
        )

        identifier = entity.to_identifier()

        assert identifier.entity_type == 'component'
        assert identifier.key == 'testdriver'  # Normalized
        assert identifier.ecosystem == 'fprime'
        assert identifier.uri == 'http://proves.space/fprime/component/testdriver'


class TestVerificationStatus:
    """Test verification status checks"""

    def test_is_verified_true(self):
        """Should return True when human_verified"""
        entity = CoreEntity(
            id=uuid4(),
            entity_type='component',
            canonical_key='test',
            name='test',
            ecosystem='fprime',
            verification_status='human_verified'
        )

        assert entity.is_verified() is True

    def test_is_verified_false(self):
        """Should return False when not human_verified"""
        entity = CoreEntity(
            id=uuid4(),
            entity_type='component',
            canonical_key='test',
            name='test',
            ecosystem='fprime',
            verification_status='pending'
        )

        assert entity.is_verified() is False


class TestExportability:
    """Test exportability checks"""

    def test_is_exportable_verified_current(self):
        """Verified current entity should be exportable"""
        entity = CoreEntity(
            id=uuid4(),
            entity_type='component',
            canonical_key='test',
            name='test',
            ecosystem='fprime',
            verification_status='human_verified',
            is_current=True
        )

        assert entity.is_exportable() is True

    def test_is_exportable_auto_approved(self):
        """Auto-approved should also be exportable"""
        entity = CoreEntity(
            id=uuid4(),
            entity_type='component',
            canonical_key='test',
            name='test',
            ecosystem='fprime',
            verification_status='auto_approved',
            is_current=True
        )

        assert entity.is_exportable() is True

    def test_is_exportable_not_current(self):
        """Superseded entity should not be exportable"""
        entity = CoreEntity(
            id=uuid4(),
            entity_type='component',
            canonical_key='test',
            name='test',
            ecosystem='fprime',
            verification_status='human_verified',
            is_current=False
        )

        assert entity.is_exportable() is False

    def test_is_exportable_pending(self):
        """Pending entity should not be exportable"""
        entity = CoreEntity(
            id=uuid4(),
            entity_type='component',
            canonical_key='test',
            name='test',
            ecosystem='fprime',
            verification_status='pending',
            is_current=True
        )

        assert entity.is_exportable() is False


class TestEpistemicRisk:
    """Test epistemic risk assessment"""

    def test_get_epistemic_risk_with_dimensions(self):
        """Should return risk when dimensions present"""
        dims = FramesDimensions(
            knowledge_form='embodied',
            formalizability='tacit'
        )

        entity = CoreEntity(
            id=uuid4(),
            entity_type='component',
            canonical_key='test',
            name='test',
            ecosystem='fprime',
            verification_status='human_verified',
            dimensions=dims
        )

        assert entity.get_epistemic_risk() == 'high_loss_risk'

    def test_get_epistemic_risk_no_dimensions(self):
        """Should return None when no dimensions"""
        entity = CoreEntity(
            id=uuid4(),
            entity_type='component',
            canonical_key='test',
            name='test',
            ecosystem='fprime',
            verification_status='human_verified'
        )

        assert entity.get_epistemic_risk() is None


class TestSerialization:
    """Test to_dict / from_dict"""

    def test_to_dict_minimal(self):
        """Should serialize minimal entity"""
        entity_id = uuid4()
        entity = CoreEntity(
            id=entity_id,
            entity_type='component',
            canonical_key='TestDriver',
            name='TestDriver',
            ecosystem='fprime',
            verification_status='human_verified'
        )

        data = entity.to_dict()

        assert data['id'] == str(entity_id)
        assert data['entity_type'] == 'component'
        assert data['canonical_key'] == 'TestDriver'
        assert data['name'] == 'TestDriver'
        assert data['ecosystem'] == 'fprime'
        assert data['verification_status'] == 'human_verified'
        assert 'identifier' in data

    def test_to_dict_with_dimensions(self):
        """Should include dimensions when present"""
        dims = FramesDimensions(
            contact_level='direct',
            contact_confidence=0.9
        )

        entity = CoreEntity(
            id=uuid4(),
            entity_type='component',
            canonical_key='test',
            name='test',
            ecosystem='fprime',
            verification_status='human_verified',
            dimensions=dims
        )

        data = entity.to_dict()

        assert 'dimensions' in data
        assert data['dimensions']['contact_level'] == 'direct'
        assert 'epistemic_risk' in data
        assert 'dimensional_confidence_avg' in data

    def test_from_dict_minimal(self):
        """Should deserialize minimal entity"""
        entity_id = uuid4()
        data = {
            'id': str(entity_id),
            'entity_type': 'component',
            'canonical_key': 'TestDriver',
            'name': 'TestDriver',
            'ecosystem': 'fprime',
            'verification_status': 'human_verified'
        }

        entity = CoreEntity.from_dict(data)

        assert entity.id == entity_id
        assert entity.entity_type == 'component'
        assert entity.canonical_key == 'TestDriver'
        assert entity.ecosystem == 'fprime'

    def test_from_dict_with_dimensions(self):
        """Should deserialize with dimensions"""
        data = {
            'id': str(uuid4()),
            'entity_type': 'component',
            'canonical_key': 'test',
            'name': 'test',
            'ecosystem': 'fprime',
            'verification_status': 'human_verified',
            'dimensions': {
                'contact_level': 'direct',
                'contact_confidence': 0.9,
                'contact_reasoning': 'Directly observed',
                'knowledge_form': None,
                'knowledge_form_confidence': None,
                'knowledge_form_reasoning': None,
                'directionality': None,
                'directionality_confidence': None,
                'directionality_reasoning': None,
                'temporality': None,
                'temporality_confidence': None,
                'temporality_reasoning': None,
                'formalizability': None,
                'formalizability_confidence': None,
                'formalizability_reasoning': None,
                'carrier': None,
                'carrier_confidence': None,
                'carrier_reasoning': None,
            }
        }

        entity = CoreEntity.from_dict(data)

        assert entity.dimensions is not None
        assert entity.dimensions.contact_level == 'direct'
        assert entity.dimensions.contact_confidence == 0.9

    def test_roundtrip(self):
        """Should roundtrip through dict"""
        original_id = uuid4()
        snapshot_id = uuid4()

        original = CoreEntity(
            id=original_id,
            entity_type='component',
            canonical_key='TestDriver',
            name='TestDriver',
            display_name='Test Driver Component',
            ecosystem='fprime',
            namespace='test.components',
            attributes={'version': '1.0', 'license': 'Apache-2.0'},
            verification_status='human_verified',
            verified_by='test-user',
            verified_at=datetime(2025, 1, 15, 10, 0, 0),
            source_snapshot_id=snapshot_id,
            version=2,
            is_current=True
        )

        data = original.to_dict()
        reconstructed = CoreEntity.from_dict(data)

        assert reconstructed.id == original.id
        assert reconstructed.canonical_key == original.canonical_key
        assert reconstructed.ecosystem == original.ecosystem
        assert reconstructed.verification_status == original.verification_status
        assert reconstructed.version == original.version
        assert reconstructed.source_snapshot_id == original.source_snapshot_id


class TestStringRepresentation:
    """Test string representations"""

    def test_str_verified(self):
        """Should show verified status in str()"""
        entity = CoreEntity(
            id=uuid4(),
            entity_type='component',
            canonical_key='TestDriver',
            name='TestDriver',
            ecosystem='fprime',
            verification_status='human_verified'
        )

        s = str(entity)
        assert 'fprime' in s
        assert 'component' in s
        assert 'TestDriver' in s
        assert 'verified' in s

    def test_str_pending(self):
        """Should show pending status in str()"""
        entity = CoreEntity(
            id=uuid4(),
            entity_type='component',
            canonical_key='TestDriver',
            name='TestDriver',
            ecosystem='fprime',
            verification_status='pending'
        )

        s = str(entity)
        assert 'pending' in s


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
