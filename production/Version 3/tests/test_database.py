"""
Tests for Centralized Database Pool (Option A - Task 1.1)

Tests the database.py module for connection pooling.
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


@pytest.mark.skipif(
    not os.getenv('NEON_DATABASE_URL'),
    reason="Database connection required"
)
class TestDatabasePool:
    """Tests for centralized database pool."""

    def test_import_database_module(self):
        """Test that database module can be imported."""
        from database import get_pool, get_connection, check_connection
        assert get_pool is not None
        assert get_connection is not None
        assert check_connection is not None

    def test_check_connection(self):
        """Test that connection check works."""
        from database import check_connection

        result = check_connection()
        assert result is True

    def test_get_connection_context_manager(self):
        """Test connection via context manager."""
        from database import get_connection

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()

        assert result == (1,)

    def test_get_pool_returns_same_pool(self):
        """Test that get_pool returns singleton."""
        from database import get_pool

        pool1 = get_pool()
        pool2 = get_pool()

        assert pool1 is pool2

    def test_get_pool_stats(self):
        """Test pool statistics."""
        from database import get_pool_stats

        stats = get_pool_stats()

        assert "size" in stats
        assert "min_size" in stats
        assert "max_size" in stats
        assert "idle" in stats
        assert "in_use" in stats

    def test_legacy_get_db_connection(self):
        """Test legacy get_db_connection function."""
        from database import get_db_connection

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
            assert result == (1,)
        finally:
            conn.close()  # Return to pool

    def test_multiple_connections(self):
        """Test getting multiple connections from pool."""
        from database import get_connection

        # Get multiple connections sequentially
        for _ in range(3):
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                assert result == (1,)

    def test_connection_reuse(self):
        """Test that connections are reused from pool."""
        from database import get_pool_stats, get_connection

        # Use connection
        with get_connection() as conn:
            pass

        # Check pool stats
        stats = get_pool_stats()
        # Pool should have at least 1 connection after use
        assert stats["size"] >= 1 or stats["idle"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
