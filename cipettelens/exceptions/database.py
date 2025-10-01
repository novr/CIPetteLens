"""
Database related exceptions.
"""

from .base import CIPetteLensException


class DatabaseException(CIPetteLensException):
    """Base exception for database operations."""

    pass


class DatabaseConnectionError(DatabaseException):
    """Exception raised when database connection fails."""

    def __init__(self, message: str, db_path: str | None = None):
        super().__init__(message, "DATABASE_CONNECTION_ERROR")
        self.db_path = db_path
