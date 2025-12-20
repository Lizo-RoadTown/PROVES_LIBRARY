#!/usr/bin/env python3
"""
Knowledge Graph Manager for PROVES Library
CRUD operations for nodes and relationships (ERV)
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
import json
from db_connector import get_db


class GraphManager:
    """Manages knowledge graph nodes and relationships"""

    def __init__(self):
        self.db = get_db()

    # ============================================
    # NODES
    # ============================================

    def create_node(
        self,
        name: str,
        node_type: str,
        description: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> UUID:
        """
        Create a knowledge graph node

        Args:
            name: Node name
            node_type: Type (component, hardware, pattern, risk, resource)
            description: Optional description
            properties: Optional JSON properties
            embedding: Optional vector embedding

        Returns:
            Node UUID
        """
        query = """
            INSERT INTO kg_nodes (name, node_type, description, properties, embedding)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self.db.fetch_one(
            query,
            (name, node_type, description, json.dumps(properties or {}), embedding)
        )
        return result['id']

    def get_node(self, node_id: UUID) -> Optional[Dict[str, Any]]:
        """Get node by ID"""
        query = "SELECT * FROM kg_nodes WHERE id = %s"
        return self.db.fetch_one(query, (str(node_id),))

    def get_node_by_name(self, name: str, node_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get node by name and optional type"""
        if node_type:
            query = "SELECT * FROM kg_nodes WHERE name = %s AND node_type = %s"
            return self.db.fetch_one(query, (name, node_type))
        else:
            query = "SELECT * FROM kg_nodes WHERE name = %s"
            return self.db.fetch_one(query, (name,))

    def search_nodes(
        self,
        node_type: Optional[str] = None,
        name_pattern: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search nodes with filters

        Args:
            node_type: Filter by type
            name_pattern: Filter by name (case-insensitive LIKE)
            limit: Max results

        Returns:
            List of nodes
        """
        conditions = []
        params = []

        if node_type:
            conditions.append("node_type = %s")
            params.append(node_type)

        if name_pattern:
            conditions.append("name ILIKE %s")
            params.append(f"%{name_pattern}%")

        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        query = f"""
            SELECT * FROM kg_nodes
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT %s
        """
        params.append(limit)

        return self.db.fetch_all(query, tuple(params))

    def update_node(self, node_id: UUID, updates: Dict[str, Any]) -> bool:
        """
        Update node fields

        Args:
            node_id: Node UUID
            updates: Dict of field -> value

        Returns:
            True if updated
        """
        allowed_fields = {'name', 'description', 'properties', 'embedding'}
        updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not updates:
            return False

        # Convert properties to JSON if present
        if 'properties' in updates:
            updates['properties'] = json.dumps(updates['properties'])

        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        query = f"UPDATE kg_nodes SET {set_clause} WHERE id = %s"

        self.db.execute(query, (*updates.values(), str(node_id)))
        return True

    def delete_node(self, node_id: UUID) -> bool:
        """Delete node (cascades to relationships)"""
        query = "DELETE FROM kg_nodes WHERE id = %s"
        self.db.execute(query, (str(node_id),))
        return True

    # ============================================
    # RELATIONSHIPS (ERV)
    # ============================================

    def create_relationship(
        self,
        source_node_id: UUID,
        target_node_id: UUID,
        relationship_type: str,
        strength: Optional[float] = None,
        description: Optional[str] = None,
        cascade_domain: Optional[str] = None,
        is_critical: bool = False,
        evidence_entry_id: Optional[UUID] = None
    ) -> UUID:
        """
        Create a relationship between nodes

        Args:
            source_node_id: Source node UUID
            target_node_id: Target node UUID
            relationship_type: ERV type (depends_on, conflicts_with, enables, requires, mitigates, causes)
            strength: Confidence/importance (0.0-1.0)
            description: Optional description
            cascade_domain: Optional domain (power, data, thermal, timing)
            is_critical: Whether this is a critical cascade path
            evidence_entry_id: Library entry documenting this relationship

        Returns:
            Relationship UUID
        """
        query = """
            INSERT INTO kg_relationships (
                source_node_id, target_node_id, relationship_type,
                strength, description, cascade_domain, is_critical, evidence_entry_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self.db.fetch_one(
            query,
            (
                str(source_node_id), str(target_node_id), relationship_type,
                strength, description, cascade_domain, is_critical,
                str(evidence_entry_id) if evidence_entry_id else None
            )
        )
        return result['id']

    def get_relationship(self, rel_id: UUID) -> Optional[Dict[str, Any]]:
        """Get relationship by ID"""
        query = "SELECT * FROM kg_relationships WHERE id = %s"
        return self.db.fetch_one(query, (str(rel_id),))

    def get_node_relationships(
        self,
        node_id: UUID,
        direction: str = 'both',
        relationship_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all relationships for a node

        Args:
            node_id: Node UUID
            direction: 'outgoing', 'incoming', or 'both'
            relationship_type: Optional filter by type

        Returns:
            List of relationships
        """
        conditions = []
        params = [str(node_id)]

        if direction == 'outgoing':
            conditions.append("source_node_id = %s")
        elif direction == 'incoming':
            conditions.append("target_node_id = %s")
        else:  # both
            conditions.append("(source_node_id = %s OR target_node_id = %s)")
            params.append(str(node_id))

        if relationship_type:
            conditions.append("relationship_type = %s")
            params.append(relationship_type)

        where_clause = " AND ".join(conditions)
        query = f"""
            SELECT r.*,
                   sn.name as source_name,
                   tn.name as target_name
            FROM kg_relationships r
            JOIN kg_nodes sn ON r.source_node_id = sn.id
            JOIN kg_nodes tn ON r.target_node_id = tn.id
            WHERE {where_clause}
            ORDER BY r.created_at DESC
        """

        return self.db.fetch_all(query, tuple(params))

    def find_cascade_path(
        self,
        start_node_id: UUID,
        cascade_domain: str,
        max_depth: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find cascade paths from a starting node

        Args:
            start_node_id: Starting node UUID
            cascade_domain: Domain to trace (power, data, thermal, timing)
            max_depth: Maximum path depth

        Returns:
            List of paths (each path is a list of relationships)
        """
        # Recursive CTE to find paths
        query = """
            WITH RECURSIVE cascade_paths AS (
                -- Base case: direct relationships
                SELECT
                    r.id,
                    r.source_node_id,
                    r.target_node_id,
                    r.relationship_type,
                    r.cascade_domain,
                    r.is_critical,
                    sn.name as source_name,
                    tn.name as target_name,
                    1 as depth,
                    ARRAY[r.id] as path
                FROM kg_relationships r
                JOIN kg_nodes sn ON r.source_node_id = sn.id
                JOIN kg_nodes tn ON r.target_node_id = tn.id
                WHERE r.source_node_id = %s
                  AND r.cascade_domain = %s

                UNION

                -- Recursive case: follow the chain
                SELECT
                    r.id,
                    r.source_node_id,
                    r.target_node_id,
                    r.relationship_type,
                    r.cascade_domain,
                    r.is_critical,
                    sn.name as source_name,
                    tn.name as target_name,
                    cp.depth + 1,
                    cp.path || r.id
                FROM kg_relationships r
                JOIN kg_nodes sn ON r.source_node_id = sn.id
                JOIN kg_nodes tn ON r.target_node_id = tn.id
                JOIN cascade_paths cp ON r.source_node_id = cp.target_node_id
                WHERE r.cascade_domain = %s
                  AND cp.depth < %s
                  AND NOT r.id = ANY(cp.path)  -- Prevent cycles
            )
            SELECT * FROM cascade_paths
            ORDER BY depth, is_critical DESC
        """

        return self.db.fetch_all(query, (str(start_node_id), cascade_domain, cascade_domain, max_depth))

    # ============================================
    # UTILITY FUNCTIONS
    # ============================================

    def get_statistics(self) -> Dict[str, int]:
        """Get graph statistics"""
        stats = {}

        # Node counts by type
        node_stats = self.db.fetch_all("""
            SELECT node_type, COUNT(*) as count
            FROM kg_nodes
            GROUP BY node_type
            ORDER BY count DESC
        """)
        stats['nodes_by_type'] = {row['node_type']: row['count'] for row in node_stats}

        # Relationship counts by type
        rel_stats = self.db.fetch_all("""
            SELECT relationship_type, COUNT(*) as count
            FROM kg_relationships
            GROUP BY relationship_type
            ORDER BY count DESC
        """)
        stats['relationships_by_type'] = {row['relationship_type']: row['count'] for row in rel_stats}

        # Total counts
        totals = self.db.fetch_one("""
            SELECT
                (SELECT COUNT(*) FROM kg_nodes) as total_nodes,
                (SELECT COUNT(*) FROM kg_relationships) as total_relationships
        """)
        stats.update(totals)

        return stats


if __name__ == '__main__':
    # Test graph manager
    print("Testing Graph Manager...")

    gm = GraphManager()

    # Get statistics
    stats = gm.get_statistics()
    print(f"\n📊 Graph Statistics:")
    print(f"  Total nodes: {stats['total_nodes']}")
    print(f"  Total relationships: {stats['total_relationships']}")

    if stats['nodes_by_type']:
        print(f"\n  Nodes by type:")
        for node_type, count in stats['nodes_by_type'].items():
            print(f"    {node_type}: {count}")

    if stats['relationships_by_type']:
        print(f"\n  Relationships by type:")
        for rel_type, count in stats['relationships_by_type'].items():
            print(f"    {rel_type}: {count}")

    # Search for example nodes
    print(f"\n🔍 Searching for hardware nodes...")
    hardware = gm.search_nodes(node_type='hardware', limit=5)
    for node in hardware:
        print(f"  - {node['name']}: {node['description']}")
