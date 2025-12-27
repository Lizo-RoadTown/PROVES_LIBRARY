#!/usr/bin/env python3
"""
Database connection manager for PROVES Library
Provides connection pooling and query utilities
"""
import os
from typing import Optional, Any, Dict, List
from contextlib import contextmanager
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor, execute_values
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseConnector:
    """Manages database connections and provides query utilities"""

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize database connector

        Args:
            db_url: Database URL (defaults to NEON_DATABASE_URL from .env)
        """
        self.db_url = db_url or os.getenv('NEON_DATABASE_URL')
        if not self.db_url:
            raise ValueError("Database URL not provided and NEON_DATABASE_URL not set")

        # Connection pool (min 1, max 10 connections)
        self.pool = SimpleConnectionPool(1, 10, self.db_url)

    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool (context manager)

        Usage:
            with db.get_connection() as conn:
                cur = conn.cursor()
                ...
        """
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)

    @contextmanager
    def get_cursor(self, dict_cursor: bool = True):
        """
        Get a cursor (context manager)

        Args:
            dict_cursor: If True, returns RealDictCursor (rows as dicts)

        Usage:
            with db.get_cursor() as cur:
                cur.execute("SELECT * FROM table")
                rows = cur.fetchall()
        """
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cur = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cur
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cur.close()

    def execute(self, query: str, params: Optional[tuple] = None) -> None:
        """
        Execute a query (INSERT, UPDATE, DELETE)

        Args:
            query: SQL query
            params: Query parameters
        """
        with self.get_cursor() as cur:
            cur.execute(query, params)

    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Row as dict or None
        """
        with self.get_cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()

    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Fetch all rows

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            List of rows as dicts
        """
        with self.get_cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def insert_many(self, table: str, columns: List[str], values: List[tuple]) -> None:
        """
        Bulk insert rows

        Args:
            table: Table name
            columns: Column names
            values: List of value tuples
        """
        with self.get_cursor(dict_cursor=False) as cur:
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES %s"
            execute_values(cur, query, values)

    def close(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()


# Singleton instance
_db_instance: Optional[DatabaseConnector] = None


def get_db() -> DatabaseConnector:
    """Get or create singleton database connector instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseConnector()
    return _db_instance


if __name__ == '__main__':
    # Test connection
    print("Testing database connection...")
    try:
        db = get_db()
        result = db.fetch_one("SELECT version() as version")
        print(f"[YES] Connected to PostgreSQL: {result['version']}")

        # Test statistics view
        stats = db.fetch_all("SELECT * FROM database_statistics ORDER BY table_name")
        print("\n📊 Database Statistics:")
        for row in stats:
            print(f"  {row['table_name']}: {row['row_count']} rows")

    except Exception as e:
        print(f"[NO] Connection failed: {e}")
