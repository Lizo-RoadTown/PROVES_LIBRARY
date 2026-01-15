"""
Tests for JSON Schema Validation (Option A - Task 1.2)

Tests the schema_validator.py module for extraction validation.
"""
import os
import sys
import pytest
from pathlib import Path

# Setup paths
version3_folder = Path(__file__).parent.parent
project_root = version3_folder.parent.parent
production_root = project_root / 'production'

sys.path.insert(0, str(production_root))
sys.path.insert(0, str(version3_folder))


class TestSchemaValidator:
    """Tests for extraction schema validation."""

    def test_import_schema_validator(self):
        """Test that schema validator can be imported."""
        from schema_validator import validate_extraction, ValidationResult
        assert validate_extraction is not None
        assert ValidationResult is not None

    def test_valid_minimal_extraction(self):
        """Test validation of minimal valid extraction."""
        from schema_validator import validate_extraction

        result = validate_extraction({
            "candidate_type": "component",
            "candidate_key": "test_component",
            "raw_evidence": "This is test evidence"
        })

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_valid_full_extraction(self):
        """Test validation of fully populated extraction."""
        from schema_validator import validate_extraction

        result = validate_extraction({
            "candidate_type": "component",
            "candidate_key": "ms5611_barometer",
            "raw_evidence": "The MS5611 is a barometric pressure sensor",
            "source_snapshot_id": "12345678-1234-1234-1234-123456789abc",
            "ecosystem": "proveskit",
            "description": "Barometric pressure sensor for altitude",
            "confidence_score": 0.85,
            "confidence_reason": "Clear documentation",
            "lineage_verified": True,
            "lineage_confidence": 0.95,
            "epistemic_defaults": {
                "observer_type": "llm",
                "observer_id": "claude-sonnet-4-5",
                "contact_mode": "inferred"
            },
            "epistemic_overrides": {
                "contact_strength": 0.9
            }
        })

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_missing_required_field(self):
        """Test that missing required fields are caught."""
        from schema_validator import validate_extraction

        # Missing candidate_type
        result = validate_extraction({
            "candidate_key": "test",
            "raw_evidence": "test"
        })
        assert result.is_valid is False
        assert any("candidate_type" in e for e in result.errors)

        # Missing candidate_key
        result = validate_extraction({
            "candidate_type": "component",
            "raw_evidence": "test"
        })
        assert result.is_valid is False
        assert any("candidate_key" in e for e in result.errors)

        # Missing raw_evidence
        result = validate_extraction({
            "candidate_type": "component",
            "candidate_key": "test"
        })
        assert result.is_valid is False
        assert any("raw_evidence" in e for e in result.errors)

    def test_invalid_candidate_type(self):
        """Test that invalid candidate_type is caught."""
        from schema_validator import validate_extraction

        result = validate_extraction({
            "candidate_type": "invalid_type",
            "candidate_key": "test",
            "raw_evidence": "test"
        })

        assert result.is_valid is False
        assert any("candidate_type" in e for e in result.errors)

    def test_invalid_ecosystem(self):
        """Test that invalid ecosystem is caught."""
        from schema_validator import validate_extraction

        result = validate_extraction({
            "candidate_type": "component",
            "candidate_key": "test",
            "raw_evidence": "test",
            "ecosystem": "invalid_ecosystem"
        })

        assert result.is_valid is False
        assert any("ecosystem" in e for e in result.errors)

    def test_confidence_score_out_of_range(self):
        """Test that confidence scores out of range are caught."""
        from schema_validator import validate_extraction

        # Score too high
        result = validate_extraction({
            "candidate_type": "component",
            "candidate_key": "test",
            "raw_evidence": "test",
            "confidence_score": 1.5
        })
        assert result.is_valid is False
        assert any("confidence_score" in e for e in result.errors)

        # Score too low
        result = validate_extraction({
            "candidate_type": "component",
            "candidate_key": "test",
            "raw_evidence": "test",
            "confidence_score": -0.5
        })
        assert result.is_valid is False
        assert any("confidence_score" in e for e in result.errors)

    def test_valid_confidence_scores(self):
        """Test that valid confidence scores pass."""
        from schema_validator import validate_extraction

        for score in [0.0, 0.5, 1.0]:
            result = validate_extraction({
                "candidate_type": "component",
                "candidate_key": "test",
                "raw_evidence": "test",
                "confidence_score": score
            })
            assert result.is_valid is True, f"Failed for score {score}"

    def test_invalid_epistemic_keys(self):
        """Test that invalid epistemic keys are caught."""
        from schema_validator import validate_extraction

        result = validate_extraction({
            "candidate_type": "component",
            "candidate_key": "test",
            "raw_evidence": "test",
            "epistemic_defaults": {
                "invalid_key": "should fail"
            }
        })

        assert result.is_valid is False
        assert any("epistemic_defaults" in e for e in result.errors)

    def test_all_valid_candidate_types(self):
        """Test that all valid candidate types are accepted."""
        from schema_validator import validate_extraction, VALID_CANDIDATE_TYPES

        for ct in VALID_CANDIDATE_TYPES:
            result = validate_extraction({
                "candidate_type": ct,
                "candidate_key": "test",
                "raw_evidence": "test"
            })
            assert result.is_valid is True, f"Failed for type {ct}"

    def test_all_valid_ecosystems(self):
        """Test that all valid ecosystems are accepted."""
        from schema_validator import validate_extraction, VALID_ECOSYSTEMS

        for eco in VALID_ECOSYSTEMS:
            result = validate_extraction({
                "candidate_type": "component",
                "candidate_key": "test",
                "raw_evidence": "test",
                "ecosystem": eco
            })
            assert result.is_valid is True, f"Failed for ecosystem {eco}"

    def test_validate_or_raise_valid(self):
        """Test validate_extraction_or_raise with valid data."""
        from schema_validator import validate_extraction_or_raise

        data = {
            "candidate_type": "component",
            "candidate_key": "test",
            "raw_evidence": "test"
        }

        result = validate_extraction_or_raise(data)
        assert result == data

    def test_validate_or_raise_invalid(self):
        """Test validate_extraction_or_raise with invalid data."""
        from schema_validator import validate_extraction_or_raise

        with pytest.raises(ValueError) as exc_info:
            validate_extraction_or_raise({
                "candidate_type": "invalid",
                "candidate_key": "test",
                "raw_evidence": "test"
            })

        assert "validation failed" in str(exc_info.value).lower()


class TestSchemaFile:
    """Tests for the JSON schema file itself."""

    def test_schema_file_exists(self):
        """Test that schema file exists."""
        schema_path = production_root / 'schemas' / 'extraction_schema.json'
        assert schema_path.exists(), f"Schema file not found: {schema_path}"

    def test_schema_is_valid_json(self):
        """Test that schema file is valid JSON."""
        import json

        schema_path = production_root / 'schemas' / 'extraction_schema.json'
        with open(schema_path, 'r') as f:
            schema = json.load(f)

        assert "$schema" in schema
        assert "definitions" in schema
        assert "properties" in schema

    def test_schema_has_required_definitions(self):
        """Test that schema has all required definitions."""
        import json

        schema_path = production_root / 'schemas' / 'extraction_schema.json'
        with open(schema_path, 'r') as f:
            schema = json.load(f)

        required_defs = [
            'candidateType',
            'ecosystemType',
            'observerType',
            'contactMode',
            'patternStorage',
            'confidenceScore',
            'epistemicFields'
        ]

        for def_name in required_defs:
            assert def_name in schema['definitions'], f"Missing definition: {def_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
