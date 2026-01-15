"""
Centralized Database Connection Pool (Option A - Task 1.1)

This module provides a single connection pool for all v3 agents.
Instead of each tool creating its own connection, all tools share
this pool, reducing connection overhead and improving reliability.

Usage:
    from database import get_connection, get_pool

    # Option 1: Use context manager (recommended)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()

    # Option 2: Get the pool directly for advanced use
    pool = get_pool()
    with pool.connection() as conn:
        ...
"""
import os
import atexit
from pathlib import Path
from contextlib import contextmanager
from typing import Optional
from threading import Lock

import psycopg
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv

# Thread-safe singleton pattern
_pool: Optional[ConnectionPool] = None
_pool_lock = Lock()


def _get_db_url() -> str:
    """Get database URL from environment, loading .env if needed."""
    # Check if already loaded
    db_url = os.environ.get('NEON_DATABASE_URL')
    if db_url:
        return db_url

    # Try to load from .env
    version3_folder = Path(__file__).parent
    project_root = version3_folder.parent.parent
    load_dotenv(project_root / '.env')

    db_url = os.environ.get('NEON_DATABASE_URL')
    if not db_url:
        raise ValueError(
            "NEON_DATABASE_URL not set. "
            "Check your .env file or environment variables."
        )
    return db_url


def get_pool() -> ConnectionPool:
    """
    Get the shared connection pool (singleton).

    Returns:
        ConnectionPool: The shared psycopg connection pool

    Note:
        Pool is created on first call with the following settings:
        - min_size: 2 (keep at least 2 connections ready)
        - max_size: 20 (max 20 concurrent connections - handles agent parallel extractions)
        - timeout: 60 seconds (increased for busy periods)
        - keepalive settings for long-running connections
    """
    global _pool

    if _pool is not None:
        return _pool

    with _pool_lock:
        # Double-check after acquiring lock
        if _pool is not None:
            return _pool

        db_url = _get_db_url()

        _pool = ConnectionPool(
            conninfo=db_url,
            min_size=2,
            max_size=20,
            timeout=60,
            open=True,  # Explicitly open (addresses deprecation warning)
            kwargs={
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
            }
        )

        # Register cleanup on exit
        atexit.register(_cleanup_pool)

        return _pool


def _cleanup_pool():
    """Clean up the connection pool on exit."""
    global _pool
    if _pool is not None:
        try:
            _pool.close()
        except Exception:
            pass  # Ignore errors during cleanup
        _pool = None


@contextmanager
def get_connection():
    """
    Get a connection from the pool using a context manager.

    Usage:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()

    Note:
        Connection is automatically returned to pool when context exits.
        Uncommitted transactions are rolled back.
    """
    pool = get_pool()
    with pool.connection() as conn:
        yield conn


def get_db_connection():
    """
    Legacy compatibility function - returns a connection from the pool.

    DEPRECATED: Prefer using get_connection() context manager instead.

    Warning:
        When using this function directly, you MUST close the connection
        when done, or it will be leaked from the pool.

    Usage:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        finally:
            conn.close()  # Returns connection to pool
    """
    pool = get_pool()
    return pool.getconn()


def check_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                return result == (1,)
    except Exception:
        return False


def get_pool_stats() -> dict:
    """
    Get current pool statistics.

    Returns:
        dict: Pool statistics including:
            - size: Current number of connections in pool
            - min_size: Minimum pool size
            - max_size: Maximum pool size
            - idle: Number of idle connections
            - in_use: Number of connections currently in use
    """
    pool = get_pool()
    stats = pool.get_stats()
    return {
        "size": stats.get("pool_size", 0),
        "min_size": stats.get("pool_min", 2),
        "max_size": stats.get("pool_max", 20),
        "idle": stats.get("pool_available", 0),
        "in_use": stats.get("requests_waiting", 0),
    }


# ============================================================================
# For backward compatibility, also export these
# ============================================================================

# This allows existing code to do:
# from database import get_db_connection
# And it will work with the pool

__all__ = [
    'get_pool',
    'get_connection',
    'get_db_connection',  # Legacy
    'check_connection',
    'get_pool_stats',
]
