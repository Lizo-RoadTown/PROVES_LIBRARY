"""
JSON Schema Validation for Extractions (Option A - Task 1.2)

This module provides schema validation for extraction data before storage.
It catches invalid data early, improving data quality.

Usage:
    from schema_validator import validate_extraction, ValidationResult

    # Validate extraction data
    result = validate_extraction({
        "candidate_type": "component",
        "candidate_key": "test_component",
        "raw_evidence": "Test evidence text"
    })

    if result.is_valid:
        # Proceed with storage
        pass
    else:
        # Handle validation errors
        for error in result.errors:
            print(f"Error: {error}")
"""
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

try:
    import jsonschema
    from jsonschema import Draft7Validator, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


@dataclass
class ValidationResult:
    """Result of schema validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    data: Optional[Dict[str, Any]] = None


# Load schema once at module level
_schema: Optional[Dict] = None


def _get_schema() -> Dict:
    """Load and cache the extraction schema."""
    global _schema

    if _schema is not None:
        return _schema

    schema_path = Path(__file__).parent.parent / 'schemas' / 'extraction_schema.json'

    if not schema_path.exists():
        raise FileNotFoundError(
            f"Schema file not found: {schema_path}. "
            "Make sure extraction_schema.json exists in production/schemas/"
        )

    with open(schema_path, 'r', encoding='utf-8') as f:
        _schema = json.load(f)

    return _schema


def validate_extraction(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate extraction data against the JSON schema.

    Args:
        data: Dictionary containing extraction data

    Returns:
        ValidationResult with is_valid, errors, and validated data

    Example:
        result = validate_extraction({
            "candidate_type": "component",
            "candidate_key": "ms5611_barometer",
            "raw_evidence": "The MS5611 is a barometric pressure sensor"
        })
    """
    if not JSONSCHEMA_AVAILABLE:
        # If jsonschema not installed, do basic validation
        return _basic_validation(data)

    schema = _get_schema()
    validator = Draft7Validator(schema)

    errors = []
    for error in validator.iter_errors(data):
        # Format error message
        path = '.'.join(str(p) for p in error.absolute_path) if error.absolute_path else 'root'
        errors.append(f"{path}: {error.message}")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        data=data if len(errors) == 0 else None
    )


def _basic_validation(data: Dict[str, Any]) -> ValidationResult:
    """
    Basic validation without jsonschema library.
    Checks required fields and enum values.
    """
    errors = []

    # Check required fields
    required = ['candidate_type', 'candidate_key', 'raw_evidence']
    for field in required:
        if field not in data or data[field] is None:
            errors.append(f"Missing required field: {field}")
        elif field == 'candidate_key' and len(str(data[field])) == 0:
            errors.append(f"Field '{field}' cannot be empty")

    # Check candidate_type enum (from database enum)
    valid_types = ['component', 'port', 'command', 'telemetry', 'event', 'parameter', 'data_type', 'dependency', 'connection', 'inheritance']
    if data.get('candidate_type') and data['candidate_type'] not in valid_types:
        errors.append(
            f"candidate_type: '{data['candidate_type']}' is not one of {valid_types}"
        )

    # Check ecosystem enum (from database enum)
    valid_ecosystems = ['fprime', 'proveskit', 'pysquared', 'cubesat_general', 'external']
    if data.get('ecosystem') and data['ecosystem'] not in valid_ecosystems:
        errors.append(
            f"ecosystem: '{data['ecosystem']}' is not one of {valid_ecosystems}"
        )

    # Check confidence scores
    for score_field in ['confidence_score', 'lineage_confidence', 'contact_strength']:
        if score_field in data and data[score_field] is not None:
            score = data[score_field]
            if not isinstance(score, (int, float)):
                errors.append(f"{score_field}: must be a number")
            elif not (0.0 <= score <= 1.0):
                errors.append(f"{score_field}: {score} is not in range [0.0, 1.0]")

    # Check epistemic fields if present
    valid_epistemic_keys = {
        'observer_id', 'observer_type', 'contact_mode', 'contact_strength',
        'signal_type', 'pattern_storage', 'representation_media',
        'dependencies', 'sequence_role', 'validity_conditions', 'assumptions',
        'scope', 'observed_at', 'valid_from', 'valid_to', 'refresh_trigger',
        'staleness_risk', 'author_id', 'intent', 'uncertainty_notes',
        'reenactment_required', 'practice_interval', 'skill_transferability'
    }

    for ep_field in ['epistemic_defaults', 'epistemic_overrides']:
        if ep_field in data and data[ep_field] is not None:
            if not isinstance(data[ep_field], dict):
                errors.append(f"{ep_field}: must be an object")
            else:
                invalid_keys = set(data[ep_field].keys()) - valid_epistemic_keys
                if invalid_keys:
                    errors.append(f"{ep_field}: invalid keys {sorted(invalid_keys)}")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        data=data if len(errors) == 0 else None
    )


def validate_extraction_or_raise(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate extraction data, raising an exception if invalid.

    Args:
        data: Dictionary containing extraction data

    Returns:
        The validated data if valid

    Raises:
        ValueError: If validation fails, with error details
    """
    result = validate_extraction(data)
    if not result.is_valid:
        error_msg = "Extraction validation failed:\n" + "\n".join(
            f"  - {e}" for e in result.errors
        )
        raise ValueError(error_msg)
    return result.data


# Convenience constants for valid enum values (from database enums)
VALID_CANDIDATE_TYPES = ['component', 'port', 'command', 'telemetry', 'event', 'parameter', 'data_type', 'dependency', 'connection', 'inheritance']
VALID_ECOSYSTEMS = ['fprime', 'proveskit', 'pysquared', 'cubesat_general', 'external']
VALID_OBSERVER_TYPES = ['human', 'sensor', 'algorithm', 'llm']
VALID_CONTACT_MODES = ['direct', 'inferred', 'cited', 'simulated']
VALID_PATTERN_STORAGE = ['url', 'file', 'memory', 'db']
VALID_SEQUENCE_ROLES = ['predecessor', 'successor', 'parallel']


__all__ = [
    'validate_extraction',
    'validate_extraction_or_raise',
    'ValidationResult',
    'VALID_CANDIDATE_TYPES',
    'VALID_ECOSYSTEMS',
    'VALID_OBSERVER_TYPES',
    'VALID_CONTACT_MODES',
    'VALID_PATTERN_STORAGE',
    'VALID_SEQUENCE_ROLES',
]
