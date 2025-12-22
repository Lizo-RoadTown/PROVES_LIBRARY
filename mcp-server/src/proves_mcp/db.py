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
        self.connection_string = connection_string or settings.neon_database_url
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
    
    async def search_entries(
        self,
        query: str,
        domain: Optional[str] = None,
        entry_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search library entries using semantic similarity and keyword matching.
        
        Args:
            query: Search query text
            domain: Filter by domain (software, build, ops, etc.)
            entry_type: Filter by entry type (pattern, failure, component, etc.)
            tags: Filter by tags
            limit: Maximum results to return
            
        Returns:
            List of matching entries with relevance scores
        """
        async with self.get_connection() as conn:
            # Build query with optional filters
            sql = """
                SELECT 
                    id,
                    title,
                    domain,
                    entry_type,
                    summary,
                    tags,
                    quality_score,
                    1 - (embedding <=> $1::vector) as similarity
                FROM library_entries
                WHERE 1=1
            """
            params = []
            param_count = 1
            
            # TODO: Generate embedding for query
            # For now, use text search as fallback
            sql = """
                SELECT 
                    id,
                    title,
                    domain,
                    entry_type,
                    summary,
                    tags,
                    quality_score,
                    ts_rank(to_tsvector('english', content), plainto_tsquery('english', $1)) as similarity
                FROM library_entries
                WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $1)
            """
            params.append(query)
            param_count += 1
            
            if domain:
                sql += f" AND domain = ${param_count}"
                params.append(domain)
                param_count += 1
            
            if entry_type:
                sql += f" AND entry_type = ${param_count}"
                params.append(entry_type)
                param_count += 1
            
            if tags:
                sql += f" AND tags && ${param_count}"
                params.append(tags)
                param_count += 1
            
            sql += f" ORDER BY similarity DESC LIMIT ${param_count}"
            params.append(limit)
            
            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                results = await cur.fetchall()
                return [dict(row) for row in results]
    
    async def get_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific library entry by ID.
        
        Args:
            entry_id: UUID of the entry
            
        Returns:
            Full entry content or None if not found
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT 
                        id, title, domain, entry_type, content, summary,
                        tags, sources, quality_score, quality_tier,
                        created_at, updated_at
                    FROM library_entries
                    WHERE id = $1
                    """,
                    [entry_id]
                )
                result = await cur.fetchone()
                return dict(result) if result else None
    
    async def get_relationships(
        self,
        component: str,
        relationship_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get relationships for a component.
        
        Args:
            component: Component name or ID
            relationship_type: Filter by type (depends_on, conflicts_with, etc.)
            
        Returns:
            List of relationships
        """
        async with self.get_connection() as conn:
            sql = """
                SELECT 
                    r.id,
                    r.relationship_type,
                    r.confidence_score,
                    r.description,
                    source.title as source_title,
                    target.title as target_title
                FROM relationships r
                JOIN library_entries source ON r.source_entry_id = source.id
                JOIN library_entries target ON r.target_entry_id = target.id
                WHERE source.title ILIKE $1 OR target.title ILIKE $1
            """
            params = [f"%{component}%"]
            
            if relationship_type:
                sql += " AND r.relationship_type = $2"
                params.append(relationship_type)
            
            sql += " ORDER BY r.confidence_score DESC"
            
            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                results = await cur.fetchall()
                return [dict(row) for row in results]
    
    async def find_conflicts(self, component: str) -> List[Dict[str, Any]]:
        """
        Find known conflicts for a component.
        
        Args:
            component: Component name to check
            
        Returns:
            List of conflict entries
        """
        return await self.get_relationships(component, "conflicts_with")
    
    async def list_components(
        self,
        domain: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List components in the library.
        
        Args:
            domain: Filter by domain
            limit: Maximum results
            
        Returns:
            List of components
        """
        async with self.get_connection() as conn:
            sql = """
                SELECT id, title, domain, entry_type, summary, tags
                FROM library_entries
                WHERE entry_type = 'component'
            """
            params = []
            
            if domain:
                sql += " AND domain = $1"
                params.append(domain)
            
            sql += f" ORDER BY title LIMIT ${len(params) + 1}"
            params.append(limit)
            
            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                results = await cur.fetchall()
                return [dict(row) for row in results]


# Singleton instance
db = DatabaseClient()
