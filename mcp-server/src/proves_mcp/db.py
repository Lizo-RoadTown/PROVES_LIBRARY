"""Database client for PROVES Library MCP Server."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, List, Dict, Any

import psycopg
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector_async

from proves_mcp.config import settings

logger = logging.getLogger(__name__)


class DatabaseClient:
    """Async PostgreSQL client for the PROVES Library knowledge graph."""

    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or settings.database_url
        self._pool = None

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[psycopg.AsyncConnection, None]:
        """Get a database connection."""
        async with await psycopg.AsyncConnection.connect(
            self.connection_string,
            row_factory=dict_row
        ) as conn:
            await register_vector_async(conn)
            yield conn

    async def search_extractions(
        self,
        query: str,
        candidate_type: Optional[str] = None,
        ecosystem: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search staging extractions using text matching.

        Args:
            query: Search query text
            candidate_type: Filter by type (component, interface, subsystem, etc.)
            ecosystem: Filter by ecosystem (fprime, proveskit, generic)
            status: Filter by status (pending, accepted, rejected, etc.)
            limit: Maximum results to return

        Returns:
            List of matching extractions with relevance scores
        """
        async with self.get_connection() as conn:
            sql = """
                SELECT
                    extraction_id,
                    candidate_key,
                    candidate_type,
                    candidate_payload,
                    confidence_score,
                    status,
                    ecosystem,
                    evidence,
                    created_at
                FROM staging_extractions
                WHERE (
                    candidate_key ILIKE $1
                    OR candidate_payload::text ILIKE $1
                    OR (evidence->>'source_text')::text ILIKE $1
                )
            """
            params = [f"%{query}%"]
            param_count = 2

            if candidate_type:
                sql += f" AND candidate_type = ${param_count}"
                params.append(candidate_type)
                param_count += 1

            if ecosystem:
                sql += f" AND ecosystem = ${param_count}"
                params.append(ecosystem)
                param_count += 1

            if status:
                sql += f" AND status = ${param_count}"
                params.append(status)
                param_count += 1

            sql += f" ORDER BY confidence_score DESC NULLS LAST, created_at DESC LIMIT ${param_count}"
            params.append(limit)

            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                results = await cur.fetchall()
                return [dict(row) for row in results]

    async def search_core_entities(
        self,
        query: str,
        entity_type: Optional[str] = None,
        ecosystem: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search verified core entities.

        Args:
            query: Search query text
            entity_type: Filter by type (component, interface, subsystem)
            ecosystem: Filter by ecosystem (fprime, proveskit, generic)
            limit: Maximum results to return

        Returns:
            List of matching entities
        """
        async with self.get_connection() as conn:
            sql = """
                SELECT
                    id,
                    entity_type,
                    canonical_key,
                    name,
                    display_name,
                    attributes,
                    ecosystem,
                    created_at
                FROM core_entities
                WHERE is_current = TRUE
                AND (
                    canonical_key ILIKE $1
                    OR name ILIKE $1
                    OR display_name ILIKE $1
                    OR attributes::text ILIKE $1
                )
            """
            params = [f"%{query}%"]
            param_count = 2

            if entity_type:
                sql += f" AND entity_type = ${param_count}"
                params.append(entity_type)
                param_count += 1

            if ecosystem:
                sql += f" AND ecosystem = ${param_count}"
                params.append(ecosystem)
                param_count += 1

            sql += f" ORDER BY name LIMIT ${param_count}"
            params.append(limit)

            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                results = await cur.fetchall()
                return [dict(row) for row in results]

    async def get_extraction(self, extraction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific extraction by ID.

        Args:
            extraction_id: UUID of the extraction

        Returns:
            Full extraction content or None if not found
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT
                        extraction_id, candidate_key, candidate_type,
                        candidate_payload, snapshot_id, pipeline_run_id,
                        confidence_score, status, evidence, ecosystem,
                        created_at, updated_at, reviewed_by, reviewed_at
                    FROM staging_extractions
                    WHERE extraction_id = $1
                    """,
                    [extraction_id]
                )
                result = await cur.fetchone()
                return dict(result) if result else None

    async def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a verified core entity by ID.

        Args:
            entity_id: UUID of the entity

        Returns:
            Full entity content or None if not found
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT
                        id, entity_type, canonical_key, name, display_name,
                        attributes, ecosystem, source_snapshot_id,
                        is_current, version, created_at, updated_at
                    FROM core_entities
                    WHERE id = $1
                    """,
                    [entity_id]
                )
                result = await cur.fetchone()
                return dict(result) if result else None

    async def list_entities(
        self,
        entity_type: Optional[str] = None,
        ecosystem: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List verified core entities.

        Args:
            entity_type: Filter by type (component, interface, subsystem)
            ecosystem: Filter by ecosystem (fprime, proveskit, generic)
            limit: Maximum results

        Returns:
            List of entities
        """
        async with self.get_connection() as conn:
            sql = """
                SELECT id, entity_type, canonical_key, name, display_name,
                       attributes, ecosystem
                FROM core_entities
                WHERE is_current = TRUE
            """
            params = []
            param_count = 1

            if entity_type:
                sql += f" AND entity_type = ${param_count}"
                params.append(entity_type)
                param_count += 1

            if ecosystem:
                sql += f" AND ecosystem = ${param_count}"
                params.append(ecosystem)
                param_count += 1

            sql += f" ORDER BY name LIMIT ${param_count}"
            params.append(limit)

            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                results = await cur.fetchall()
                return [dict(row) for row in results]

    async def get_extraction_stats(self) -> Dict[str, Any]:
        """Get statistics about extractions in the system."""
        async with self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT
                        status,
                        COUNT(*) as count
                    FROM staging_extractions
                    GROUP BY status
                """)
                status_counts = await cur.fetchall()

                await cur.execute("""
                    SELECT
                        candidate_type,
                        COUNT(*) as count
                    FROM staging_extractions
                    GROUP BY candidate_type
                """)
                type_counts = await cur.fetchall()

                await cur.execute("""
                    SELECT COUNT(*) as total FROM core_entities WHERE is_current = TRUE
                """)
                entity_count = await cur.fetchone()

                return {
                    "extraction_status": {row['status']: row['count'] for row in status_counts},
                    "extraction_types": {row['candidate_type']: row['count'] for row in type_counts},
                    "verified_entities": entity_count['total'] if entity_count else 0
                }


# Singleton instance
db = DatabaseClient()
