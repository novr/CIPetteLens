"""
Database connection pool for performance optimization.
"""

import sqlite3
import threading
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from ..config import config


class DatabaseConnectionPool:
    """Thread-safe SQLite connection pool."""

    def __init__(self, db_path: str | None = None, max_connections: int = 10):
        """Initialize connection pool."""
        self.db_path = Path(db_path or config.DATABASE_PATH or "db/data.sqlite")
        self.max_connections = max_connections
        self._pool: list[sqlite3.Connection] = []
        self._lock = threading.Lock()
        self._created_connections = 0

        # Ensure database directory exists
        self.db_path.parent.mkdir(exist_ok=True)

        # Initialize database schema
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database with optimized schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create metrics table with optimized structure
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repository TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create optimized indexes
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_repository_timestamp
                ON metrics(repository, timestamp DESC)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_metric_name_timestamp
                ON metrics(metric_name, timestamp DESC)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_repository_metric_timestamp
                ON metrics(repository, metric_name, timestamp DESC)
            """
            )

            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")

            # Optimize SQLite settings
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA temp_store=MEMORY")

            conn.commit()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection from the pool."""
        conn = None
        try:
            with self._lock:
                if self._pool:
                    conn = self._pool.pop()
                elif self._created_connections < self.max_connections:
                    conn = sqlite3.connect(
                        str(self.db_path), timeout=30.0, check_same_thread=False
                    )
                    conn.row_factory = sqlite3.Row
                    self._created_connections += 1
                else:
                    # Wait for a connection to become available
                    conn = sqlite3.connect(
                        str(self.db_path), timeout=30.0, check_same_thread=False
                    )
                    conn.row_factory = sqlite3.Row

            yield conn
        finally:
            if conn:
                with self._lock:
                    if len(self._pool) < self.max_connections:
                        self._pool.append(conn)
                    else:
                        conn.close()
                        self._created_connections -= 1

    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self._lock:
            for conn in self._pool:
                conn.close()
            self._pool.clear()
            self._created_connections = 0


# Global connection pool instance
_connection_pool: DatabaseConnectionPool | None = None
_connection_pool_lock = threading.Lock()


def get_connection_pool() -> DatabaseConnectionPool:
    """Get the global connection pool instance."""
    global _connection_pool
    with _connection_pool_lock:
        if _connection_pool is None:
            _connection_pool = DatabaseConnectionPool()
        return _connection_pool


def close_connection_pool() -> None:
    """Close the global connection pool."""
    global _connection_pool
    with _connection_pool_lock:
        if _connection_pool:
            _connection_pool.close_all()
            _connection_pool = None
