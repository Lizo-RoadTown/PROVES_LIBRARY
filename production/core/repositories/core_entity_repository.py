"""
CoreEntity Repository Interface

Abstract interface for querying verified entities from storage.
Read-only by design - no write/update operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from production.core.domain.core_entity import CoreEntity


class CoreEntityRepository(ABC):
    """
    Abstract repository for querying verified CoreEntity instances.

    Design principles:
    - Read-only: No write/update methods (extraction owns write path)
    - Verified only: Only queries entities with is_current=TRUE
    - Type-safe: Returns domain models, not raw database rows
    """

    @abstractmethod
    def get_by_id(self, entity_id: UUID) -> Optional[CoreEntity]:
        """
        Retrieve a single entity by its UUID.

        Args:
            entity_id: UUID of the entity

        Returns:
            CoreEntity if found, None otherwise
        """
        pass

    @abstractmethod
    def get_by_canonical_key(self, canonical_key: str) -> Optional[CoreEntity]:
        """
        Retrieve entity by its canonical key.

        Args:
            canonical_key: Unique canonical key (e.g. 'TestDriver')

        Returns:
            CoreEntity if found, None otherwise

        Note:
            Only returns current version (is_current=TRUE)
        """
        pass

    @abstractmethod
    def find_by_type(self, entity_type: str, limit: int = 100) -> List[CoreEntity]:
        """
        Find entities by type.

        Args:
            entity_type: Entity type (e.g. 'component', 'port', 'telemetry')
            limit: Maximum number of results

        Returns:
            List of CoreEntity instances (may be empty)
        """
        pass

    @abstractmethod
    def find_by_ecosystem(self, ecosystem: str, limit: int = 100) -> List[CoreEntity]:
        """
        Find entities by ecosystem.

        Args:
            ecosystem: Ecosystem name (e.g. 'fprime', 'ros2')
            limit: Maximum number of results

        Returns:
            List of CoreEntity instances (may be empty)
        """
        pass

    @abstractmethod
    def find_verified(self, limit: int = 100) -> List[CoreEntity]:
        """
        Find all verified entities ready for export.

        Args:
            limit: Maximum number of results

        Returns:
            List of verified CoreEntity instances

        Note:
            Only includes entities with verification_status in
            ['human_verified', 'auto_approved']
        """
        pass

    @abstractmethod
    def find_by_namespace(self, namespace: str, limit: int = 100) -> List[CoreEntity]:
        """
        Find entities by namespace.

        Args:
            namespace: Namespace string (e.g. 'Svc.ActiveLogger')
            limit: Maximum number of results

        Returns:
            List of CoreEntity instances (may be empty)
        """
        pass

    @abstractmethod
    def count_by_type(self) -> dict:
        """
        Count entities grouped by type.

        Returns:
            Dict mapping entity_type -> count
            Example: {'component': 45, 'port': 123, 'telemetry': 67}
        """
        pass

    @abstractmethod
    def count_by_verification_status(self) -> dict:
        """
        Count entities grouped by verification status.

        Returns:
            Dict mapping verification_status -> count
            Example: {'human_verified': 120, 'pending': 34}
        """
        pass
