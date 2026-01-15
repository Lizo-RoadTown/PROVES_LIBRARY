"""
Tests for PostgresRawSnapshotRepository

Tests against real Neon database.
"""

import pytest
from uuid import UUID

from production.core.repositories.postgres_raw_snapshot_repository import PostgresRawSnapshotRepository
from production.core.domain.raw_snapshot import RawSnapshot


@pytest.fixture
def repo():
    """Create repository instance"""
    return PostgresRawSnapshotRepository()


class TestGetById:
    """Test get_by_id queries"""

    def test_get_by_id_returns_snapshot(self, repo):
        """Should retrieve snapshot by UUID"""
        # Get any snapshot first using find_by_source_url on a known URL
        snapshots = repo.find_by_source_url('https://proveskit.github.io/pysquared/frozen-modules/', limit=1)
        if not snapshots:
            # Try getting from any source
            pytest.skip("No snapshots in database")

        snapshot_id = snapshots[0].id

        # Retrieve by ID
        snapshot = repo.get_by_id(snapshot_id)

        assert snapshot is not None
        assert isinstance(snapshot, RawSnapshot)
        assert snapshot.id == snapshot_id
        assert snapshot.source_url is not None
        assert snapshot.checksum is not None
        assert snapshot.fetched_at is not None

    def test_get_by_id_not_found(self, repo):
        """Should return None for non-existent UUID"""
        fake_id = UUID('00000000-0000-0000-0000-000000000000')
        snapshot = repo.get_by_id(fake_id)
        assert snapshot is None


class TestFindBySourceUrl:
    """Test find_by_source_url queries"""

    def test_find_by_source_url_returns_list(self, repo):
        """Should return list of snapshots for given URL"""
        # Use a URL that likely has snapshots
        test_url = 'https://proveskit.github.io/pysquared/frozen-modules/'

        snapshots = repo.find_by_source_url(test_url, limit=10)

        # If no snapshots found for test URL, skip
        if not snapshots:
            pytest.skip(f"No snapshots found for {test_url}")

        assert isinstance(snapshots, list)
        assert len(snapshots) > 0
        assert all(s.source_url == test_url for s in snapshots)
        assert all(isinstance(s, RawSnapshot) for s in snapshots)

    def test_find_by_source_url_respects_limit(self, repo):
        """Should respect limit parameter"""
        test_url = 'https://proveskit.github.io/pysquared/frozen-modules/'

        snapshots = repo.find_by_source_url(test_url, limit=3)
        assert len(snapshots) <= 3

    def test_find_by_source_url_not_found(self, repo):
        """Should return empty list for non-existent URL"""
        snapshots = repo.find_by_source_url('https://example.com/nonexistent/12345', limit=10)
        assert snapshots == []

    def test_find_by_source_url_ordered_by_time(self, repo):
        """Should return snapshots ordered by captured_at DESC"""
        test_url = 'https://proveskit.github.io/pysquared/frozen-modules/'

        snapshots = repo.find_by_source_url(test_url, limit=10)

        if len(snapshots) < 2:
            pytest.skip("Need at least 2 snapshots to test ordering")

        # Check descending order (most recent first)
        for i in range(len(snapshots) - 1):
            assert snapshots[i].fetched_at >= snapshots[i + 1].fetched_at


class TestGetLatestForUrl:
    """Test get_latest_for_url queries"""

    def test_get_latest_for_url_returns_most_recent(self, repo):
        """Should return most recent snapshot for URL"""
        test_url = 'https://proveskit.github.io/pysquared/frozen-modules/'

        snapshot = repo.get_latest_for_url(test_url)

        if not snapshot:
            pytest.skip(f"No snapshots found for {test_url}")

        assert isinstance(snapshot, RawSnapshot)
        assert snapshot.source_url == test_url

        # Verify it's actually the latest by comparing with all snapshots
        all_snapshots = repo.find_by_source_url(test_url, limit=100)
        if all_snapshots:
            latest_time = max(s.fetched_at for s in all_snapshots)
            assert snapshot.fetched_at == latest_time

    def test_get_latest_for_url_not_found(self, repo):
        """Should return None for non-existent URL"""
        snapshot = repo.get_latest_for_url('https://example.com/nonexistent/12345')
        assert snapshot is None


class TestDomainMapping:
    """Test mapping from database to domain model"""

    def test_snapshot_has_all_required_fields(self, repo):
        """Mapped snapshot should have all required fields"""
        # Try to get any snapshot
        test_url = 'https://proveskit.github.io/pysquared/frozen-modules/'
        snapshot = repo.get_latest_for_url(test_url)

        if not snapshot:
            pytest.skip("No snapshots in database")

        # Required fields
        assert snapshot.id is not None
        assert snapshot.source_url is not None
        assert snapshot.checksum is not None
        assert snapshot.fetched_at is not None

    def test_snapshot_handles_optional_payload(self, repo):
        """Mapped snapshot should handle NULL or empty payload"""
        test_url = 'https://proveskit.github.io/pysquared/frozen-modules/'
        snapshot = repo.get_latest_for_url(test_url)

        if not snapshot:
            pytest.skip("No snapshots in database")

        # raw_payload may be empty dict if NULL
        assert snapshot.raw_payload is not None
        assert isinstance(snapshot.raw_payload, dict)

    def test_snapshot_checksum_mapped_correctly(self, repo):
        """Should map content_hash column to checksum field"""
        test_url = 'https://proveskit.github.io/pysquared/frozen-modules/'
        snapshot = repo.get_latest_for_url(test_url)

        if not snapshot:
            pytest.skip("No snapshots in database")

        # Checksum should be a non-empty string (SHA256 hash or 'unknown')
        assert snapshot.checksum is not None
        assert isinstance(snapshot.checksum, str)
        assert len(snapshot.checksum) > 0

    def test_snapshot_fetched_at_mapped_correctly(self, repo):
        """Should map captured_at column to fetched_at field"""
        test_url = 'https://proveskit.github.io/pysquared/frozen-modules/'
        snapshot = repo.get_latest_for_url(test_url)

        if not snapshot:
            pytest.skip("No snapshots in database")

        # fetched_at should be a datetime
        assert snapshot.fetched_at is not None
        from datetime import datetime
        assert isinstance(snapshot.fetched_at, datetime)


class TestProvenanceUseCase:
    """Test typical provenance lookup use cases"""

    def test_can_trace_extraction_to_snapshot(self, repo):
        """Should be able to look up snapshot from extraction reference"""
        # This simulates the use case where we have a snapshot_id from an extraction
        # and want to retrieve the original source
        test_url = 'https://proveskit.github.io/pysquared/frozen-modules/'
        latest = repo.get_latest_for_url(test_url)

        if not latest:
            pytest.skip("No snapshots in database")

        # Use the ID to look up the snapshot (as would happen in provenance queries)
        snapshot = repo.get_by_id(latest.id)

        assert snapshot is not None
        assert snapshot.id == latest.id
        assert snapshot.source_url == test_url

    def test_can_find_historical_snapshots(self, repo):
        """Should be able to retrieve snapshot history for a URL"""
        test_url = 'https://proveskit.github.io/pysquared/frozen-modules/'

        snapshots = repo.find_by_source_url(test_url, limit=100)

        if not snapshots:
            pytest.skip(f"No snapshots found for {test_url}")

        # Should have snapshots ordered by time
        assert len(snapshots) > 0
        assert all(isinstance(s, RawSnapshot) for s in snapshots)

        # All should be from the same URL
        assert all(s.source_url == test_url for s in snapshots)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
