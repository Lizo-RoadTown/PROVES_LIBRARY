"""
Pytest Configuration for Version 3 Tests

Provides fixtures and configuration for integration tests.
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

# Load environment
from dotenv import load_dotenv
load_dotenv(project_root / '.env')


@pytest.fixture(scope="session")
def db_connection():
    """Database connection fixture - session scoped for efficiency."""
    import psycopg

    db_url = os.environ.get('NEON_DATABASE_URL')
    if not db_url:
        pytest.skip("NEON_DATABASE_URL not set")

    conn = psycopg.connect(db_url)
    yield conn
    conn.close()


@pytest.fixture
def mock_snapshot_content():
    """Mock snapshot content for lineage testing."""
    return {
        "content": """
        # Test Component Documentation

        The MS5611 Barometer is a high-precision digital barometer
        that communicates via I2C protocol. It provides pressure and
        temperature readings for altitude calculation.

        ## Interface Specification

        - I2C Address: 0x77 (CSB high) or 0x76 (CSB low)
        - Clock Speed: Up to 3.4 MHz
        - Power Supply: 1.8V to 3.6V

        ## Data Flow

        The component outputs 24-bit pressure data and 24-bit temperature data.
        """,
        "format": "text"
    }


@pytest.fixture
def valid_extraction_data():
    """Valid extraction data for storage tests."""
    return {
        "candidate_type": "component",
        "candidate_key": "ms5611_barometer_test",
        "raw_evidence": "The MS5611 Barometer is a high-precision digital barometer",
        "description": "High-precision digital barometer for altitude calculation",
        "confidence_score": 0.85,
        "confidence_reason": "Clear documentation with explicit description",
        "ecosystem": "proveskit",
        "epistemic_defaults": {
            "observer_type": "llm",
            "observer_id": "pytest-test",
            "contact_mode": "inferred",
            "pattern_storage": "url"
        },
        "epistemic_overrides": {
            "contact_strength": 0.9
        },
        "lineage_verified": True,
        "lineage_confidence": 0.95
    }
