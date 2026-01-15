"""Tests for FRAMES dimensional metadata"""

import pytest
from production.core.domain.frames_dimensions import FramesDimensions


class TestValidation:
    """Test dimensional validation"""

    def test_validate_valid_dimensions(self):
        """Valid dimensions should pass validation"""
        dims = FramesDimensions(
            contact_level='direct',
            contact_confidence=0.9,
            formalizability='portable',
            formalizability_confidence=0.8
        )

        errors = dims.validate()
        assert len(errors) == 0

    def test_validate_confidence_out_of_range(self):
        """Confidence outside 0-1 should fail"""
        dims = FramesDimensions(
            contact_level='direct',
            contact_confidence=1.5  # Invalid
        )

        errors = dims.validate()
        assert len(errors) == 1
        assert 'contact_confidence' in errors[0]

    def test_validate_invalid_enum_value(self):
        """Invalid enum value should fail"""
        dims = FramesDimensions(
            knowledge_form='invalid'  # Not in valid set
        )

        errors = dims.validate()
        assert len(errors) == 1
        assert 'knowledge_form' in errors[0]

    def test_validate_all_valid_enums(self):
        """All valid enum values should pass"""
        dims = FramesDimensions(
            knowledge_form='embodied',
            contact_level='direct',
            directionality='forward',
            temporality='snapshot',
            formalizability='portable',
            carrier='artifact'
        )

        errors = dims.validate()
        assert len(errors) == 0


class TestCompleteness:
    """Test completeness checking"""

    def test_is_complete_all_dimensions(self):
        """Should be complete when all dimensions set"""
        dims = FramesDimensions(
            knowledge_form='embodied',
            contact_level='direct',
            directionality='forward',
            temporality='snapshot',
            formalizability='portable',
            carrier='artifact'
        )

        assert dims.is_complete() is True

    def test_is_complete_missing_dimensions(self):
        """Should not be complete when dimensions missing"""
        dims = FramesDimensions(
            contact_level='direct',
            formalizability='portable'
        )

        assert dims.is_complete() is False


class TestConfidenceCalculation:
    """Test average confidence calculation"""

    def test_avg_confidence_all_dimensions(self):
        """Should average all confidence values"""
        dims = FramesDimensions(
            knowledge_form='embodied',
            knowledge_form_confidence=1.0,
            contact_level='direct',
            contact_confidence=0.8,
            directionality='forward',
            directionality_confidence=0.9,
            temporality='snapshot',
            temporality_confidence=0.7,
            formalizability='portable',
            formalizability_confidence=0.6,
            carrier='artifact',
            carrier_confidence=0.5
        )

        avg = dims.avg_confidence()
        expected = (1.0 + 0.8 + 0.9 + 0.7 + 0.6 + 0.5) / 6
        assert abs(avg - expected) < 0.01

    def test_avg_confidence_partial_dimensions(self):
        """Should average only dimensions with confidence"""
        dims = FramesDimensions(
            contact_level='direct',
            contact_confidence=0.9,
            formalizability='portable',
            formalizability_confidence=0.7
        )

        avg = dims.avg_confidence()
        assert abs(avg - 0.8) < 0.01

    def test_avg_confidence_no_confidences(self):
        """Should return None when no confidences"""
        dims = FramesDimensions(
            contact_level='direct'
        )

        assert dims.avg_confidence() is None


class TestEpistemicRisk:
    """Test epistemic risk assessment"""

    def test_high_loss_risk(self):
        """Embodied + tacit should be high loss risk"""
        dims = FramesDimensions(
            knowledge_form='embodied',
            formalizability='tacit'
        )

        assert dims.assess_epistemic_risk() == 'high_loss_risk'

    def test_inference_cascade_risk(self):
        """Indirect + backward should be inference cascade risk"""
        dims = FramesDimensions(
            contact_level='indirect',
            directionality='backward'
        )

        assert dims.assess_epistemic_risk() == 'inference_cascade_risk'

    def test_temporal_context_missing(self):
        """History/lifecycle should flag temporal context"""
        dims = FramesDimensions(
            temporality='history'
        )

        assert dims.assess_epistemic_risk() == 'temporal_context_missing'

    def test_low_risk(self):
        """Safe dimensions should be low risk"""
        dims = FramesDimensions(
            knowledge_form='inferred',
            contact_level='direct',
            directionality='forward',
            temporality='snapshot',
            formalizability='portable'
        )

        assert dims.assess_epistemic_risk() == 'low_risk'


class TestSerialization:
    """Test to_dict / from_dict"""

    def test_to_dict(self):
        """Should serialize to dictionary"""
        dims = FramesDimensions(
            contact_level='direct',
            contact_confidence=0.9,
            contact_reasoning='Directly observed'
        )

        data = dims.to_dict()

        assert data['contact_level'] == 'direct'
        assert data['contact_confidence'] == 0.9
        assert data['contact_reasoning'] == 'Directly observed'

    def test_from_dict(self):
        """Should deserialize from dictionary"""
        data = {
            'contact_level': 'direct',
            'contact_confidence': 0.9,
            'contact_reasoning': 'Directly observed',
            'formalizability': 'portable',
            'formalizability_confidence': 0.8,
            'formalizability_reasoning': 'Well documented',
            'knowledge_form': None,
            'knowledge_form_confidence': None,
            'knowledge_form_reasoning': None,
            'directionality': None,
            'directionality_confidence': None,
            'directionality_reasoning': None,
            'temporality': None,
            'temporality_confidence': None,
            'temporality_reasoning': None,
            'carrier': None,
            'carrier_confidence': None,
            'carrier_reasoning': None,
        }

        dims = FramesDimensions.from_dict(data)

        assert dims.contact_level == 'direct'
        assert dims.contact_confidence == 0.9
        assert dims.formalizability == 'portable'

    def test_roundtrip(self):
        """Should roundtrip through dict"""
        original = FramesDimensions(
            knowledge_form='embodied',
            knowledge_form_confidence=0.95,
            contact_level='direct',
            contact_confidence=0.9
        )

        data = original.to_dict()
        reconstructed = FramesDimensions.from_dict(data)

        assert reconstructed.knowledge_form == original.knowledge_form
        assert reconstructed.knowledge_form_confidence == original.knowledge_form_confidence
        assert reconstructed.contact_level == original.contact_level
        assert reconstructed.contact_confidence == original.contact_confidence


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
