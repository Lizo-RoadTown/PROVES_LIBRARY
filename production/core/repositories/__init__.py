"""
Repository Interfaces

Read-only repository pattern for accessing verified knowledge from Neon.
"""

from .core_entity_repository import CoreEntityRepository
from .raw_snapshot_repository import RawSnapshotRepository

__all__ = [
    'CoreEntityRepository',
    'RawSnapshotRepository',
]
