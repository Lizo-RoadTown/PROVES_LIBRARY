"""
Base exporter for PROVES knowledge graph exports.

Defines common interface and result format for all exporters.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path

from production.core.domain.core_entity import CoreEntity


@dataclass
class ExportResult:
    """
    Result of an export operation.

    Attributes:
        success: Whether export succeeded
        format: Export format name
        output_path: Path to exported file (if file-based)
        data: In-memory export data (if memory-based)
        entity_count: Number of entities exported
        metadata: Additional export metadata
        errors: Any errors encountered
    """
    success: bool
    format: str
    output_path: Optional[Path] = None
    data: Optional[Any] = None
    entity_count: int = 0
    metadata: Dict[str, Any] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.errors is None:
            self.errors = []


class BaseExporter(ABC):
    """
    Abstract base class for all PROVES exporters.

    Exporters convert domain models to external formats for integration
    with machine learning frameworks, mission control systems, and
    visualization tools.

    Key principles:
    1. Read-only: Exporters never modify the database
    2. Format-agnostic domain: Domain models don't know about export formats
    3. FRAMES preservation: Epistemic metadata preserved where possible
    4. URI-based identity: Use stable PROVES URIs for entity references
    """

    @abstractmethod
    def export(
        self,
        entities: List[CoreEntity],
        output_path: Optional[Path] = None,
        **kwargs
    ) -> ExportResult:
        """
        Export entities to target format.

        Args:
            entities: List of CoreEntity instances to export
            output_path: Optional file path for file-based exports
            **kwargs: Format-specific export options

        Returns:
            ExportResult with success status and output location/data

        Raises:
            ValueError: If entities list is empty or invalid
            IOError: If file write fails (for file-based exports)
        """
        pass

    def validate_entities(self, entities: List[CoreEntity]) -> List[str]:
        """
        Validate entities are exportable.

        Args:
            entities: List of entities to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not entities:
            errors.append("Entity list is empty")
            return errors

        for i, entity in enumerate(entities):
            if not isinstance(entity, CoreEntity):
                errors.append(f"Entity {i} is not a CoreEntity instance")
            elif not entity.is_exportable():
                errors.append(
                    f"Entity {i} ({entity.canonical_key}) is not exportable: "
                    f"status={entity.verification_status}, is_current={entity.is_current}"
                )

        return errors

    def filter_exportable(self, entities: List[CoreEntity]) -> List[CoreEntity]:
        """
        Filter entities to only exportable ones.

        Args:
            entities: List of all entities

        Returns:
            List containing only exportable entities
        """
        return [e for e in entities if e.is_exportable()]

    def get_entity_uri(self, entity: CoreEntity) -> str:
        """
        Get stable URI for entity.

        Args:
            entity: CoreEntity instance

        Returns:
            PROVES URI (e.g., 'http://proves.space/fprime/component/testdriver')
        """
        return entity.to_identifier().uri

    def get_entity_urn(self, entity: CoreEntity) -> str:
        """
        Get URN for entity.

        Args:
            entity: CoreEntity instance

        Returns:
            PROVES URN (e.g., 'urn:proves:fprime:component:testdriver')
        """
        return entity.to_identifier().urn
