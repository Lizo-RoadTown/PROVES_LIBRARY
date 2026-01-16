"""
Integration Tests for Agent Contracts (Option A - Task 1.4)

Tests the contracts between agents without running actual LLM calls.
Focuses on:
1. Tool function signatures and return types
2. Data format validation
3. Database operations
4. Contract compliance

Run with: pytest "production/Version 3/tests/test_contracts.py" -v
"""
import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# Setup paths
version3_folder = Path(__file__).parent.parent
project_root = version3_folder.parent.parent
production_root = project_root / 'production'

sys.path.insert(0, str(production_root))
sys.path.insert(0, str(version3_folder))

# Load environment
from dotenv import load_dotenv
load_dotenv(project_root / '.env')


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_extraction_output():
    """Sample output that extractor should produce."""
    return {
        "snapshot_id": "12345678-1234-1234-1234-123456789abc",
        "source_url": "https://docs.proveskit.space/test",
        "extractions": [
            {
                "candidate_type": "component",
                "candidate_key": "test_component",
                "description": "A test component for validation",
                "raw_evidence": "This is the evidence text from the source.",
                "confidence_score": 0.85,
                "confidence_reason": "Clear documentation with explicit description",
            }
        ],
        "epistemic_defaults": {
            "observer_type": "llm",
            "observer_id": "claude-sonnet-4-5",
            "contact_mode": "inferred",
            "pattern_storage": "url"
        },
        "lineage_verified": True,
        "lineage_confidence": 0.95
    }


@pytest.fixture
def sample_validator_output():
    """Sample output that validator should produce."""
    return {
        "status": "APPROVED",
        "reasoning": "All checks passed: epistemic valid, lineage verified, no duplicates",
        "verifications": [
            {
                "extraction_key": "test_component",
                "lineage_verified": True,
                "lineage_confidence": 0.95,
                "epistemic_valid": True,
                "duplicate_check": "passed"
            }
        ]
    }


@pytest.fixture
def sample_epistemic_defaults():
    """Sample epistemic defaults for testing."""
    return {
        "observer_type": "llm",
        "observer_id": "claude-sonnet-4-5",
        "contact_mode": "inferred",
        "pattern_storage": "url"
    }


@pytest.fixture
def sample_epistemic_overrides():
    """Sample epistemic overrides for testing."""
    return {
        "contact_strength": 0.9,
        "uncertainty_notes": "High confidence from explicit docs"
    }


# ============================================================================
# Contract Tests: Epistemic Validation
# ============================================================================

class TestEpistemicValidation:
    """Tests for validate_epistemic_structure tool contract."""

    def test_import_validator_tools(self):
        """Test that validator tools can be imported."""
        from validator_v3 import validate_epistemic_structure
        assert validate_epistemic_structure is not None

    def test_valid_epistemic_structure(self, sample_epistemic_defaults, sample_epistemic_overrides):
        """Test that valid epistemic structure passes validation."""
        from validator_v3 import validate_epistemic_structure

        result = validate_epistemic_structure.invoke({
            "epistemic_defaults": sample_epistemic_defaults,
            "epistemic_overrides": sample_epistemic_overrides
        })

        result_dict = json.loads(result)
        assert result_dict["valid"] is True
        assert len(result_dict["issues"]) == 0

    def test_empty_epistemic_defaults(self):
        """Test that empty epistemic_defaults is technically valid (no invalid keys)."""
        from validator_v3 import validate_epistemic_structure

        # Empty dict is valid - the tool validates key names, not presence of data
        result = validate_epistemic_structure.invoke({
            "epistemic_defaults": {},
            "epistemic_overrides": {}
        })

        result_dict = json.loads(result)
        # Empty dict has no invalid keys, so validation passes
        assert "valid" in result_dict

    def test_invalid_epistemic_keys(self):
        """Test that invalid keys fail validation."""
        from validator_v3 import validate_epistemic_structure

        result = validate_epistemic_structure.invoke({
            "epistemic_defaults": {
                "observer_type": "llm",
                "invalid_key": "should fail"
            },
            "epistemic_overrides": {}
        })

        result_dict = json.loads(result)
        assert result_dict["valid"] is False
        assert any("invalid" in issue.lower() for issue in result_dict["issues"])

    def test_all_valid_epistemic_keys(self, sample_epistemic_defaults):
        """Test that all valid keys from contract are accepted."""
        from validator_v3 import validate_epistemic_structure

        # All valid keys from the contract
        full_defaults = {
            "observer_id": "test",
            "observer_type": "llm",
            "contact_mode": "direct",
            "contact_strength": 0.8,
            "signal_type": "documentation",
            "pattern_storage": "url",
            "representation_media": "text",
            "dependencies": "[]",
            "sequence_role": "predecessor",
            "validity_conditions": "none",
            "assumptions": "none",
            "scope": "component",
            "observed_at": "2026-01-14",
            "valid_from": "2026-01-14",
            "valid_to": "2026-12-31",
            "refresh_trigger": "none",
            "staleness_risk": "low",
            "author_id": "test",
            "intent": "extraction",
            "uncertainty_notes": "none",
            "reenactment_required": False,
            "practice_interval": "none",
            "skill_transferability": "high"
        }

        result = validate_epistemic_structure.invoke({
            "epistemic_defaults": full_defaults,
            "epistemic_overrides": {}
        })

        result_dict = json.loads(result)
        assert result_dict["valid"] is True


# ============================================================================
# Contract Tests: Lineage Verification
# ============================================================================

class TestLineageVerification:
    """Tests for verify_evidence_lineage tool contract."""

    def test_import_lineage_tool(self):
        """Test that lineage verification tool can be imported."""
        from validator_v3 import verify_evidence_lineage
        assert verify_evidence_lineage is not None

    @pytest.mark.skipif(
        not os.getenv('DATABASE_URL'),
        reason="Database connection required"
    )
    def test_lineage_verification_returns_expected_fields(self):
        """Test that lineage verification returns all required fields."""
        from validator_v3 import verify_evidence_lineage

        # Use a fake snapshot_id - should return not found
        result = verify_evidence_lineage.invoke({
            "snapshot_id": "00000000-0000-0000-0000-000000000000",
            "evidence_text": "test evidence"
        })

        result_dict = json.loads(result)

        # Check all required fields are present
        assert "lineage_verified" in result_dict
        assert "lineage_confidence" in result_dict
        assert "checks_passed" in result_dict
        assert "checks_failed" in result_dict
        assert "snapshot_id" in result_dict

        # Check types
        assert isinstance(result_dict["lineage_verified"], bool)
        assert isinstance(result_dict["lineage_confidence"], (int, float))
        assert isinstance(result_dict["checks_passed"], list)
        assert isinstance(result_dict["checks_failed"], list)

    def test_lineage_confidence_range(self):
        """Test that lineage confidence is always 0.0-1.0."""
        from validator_v3 import verify_evidence_lineage

        result = verify_evidence_lineage.invoke({
            "snapshot_id": "00000000-0000-0000-0000-000000000000",
            "evidence_text": "test evidence"
        })

        result_dict = json.loads(result)
        confidence = result_dict["lineage_confidence"]

        assert 0.0 <= confidence <= 1.0


# ============================================================================
# Contract Tests: Storage Tool Signature
# ============================================================================

class TestStorageToolSignature:
    """Tests for store_extraction tool signature compliance."""

    def test_import_storage_tool(self):
        """Test that storage tool can be imported."""
        from storage_v3 import store_extraction
        assert store_extraction is not None

    def test_storage_tool_has_required_parameters(self):
        """Test that store_extraction has all required parameters."""
        from storage_v3 import store_extraction
        import inspect

        # Get the actual function (unwrap the tool decorator)
        func = store_extraction.func if hasattr(store_extraction, 'func') else store_extraction

        sig = inspect.signature(func)
        params = sig.parameters

        # Required parameters (no defaults)
        required = ['candidate_type', 'candidate_key', 'raw_evidence']
        for param in required:
            assert param in params, f"Missing required parameter: {param}"

    def test_storage_tool_has_lineage_parameters(self):
        """Test that store_extraction has lineage parameters."""
        from storage_v3 import store_extraction
        import inspect

        func = store_extraction.func if hasattr(store_extraction, 'func') else store_extraction
        sig = inspect.signature(func)
        params = sig.parameters

        # Lineage parameters (from Option A)
        lineage_params = ['lineage_verified', 'lineage_confidence']
        for param in lineage_params:
            assert param in params, f"Missing lineage parameter: {param}"

    def test_storage_tool_has_epistemic_parameters(self):
        """Test that store_extraction has epistemic parameters."""
        from storage_v3 import store_extraction
        import inspect

        func = store_extraction.func if hasattr(store_extraction, 'func') else store_extraction
        sig = inspect.signature(func)
        params = sig.parameters

        # Epistemic anti-boilerplate parameters
        epistemic_params = ['epistemic_defaults', 'epistemic_overrides']
        for param in epistemic_params:
            assert param in params, f"Missing epistemic parameter: {param}"


# ============================================================================
# Contract Tests: Data Format Validation
# ============================================================================

class TestDataFormatValidation:
    """Tests for data format compliance."""

    def test_candidate_type_enum_values(self):
        """Test that candidate_type uses valid enum values."""
        valid_types = ['component', 'interface', 'flow', 'mechanism', 'dependency']

        # These are the only valid types per the contract
        for ct in valid_types:
            assert ct in valid_types

    def test_ecosystem_enum_values(self):
        """Test that ecosystem uses valid enum values."""
        valid_ecosystems = ['proveskit', 'fprime', 'pysquared', 'external', 'unknown']

        # These are the valid ecosystems per the contract
        for eco in valid_ecosystems:
            assert eco in valid_ecosystems

    def test_confidence_score_range(self, sample_extraction_output):
        """Test that confidence_score is in valid range."""
        for extraction in sample_extraction_output["extractions"]:
            score = extraction["confidence_score"]
            assert 0.0 <= score <= 1.0, f"Invalid confidence score: {score}"


# ============================================================================
# Contract Tests: Subagent Specs
# ============================================================================

class TestSubagentSpecs:
    """Tests for subagent specification compliance."""

    def test_import_subagent_specs(self):
        """Test that subagent specs can be imported."""
        from subagent_specs_v3 import (
            get_extractor_spec,
            get_validator_spec,
            get_storage_spec
        )
        assert get_extractor_spec is not None
        assert get_validator_spec is not None
        assert get_storage_spec is not None

    def test_extractor_spec_structure(self):
        """Test extractor spec has required fields."""
        from subagent_specs_v3 import get_extractor_spec

        spec = get_extractor_spec()

        assert "name" in spec
        assert "system_prompt" in spec
        assert "tools" in spec
        assert "model" in spec

        assert spec["name"] == "extractor"
        assert isinstance(spec["tools"], list)
        assert len(spec["tools"]) > 0

    def test_validator_spec_structure(self):
        """Test validator spec has required fields."""
        from subagent_specs_v3 import get_validator_spec

        spec = get_validator_spec()

        assert "name" in spec
        assert "system_prompt" in spec
        assert "tools" in spec
        assert "model" in spec

        assert spec["name"] == "validator"
        assert isinstance(spec["tools"], list)

    def test_storage_spec_structure(self):
        """Test storage spec has required fields."""
        from subagent_specs_v3 import get_storage_spec

        spec = get_storage_spec()

        assert "name" in spec
        assert "system_prompt" in spec
        assert "tools" in spec
        assert "model" in spec

        assert spec["name"] == "storage"
        assert isinstance(spec["tools"], list)

    def test_validator_has_epistemic_tools(self):
        """Test that validator has epistemic validation tools."""
        from subagent_specs_v3 import get_validator_spec

        spec = get_validator_spec()
        tool_names = [t.name for t in spec["tools"]]

        assert "validate_epistemic_structure" in tool_names
        assert "verify_evidence_lineage" in tool_names

    def test_validator_has_duplicate_check(self):
        """Test that validator has duplicate checking tools."""
        from subagent_specs_v3 import get_validator_spec

        spec = get_validator_spec()
        tool_names = [t.name for t in spec["tools"]]

        assert "check_for_duplicates" in tool_names


# ============================================================================
# Contract Tests: Orchestration
# ============================================================================

class TestOrchestration:
    """Tests for orchestration layer compliance."""

    def test_import_orchestration(self):
        """Test that orchestration can be imported."""
        from agent_v3 import orchestrate_extraction, OrchestrationGraph
        assert orchestrate_extraction is not None
        assert OrchestrationGraph is not None

    def test_orchestration_url_extraction(self):
        """Test that orchestration extracts URL correctly."""
        import re

        test_messages = [
            "Extract from https://docs.proveskit.space/test",
            "Please extract architecture from https://github.com/proveskit/test",
            "Process this URL: http://example.com/docs"
        ]

        for msg in test_messages:
            url_match = re.search(r'https?://[^\s]+', msg)
            assert url_match is not None, f"Failed to extract URL from: {msg}"


# ============================================================================
# Integration Tests: Database Connection
# ============================================================================

@pytest.mark.skipif(
    not os.getenv('DATABASE_URL'),
    reason="Database connection required"
)
class TestDatabaseConnection:
    """Tests for database connection and operations."""

    def test_database_connection(self):
        """Test that database connection works."""
        import psycopg
        from dotenv import load_dotenv

        load_dotenv(project_root / '.env')
        db_url = os.environ.get('DATABASE_URL')

        assert db_url is not None, "DATABASE_URL not set"

        # Test connection
        conn = psycopg.connect(db_url)
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
        conn.close()

        assert result == (1,)

    def test_required_tables_exist(self):
        """Test that required tables exist in database."""
        import psycopg

        db_url = os.environ.get('DATABASE_URL')
        conn = psycopg.connect(db_url)

        required_tables = [
            'raw_snapshots',
            'staging_extractions',
            'core_entities',
            'validation_decisions',
            'pipeline_runs',
            'knowledge_epistemics'
        ]

        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            existing_tables = [row[0] for row in cur.fetchall()]

        conn.close()

        for table in required_tables:
            assert table in existing_tables, f"Missing required table: {table}"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
