"""
Tests for PostgresCoreEntityRepository

Tests against real Neon database.
"""

import pytest
from uuid import UUID

from production.core.repositories.postgres_core_entity_repository import PostgresCoreEntityRepository
from production.core.domain.core_entity import CoreEntity


@pytest.fixture
def repo():
    """Create repository instance"""
    return PostgresCoreEntityRepository()


class TestGetById:
    """Test get_by_id queries"""

    def test_get_by_id_returns_entity(self, repo):
        """Should retrieve entity by UUID"""
        # Get any entity first
        entities = repo.find_verified(limit=1)
        if not entities:
            pytest.skip("No verified entities in database")

        entity_id = entities[0].id

        # Retrieve by ID
        entity = repo.get_by_id(entity_id)

        assert entity is not None
        assert isinstance(entity, CoreEntity)
        assert entity.id == entity_id
        assert entity.is_current is True

    def test_get_by_id_not_found(self, repo):
        """Should return None for non-existent UUID"""
        fake_id = UUID('00000000-0000-0000-0000-000000000000')
        entity = repo.get_by_id(fake_id)
        assert entity is None


class TestGetByCanonicalKey:
    """Test get_by_canonical_key queries"""

    def test_get_by_canonical_key_returns_entity(self, repo):
        """Should retrieve entity by canonical key"""
        # Get any entity first
        entities = repo.find_verified(limit=1)
        if not entities:
            pytest.skip("No verified entities in database")

        canonical_key = entities[0].canonical_key

        # Retrieve by key
        entity = repo.get_by_canonical_key(canonical_key)

        assert entity is not None
        assert isinstance(entity, CoreEntity)
        assert entity.canonical_key == canonical_key
        assert entity.is_current is True

    def test_get_by_canonical_key_not_found(self, repo):
        """Should return None for non-existent key"""
        entity = repo.get_by_canonical_key('NonExistentKey12345')
        assert entity is None


class TestFindByType:
    """Test find_by_type queries"""

    def test_find_by_type_returns_list(self, repo):
        """Should return list of entities for given type"""
        # Get type counts to find a type with entities
        counts = repo.count_by_type()
        if not counts:
            pytest.skip("No entities in database")

        entity_type = next(iter(counts.keys()))

        # Query by type
        entities = repo.find_by_type(entity_type, limit=10)

        assert isinstance(entities, list)
        assert len(entities) > 0
        assert all(e.entity_type == entity_type for e in entities)
        assert all(e.is_current is True for e in entities)

    def test_find_by_type_respects_limit(self, repo):
        """Should respect limit parameter"""
        counts = repo.count_by_type()
        if not counts:
            pytest.skip("No entities in database")

        entity_type = next(iter(counts.keys()))

        entities = repo.find_by_type(entity_type, limit=3)
        assert len(entities) <= 3

    def test_find_by_type_not_found(self, repo):
        """Should raise error for invalid enum type"""
        # PostgreSQL enum validation is strict - invalid values raise errors
        import psycopg.errors
        with pytest.raises(psycopg.errors.InvalidTextRepresentation):
            repo.find_by_type('NonExistentType12345', limit=10)


class TestFindByEcosystem:
    """Test find_by_ecosystem queries"""

    def test_find_by_ecosystem_returns_list(self, repo):
        """Should return list of entities for given ecosystem"""
        # Get any entity to find an ecosystem
        all_entities = repo.find_verified(limit=1)
        if not all_entities:
            pytest.skip("No entities in database")

        ecosystem = all_entities[0].ecosystem

        # Query by ecosystem
        entities = repo.find_by_ecosystem(ecosystem, limit=10)

        assert isinstance(entities, list)
        assert len(entities) > 0
        assert all(e.ecosystem == ecosystem for e in entities)
        assert all(e.is_current is True for e in entities)

    def test_find_by_ecosystem_not_found(self, repo):
        """Should raise error for invalid enum ecosystem"""
        # PostgreSQL enum validation is strict - invalid values raise errors
        import psycopg.errors
        with pytest.raises(psycopg.errors.InvalidTextRepresentation):
            repo.find_by_ecosystem('NonExistentEcosystem12345', limit=10)


class TestFindVerified:
    """Test find_verified queries"""

    def test_find_verified_returns_only_verified(self, repo):
        """Should return only verified entities"""
        entities = repo.find_verified(limit=10)

        assert isinstance(entities, list)
        # All returned entities must be verified
        for entity in entities:
            assert entity.is_current is True
            assert entity.verification_status in ['human_verified', 'auto_approved']

    def test_find_verified_respects_limit(self, repo):
        """Should respect limit parameter"""
        entities = repo.find_verified(limit=5)
        assert len(entities) <= 5


class TestFindByNamespace:
    """Test find_by_namespace queries"""

    def test_find_by_namespace_returns_list(self, repo):
        """Should return list of entities for given namespace"""
        # Find any entity with a namespace
        all_entities = repo.find_verified(limit=100)
        entities_with_namespace = [e for e in all_entities if e.namespace]

        if not entities_with_namespace:
            pytest.skip("No entities with namespace in database")

        namespace = entities_with_namespace[0].namespace

        # Query by namespace
        entities = repo.find_by_namespace(namespace, limit=10)

        assert isinstance(entities, list)
        assert len(entities) > 0
        assert all(e.namespace == namespace for e in entities)
        assert all(e.is_current is True for e in entities)

    def test_find_by_namespace_not_found(self, repo):
        """Should return empty list for non-existent namespace"""
        entities = repo.find_by_namespace('NonExistent.Namespace.12345', limit=10)
        assert entities == []


class TestCountByType:
    """Test count_by_type aggregation"""

    def test_count_by_type_returns_dict(self, repo):
        """Should return dict mapping entity_type -> count"""
        counts = repo.count_by_type()

        assert isinstance(counts, dict)
        assert all(isinstance(k, str) for k in counts.keys())
        assert all(isinstance(v, int) for v in counts.values())
        assert all(v > 0 for v in counts.values())

    def test_count_by_type_matches_find_by_type(self, repo):
        """Count should match actual query results"""
        counts = repo.count_by_type()
        if not counts:
            pytest.skip("No entities in database")

        # Pick a type and verify count
        entity_type = next(iter(counts.keys()))
        expected_count = counts[entity_type]

        # Get all entities of that type
        entities = repo.find_by_type(entity_type, limit=1000)

        # Count should match (if we got all of them)
        if len(entities) < 1000:
            assert len(entities) == expected_count


class TestCountByVerificationStatus:
    """Test count_by_verification_status aggregation"""

    def test_count_by_verification_status_returns_dict(self, repo):
        """Should return dict mapping verification_status -> count"""
        counts = repo.count_by_verification_status()

        assert isinstance(counts, dict)
        assert all(isinstance(k, str) for k in counts.keys())
        assert all(isinstance(v, int) for v in counts.values())
        assert all(v > 0 for v in counts.values())

    def test_count_includes_common_statuses(self, repo):
        """Should include expected verification statuses"""
        counts = repo.count_by_verification_status()
        if not counts:
            pytest.skip("No entities in database")

        # Should have at least one of the common statuses
        common_statuses = {'pending', 'human_verified', 'auto_approved'}
        found_statuses = set(counts.keys())

        assert len(found_statuses & common_statuses) > 0


class TestDomainMapping:
    """Test mapping from database to domain model"""

    def test_entity_has_all_required_fields(self, repo):
        """Mapped entity should have all required fields"""
        entities = repo.find_verified(limit=1)
        if not entities:
            pytest.skip("No verified entities in database")

        entity = entities[0]

        # Required fields
        assert entity.id is not None
        assert entity.entity_type is not None
        assert entity.canonical_key is not None
        assert entity.name is not None
        assert entity.ecosystem is not None
        assert entity.is_current is True

    def test_entity_handles_optional_fields(self, repo):
        """Mapped entity should handle NULL optional fields"""
        entities = repo.find_verified(limit=10)
        if not entities:
            pytest.skip("No entities in database")

        # Should not raise errors for optional fields
        for entity in entities:
            _ = entity.display_name  # May be None
            _ = entity.namespace  # May be None
            _ = entity.attributes  # May be empty dict
            _ = entity.verified_by  # May be None
            _ = entity.verified_at  # May be None

    def test_entity_has_domain_methods(self, repo):
        """Mapped entity should have domain logic methods"""
        entities = repo.find_verified(limit=1)
        if not entities:
            pytest.skip("No verified entities in database")

        entity = entities[0]

        # Domain methods from CoreEntity
        assert hasattr(entity, 'is_verified')
        assert hasattr(entity, 'is_exportable')
        assert hasattr(entity, 'to_identifier')

        # Should be verified since we queried verified entities
        assert entity.is_verified() is True
        assert entity.is_exportable() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
